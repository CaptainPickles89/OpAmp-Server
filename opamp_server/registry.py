"""In-memory agent registry — fast per-request lookups with no I/O."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentRecord:
    """State for a single connected agent."""

    instance_uid: bytes          # raw 16-byte UUID v7
    first_seen: int              # unix timestamp nanoseconds
    last_seen: int               # unix timestamp nanoseconds
    capabilities: int            # AgentCapabilities bitmask
    sequence_num: int            # last received sequence number
    description: Optional[dict] = field(default=None)


class AgentRegistry:
    """Thread-safe in-memory registry of connected agents.

    This is the single source of truth for per-request agent state.
    All reads/writes are in-memory; persistence is handled separately.
    """

    def __init__(self) -> None:
        self._agents: dict[bytes, AgentRecord] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def upsert(self, record: AgentRecord) -> None:
        """Insert or update an agent record.

        Args:
            record: The agent record to store. Keyed by instance_uid.
        """
        async with self._lock:
            self._agents[record.instance_uid] = record

    async def get(self, uid: bytes) -> Optional[AgentRecord]:
        """Retrieve an agent record by instance_uid.

        Args:
            uid: Raw 16-byte instance_uid.

        Returns:
            AgentRecord if found, None if agent is unknown.
        """
        async with self._lock:
            return self._agents.get(uid)

    async def all(self) -> list[AgentRecord]:
        """Return all registered agent records.

        Returns:
            List of all AgentRecord instances (copy of values).
        """
        async with self._lock:
            return list(self._agents.values())

    async def hydrate(self, records: list[AgentRecord]) -> None:
        """Bulk-load records from persistence on startup.

        Replaces all current in-memory state. Used during server startup
        to restore registry from SQLite.

        Args:
            records: List of AgentRecord instances loaded from persistence.
        """
        async with self._lock:
            self._agents = {r.instance_uid: r for r in records}

    async def count(self) -> int:
        """Return the number of registered agents."""
        async with self._lock:
            return len(self._agents)
