"""OpAMP HTTP handler — /v1/opamp POST endpoint."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Request, Response
from google.protobuf.message import DecodeError

import opamp_pb2 as opamp
from opamp_server.config import settings
from opamp_server.limiter import limiter
from opamp_server.protocol import (
    FLAG_REPORT_FULL_STATE,
    ERROR_TYPE_BAD_REQUEST,
    build_error_response,
    build_success_response,
    detect_sequence_gap,
    parse_agent_uid,
)

PROTOBUF_CONTENT_TYPE = "application/x-protobuf"

router = APIRouter()
log = structlog.get_logger(__name__)

# In-memory sequence tracker: uid_hex -> last_sequence_num
# Replaced by full registry in 01-04-registry plan
_sequence_store: dict[str, int] = {}


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

    # Sequence gap detection
    stored_seq = _sequence_store.get(uid_hex)
    gap_detected = detect_sequence_gap(msg.sequence_num, stored_seq)
    _sequence_store[uid_hex] = msg.sequence_num

    flags = FLAG_REPORT_FULL_STATE if gap_detected else 0

    if gap_detected:
        log.info(
            "sequence_gap_detected",
            instance_uid=uid_hex,
            expected_seq=stored_seq + 1 if stored_seq is not None else None,
            received_seq=msg.sequence_num,
        )

    response_body = build_success_response(agent_uid=agent_uid, flags=flags)

    log.info(
        "opamp_response_sent",
        instance_uid=uid_hex,
        flags=flags,
        response_size=len(response_body),
    )

    return Response(
        content=response_body,
        media_type=PROTOBUF_CONTENT_TYPE,
    )
