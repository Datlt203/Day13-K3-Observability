from __future__ import annotations

import time
import uuid
import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Context variables live longer than a request in some ASGI execution
        # paths.  Reset them at both boundaries so a prior user's metadata can
        # never be attached to the next request's logs.
        clear_contextvars()

        incoming_id = request.headers.get("x-request-id", "").strip().lower()
        if re.fullmatch(r"req-[0-9a-f]{8}", incoming_id):
            correlation_id = incoming_id
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(
                int((time.perf_counter() - start) * 1000)
            )
            return response
        finally:
            clear_contextvars()
