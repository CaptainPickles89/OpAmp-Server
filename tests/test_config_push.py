"""Integration tests for Phase 2: Config Push and Rollback.

Tests cover the full lifecycle:
  CFGMG-01: POST /api/v1/collectors/{id}/config accepted
  CFGMG-02: ServerToAgent includes remote_config on next poll
  CFGMG-03: State transitions via RemoteConfigStatus acknowledgements
  CFGMG-04: FAILED status triggers automatic rollback push
  CFGMG-05: Double-push rejected with 409 Conflict
"""
from __future__ import annotations

import hashlib

import pytest
import pytest_asyncio

import opamp_pb2 as opamp


VALID_YAML = """\
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


# ---------------------------------------------------------------------------
# CFGMG-01: POST config accepted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_post_config_accepted(async_client, registered_agent_uid):
    """POST /api/v1/collectors/{id}/config with valid YAML returns 202."""
    uid_hex = registered_agent_uid.hex()
    resp = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["push_state"] == "PUSH_PENDING"
    assert body["instance_uid"] == uid_hex
    assert "config_hash" in body


@pytest.mark.asyncio
async def test_post_config_invalid_yaml(async_client, registered_agent_uid):
    """POST /api/v1/collectors/{id}/config with invalid YAML returns 400."""
    uid_hex = registered_agent_uid.hex()
    resp = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content="not: valid: yaml: [unclosed",
        headers={"Content-Type": "text/yaml"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "invalid_yaml"


@pytest.mark.asyncio
async def test_post_config_unknown_collector(async_client):
    """POST /api/v1/collectors/{id}/config for unknown UID returns 404."""
    uid_hex = "deadbeef" * 4  # 32-char fake hex, 16 bytes
    resp = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "collector_not_found"


# ---------------------------------------------------------------------------
# CFGMG-05: Double-push rejected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_double_push_rejected(async_client, registered_agent_uid):
    """Second POST while first is PUSH_PENDING returns 409 Conflict."""
    uid_hex = registered_agent_uid.hex()
    # First push
    resp1 = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    assert resp1.status_code == 202

    # Second push immediately (still PUSH_PENDING)
    resp2 = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    assert resp2.status_code == 409
    body = resp2.json()
    assert body["detail"]["error"] == "push_in_progress"


# ---------------------------------------------------------------------------
# CFGMG-02: remote_config included in next ServerToAgent poll
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_push_delivered_on_poll(async_client, registered_agent_uid, opamp_agent_message):
    """After a config push, next AgentToServer poll gets ServerToAgent with remote_config."""
    uid_hex = registered_agent_uid.hex()
    # Queue push
    await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    # Simulate collector poll (AgentToServer with no remote_config_status)
    agent_msg = opamp_agent_message(registered_agent_uid, sequence_num=2)
    resp = await async_client.post(
        "/v1/opamp",
        content=agent_msg.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    assert resp.status_code == 200
    server_msg = opamp.ServerToAgent()
    server_msg.ParseFromString(resp.content)
    # remote_config MUST be present with key "collector.yaml"
    assert server_msg.HasField("remote_config")
    assert "collector.yaml" in server_msg.remote_config.config.config_map
    cfg_file = server_msg.remote_config.config.config_map["collector.yaml"]
    assert cfg_file.content_type == "text/yaml"
    assert VALID_YAML.encode("utf-8") == cfg_file.body


# ---------------------------------------------------------------------------
# CFGMG-03: APPLIED status transitions state to IDLE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_applied_status_clears_state(async_client, registered_agent_uid, opamp_agent_message):
    """After collector sends APPLIED status, push state transitions to IDLE."""
    uid_hex = registered_agent_uid.hex()
    config_hash = hashlib.sha256(VALID_YAML.encode()).digest()

    # Queue push
    await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )

    # Simulate collector reporting APPLIED
    agent_msg = opamp_agent_message(
        registered_agent_uid,
        sequence_num=2,
        remote_config_status_hash=config_hash,
        remote_config_status_value=opamp.RemoteConfigStatuses_APPLIED,
    )
    resp = await async_client.post(
        "/v1/opamp",
        content=agent_msg.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    assert resp.status_code == 200

    # Next poll should NOT include remote_config (state is now IDLE)
    agent_msg2 = opamp_agent_message(registered_agent_uid, sequence_num=3)
    resp2 = await async_client.post(
        "/v1/opamp",
        content=agent_msg2.SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    server_msg = opamp.ServerToAgent()
    server_msg.ParseFromString(resp2.content)
    assert not server_msg.HasField("remote_config")


# ---------------------------------------------------------------------------
# CFGMG-04: FAILED status triggers rollback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_triggers_rollback(
    async_client, registered_agent_uid, opamp_agent_message
):
    """When collector reports FAILED, next poll delivers previous confirmed config."""
    uid_hex = registered_agent_uid.hex()

    # First push + APPLIED (creates confirmed config)
    first_yaml = VALID_YAML
    first_hash = hashlib.sha256(first_yaml.encode()).digest()
    await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=first_yaml,
        headers={"Content-Type": "text/yaml"},
    )
    # Deliver first push
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(registered_agent_uid, sequence_num=2).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    # Collector ACKs APPLIED for first config
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(
            registered_agent_uid,
            sequence_num=3,
            remote_config_status_hash=first_hash,
            remote_config_status_value=opamp.RemoteConfigStatuses_APPLIED,
        ).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )

    # Second push (will fail)
    bad_yaml = "receivers:\n  broken: {}\n"
    bad_hash = hashlib.sha256(bad_yaml.encode()).digest()
    await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=bad_yaml,
        headers={"Content-Type": "text/yaml"},
    )
    # Deliver second push
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(registered_agent_uid, sequence_num=4).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )

    # Collector reports FAILED for second push
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(
            registered_agent_uid,
            sequence_num=5,
            remote_config_status_hash=bad_hash,
            remote_config_status_value=opamp.RemoteConfigStatuses_FAILED,
            remote_config_error="pipeline validation failed",
        ).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )

    # Next poll MUST deliver the first (confirmed) config as rollback
    resp = await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(registered_agent_uid, sequence_num=6).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    server_msg = opamp.ServerToAgent()
    server_msg.ParseFromString(resp.content)
    assert server_msg.HasField("remote_config")
    rollback_body = server_msg.remote_config.config.config_map["collector.yaml"].body
    assert rollback_body == first_yaml.encode("utf-8")


@pytest.mark.asyncio
async def test_rollback_no_previous_config(
    async_client, registered_agent_uid, opamp_agent_message
):
    """When FAILED and no previous confirmed config, state goes to FAILED — no rollback."""
    uid_hex = registered_agent_uid.hex()
    config_hash = hashlib.sha256(VALID_YAML.encode()).digest()

    # Single push (no previous confirmed config)
    await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=VALID_YAML,
        headers={"Content-Type": "text/yaml"},
    )
    # Deliver
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(registered_agent_uid, sequence_num=2).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    # Collector reports FAILED
    await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(
            registered_agent_uid,
            sequence_num=3,
            remote_config_status_hash=config_hash,
            remote_config_status_value=opamp.RemoteConfigStatuses_FAILED,
            remote_config_error="validation error",
        ).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )

    # Next poll should NOT deliver a config (no rollback target)
    resp = await async_client.post(
        "/v1/opamp",
        content=opamp_agent_message(registered_agent_uid, sequence_num=4).SerializeToString(),
        headers={"Content-Type": "application/x-protobuf"},
    )
    server_msg = opamp.ServerToAgent()
    server_msg.ParseFromString(resp.content)
    assert not server_msg.HasField("remote_config")
