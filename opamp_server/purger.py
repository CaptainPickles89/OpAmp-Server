"""Background purge loop for stale collectors."""
from __future__ import annotations

import asyncio
import time

import structlog

import opamp_server.config as _config
from opamp_server import persistence
from opamp_server.registry import AgentRegistry

log = structlog.get_logger(__name__)

ACTIVE_PUSH_STATES = frozenset({"PUSH_PENDING", "APPLYING"})


def _settings():
    """Return current settings, respecting any module reloads in tests."""
    return _config.settings


async def run_purge_sweep(registry: AgentRegistry) -> int:
    """Identify and purge stale agents. Returns count purged.

    An agent is considered stale when its last_seen timestamp is older than
    settings.collector_ttl_hours. Agents with an active push in progress
    (PUSH_PENDING or APPLYING) are skipped to avoid purging mid-delivery.

    Args:
        registry: The in-memory AgentRegistry to scan and evict from.

    Returns:
        Number of agents purged in this sweep.
    """
    ttl_ns = _settings().collector_ttl_hours * 3_600 * 1_000_000_000
    cutoff_ns = time.time_ns() - ttl_ns

    all_agents = await registry.all()
    to_purge = [
        a for a in all_agents
        if a.last_seen < cutoff_ns and a.push_state not in ACTIVE_PUSH_STATES
    ]

    for agent in to_purge:
        uid_hex = agent.instance_uid.hex()
        await persistence.purge_agent(agent.instance_uid)
        await registry.remove(agent.instance_uid)
        log.info("collector_purged", instance_uid=uid_hex)

    return len(to_purge)


async def start_purge_loop(registry: AgentRegistry) -> None:
    """Background loop: sleep first, then sweep, repeat.

    Sleeping before the first sweep prevents purging agents that just
    re-connected during a server restart.

    Args:
        registry: The in-memory AgentRegistry to pass to each sweep.
    """
    while True:
        await asyncio.sleep(_settings().purge_interval_hours * 3_600)
        try:
            count = await run_purge_sweep(registry)
            log.info("purge_sweep_complete", purged=count)
        except Exception:
            log.exception("purge_sweep_error")
