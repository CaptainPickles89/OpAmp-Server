"""Unit tests for SQLite persistence layer."""
from __future__ import annotations

import time
import pytest
from opamp_server.registry import AgentRecord


class TestInitDb:
    async def test_creates_agents_table(self, tmp_path, monkeypatch):
        """REGST-02: init_db creates agents table with WAL mode."""
        import aiosqlite
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        await persistence.init_db()

        async with aiosqlite.connect(str(tmp_path / "test.db")) as db:
            # Verify WAL mode
            async with db.execute("PRAGMA journal_mode") as cursor:
                row = await cursor.fetchone()
                assert row[0] == "wal"
            # Verify tables exist
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
            ) as cursor:
                assert await cursor.fetchone() is not None

    async def test_creates_health_snapshots_table(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        await persistence.init_db()

        import aiosqlite
        async with aiosqlite.connect(str(tmp_path / "test.db")) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='health_snapshots'"
            ) as cursor:
                assert await cursor.fetchone() is not None


class TestUpsertAndLoad:
    async def test_upsert_and_load_round_trip(self, tmp_path, monkeypatch):
        """REGST-03: upsert_agent writes, load_all_agents reads back same record."""
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence

        await persistence.init_db()
        now = time.time_ns()
        record = AgentRecord(
            instance_uid=b"\x01" * 16,
            first_seen=now,
            last_seen=now,
            capabilities=0x805,
            sequence_num=42,
        )
        await persistence.upsert_agent(record)
        loaded = await persistence.load_all_agents()
        assert len(loaded) == 1
        assert loaded[0].instance_uid == b"\x01" * 16
        assert loaded[0].sequence_num == 42


class TestHealthSnapshotRetention:
    async def test_retention_enforced(self, tmp_path, monkeypatch):
        """REGST-04: health_snapshot_retention limits rows per agent."""
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        monkeypatch.setenv("OPAMP_HEALTH_SNAPSHOT_RETENTION", "3")
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        import aiosqlite

        await persistence.init_db()
        uid = b"\x01" * 16
        # Insert agent first
        now = time.time_ns()
        await persistence.upsert_agent(AgentRecord(
            instance_uid=uid, first_seen=now, last_seen=now,
            capabilities=0, sequence_num=0
        ))
        # Store 5 snapshots (retention=3)
        for i in range(5):
            await persistence.store_health_snapshot(
                instance_uid=uid, healthy=True, status="ok",
                last_error=None, details=None
            )

        async with aiosqlite.connect(str(tmp_path / "test.db")) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM health_snapshots WHERE instance_uid = ?",
                (uid.hex(),)
            ) as cursor:
                count = (await cursor.fetchone())[0]
        assert count <= 3
