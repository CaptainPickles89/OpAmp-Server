"""Config push state machine for OpAMP remote configuration management.

Orchestrates the full lifecycle of a config push:
  IDLE -> PUSH_PENDING -> APPLYING -> APPLIED / FAILED -> (rollback) -> PUSH_PENDING

This module owns the business logic. It is called by:
  - The REST API endpoint (POST /api/v1/collectors/{id}/config) via queue_config_push()
  - The OpAMP handler after each AgentToServer message via process_remote_config_status()
"""
from __future__ import annotations

import asyncio
from typing import Optional

import structlog
import yaml

import opamp_pb2 as opamp
from opamp_server import persistence
from opamp_server.protocol import (
    CAPABILITY_ACCEPTS_REMOTE_CONFIG,
    build_remote_config,
    compute_config_hash,
)
from opamp_server.registry import AgentRecord, AgentRegistry

log = structlog.get_logger(__name__)


async def queue_config_push(
    agent_uid: bytes,
    config_body: str,
    registry: AgentRegistry,
) -> dict:
    """Queue a config push for a specific agent.

    Validates the YAML, checks for in-progress pushes, then queues the new config.

    Args:
        agent_uid: Raw 16-byte agent instance_uid.
        config_body: Raw YAML string to push.
        registry: In-memory AgentRegistry.

    Returns:
        Dict with keys: 'push_state' (str), 'config_hash' (str hex), 'instance_uid' (str hex).

    Raises:
        ValueError: If config_body is not valid YAML. Exception message starts with "invalid_yaml".
        KeyError: If agent is not found in registry. Exception message starts with "collector_not_found".
        RuntimeError: If a push is already in progress. Exception message starts with "push_in_progress".
    """
    # Validate YAML
    try:
        yaml.safe_load(config_body)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid_yaml: {exc}") from exc

    # Check agent exists
    existing = await registry.get(agent_uid)
    if existing is None:
        raise KeyError(f"collector_not_found: {agent_uid.hex()}")

    # Check for in-progress push (PUSH_PENDING or APPLYING)
    if existing.push_state in ("PUSH_PENDING", "APPLYING"):
        raise RuntimeError(f"push_in_progress: current_state={existing.push_state}")

    # Compute hash and store
    config_hash_bytes = compute_config_hash(config_body)
    config_hash_hex = config_hash_bytes.hex()

    # Persist to SQLite (fire-and-forget — don't block the response)
    asyncio.ensure_future(
        persistence.store_config_push(
            instance_uid=agent_uid,
            config_hash=config_hash_hex,
            config_body=config_body,
            is_rollback=False,
        )
    )

    # Update in-memory state
    await registry.set_push_state(
        uid=agent_uid,
        push_state="PUSH_PENDING",
        pending_config_hash=config_hash_bytes,
        pending_config_body=config_body,
    )

    log.info(
        "config_push_queued",
        instance_uid=agent_uid.hex(),
        config_hash=config_hash_hex[:16],
    )

    return {
        "push_state": "PUSH_PENDING",
        "config_hash": config_hash_hex,
        "instance_uid": agent_uid.hex(),
    }


async def process_remote_config_status(
    agent_uid: bytes,
    status: "opamp.RemoteConfigStatus",
    registry: AgentRegistry,
    is_rollback_push: bool = False,
    prev_config_override: Optional[dict] = None,
) -> None:
    """Process a RemoteConfigStatus acknowledgement from an agent.

    Updates push state based on the agent's acknowledgement:
    - APPLIED: marks push as confirmed, clears pending fields -> IDLE
    - APPLYING: no-op (already transitioned when config was delivered)
    - FAILED: records failure, triggers rollback if previous confirmed config exists

    Rollback anti-loop: if the current push is already a rollback (is_rollback_push=True)
    and it fails, go to FAILED state without attempting another rollback.

    Args:
        agent_uid: Raw 16-byte agent instance_uid.
        status: RemoteConfigStatus message from AgentToServer.
        registry: In-memory AgentRegistry.
        is_rollback_push: True if the current pending push is a server-initiated rollback.
        prev_config_override: Optional override for the previous confirmed config dict
            (used in unit tests to avoid DB calls). If None, queries persistence.
    """
    existing = await registry.get(agent_uid)
    if existing is None:
        return

    incoming_hash = status.last_remote_config_hash  # bytes
    incoming_status = status.status                  # int enum value

    # Only process if the hash matches our pending/applying config
    if (
        existing.pending_config_hash is None
        or existing.pending_config_hash != incoming_hash
    ):
        log.debug(
            "remote_config_status_hash_mismatch",
            instance_uid=agent_uid.hex(),
            expected=existing.pending_config_hash.hex() if existing.pending_config_hash else None,
            received=incoming_hash.hex() if incoming_hash else None,
        )
        return

    config_hash_hex = incoming_hash.hex()

    if incoming_status == opamp.RemoteConfigStatuses_APPLIED:  # 1
        # Transition: APPLYING -> APPLIED -> IDLE
        await registry.set_push_state(
            uid=agent_uid,
            push_state="IDLE",
            pending_config_hash=None,
            pending_config_body=None,
        )
        asyncio.ensure_future(
            persistence.record_push_applied(agent_uid, config_hash_hex)
        )
        log.info("config_applied", instance_uid=agent_uid.hex(), config_hash=config_hash_hex[:16])

    elif incoming_status == opamp.RemoteConfigStatuses_APPLYING:  # 2
        # Already transitioned to APPLYING when config was delivered — no-op confirmation
        log.debug("config_applying", instance_uid=agent_uid.hex())

    elif incoming_status == opamp.RemoteConfigStatuses_FAILED:  # 3
        error_msg = status.error_message or None
        asyncio.ensure_future(
            persistence.record_push_failed(agent_uid, config_hash_hex, error_msg)
        )
        log.warning(
            "config_failed",
            instance_uid=agent_uid.hex(),
            config_hash=config_hash_hex[:16],
            error=error_msg,
            is_rollback=is_rollback_push,
        )

        if is_rollback_push:
            # Anti-loop: rollback failed -> go to FAILED, no further rollback
            await registry.set_push_state(
                uid=agent_uid,
                push_state="FAILED",
                pending_config_hash=None,
                pending_config_body=None,
            )
            log.error(
                "config_rollback_also_failed",
                instance_uid=agent_uid.hex(),
                error=error_msg,
            )
            return

        # Attempt rollback: find previous confirmed config
        if prev_config_override is not None:
            prev = prev_config_override
        else:
            prev = await persistence.get_previous_confirmed_config(agent_uid)

        if prev:
            rollback_hash_bytes = bytes.fromhex(prev["config_hash"])
            rollback_body = prev["config_body"]

            # Store rollback push row
            asyncio.ensure_future(
                persistence.store_config_push(
                    instance_uid=agent_uid,
                    config_hash=prev["config_hash"],
                    config_body=rollback_body,
                    is_rollback=True,
                )
            )

            await registry.set_push_state(
                uid=agent_uid,
                push_state="PUSH_PENDING",
                pending_config_hash=rollback_hash_bytes,
                pending_config_body=rollback_body,
                is_rollback_push=True,
            )
            log.warning(
                "config_rollback_queued",
                instance_uid=agent_uid.hex(),
                rollback_hash=prev["config_hash"][:16],
            )
        else:
            # No previous confirmed config — cannot rollback
            await registry.set_push_state(
                uid=agent_uid,
                push_state="FAILED",
                pending_config_hash=None,
                pending_config_body=None,
            )
            log.error(
                "config_failed_no_rollback_available",
                instance_uid=agent_uid.hex(),
                error=error_msg,
            )
