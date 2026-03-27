"""Shared test fixtures for the opamp_server test suite."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import opamp_pb2 as opamp


@pytest.fixture
def valid_agent_uid() -> bytes:
    """Return a fixed 16-byte agent instance_uid for testing."""
    # Fixed test UID — not a real UUID v7, but valid 16 bytes
    return b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"


@pytest.fixture
def valid_agent_to_server_bytes(valid_agent_uid: bytes) -> bytes:
    """Return serialized AgentToServer protobuf bytes for a healthy agent."""
    msg = opamp.AgentToServer()
    msg.instance_uid = valid_agent_uid
    msg.sequence_num = 1
    # ReportsStatus (0x01) | ReportsEffectiveConfig (0x04) | ReportsHealth (0x800)
    msg.capabilities = 0x805
    return msg.SerializeToString()


@pytest.fixture
def agent_to_server_with_gap(valid_agent_uid: bytes) -> bytes:
    """Return serialized AgentToServer with a sequence gap (seq=5 after seq=1)."""
    msg = opamp.AgentToServer()
    msg.instance_uid = valid_agent_uid
    msg.sequence_num = 5  # gap — server last saw 1, expects 2
    msg.capabilities = 0x805
    return msg.SerializeToString()


@pytest_asyncio.fixture
async def async_client(monkeypatch, tmp_path):
    """Async HTTP client connected to the FastAPI test app.

    Uses a temporary directory for SQLite to isolate each test.
    """
    monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test_registry.db"))
    monkeypatch.setenv("OPAMP_RATE_LIMIT", "1000/minute")  # disable rate limit in tests

    # Import after env vars are set so Settings picks them up
    from importlib import reload
    import opamp_server.config as cfg_module
    reload(cfg_module)
    from opamp_server.main import create_app
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def in_memory_db_path(tmp_path) -> str:
    """Return a path for an isolated test SQLite database."""
    return str(tmp_path / "test.db")
