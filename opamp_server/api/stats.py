"""Fleet health statistics endpoint."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from opamp_server import persistence

router = APIRouter()
log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------


class StatsResponse(BaseModel):
    healthy_count: int
    total_count: int


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
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request) -> JSONResponse:
    """Return fleet health summary counts.

    Returns:
        200 OK with JSON containing:
        - healthy_count: number of agents with 'healthy' status
        - total_count: total number of registered agents
    """
    registry = request.app.state.registry
    agents = await registry.all()
    total = len(agents)

    if total == 0:
        return JSONResponse(status_code=200, content={"healthy_count": 0, "total_count": 0})

    uid_hexes = [a.instance_uid.hex() for a in agents]
    health_map = await persistence.get_latest_health_statuses(uid_hexes)

    healthy = sum(
        1 for a in agents
        if _derive_health_status(health_map.get(a.instance_uid.hex())) == "healthy"
    )

    log.info("stats_fetched", healthy=healthy, total=total)
    return JSONResponse(status_code=200, content={"healthy_count": healthy, "total_count": total})
