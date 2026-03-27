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
    # Phase 2: config push state machine
    push_state: str = field(default="IDLE")
    # IDLE | PUSH_PENDING | APPLYING | APPLIED | FAILED
    pending_config_hash: Optional[bytes] = field(default=None)
    # SHA-256 bytes of the pending config (raw 32 bytes)
    pending_config_body: Optional[str] = field(default=None)
    # Raw YAML string of the pending config
    is_rollback_push: bool = field(default=False)
    # True if the current pending push is a server-initiated rollback


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

    async def set_push_state(
        self,
        uid: bytes,
        push_state: str,
        pending_config_hash: Optional[bytes] = None,
        pending_config_body: Optional[str] = None,
        is_rollback_push: bool = False,
    ) -> None:
        """Atomically update push state and pending config fields for an agent.

        Creates a new AgentRecord with updated push fields (immutable update pattern).
        Does nothing if agent is not found.

        Args:
            uid: Agent's raw 16-byte instance_uid.
            push_state: New state string: IDLE / PUSH_PENDING / APPLYING / APPLIED / FAILED.
            pending_config_hash: SHA-256 bytes of config being pushed; None to clear.
            pending_config_body: YAML string of config being pushed; None to clear.
            is_rollback_push: True if this push was triggered by server-initiated rollback.
        """
        async with self._lock:
            existing = self._agents.get(uid)
            if existing is None:
                return
            updated = AgentRecord(
                instance_uid=existing.instance_uid,
                first_seen=existing.first_seen,
                last_seen=existing.last_seen,
                capabilities=existing.capabilities,
                sequence_num=existing.sequence_num,
                description=existing.description,
                push_state=push_state,
                pending_config_hash=pending_config_hash,
                pending_config_body=pending_config_body,
                is_rollback_push=is_rollback_push,
            )
            self._agents[uid] = updated
