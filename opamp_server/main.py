"""FastAPI application factory for the OpAMP server."""
from __future__ import annotations

import structlog
from fastapi import FastAPI

from opamp_server.config import settings
from opamp_server.handler import router
from opamp_server.logging_config import configure_logging


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

    app.include_router(router)

    @app.on_event("startup")
    async def on_startup() -> None:
        log.info("opamp_server_started", host=settings.host, port=settings.port)

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        log.info("opamp_server_stopped")

    return app


app = create_app()
