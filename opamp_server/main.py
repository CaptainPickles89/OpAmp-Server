"""FastAPI application factory for the OpAMP server."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request, Response
from slowapi.errors import RateLimitExceeded

from opamp_server.config import settings
from opamp_server.handler import router
from opamp_server.limiter import limiter
from opamp_server.logging_config import configure_logging
from opamp_server.middleware import MaxBodySizeMiddleware
from opamp_server.persistence import init_db, load_all_agents
from opamp_server.protocol import ERROR_TYPE_UNAVAILABLE, build_error_response
from opamp_server.registry import AgentRegistry

PROTOBUF_CONTENT_TYPE = "application/x-protobuf"

registry = AgentRegistry()


def _opamp_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Override slowapi's default JSON 429 response with binary ServerErrorResponse.

    Args:
        request: The rate-limited request.
        exc: The RateLimitExceeded exception from slowapi.

    Returns:
        Binary-encoded ServerErrorResponse wrapped in ServerToAgent.
    """
    return Response(
        content=build_error_response(
            error_type=ERROR_TYPE_UNAVAILABLE,
            error_message=f"Rate limit exceeded: {exc.detail}",
        ),
        media_type=PROTOBUF_CONTENT_TYPE,
        status_code=200,
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    configure_logging(settings.log_level)
    log = structlog.get_logger(__name__)

    app = FastAPI(
        title="OpAMP Server",
        description="Spec-compliant OpenTelemetry Agent Management Protocol server",
        version="0.1.0",
    )

    # State for slowapi and registry
    app.state.limiter = limiter
    app.state.registry = registry

    # Register custom rate limit handler (returns binary protobuf, not JSON)
    app.add_exception_handler(RateLimitExceeded, _opamp_rate_limit_handler)

    # Body size limit middleware (applied before routing)
    app.add_middleware(MaxBodySizeMiddleware, max_body_size=settings.max_body_size)

    app.include_router(router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        records = await load_all_agents()
        await registry.hydrate(records)
        agent_count = await registry.count()
        log.info(
            "opamp_server_started",
            host=settings.host,
            port=settings.port,
            agents_restored=agent_count,
        )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        log.info("opamp_server_stopped")

    return app


app = create_app()
