"""Collector fleet REST endpoints.

GET /api/v1/collectors       — list all registered collectors (API-01)
GET /api/v1/collectors/{id}  — full detail for a single collector (API-02)
"""
from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from opamp_server import persistence

router = APIRouter()
log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class CollectorSummary(BaseModel):
    instance_uid: str
    last_seen: int
    health_status: str
    capabilities: int
    resource_attributes: dict[str, str] = {}


class HealthSnapshot(BaseModel):
    recorded_at: int
    healthy: bool
    status: Optional[str] = None
    last_error: Optional[str] = None


class EffectiveConfig(BaseModel):
    recorded_at: int
    config_hash: str
    config_json: dict


class PushStatus(BaseModel):
    push_state: str
    pending_config_hash: Optional[str] = None


class CollectorDetail(BaseModel):
    instance_uid: str
    first_seen: int
    last_seen: int
    health_status: str
    capabilities: int
    resource_attributes: dict[str, str] = {}
    health_history: list[HealthSnapshot]
    effective_config: Optional[EffectiveConfig] = None
    push_status: PushStatus


# ---------------------------------------------------------------------------
# Health status derivation
# ---------------------------------------------------------------------------

def _derive_health_status(snapshot: dict | None) -> str:
    """Derive health_status string from the most recent health snapshot.

    Args:
        snapshot: Dict with keys 'healthy' (bool), 'status' (str|None).
                  None if no health data has been received for this agent.

    Returns:
        One of: 'healthy', 'degraded', 'unhealthy', 'unknown'
    """
    if snapshot is None:
        return "unknown"
    if snapshot["healthy"]:
        return "healthy"
    status_str = (snapshot.get("status") or "").lower()
    if "degraded" in status_str:
        return "degraded"
    return "unhealthy"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/collectors", response_model=list[CollectorSummary])
async def list_collectors(request: Request) -> JSONResponse:
    """Return all registered collectors with summary fields.

    Returns:
        200 OK with JSON array. Each item contains:
        - instance_uid: hex string
        - last_seen: unix nanoseconds
        - health_status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
        - capabilities: integer bitmask
    """
    registry = request.app.state.registry
    agents = await registry.all()

    if not agents:
        return JSONResponse(status_code=200, content=[])

    # Batch-fetch latest health snapshot and resource attributes per agent (single SQL query each)
    uid_hexes = [a.instance_uid.hex() for a in agents]
    health_map = await persistence.get_latest_health_statuses(uid_hexes)
    resource_attrs_map = await persistence.get_resource_attrs_for_agents(uid_hexes)

    result = []
    for agent in agents:
        uid_hex = agent.instance_uid.hex()
        snapshot = health_map.get(uid_hex)
        result.append({
            "instance_uid": uid_hex,
            "last_seen": agent.last_seen,
            "health_status": _derive_health_status(snapshot),
            "capabilities": agent.capabilities,
            "resource_attributes": resource_attrs_map.get(uid_hex, {}),
        })

    log.info("collectors_listed", count=len(result))
    return JSONResponse(status_code=200, content=result)


@router.get("/collectors/attrs/keys")
async def list_attr_keys() -> JSONResponse:
    """Return all distinct resource attribute keys across all collectors, sorted.

    Returns:
        200 OK with JSON object containing a 'keys' list of sorted unique key strings.
        Example: {"keys": ["env", "host.name", "os.type"]}
    """
    keys = await persistence.get_all_resource_attr_keys()
    return JSONResponse(status_code=200, content={"keys": keys})


@router.get("/collectors/{collector_id}", response_model=CollectorDetail)
async def get_collector(collector_id: str, request: Request) -> JSONResponse:
    """Return full detail for a single collector.

    Args:
        collector_id: Hex-encoded instance_uid (32 hex chars, no dashes).

    Returns:
        200 OK with full collector JSON on success.

    Raises:
        400 Bad Request if collector_id is not valid hex.
        404 Not Found if no collector with that ID is registered.
    """
    # Validate collector_id is valid hex
    try:
        agent_uid = bytes.fromhex(collector_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_collector_id", "detail": f"Not valid hex: {collector_id}"},
        )

    registry = request.app.state.registry
    agent = await registry.get(agent_uid)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "collector_not_found", "instance_uid": collector_id},
        )

    uid_hex = agent.instance_uid.hex()

    # Fetch health data (newest-first, limit 10)
    health_rows = await persistence.get_health_history(agent_uid, limit=10)
    resource_attrs_map = await persistence.get_resource_attrs_for_agents([uid_hex])
    health_status = _derive_health_status(health_rows[0] if health_rows else None)

    # Fetch most recent effective config
    effective_config_row = await persistence.get_latest_effective_config(agent_uid)
    effective_config = (
        {
            "recorded_at": effective_config_row["recorded_at"],
            "config_hash": effective_config_row["config_hash"],
            "config_json": effective_config_row["config_json"],
        }
        if effective_config_row is not None
        else None
    )

    # Push status from in-memory registry (authoritative — no DB call needed)
    push_status = {
        "push_state": agent.push_state,
        "pending_config_hash": (
            agent.pending_config_hash.hex()
            if agent.pending_config_hash is not None
            else None
        ),
    }

    result = {
        "instance_uid": uid_hex,
        "first_seen": agent.first_seen,
        "last_seen": agent.last_seen,
        "health_status": health_status,
        "capabilities": agent.capabilities,
        "resource_attributes": resource_attrs_map.get(uid_hex, {}),
        "health_history": health_rows,
        "effective_config": effective_config,
        "push_status": push_status,
    }

    log.info("collector_detail_fetched", instance_uid=uid_hex)
    return JSONResponse(status_code=200, content=result)
