"""SQLite persistence layer for the agent registry.

Uses aiosqlite for non-blocking async I/O compatible with FastAPI.
WAL mode is enabled at startup for concurrent read safety.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog

import opamp_server.config as _config
from opamp_server.registry import AgentRecord


def _settings():
    """Return the current settings object, respecting any module reloads."""
    return _config.settings

log = structlog.get_logger(__name__)

_CREATE_AGENTS = """
CREATE TABLE IF NOT EXISTS agents (
    instance_uid TEXT PRIMARY KEY,
    first_seen   INTEGER NOT NULL,
    last_seen    INTEGER NOT NULL,
    capabilities INTEGER NOT NULL DEFAULT 0,
    sequence_num INTEGER NOT NULL DEFAULT 0,
    description_json TEXT,
    updated_at   INTEGER NOT NULL
);
"""

_CREATE_HEALTH_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS health_snapshots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_uid TEXT NOT NULL REFERENCES agents(instance_uid),
    recorded_at  INTEGER NOT NULL,
    healthy      INTEGER NOT NULL,
    status       TEXT,
    last_error   TEXT,
    details_json TEXT
);
"""

_CREATE_HEALTH_INDEX = """
CREATE INDEX IF NOT EXISTS idx_health_agent
    ON health_snapshots(instance_uid, recorded_at DESC);
"""

_CREATE_EFFECTIVE_CONFIGS = """
CREATE TABLE IF NOT EXISTS effective_configs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_uid TEXT NOT NULL REFERENCES agents(instance_uid),
    recorded_at  INTEGER NOT NULL,
    config_hash  TEXT NOT NULL,
    config_json  TEXT NOT NULL
);
"""

_CREATE_CONFIG_INDEX = """
CREATE INDEX IF NOT EXISTS idx_config_agent
    ON effective_configs(instance_uid, recorded_at DESC);
"""

_CREATE_CONFIG_PUSHES = """
CREATE TABLE IF NOT EXISTS config_pushes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_uid    TEXT NOT NULL REFERENCES agents(instance_uid),
    config_hash     TEXT NOT NULL,
    config_body     TEXT NOT NULL,
    push_state      TEXT NOT NULL DEFAULT 'IDLE',
    pushed_at       INTEGER NOT NULL,
    confirmed_at    INTEGER,
    failed_at       INTEGER,
    error_message   TEXT,
    is_rollback     INTEGER NOT NULL DEFAULT 0
);
"""

_CREATE_PUSH_INDEX = """
CREATE INDEX IF NOT EXISTS idx_push_agent
    ON config_pushes(instance_uid, pushed_at DESC);
"""

_CREATE_RESOURCE_ATTRS = """
CREATE TABLE IF NOT EXISTS agent_resource_attrs (
    instance_uid TEXT NOT NULL REFERENCES agents(instance_uid),
    key          TEXT NOT NULL,
    value        TEXT NOT NULL,
    updated_at   INTEGER NOT NULL,
    PRIMARY KEY (instance_uid, key)
);
"""

_CREATE_RESOURCE_ATTR_KEY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_resource_attr_key
    ON agent_resource_attrs(key);
"""


async def init_db() -> None:
    """Initialize the SQLite database — create tables and enable WAL mode.

    Must be called once at server startup before any other persistence calls.
    """
    db_path = Path(_settings().db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute(_CREATE_AGENTS)
        await db.execute(_CREATE_HEALTH_SNAPSHOTS)
        await db.execute(_CREATE_HEALTH_INDEX)
        await db.execute(_CREATE_EFFECTIVE_CONFIGS)
        await db.execute(_CREATE_CONFIG_INDEX)
        await db.execute(_CREATE_CONFIG_PUSHES)
        await db.execute(_CREATE_PUSH_INDEX)
        await db.execute(_CREATE_RESOURCE_ATTRS)
        await db.execute(_CREATE_RESOURCE_ATTR_KEY_INDEX)
        await db.commit()

    log.info("db_initialized", db_path=str(db_path))


async def load_all_agents() -> list[AgentRecord]:
    """Load all agent records from SQLite for registry hydration.

    Returns:
        List of AgentRecord instances, one per row in agents table.
    """
    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return []

    records: list[AgentRecord] = []
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT instance_uid, first_seen, last_seen, capabilities, sequence_num, description_json "
            "FROM agents"
        ) as cursor:
            async for row in cursor:
                records.append(
                    AgentRecord(
                        instance_uid=bytes.fromhex(row["instance_uid"]),
                        first_seen=row["first_seen"],
                        last_seen=row["last_seen"],
                        capabilities=row["capabilities"],
                        sequence_num=row["sequence_num"],
                        description=json.loads(row["description_json"])
                        if row["description_json"]
                        else None,
                    )
                )
    log.info("registry_hydrated", agent_count=len(records))
    return records


async def upsert_agent(record: AgentRecord) -> None:
    """Insert or update an agent row in SQLite.

    Args:
        record: AgentRecord with current state to persist.
    """
    uid_hex = record.instance_uid.hex()
    now = time.time_ns()
    async with aiosqlite.connect(_settings().db_path) as db:
        await db.execute(
            """
            INSERT INTO agents (instance_uid, first_seen, last_seen, capabilities, sequence_num, description_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(instance_uid) DO UPDATE SET
                last_seen = excluded.last_seen,
                capabilities = excluded.capabilities,
                sequence_num = excluded.sequence_num,
                description_json = excluded.description_json,
                updated_at = excluded.updated_at
            """,
            (
                uid_hex,
                record.first_seen,
                record.last_seen,
                record.capabilities,
                record.sequence_num,
                json.dumps(record.description) if record.description else None,
                now,
            ),
        )
        await db.commit()


async def store_health_snapshot(
    instance_uid: bytes,
    healthy: bool,
    status: Optional[str],
    last_error: Optional[str],
    details: Optional[dict],
) -> None:
    """Store a ComponentHealth snapshot and enforce retention limit.

    Keeps only the most recent ``settings.health_snapshot_retention`` rows per agent.

    Args:
        instance_uid: Agent's 16-byte UID.
        healthy: Whether the agent reported healthy.
        status: Status string from ComponentHealth.status.
        last_error: Error string from ComponentHealth.last_error.
        details: Full ComponentHealth as dict (for JSON serialization).
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    retention = _settings().health_snapshot_retention

    async with aiosqlite.connect(_settings().db_path) as db:
        await db.execute(
            """
            INSERT INTO health_snapshots (instance_uid, recorded_at, healthy, status, last_error, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (uid_hex, now, 1 if healthy else 0, status, last_error,
             json.dumps(details) if details else None),
        )
        # Enforce retention: delete oldest rows beyond limit
        await db.execute(
            """
            DELETE FROM health_snapshots
            WHERE instance_uid = ? AND id NOT IN (
                SELECT id FROM health_snapshots
                WHERE instance_uid = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            )
            """,
            (uid_hex, uid_hex, retention),
        )
        await db.commit()


async def store_effective_config(
    instance_uid: bytes,
    config_hash: str,
    config_data: dict,
) -> None:
    """Store an effective config snapshot and enforce retention limit.

    Keeps only the most recent ``settings.effective_config_retention`` rows per agent.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hash of config content for deduplication.
        config_data: Full EffectiveConfig as dict (for JSON serialization).
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    retention = _settings().effective_config_retention

    async with aiosqlite.connect(_settings().db_path) as db:
        await db.execute(
            """
            INSERT INTO effective_configs (instance_uid, recorded_at, config_hash, config_json)
            VALUES (?, ?, ?, ?)
            """,
            (uid_hex, now, config_hash, json.dumps(config_data)),
        )
        await db.execute(
            """
            DELETE FROM effective_configs
            WHERE instance_uid = ? AND id NOT IN (
                SELECT id FROM effective_configs
                WHERE instance_uid = ?
                ORDER BY recorded_at DESC
                LIMIT ?
            )
            """,
            (uid_hex, uid_hex, retention),
        )
        await db.commit()


async def store_config_push(
    instance_uid: bytes,
    config_hash: str,
    config_body: str,
    is_rollback: bool = False,
) -> int:
    """Insert a new config push row in PUSH_PENDING state.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hex SHA-256 string (64 chars).
        config_body: Raw YAML string to push.
        is_rollback: True if this push is a server-initiated rollback.

    Returns:
        Integer id of the newly inserted row.
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    async with aiosqlite.connect(_settings().db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO config_pushes
                (instance_uid, config_hash, config_body, push_state, pushed_at, is_rollback)
            VALUES (?, ?, ?, 'PUSH_PENDING', ?, ?)
            """,
            (uid_hex, config_hash, config_body, now, 1 if is_rollback else 0),
        )
        await db.commit()
        return cursor.lastrowid


async def update_push_state(
    instance_uid: bytes,
    config_hash: str,
    new_state: str,
    confirmed_at: Optional[int] = None,
    failed_at: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    """Update push_state for the most recent push row matching instance_uid + config_hash.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hex SHA-256 string identifying which push row to update.
        new_state: Target state: APPLYING / APPLIED / FAILED / IDLE.
        confirmed_at: Unix ns timestamp; set when transitioning to APPLIED.
        failed_at: Unix ns timestamp; set when transitioning to FAILED.
        error_message: Error detail from RemoteConfigStatus; set on FAILED.
    """
    uid_hex = instance_uid.hex()
    async with aiosqlite.connect(_settings().db_path) as db:
        await db.execute(
            """
            UPDATE config_pushes
            SET push_state = ?,
                confirmed_at = COALESCE(?, confirmed_at),
                failed_at = COALESCE(?, failed_at),
                error_message = COALESCE(?, error_message)
            WHERE instance_uid = ?
              AND config_hash = ?
              AND id = (
                  SELECT id FROM config_pushes
                  WHERE instance_uid = ? AND config_hash = ?
                  ORDER BY pushed_at DESC
                  LIMIT 1
              )
            """,
            (new_state, confirmed_at, failed_at, error_message, uid_hex, config_hash, uid_hex, config_hash),
        )
        await db.commit()


async def record_push_applied(instance_uid: bytes, config_hash: str) -> None:
    """Mark the matching push row as APPLIED with confirmed_at timestamp.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hex SHA-256 of the config that was applied.
    """
    await update_push_state(
        instance_uid=instance_uid,
        config_hash=config_hash,
        new_state="APPLIED",
        confirmed_at=time.time_ns(),
    )
    log.info("push_state_applied", instance_uid=instance_uid.hex(), config_hash=config_hash[:16])


async def record_push_failed(
    instance_uid: bytes,
    config_hash: str,
    error_message: Optional[str],
) -> None:
    """Mark the matching push row as FAILED with failed_at timestamp.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hex SHA-256 of the config that failed.
        error_message: Error detail from RemoteConfigStatus.error_message.
    """
    await update_push_state(
        instance_uid=instance_uid,
        config_hash=config_hash,
        new_state="FAILED",
        failed_at=time.time_ns(),
        error_message=error_message,
    )
    log.warning(
        "push_state_failed",
        instance_uid=instance_uid.hex(),
        config_hash=config_hash[:16],
        error=error_message,
    )


async def get_previous_confirmed_config(instance_uid: bytes) -> Optional[dict]:
    """Get the most recently APPLIED config for rollback.

    Returns the last config that successfully reached APPLIED state,
    which is the safe target for server-initiated rollback.

    Args:
        instance_uid: Agent's 16-byte UID.

    Returns:
        Dict with keys 'config_hash' (hex str) and 'config_body' (YAML str),
        or None if no confirmed config exists for this agent.
    """
    uid_hex = instance_uid.hex()
    async with aiosqlite.connect(_settings().db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT config_hash, config_body
            FROM config_pushes
            WHERE instance_uid = ? AND push_state = 'APPLIED'
            ORDER BY confirmed_at DESC
            LIMIT 1
            """,
            (uid_hex,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {"config_hash": row["config_hash"], "config_body": row["config_body"]}


async def purge_agent(instance_uid: bytes) -> None:
    """Delete all rows for an agent across all tables, ordered by FK dependency.

    Delete order: health_snapshots -> effective_configs -> config_pushes -> agents.
    Phase 9 will add agent_resource_attrs before the agents delete.

    Args:
        instance_uid: Agent's raw 16-byte UID.
    """
    uid_hex = instance_uid.hex()
    async with aiosqlite.connect(_settings().db_path) as db:
        await db.execute("DELETE FROM health_snapshots WHERE instance_uid = ?", (uid_hex,))
        await db.execute("DELETE FROM effective_configs WHERE instance_uid = ?", (uid_hex,))
        await db.execute("DELETE FROM config_pushes WHERE instance_uid = ?", (uid_hex,))
        await db.execute("DELETE FROM agent_resource_attrs WHERE instance_uid = ?", (uid_hex,))
        await db.execute("DELETE FROM agents WHERE instance_uid = ?", (uid_hex,))
        await db.commit()


async def load_all_push_states() -> list[dict]:
    """Load in-flight push states for registry hydration on server startup.

    Only returns rows where push_state is PUSH_PENDING or APPLYING.
    APPLYING rows are treated as PUSH_PENDING on hydration (re-deliver after restart).

    Returns:
        List of dicts with keys: 'instance_uid' (hex str), 'config_hash' (hex str),
        'config_body' (YAML str), 'push_state' (str).
    """
    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return []

    rows: list[dict] = []
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT instance_uid, config_hash, config_body, push_state, is_rollback
            FROM config_pushes
            WHERE push_state IN ('PUSH_PENDING', 'APPLYING')
            ORDER BY pushed_at DESC
            """,
        ) as cursor:
            async for row in cursor:
                rows.append({
                    "instance_uid": row["instance_uid"],
                    "config_hash": row["config_hash"],
                    "config_body": row["config_body"],
                    # APPLYING -> PUSH_PENDING on restart (re-deliver)
                    "push_state": "PUSH_PENDING",
                    "is_rollback": bool(row["is_rollback"]),
                })
    log.info("push_states_hydrated", count=len(rows))
    return rows


async def get_latest_health_statuses(instance_uids: list[str]) -> dict[str, dict]:
    """Batch-fetch the most recent health snapshot per agent for the list endpoint.

    Uses a single SQL query with GROUP BY to avoid N+1 queries.
    Agents with no health snapshots are absent from the returned dict
    (caller interprets absence as 'unknown' health status).

    Args:
        instance_uids: List of hex UID strings (32-char hex, no dashes).

    Returns:
        Dict mapping hex UID string -> {'healthy': bool, 'status': str|None, 'last_error': str|None}.
        Empty dict if instance_uids is empty or no snapshots exist.
    """
    if not instance_uids:
        return {}

    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return {}

    placeholders = ",".join("?" * len(instance_uids))
    result: dict[str, dict] = {}

    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"""
            SELECT h.instance_uid, h.healthy, h.status, h.last_error
            FROM health_snapshots h
            INNER JOIN (
                SELECT instance_uid, MAX(recorded_at) AS latest
                FROM health_snapshots
                WHERE instance_uid IN ({placeholders})
                GROUP BY instance_uid
            ) sub ON h.instance_uid = sub.instance_uid
                  AND h.recorded_at = sub.latest
            """,
            instance_uids,
        ) as cursor:
            async for row in cursor:
                result[row["instance_uid"]] = {
                    "healthy": bool(row["healthy"]),
                    "status": row["status"],
                    "last_error": row["last_error"],
                }

    return result


async def get_health_history(instance_uid: bytes, limit: int = 10) -> list[dict]:
    """Return the most recent N health snapshots for a single agent, newest first.

    Args:
        instance_uid: Agent's raw 16-byte instance_uid.
        limit: Maximum number of snapshots to return (default 10).

    Returns:
        List of dicts with keys: 'recorded_at' (int ns), 'healthy' (bool),
        'status' (str|None), 'last_error' (str|None).
        Empty list if agent has no snapshots or DB does not exist.
    """
    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return []

    uid_hex = instance_uid.hex()
    rows: list[dict] = []

    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT recorded_at, healthy, status, last_error
            FROM health_snapshots
            WHERE instance_uid = ?
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (uid_hex, limit),
        ) as cursor:
            async for row in cursor:
                rows.append({
                    "recorded_at": row["recorded_at"],
                    "healthy": bool(row["healthy"]),
                    "status": row["status"],
                    "last_error": row["last_error"],
                })

    return rows


async def get_latest_effective_config(instance_uid: bytes) -> Optional[dict]:
    """Return the most recent effective config snapshot for a single agent.

    Args:
        instance_uid: Agent's raw 16-byte instance_uid.

    Returns:
        Dict with keys: 'recorded_at' (int ns), 'config_hash' (str), 'config_json' (dict).
        None if agent has no effective config records or DB does not exist.
    """
    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return None

    uid_hex = instance_uid.hex()

    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT recorded_at, config_hash, config_json
            FROM effective_configs
            WHERE instance_uid = ?
            ORDER BY recorded_at DESC
            LIMIT 1
            """,
            (uid_hex,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "recorded_at": row["recorded_at"],
                "config_hash": row["config_hash"],
                "config_json": json.loads(row["config_json"]),
            }


async def upsert_resource_attrs(instance_uid: bytes, attrs: dict[str, str]) -> None:
    """Insert or update resource attribute key/value rows for an agent.

    Uses ON CONFLICT upsert so repeated calls for the same key overwrite the value.

    Args:
        instance_uid: Agent's raw 16-byte UID.
        attrs: Mapping of attribute key to string value.
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    async with aiosqlite.connect(_settings().db_path) as db:
        for key, value in attrs.items():
            await db.execute(
                """
                INSERT INTO agent_resource_attrs (instance_uid, key, value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(instance_uid, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (uid_hex, key, value, now),
            )
        await db.commit()


async def get_resource_attrs_for_agents(
    instance_uids: list[str],
) -> dict[str, dict[str, str]]:
    """Batch-fetch resource attributes for a list of agents.

    Args:
        instance_uids: List of hex UID strings (32-char hex, no dashes).

    Returns:
        Dict mapping hex UID string -> {key: value} attribute dict.
        Empty dict if instance_uids is empty or no attributes exist.
    """
    if not instance_uids:
        return {}

    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return {}

    placeholders = ",".join("?" * len(instance_uids))
    result: dict[str, dict[str, str]] = {}

    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT instance_uid, key, value FROM agent_resource_attrs "
            f"WHERE instance_uid IN ({placeholders})",
            instance_uids,
        ) as cursor:
            async for row in cursor:
                uid = row["instance_uid"]
                if uid not in result:
                    result[uid] = {}
                result[uid][row["key"]] = row["value"]

    return result


async def get_all_resource_attr_keys() -> list[str]:
    """Return all distinct resource attribute keys stored across all agents, sorted.

    Returns:
        Sorted list of unique key strings.
        Empty list if no attributes exist or DB does not exist.
    """
    db_path = Path(_settings().db_path)
    if not db_path.exists():
        return []

    keys: list[str] = []

    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT DISTINCT key FROM agent_resource_attrs ORDER BY key"
        ) as cursor:
            async for row in cursor:
                keys.append(row[0])

    return keys
