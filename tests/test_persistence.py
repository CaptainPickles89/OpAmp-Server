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


# ---------------------------------------------------------------------------
# Phase 9 stubs — resource attribute persistence (COLS-01, COLS-02, COLS-03)
# ---------------------------------------------------------------------------


class TestResourceAttrs:
    async def test_upsert_resource_attrs_inserts_rows(self, tmp_path, monkeypatch):
        """COLS-01: upsert_resource_attrs writes key/value rows to agent_resource_attrs."""
        import time
        import aiosqlite
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        from opamp_server.registry import AgentRecord

        await persistence.init_db()
        uid = b"\x01" * 16
        now = time.time_ns()
        await persistence.upsert_agent(AgentRecord(
            instance_uid=uid, first_seen=now, last_seen=now,
            capabilities=0, sequence_num=0,
        ))
        await persistence.upsert_resource_attrs(uid, {"host.name": "web-01", "os.type": "linux"})

        async with aiosqlite.connect(str(tmp_path / "test.db")) as db:
            async with db.execute(
                "SELECT key, value FROM agent_resource_attrs WHERE instance_uid = ? ORDER BY key",
                (uid.hex(),),
            ) as cursor:
                rows = await cursor.fetchall()
        assert len(rows) == 2
        assert rows[0] == ("host.name", "web-01")
        assert rows[1] == ("os.type", "linux")

    async def test_upsert_resource_attrs_updates_existing_key(self, tmp_path, monkeypatch):
        """COLS-01: upsert_resource_attrs overwrites existing key with new value."""
        import time
        import aiosqlite
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        from opamp_server.registry import AgentRecord

        await persistence.init_db()
        uid = b"\x01" * 16
        now = time.time_ns()
        await persistence.upsert_agent(AgentRecord(
            instance_uid=uid, first_seen=now, last_seen=now,
            capabilities=0, sequence_num=0,
        ))
        await persistence.upsert_resource_attrs(uid, {"host.name": "web-01"})
        await persistence.upsert_resource_attrs(uid, {"host.name": "web-02"})

        async with aiosqlite.connect(str(tmp_path / "test.db")) as db:
            async with db.execute(
                "SELECT key, value FROM agent_resource_attrs WHERE instance_uid = ? AND key = 'host.name'",
                (uid.hex(),),
            ) as cursor:
                rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0] == ("host.name", "web-02")

    async def test_get_all_resource_attr_keys_returns_distinct_keys(self, tmp_path, monkeypatch):
        """COLS-03: get_all_resource_attr_keys returns sorted unique keys across all agents."""
        import time
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        from opamp_server.registry import AgentRecord

        await persistence.init_db()
        now = time.time_ns()
        uid1 = b"\x01" * 16
        uid2 = b"\x02" * 16
        for uid in (uid1, uid2):
            await persistence.upsert_agent(AgentRecord(
                instance_uid=uid, first_seen=now, last_seen=now,
                capabilities=0, sequence_num=0,
            ))
        await persistence.upsert_resource_attrs(uid1, {"host.name": "web-01", "os.type": "linux"})
        await persistence.upsert_resource_attrs(uid2, {"host.name": "web-02", "env": "prod"})

        keys = await persistence.get_all_resource_attr_keys()
        assert keys == ["env", "host.name", "os.type"]

    async def test_get_all_resource_attr_keys_empty_db(self, tmp_path, monkeypatch):
        """COLS-03: get_all_resource_attr_keys returns [] when no attrs stored."""
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence

        await persistence.init_db()
        keys = await persistence.get_all_resource_attr_keys()
        assert keys == []

    async def test_get_resource_attrs_for_agents_batch(self, tmp_path, monkeypatch):
        """COLS-02: get_resource_attrs_for_agents returns dict mapping hex uid to attrs dict."""
        import time
        monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
        from importlib import reload
        import opamp_server.config as cfg
        reload(cfg)
        from opamp_server import persistence
        from opamp_server.registry import AgentRecord

        await persistence.init_db()
        now = time.time_ns()
        uid1 = b"\x01" * 16
        uid2 = b"\x02" * 16
        for uid in (uid1, uid2):
            await persistence.upsert_agent(AgentRecord(
                instance_uid=uid, first_seen=now, last_seen=now,
                capabilities=0, sequence_num=0,
            ))
        await persistence.upsert_resource_attrs(uid1, {"host.name": "web-01", "os.type": "linux"})
        await persistence.upsert_resource_attrs(uid2, {"host.name": "web-02"})

        result = await persistence.get_resource_attrs_for_agents([uid1.hex(), uid2.hex()])
        assert result[uid1.hex()] == {"host.name": "web-01", "os.type": "linux"}
        assert result[uid2.hex()] == {"host.name": "web-02"}
