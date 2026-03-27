"""Shared test fixtures for the opamp_server test suite."""
from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock

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
    Manually triggers app startup so init_db() runs before any request.
    """
    monkeypatch.setenv("OPAMP_DB_PATH", str(tmp_path / "test_registry.db"))
    monkeypatch.setenv("OPAMP_RATE_LIMIT", "1000/minute")  # disable rate limit in tests

    # Import after env vars are set so Settings picks them up
    from importlib import reload
    import opamp_server.config as cfg_module
    reload(cfg_module)
    from opamp_server.main import create_app
    _app = create_app()

    # Manually trigger startup lifecycle so init_db() and hydration run before requests
    for handler in _app.router.on_startup:
        await handler()

    async with AsyncClient(
        transport=ASGITransport(app=_app), base_url="http://test"
    ) as client:
        # Make the app accessible from the client for fixtures that need it
        client.app = _app  # type: ignore[attr-defined]
        yield client

    for handler in _app.router.on_shutdown:
        await handler()


@pytest.fixture
def in_memory_db_path(tmp_path) -> str:
    """Return a path for an isolated test SQLite database."""
    return str(tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Phase 2 fixtures — config push helpers
# ---------------------------------------------------------------------------

PHASE2_VALID_YAML = """\
receivers:
  otlp:
    protocols:
      http:
        endpoint: "0.0.0.0:4318"
exporters:
  debug: {}
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
"""

PHASE2_CONFIRMED_YAML = """\
receivers:
  otlp: {}
exporters:
  debug: {}
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
"""


@pytest.fixture
def config_body():
    """Valid YAML config body for use in push tests."""
    return PHASE2_VALID_YAML


@pytest_asyncio.fixture
async def registered_agent_uid(async_client):
    """Return a bytes UID for an agent that has been registered in the test registry.

    Depends on async_client to ensure app startup (init_db) has run before
    adding the agent record to the registry.
    """
    from opamp_server.registry import AgentRecord
    uid = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    record = AgentRecord(
        instance_uid=uid,
        first_seen=1_000_000_000,
        last_seen=1_000_000_000,
        capabilities=0x4807,  # ReportsStatus | AcceptsRemoteConfig | ReportsHealth | ...
        sequence_num=1,
    )
    await async_client.app.state.registry.upsert(record)
    return uid


@pytest.fixture
def opamp_agent_message():
    """Factory fixture: returns a function that builds AgentToServer messages."""

    def _build(
        uid: bytes,
        sequence_num: int = 1,
        remote_config_status_hash: bytes | None = None,
        remote_config_status_value: int | None = None,
        remote_config_error: str = "",
    ) -> opamp.AgentToServer:
        msg = opamp.AgentToServer()
        msg.instance_uid = uid
        msg.sequence_num = sequence_num
        msg.capabilities = 0x4807  # includes AcceptsRemoteConfig (0x02)
        if remote_config_status_hash is not None:
            msg.remote_config_status.last_remote_config_hash = remote_config_status_hash
            msg.remote_config_status.status = remote_config_status_value or 0
            if remote_config_error:
                msg.remote_config_status.error_message = remote_config_error
        return msg

    return _build


@pytest.fixture
def mock_registry():
    """AsyncMock registry with no agents registered."""
    registry = MagicMock()
    registry.get = AsyncMock(return_value=None)
    registry.upsert = AsyncMock()
    return registry


@pytest.fixture
def mock_registry_with_pending_push():
    """AsyncMock registry with an agent that has PUSH_PENDING state."""
    from opamp_server.registry import AgentRecord
    uid = b"\x01" * 16
    record = AgentRecord(
        instance_uid=uid,
        first_seen=1_000_000_000,
        last_seen=1_000_000_000,
        capabilities=0x4807,
        sequence_num=1,
        push_state="PUSH_PENDING",
        pending_config_hash=b"\xab" * 32,
        pending_config_body="receivers:\n  otlp: {}\n",
    )
    registry = MagicMock()
    registry.get = AsyncMock(return_value=record)
    registry.upsert = AsyncMock()
    return registry


@pytest.fixture
def mock_registry_with_applying_push():
    """AsyncMock registry with an agent in APPLYING state."""
    from opamp_server.registry import AgentRecord
    uid = b"\x01" * 16
    yaml_body = PHASE2_VALID_YAML
    config_hash = hashlib.sha256(yaml_body.encode()).digest()
    record = AgentRecord(
        instance_uid=uid,
        first_seen=1_000_000_000,
        last_seen=1_000_000_000,
        capabilities=0x4807,
        sequence_num=2,
        push_state="APPLYING",
        pending_config_hash=config_hash,
        pending_config_body=yaml_body,
    )

    # Track calls to set_push_state so tests can inspect the updated record
    _state = {"record": record}

    async def _get(uid_arg: bytes):
        return _state["record"]

    async def _set_push_state(
        uid,
        push_state,
        pending_config_hash=None,
        pending_config_body=None,
        is_rollback_push=False,
    ):
        _state["record"] = AgentRecord(
            instance_uid=_state["record"].instance_uid,
            first_seen=_state["record"].first_seen,
            last_seen=_state["record"].last_seen,
            capabilities=_state["record"].capabilities,
            sequence_num=_state["record"].sequence_num,
            description=_state["record"].description,
            push_state=push_state,
            pending_config_hash=pending_config_hash,
            pending_config_body=pending_config_body,
            is_rollback_push=is_rollback_push,
        )

    registry = MagicMock()
    registry.get = AsyncMock(side_effect=_get)
    registry.upsert = AsyncMock()
    registry.set_push_state = AsyncMock(side_effect=_set_push_state)
    return registry


@pytest.fixture
def mock_persistence():
    """Stub persistence functions to prevent DB calls in unit tests."""
    return None  # unit tests using mock_registry don't hit persistence directly


@pytest.fixture
def mock_persistence_with_confirmed_config():
    """Stub for persistence with a confirmed config available for rollback."""
    return None  # test passes prev_config_override directly to process_remote_config_status
