"""Unit tests for opamp_server.config_manager — push state machine logic.

Tests cover:
  CFGMG-01: queue_config_push validates and queues config
  CFGMG-03: State transitions fire correctly on each RemoteConfigStatus
"""
from __future__ import annotations

import hashlib

import pytest

import opamp_pb2 as opamp


VALID_YAML = """\
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


# ---------------------------------------------------------------------------
# compute_config_hash (from protocol.py)
# ---------------------------------------------------------------------------

def test_compute_config_hash_is_deterministic():
    """compute_config_hash returns same bytes for same input."""
    from opamp_server.protocol import compute_config_hash
    h1 = compute_config_hash(VALID_YAML)
    h2 = compute_config_hash(VALID_YAML)
    assert h1 == h2
    assert len(h1) == 32  # SHA-256 is 32 bytes


def test_compute_config_hash_differs_on_different_input():
    """compute_config_hash returns different bytes for different input."""
    from opamp_server.protocol import compute_config_hash
    h1 = compute_config_hash(VALID_YAML)
    h2 = compute_config_hash(VALID_YAML + "\n# extra line")
    assert h1 != h2


# ---------------------------------------------------------------------------
# build_remote_config (from protocol.py)
# ---------------------------------------------------------------------------

def test_build_remote_config_structure():
    """build_remote_config returns AgentRemoteConfig with correct structure."""
    from opamp_server.protocol import build_remote_config, compute_config_hash
    config_hash = compute_config_hash(VALID_YAML)
    remote_cfg = build_remote_config(VALID_YAML, config_hash)

    assert isinstance(remote_cfg, opamp.AgentRemoteConfig)
    assert remote_cfg.config_hash == config_hash
    assert "collector.yaml" in remote_cfg.config.config_map
    cfg_file = remote_cfg.config.config_map["collector.yaml"]
    assert cfg_file.body == VALID_YAML.encode("utf-8")
    assert cfg_file.content_type == "text/yaml"


# ---------------------------------------------------------------------------
# queue_config_push — validates YAML and rejects in-progress pushes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_queue_config_push_rejects_invalid_yaml(mock_registry, mock_persistence):
    """queue_config_push raises ValueError for invalid YAML."""
    from opamp_server.config_manager import queue_config_push
    agent_uid = b"\x01" * 16

    with pytest.raises(ValueError, match="invalid_yaml"):
        await queue_config_push(
            agent_uid=agent_uid,
            config_body="not: valid: [unclosed",
            registry=mock_registry,
        )


@pytest.mark.asyncio
async def test_queue_config_push_rejects_in_progress(
    mock_registry_with_pending_push, mock_persistence
):
    """queue_config_push raises RuntimeError when push already in progress."""
    from opamp_server.config_manager import queue_config_push
    agent_uid = b"\x01" * 16

    with pytest.raises(RuntimeError, match="push_in_progress"):
        await queue_config_push(
            agent_uid=agent_uid,
            config_body=VALID_YAML,
            registry=mock_registry_with_pending_push,
        )


# ---------------------------------------------------------------------------
# State machine transitions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_status_applied_clears_pending(mock_registry_with_applying_push):
    """APPLIED status transitions push state to IDLE and clears pending fields."""
    from opamp_server.config_manager import process_remote_config_status
    agent_uid = b"\x01" * 16
    config_hash = hashlib.sha256(VALID_YAML.encode()).digest()

    status = opamp.RemoteConfigStatus()
    status.last_remote_config_hash = config_hash
    status.status = opamp.RemoteConfigStatuses_APPLIED

    await process_remote_config_status(
        agent_uid=agent_uid,
        status=status,
        registry=mock_registry_with_applying_push,
    )
    record = await mock_registry_with_applying_push.get(agent_uid)
    assert record.push_state == "IDLE"
    assert record.pending_config_hash is None


@pytest.mark.asyncio
async def test_process_status_failed_queues_rollback(
    mock_registry_with_applying_push, mock_persistence_with_confirmed_config
):
    """FAILED status queues rollback to previous confirmed config."""
    from opamp_server.config_manager import process_remote_config_status
    agent_uid = b"\x01" * 16
    config_hash = hashlib.sha256(VALID_YAML.encode()).digest()

    status = opamp.RemoteConfigStatus()
    status.last_remote_config_hash = config_hash
    status.status = opamp.RemoteConfigStatuses_FAILED
    status.error_message = "pipeline validation failed"

    await process_remote_config_status(
        agent_uid=agent_uid,
        status=status,
        registry=mock_registry_with_applying_push,
        prev_config_override={"config_hash": config_hash.hex(), "config_body": "receivers:\n  otlp: {}\n"},
    )
    record = await mock_registry_with_applying_push.get(agent_uid)
    assert record.push_state == "PUSH_PENDING"  # rollback queued
    assert record.pending_config_body is not None
