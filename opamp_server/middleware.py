"""ASGI middleware for OpAMP server hardening."""
from __future__ import annotations

from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from opamp_server.protocol import ERROR_TYPE_BAD_REQUEST, build_error_response

PROTOBUF_CONTENT_TYPE = "application/x-protobuf"

log = structlog.get_logger(__name__)


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding the configured maximum size.

    Returns a binary-encoded ServerErrorResponse (not HTTP 413 JSON) when
    the limit is exceeded, to comply with the OpAMP protocol requirement
    that all /v1/opamp responses use application/x-protobuf.
    """

    def __init__(self, app, max_body_size: int = 1_048_576) -> None:
        """Initialize middleware.

        Args:
            app: The ASGI application to wrap.
            max_body_size: Maximum allowed request body size in bytes.
        """
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check Content-Length or stream size before passing to handler.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            Response from handler, or binary error response if body too large.
        """
        # Fast path: check Content-Length header before reading body
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_body_size:
                    log.warning(
                        "body_size_exceeded",
                        content_length=content_length,
                        max_body_size=self.max_body_size,
                        path=request.url.path,
                    )
                    return Response(
                        content=build_error_response(
                            error_type=ERROR_TYPE_BAD_REQUEST,
                            error_message=f"Request body exceeds maximum size of {self.max_body_size} bytes",
                        ),
                        media_type=PROTOBUF_CONTENT_TYPE,
                        status_code=200,
                    )
            except ValueError:
                pass  # Malformed Content-Length — let handler deal with it

        return await call_next(request)
