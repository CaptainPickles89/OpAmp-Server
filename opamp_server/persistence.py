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

from opamp_server.config import settings
from opamp_server.registry import AgentRecord

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


async def init_db() -> None:
    """Initialize the SQLite database — create tables and enable WAL mode.

    Must be called once at server startup before any other persistence calls.
    """
    db_path = Path(settings.db_path)
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
        await db.commit()

    log.info("db_initialized", db_path=str(db_path))


async def load_all_agents() -> list[AgentRecord]:
    """Load all agent records from SQLite for registry hydration.

    Returns:
        List of AgentRecord instances, one per row in agents table.
    """
    db_path = Path(settings.db_path)
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
    async with aiosqlite.connect(settings.db_path) as db:
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

    Keeps only the most recent `settings.health_snapshot_retention` rows per agent.

    Args:
        instance_uid: Agent's 16-byte UID.
        healthy: Whether the agent reported healthy.
        status: Status string from ComponentHealth.status.
        last_error: Error string from ComponentHealth.last_error.
        details: Full ComponentHealth as dict (for JSON serialization).
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    retention = settings.health_snapshot_retention

    async with aiosqlite.connect(settings.db_path) as db:
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

    Keeps only the most recent `settings.effective_config_retention` rows per agent.

    Args:
        instance_uid: Agent's 16-byte UID.
        config_hash: Hash of config content for deduplication.
        config_data: Full EffectiveConfig as dict (for JSON serialization).
    """
    uid_hex = instance_uid.hex()
    now = time.time_ns()
    retention = settings.effective_config_retention

    async with aiosqlite.connect(settings.db_path) as db:
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
    async with aiosqlite.connect(settings.db_path) as db:
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
    async with aiosqlite.connect(settings.db_path) as db:
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
    async with aiosqlite.connect(settings.db_path) as db:
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


async def load_all_push_states() -> list[dict]:
    """Load in-flight push states for registry hydration on server startup.

    Only returns rows where push_state is PUSH_PENDING or APPLYING.
    APPLYING rows are treated as PUSH_PENDING on hydration (re-deliver after restart).

    Returns:
        List of dicts with keys: 'instance_uid' (hex str), 'config_hash' (hex str),
        'config_body' (YAML str), 'push_state' (str).
    """
    db_path = Path(settings.db_path)
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
