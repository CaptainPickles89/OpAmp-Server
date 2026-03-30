"""Integration tests for GET /api/v1/stats — fleet health statistics endpoint.

Covers:
  STATUS-03: stats endpoint returns healthy_count and total_count
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# GET /api/v1/stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stats_empty_registry(async_client):
    """GET /api/v1/stats with no agents returns 200 and zeroed counts."""
    response = await async_client.get("/api/v1/stats")
    assert response.status_code == 200
    assert response.json() == {"healthy_count": 0, "total_count": 0}


@pytest.mark.asyncio
async def test_stats_one_healthy_agent(async_client, registered_agent_with_health):
    """GET /api/v1/stats with 1 healthy agent returns healthy_count=1 and total_count=1."""
    response = await async_client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy_count"] == 1
    assert data["total_count"] == 1


@pytest.mark.asyncio
async def test_stats_agent_no_health_snapshot(async_client, registered_agent_uid):
    """GET /api/v1/stats with 1 agent but no health data returns healthy_count=0, total_count=1.

    An agent with no health snapshot has status 'unknown', which is not counted as healthy.
    """
    response = await async_client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy_count"] == 0
    assert data["total_count"] == 1
