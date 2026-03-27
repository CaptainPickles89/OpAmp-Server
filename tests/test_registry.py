"""Unit tests for in-memory AgentRegistry."""
from __future__ import annotations

import time
import pytest
from opamp_server.registry import AgentRecord, AgentRegistry

TEST_UID = b"\x01" * 16
TEST_UID2 = b"\x02" * 16


def make_record(uid: bytes = TEST_UID, seq: int = 1) -> AgentRecord:
    now = time.time_ns()
    return AgentRecord(
        instance_uid=uid,
        first_seen=now,
        last_seen=now,
        capabilities=0x805,
        sequence_num=seq,
    )


class TestAgentRegistry:
    async def test_get_returns_none_for_unknown_agent(self):
        """REGST-01: Unknown agent returns None."""
        registry = AgentRegistry()
        result = await registry.get(TEST_UID)
        assert result is None

    async def test_upsert_and_get(self):
        """REGST-01: Upsert stores record, get retrieves it."""
        registry = AgentRegistry()
        record = make_record()
        await registry.upsert(record)
        result = await registry.get(TEST_UID)
        assert result is not None
        assert result.instance_uid == TEST_UID
        assert result.sequence_num == 1

    async def test_upsert_updates_existing_record(self):
        registry = AgentRegistry()
        await registry.upsert(make_record(seq=1))
        await registry.upsert(make_record(seq=2))
        result = await registry.get(TEST_UID)
        assert result.sequence_num == 2

    async def test_hydrate_loads_all_records(self):
        """REGST-03: hydrate() restores all records from persistence."""
        registry = AgentRegistry()
        records = [make_record(TEST_UID, seq=5), make_record(TEST_UID2, seq=10)]
        await registry.hydrate(records)
        assert await registry.count() == 2
        result = await registry.get(TEST_UID)
        assert result.sequence_num == 5

    async def test_all_returns_all_records(self):
        registry = AgentRegistry()
        await registry.upsert(make_record(TEST_UID))
        await registry.upsert(make_record(TEST_UID2))
        all_records = await registry.all()
        assert len(all_records) == 2
