"""Config push REST endpoint.

POST /api/v1/collectors/{id}/config — queue a YAML config push to a specific collector.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from opamp_server.config_manager import queue_config_push

router = APIRouter()
log = structlog.get_logger(__name__)


@router.post("/collectors/{collector_id}/config", status_code=202)
async def push_collector_config(
    collector_id: str,
    request: Request,
) -> JSONResponse:
    """Queue a YAML config push to a specific collector.

    Args:
        collector_id: Hex-encoded instance_uid of the target collector.
        request: FastAPI request — config YAML is read from the body.

    Returns:
        202 Accepted with push state details on success.

    Raises:
        400 Bad Request if the body is not valid YAML.
        404 Not Found if no collector with that ID is registered.
        409 Conflict if a push is already in progress for this collector.
    """
    # Validate collector_id is valid hex
    try:
        agent_uid = bytes.fromhex(collector_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_collector_id", "detail": f"Not valid hex: {collector_id}"},
        )

    # Read request body as text
    body_bytes = await request.body()
    config_body = body_bytes.decode("utf-8", errors="replace")

    registry = request.app.state.registry

    try:
        result = await queue_config_push(
            agent_uid=agent_uid,
            config_body=config_body,
            registry=registry,
        )
    except ValueError as exc:
        # invalid_yaml
        error_detail = str(exc)
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_yaml", "detail": error_detail.replace("invalid_yaml: ", "")},
        )
    except KeyError:
        # collector_not_found
        raise HTTPException(
            status_code=404,
            detail={"error": "collector_not_found", "instance_uid": collector_id},
        )
    except RuntimeError as exc:
        # push_in_progress
        error_str = str(exc)
        current_state = error_str.split("current_state=")[-1] if "current_state=" in error_str else "UNKNOWN"
        raise HTTPException(
            status_code=409,
            detail={"error": "push_in_progress", "current_state": current_state},
        )

    log.info(
        "config_push_accepted",
        instance_uid=collector_id,
        push_state=result["push_state"],
        config_hash=result["config_hash"][:16],
    )

    return JSONResponse(status_code=202, content=result)
