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
