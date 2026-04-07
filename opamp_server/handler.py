"""OpAMP HTTP handler — /v1/opamp POST endpoint."""
from __future__ import annotations

import asyncio
import hashlib
import time

import structlog
from fastapi import APIRouter, Request, Response
from google.protobuf.message import DecodeError

import opamp_pb2 as opamp
from opamp_server.config import settings
from opamp_server.config_manager import process_remote_config_status
from opamp_server.limiter import limiter
from opamp_server.protocol import (
    FLAG_REPORT_FULL_STATE,
    ERROR_TYPE_BAD_REQUEST,
    CAPABILITY_ACCEPTS_REMOTE_CONFIG,
    build_error_response,
    build_success_response,
    build_remote_config,
    detect_sequence_gap,
    parse_agent_uid,
)
from opamp_server.registry import AgentRecord, AgentRegistry
from opamp_server import persistence

PROTOBUF_CONTENT_TYPE = "application/x-protobuf"

router = APIRouter()
log = structlog.get_logger(__name__)


def _extract_string_attrs(kvs) -> dict[str, str]:
    """Extract resource attributes from repeated KeyValue, coercing to str.

    Handles all AnyValue oneof cases: string values are stored directly,
    other types (int, double, bool, bytes) are coerced via str().
    """
    result: dict[str, str] = {}
    for kv in kvs:
        which = kv.value.WhichOneof("value")
        if which == "string_value":
            result[kv.key] = kv.value.string_value
        elif which is not None:
            result[kv.key] = str(getattr(kv.value, which))
    return result


@router.post("/v1/opamp")
@limiter.limit(settings.rate_limit)
async def opamp_handler(request: Request) -> Response:
    """Handle OpAMP AgentToServer messages and return ServerToAgent responses.

    All responses — including errors — use Content-Type: application/x-protobuf.
    """
    body = await request.body()

    # Parse incoming message
    try:
        msg = opamp.AgentToServer()
        msg.ParseFromString(body)
    except (DecodeError, Exception) as exc:
        log.warning(
            "opamp_decode_error",
            error=str(exc),
            body_size=len(body),
        )
        return Response(
            content=build_error_response(
                error_type=ERROR_TYPE_BAD_REQUEST,
                error_message=f"Failed to parse AgentToServer: {exc}",
            ),
            media_type=PROTOBUF_CONTENT_TYPE,
            status_code=200,  # OpAMP errors are always HTTP 200 with error_response set
        )

    agent_uid = parse_agent_uid(msg)
    uid_hex = agent_uid.hex() if agent_uid else "<unknown>"

    log.info(
        "opamp_message_received",
        instance_uid=uid_hex,
        sequence_num=msg.sequence_num,
        capabilities=hex(msg.capabilities),
        body_size=len(body),
    )

    # Registry lookup
    registry: AgentRegistry = request.app.state.registry
    existing = await registry.get(agent_uid)

    # Sequence gap detection
    stored_seq = existing.sequence_num if existing else None
    gap_detected = detect_sequence_gap(msg.sequence_num, stored_seq)
    missing_config = not (existing and existing.has_effective_config)
    flags = FLAG_REPORT_FULL_STATE if (gap_detected or missing_config) else 0

    if gap_detected:
        log.info(
            "sequence_gap_detected",
            instance_uid=uid_hex,
            expected_seq=stored_seq + 1 if stored_seq is not None else None,
            received_seq=msg.sequence_num,
        )

    # Build updated registry record — preserve push state fields from existing record
    now_ns = time.time_ns()
    updated_record = AgentRecord(
        instance_uid=agent_uid,
        first_seen=existing.first_seen if existing else now_ns,
        last_seen=now_ns,
        capabilities=msg.capabilities,
        sequence_num=msg.sequence_num,
        description=None,  # populated from msg.agent_description if needed
        # Preserve push state from existing record (do not reset on each poll)
        push_state=existing.push_state if existing else "IDLE",
        pending_config_hash=existing.pending_config_hash if existing else None,
        pending_config_body=existing.pending_config_body if existing else None,
        is_rollback_push=existing.is_rollback_push if existing else False,
        has_effective_config=(existing.has_effective_config if existing else False) or msg.HasField("effective_config"),
    )

    # Update in-memory registry (synchronous within event loop)
    await registry.upsert(updated_record)

    # Fire-and-forget persistence (non-blocking)
    asyncio.ensure_future(persistence.upsert_agent(updated_record))

    # Store health snapshot if present
    if msg.HasField("health"):
        health = msg.health
        asyncio.ensure_future(
            persistence.store_health_snapshot(
                instance_uid=agent_uid,
                healthy=health.healthy,
                status=health.status or None,
                last_error=health.last_error or None,
                details=None,  # simplified for Phase 1
            )
        )

    # Store effective config if present
    if msg.HasField("effective_config"):
        cfg_bytes = msg.effective_config.SerializeToString()
        cfg_hash = hashlib.sha256(cfg_bytes).hexdigest()[:16]
        config_data = {
            key: {"body": file.body.decode("utf-8", errors="replace"), "content_type": file.content_type}
            for key, file in msg.effective_config.config_map.config_map.items()
        }
        asyncio.ensure_future(
            persistence.store_effective_config(
                instance_uid=agent_uid,
                config_hash=cfg_hash,
                config_data=config_data,
            )
        )

    # Store resource attributes from AgentDescription (COLS-01)
    if msg.HasField("agent_description"):
        attrs = _extract_string_attrs(
            msg.agent_description.non_identifying_attributes
        )
        if attrs:
            asyncio.ensure_future(
                persistence.upsert_resource_attrs(agent_uid, attrs)
            )

    # Process RemoteConfigStatus from incoming message (CFGMG-03 / CFGMG-04)
    if msg.HasField("remote_config_status") and msg.remote_config_status.status != 0:
        # Determine if current push is a rollback (for anti-loop guard)
        # is_rollback_push is tracked on the AgentRecord itself (set when rollback is queued)
        current_record = await registry.get(agent_uid)
        is_rollback = current_record.is_rollback_push if current_record else False
        await process_remote_config_status(
            agent_uid=agent_uid,
            status=msg.remote_config_status,
            registry=registry,
            is_rollback_push=is_rollback,
        )
        # Re-fetch record after status processing (state may have changed)
        existing = await registry.get(agent_uid)

    # Check if we need to deliver a pending config (CFGMG-02)
    remote_config_msg = None
    current_record = existing  # may have been updated by status processing above
    if (
        current_record is not None
        and current_record.push_state == "PUSH_PENDING"
        and current_record.pending_config_body is not None
        and current_record.pending_config_hash is not None
        and (current_record.capabilities & CAPABILITY_ACCEPTS_REMOTE_CONFIG)
    ):
        remote_config_msg = build_remote_config(
            config_body=current_record.pending_config_body,
            config_hash=current_record.pending_config_hash,
        )
        # Transition PUSH_PENDING -> APPLYING (optimistic: we're about to deliver)
        # Preserve is_rollback_push so anti-loop guard works when FAILED is received
        await registry.set_push_state(
            uid=agent_uid,
            push_state="APPLYING",
            pending_config_hash=current_record.pending_config_hash,
            pending_config_body=current_record.pending_config_body,
            is_rollback_push=current_record.is_rollback_push,
        )
        asyncio.ensure_future(
            persistence.update_push_state(
                instance_uid=agent_uid,
                config_hash=current_record.pending_config_hash.hex(),
                new_state="APPLYING",
            )
        )
        log.info(
            "config_delivering",
            instance_uid=uid_hex,
            config_hash=current_record.pending_config_hash.hex()[:16],
        )

    response_body = build_success_response(
        agent_uid=agent_uid,
        flags=flags,
        remote_config=remote_config_msg,
    )

    log.info(
        "opamp_response_sent",
        instance_uid=uid_hex,
        flags=flags,
        has_remote_config=remote_config_msg is not None,
        response_size=len(response_body),
    )

    return Response(
        content=response_body,
        media_type=PROTOBUF_CONTENT_TYPE,
    )
