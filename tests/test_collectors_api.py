"""Integration tests for Phase 3: REST API — collector list and detail endpoints.

Tests cover:
  API-01: GET /api/v1/collectors returns JSON array with required fields
  API-02: GET /api/v1/collectors/{id} returns full detail with health history and push status
"""
from __future__ import annotations

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# API-01: GET /api/v1/collectors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_collectors_empty(async_client):
    """GET /api/v1/collectors with no agents returns 200 and []."""
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_collectors_returns_registered_agent(async_client, registered_agent_uid):
    """GET /api/v1/collectors with one registered agent returns 200 and list with 1 item."""
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert "instance_uid" in item
    assert "last_seen" in item
    assert "health_status" in item
    assert "capabilities" in item


@pytest.mark.asyncio
async def test_list_collectors_health_status_unknown_when_no_snapshots(async_client, registered_agent_uid):
    """Registered agent with no health snapshots has health_status == 'unknown'."""
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["health_status"] == "unknown"


@pytest.mark.asyncio
async def test_list_collectors_health_status_healthy(async_client, registered_agent_with_health):
    """Agent with healthy snapshot has health_status == 'healthy'."""
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["health_status"] == "healthy"


@pytest.mark.asyncio
async def test_list_collectors_health_status_unhealthy(async_client, registered_agent_uid):
    """Agent with healthy=False snapshot has health_status == 'unhealthy'."""
    from opamp_server import persistence
    await persistence.store_health_snapshot(
        instance_uid=registered_agent_uid,
        healthy=False,
        status="Component failure",
        last_error="Connection refused",
        details={"healthy": False},
    )
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["health_status"] == "unhealthy"


# ---------------------------------------------------------------------------
# API-02: GET /api/v1/collectors/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_collector_detail_not_found(async_client):
    """GET /api/v1/collectors/{id} for unknown id returns 404 with error dict."""
    unknown_id = "deadbeef" * 4  # 32 hex chars, valid hex, not registered
    response = await async_client.get(f"/api/v1/collectors/{unknown_id}")
    assert response.status_code == 404
    body = response.json()
    # FastAPI wraps HTTPException detail in {"detail": ...}
    detail = body.get("detail", body)
    assert detail.get("error") == "collector_not_found"


@pytest.mark.asyncio
async def test_get_collector_detail_invalid_id(async_client):
    """GET /api/v1/collectors/not-valid-hex returns 400."""
    response = await async_client.get("/api/v1/collectors/not-valid-hex")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_collector_detail_basic(async_client, registered_agent_uid):
    """GET /api/v1/collectors/{id} for registered agent returns 200 with required fields."""
    uid_hex = registered_agent_uid.hex()
    response = await async_client.get(f"/api/v1/collectors/{uid_hex}")
    assert response.status_code == 200
    data = response.json()
    assert "instance_uid" in data
    assert "first_seen" in data
    assert "last_seen" in data
    assert "health_status" in data
    assert "capabilities" in data
    assert "health_history" in data
    assert "effective_config" in data
    assert "push_status" in data


@pytest.mark.asyncio
async def test_get_collector_detail_with_health_history(async_client, registered_agent_with_health):
    """Agent with health snapshots has non-empty health_history with required keys."""
    uid_hex = registered_agent_with_health.hex()
    response = await async_client.get(f"/api/v1/collectors/{uid_hex}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["health_history"], list)
    assert len(data["health_history"]) > 0
    snapshot = data["health_history"][0]
    assert "recorded_at" in snapshot
    assert "healthy" in snapshot
    assert "status" in snapshot
    assert "last_error" in snapshot


@pytest.mark.asyncio
async def test_get_collector_detail_with_effective_config(async_client, registered_agent_with_config):
    """Agent with effective_config snapshot has non-null effective_config with required keys."""
    uid_hex = registered_agent_with_config.hex()
    response = await async_client.get(f"/api/v1/collectors/{uid_hex}")
    assert response.status_code == 200
    data = response.json()
    assert data["effective_config"] is not None
    cfg = data["effective_config"]
    assert "recorded_at" in cfg
    assert "config_hash" in cfg
    assert "config_json" in cfg


@pytest.mark.asyncio
async def test_get_collector_detail_push_status_idle(async_client, registered_agent_uid):
    """Registered agent with no push has push_status.push_state == 'IDLE'."""
    uid_hex = registered_agent_uid.hex()
    response = await async_client.get(f"/api/v1/collectors/{uid_hex}")
    assert response.status_code == 200
    data = response.json()
    assert "push_status" in data
    assert data["push_status"]["push_state"] == "IDLE"


@pytest.mark.asyncio
async def test_get_collector_detail_push_status_reflects_registry(async_client, registered_agent_uid):
    """After POST /api/v1/collectors/{id}/config, GET shows push_state == 'PUSH_PENDING'."""
    uid_hex = registered_agent_uid.hex()
    # Trigger a config push to put the agent into PUSH_PENDING state
    config_body = "receivers:\n  otlp: {}\nexporters:\n  debug: {}\nservice:\n  pipelines:\n    traces:\n      receivers: [otlp]\n      exporters: [debug]\n"
    push_response = await async_client.post(
        f"/api/v1/collectors/{uid_hex}/config",
        content=config_body,
        headers={"Content-Type": "text/yaml"},
    )
    assert push_response.status_code in (200, 202), f"Push failed: {push_response.text}"

    # Now GET the detail and verify push state is PUSH_PENDING
    response = await async_client.get(f"/api/v1/collectors/{uid_hex}")
    assert response.status_code == 200
    data = response.json()
    assert data["push_status"]["push_state"] == "PUSH_PENDING"


# ---------------------------------------------------------------------------
# Phase 9 stubs — resource attributes in list endpoint (COLS-02, COLS-03)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_collectors_includes_resource_attributes(async_client, registered_agent_uid):
    """COLS-02: GET /api/v1/collectors includes resource_attributes dict per collector."""
    from opamp_server import persistence
    await persistence.upsert_resource_attrs(
        registered_agent_uid, {"host.name": "web-01", "os.type": "linux"}
    )
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "resource_attributes" in data[0]
    assert data[0]["resource_attributes"] == {"host.name": "web-01", "os.type": "linux"}


@pytest.mark.asyncio
async def test_list_collectors_resource_attributes_empty_when_none(async_client, registered_agent_uid):
    """COLS-02: GET /api/v1/collectors returns resource_attributes={} when no attrs stored."""
    response = await async_client.get("/api/v1/collectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["resource_attributes"] == {}


@pytest.mark.asyncio
async def test_attrs_keys_returns_distinct_keys(async_client, registered_agent_uid):
    """COLS-03: GET /api/v1/collectors/attrs/keys returns sorted unique keys."""
    from opamp_server import persistence
    uid2 = b"\x02" * 16
    from opamp_server.registry import AgentRecord
    import time
    now = time.time_ns()
    record2 = AgentRecord(
        instance_uid=uid2,
        first_seen=now, last_seen=now,
        capabilities=0x4807, sequence_num=1,
    )
    await async_client.app.state.registry.upsert(record2)
    await persistence.upsert_resource_attrs(
        registered_agent_uid, {"host.name": "web-01", "os.type": "linux"}
    )
    await persistence.upsert_resource_attrs(uid2, {"host.name": "web-02", "env": "prod"})

    response = await async_client.get("/api/v1/collectors/attrs/keys")
    assert response.status_code == 200
    body = response.json()
    assert "keys" in body
    assert body["keys"] == ["env", "host.name", "os.type"]


@pytest.mark.asyncio
async def test_attrs_keys_empty_when_no_attrs(async_client):
    """COLS-03: GET /api/v1/collectors/attrs/keys returns {keys: []} when no attrs exist."""
    response = await async_client.get("/api/v1/collectors/attrs/keys")
    assert response.status_code == 200
    body = response.json()
    assert body == {"keys": []}


@pytest.mark.asyncio
async def test_attrs_keys_route_not_consumed_by_collector_id(async_client):
    """COLS-03: attrs/keys route returns 200 JSON, not 400 from hex-parse of 'attrs'."""
    response = await async_client.get("/api/v1/collectors/attrs/keys")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
