"""Tests for stale-collector TTL purge (Phase 08, Plan 01)."""
from __future__ import annotations

import time
from importlib import reload

import pytest
import structlog.testing

from opamp_server.registry import AgentRecord, AgentRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record(
    uid: bytes = b"\x01" * 16,
    last_seen: int | None = None,
    push_state: str = "IDLE",
) -> AgentRecord:
    """Return an AgentRecord with configurable last_seen and push_state."""
    if last_seen is None:
        last_seen = time.time_ns()
    return AgentRecord(
        instance_uid=uid,
        first_seen=last_seen,
        last_seen=last_seen,
        capabilities=0x805,
        sequence_num=1,
        push_state=push_state,
    )


async def _setup_db(monkeypatch, tmp_path):
    """Isolate SQLite to tmp_path, reload config, and initialise DB."""
    monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test.db"))
    import opamp_server.config as cfg_module
    reload(cfg_module)
    from opamp_server import persistence
    await persistence.init_db()
    return persistence


# ---------------------------------------------------------------------------
# TestSettings
# ---------------------------------------------------------------------------

class TestSettings:
    def test_default_ttl_hours(self, monkeypatch):
        """TTL-02: collector_ttl_hours defaults to 24."""
        monkeypatch.delenv("OPAMP_COLLECTOR_TTL_HOURS", raising=False)
        import opamp_server.config as cfg_module
        reload(cfg_module)
        assert cfg_module.settings.collector_ttl_hours == 24

    def test_default_purge_interval(self, monkeypatch):
        """TTL-02: purge_interval_hours defaults to 1."""
        monkeypatch.delenv("OPAMP_PURGE_INTERVAL_HOURS", raising=False)
        import opamp_server.config as cfg_module
        reload(cfg_module)
        assert cfg_module.settings.purge_interval_hours == 1

    def test_custom_ttl_hours(self, monkeypatch):
        """TTL-02: OPAMP_COLLECTOR_TTL_HOURS=48 overrides default."""
        monkeypatch.setenv("OPAMP_COLLECTOR_TTL_HOURS", "48")
        import opamp_server.config as cfg_module
        reload(cfg_module)
        assert cfg_module.settings.collector_ttl_hours == 48


# ---------------------------------------------------------------------------
# TestRegistryRemove
# ---------------------------------------------------------------------------

class TestRegistryRemove:
    async def test_registry_remove_deletes_agent(self):
        """TTL-01: registry.remove(uid) makes registry.get(uid) return None."""
        registry = AgentRegistry()
        uid = b"\x01" * 16
        record = _make_record(uid=uid)
        await registry.upsert(record)
        assert await registry.get(uid) is not None

        await registry.remove(uid)
        assert await registry.get(uid) is None

    async def test_registry_remove_noop_for_unknown(self):
        """TTL-01: registry.remove on unknown uid does not raise."""
        registry = AgentRegistry()
        # Should not raise any exception
        await registry.remove(b"\xff" * 16)


# ---------------------------------------------------------------------------
# TestPurgeAgent
# ---------------------------------------------------------------------------

class TestPurgeAgent:
    async def test_purge_deletes_child_tables(self, monkeypatch, tmp_path):
        """TTL-01: purge_agent deletes rows from all child tables and agents."""
        import aiosqlite
        persistence = await _setup_db(monkeypatch, tmp_path)
        db_path = str(tmp_path / "test.db")

        uid = b"\x02" * 16

        # Insert agent row
        record = _make_record(uid=uid)
        await persistence.upsert_agent(record)

        # Insert child rows
        await persistence.store_health_snapshot(
            instance_uid=uid,
            healthy=True,
            status="ok",
            last_error=None,
            details={"healthy": True},
        )
        await persistence.store_effective_config(
            instance_uid=uid,
            config_hash="abc123",
            config_data={"collector.yaml": {"body": "receivers: {}", "content_type": "text/yaml"}},
        )
        await persistence.store_config_push(
            instance_uid=uid,
            config_hash="abc123",
            config_body="receivers: {}",
        )

        # Purge the agent
        await persistence.purge_agent(uid)

        uid_hex = uid.hex()
        async with aiosqlite.connect(db_path) as db:
            for table in ("agents", "health_snapshots", "effective_configs", "config_pushes"):
                async with db.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE instance_uid = ?",
                    (uid_hex,),
                ) as cursor:
                    row = await cursor.fetchone()
                    assert row[0] == 0, f"Expected 0 rows in {table} for purged agent, got {row[0]}"


# ---------------------------------------------------------------------------
# TestRunPurgeSweep
# ---------------------------------------------------------------------------

class TestRunPurgeSweep:
    async def test_stale_agent_purged(self, monkeypatch, tmp_path):
        """TTL-01: Agent with last_seen older than TTL is removed after sweep."""
        persistence = await _setup_db(monkeypatch, tmp_path)
        # Ensure default TTL is 24h
        monkeypatch.delenv("OPAMP_COLLECTOR_TTL_HOURS", raising=False)
        import opamp_server.config as cfg_module
        reload(cfg_module)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xaa" * 16
        # 25h ago in nanoseconds
        stale_ns = time.time_ns() - 25 * 3_600 * 1_000_000_000
        record = _make_record(uid=uid, last_seen=stale_ns)
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        purged = await run_purge_sweep(registry)

        assert purged == 1
        assert await registry.get(uid) is None

    async def test_fresh_agent_not_purged(self, monkeypatch, tmp_path):
        """TTL-01: Agent with last_seen within TTL remains after sweep."""
        persistence = await _setup_db(monkeypatch, tmp_path)
        monkeypatch.delenv("OPAMP_COLLECTOR_TTL_HOURS", raising=False)
        import opamp_server.config as cfg_module
        reload(cfg_module)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xbb" * 16
        record = _make_record(uid=uid, last_seen=time.time_ns())
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        purged = await run_purge_sweep(registry)

        assert purged == 0
        assert await registry.get(uid) is not None

    async def test_active_push_pending_skipped(self, monkeypatch, tmp_path):
        """TTL-04: PUSH_PENDING agent is NOT purged even if stale."""
        persistence = await _setup_db(monkeypatch, tmp_path)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xcc" * 16
        stale_ns = time.time_ns() - 25 * 3_600 * 1_000_000_000
        record = _make_record(uid=uid, last_seen=stale_ns, push_state="PUSH_PENDING")
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        purged = await run_purge_sweep(registry)

        assert purged == 0
        assert await registry.get(uid) is not None

    async def test_active_push_applying_skipped(self, monkeypatch, tmp_path):
        """TTL-04: APPLYING agent is NOT purged even if stale."""
        persistence = await _setup_db(monkeypatch, tmp_path)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xdd" * 16
        stale_ns = time.time_ns() - 25 * 3_600 * 1_000_000_000
        record = _make_record(uid=uid, last_seen=stale_ns, push_state="APPLYING")
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        purged = await run_purge_sweep(registry)

        assert purged == 0
        assert await registry.get(uid) is not None

    async def test_purge_log_entry(self, monkeypatch, tmp_path):
        """TTL-05: Each purged collector produces a structlog event 'collector_purged' with instance_uid hex."""
        persistence = await _setup_db(monkeypatch, tmp_path)
        monkeypatch.delenv("OPAMP_COLLECTOR_TTL_HOURS", raising=False)
        import opamp_server.config as cfg_module
        reload(cfg_module)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xee" * 16
        stale_ns = time.time_ns() - 25 * 3_600 * 1_000_000_000
        record = _make_record(uid=uid, last_seen=stale_ns)
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        with structlog.testing.capture_logs() as cap:
            await run_purge_sweep(registry)

        purge_events = [e for e in cap if e.get("event") == "collector_purged"]
        assert len(purge_events) == 1
        assert purge_events[0]["instance_uid"] == uid.hex()

    async def test_ttl_config_respected(self, monkeypatch, tmp_path):
        """TTL-02: OPAMP_COLLECTOR_TTL_HOURS=48 means 25h stale agent is NOT purged."""
        persistence = await _setup_db(monkeypatch, tmp_path)
        monkeypatch.setenv("OPAMP_COLLECTOR_TTL_HOURS", "48")
        import opamp_server.config as cfg_module
        reload(cfg_module)

        from opamp_server.purger import run_purge_sweep

        registry = AgentRegistry()
        uid = b"\xff" * 16
        # 25h stale — within 48h TTL so should NOT be purged
        stale_25h_ns = time.time_ns() - 25 * 3_600 * 1_000_000_000
        record = _make_record(uid=uid, last_seen=stale_25h_ns)
        await registry.upsert(record)
        await persistence.upsert_agent(record)

        purged = await run_purge_sweep(registry)

        assert purged == 0
        assert await registry.get(uid) is not None
