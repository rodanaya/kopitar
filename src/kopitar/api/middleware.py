"""
API Middleware

Starlette/FastAPI middleware for rate limiting, authentication, and logging.
"""

import logging
import os
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc", "/"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter per client IP.

    Default: 60 requests per 60-second window. Returns 429 with a
    Retry-After header when the bucket is empty. Uses an in-memory
    store so no Redis dependency is required.
    """

    def __init__(self, app: ASGIApp, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        # {ip: (request_count, window_start_timestamp)}
        self._buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.monotonic()))

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.monotonic()
        count, window_start = self._buckets[ip]

        if now - window_start >= self.window_seconds:
            count = 0
            window_start = now

        if count >= self.requests_per_minute:
            retry_after = int(self.window_seconds - (now - window_start)) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests. Please retry after the indicated time.",
                        "status_code": 429,
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._buckets[ip] = (count + 1, window_start)
        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Optional API key authentication middleware.

    Behaviour:
    - If the ``KOPITAR_API_KEY`` env var is **not** set the middleware runs in
      *dev mode*: all traffic is allowed and ``request.state.user`` is set to
      an anonymous context.
    - If the env var **is** set, every request must carry a matching
      ``X-API-Key`` header (exempted paths are always allowed).
    - On success ``request.state.user`` is populated with a dict so downstream
      handlers and dependencies can inspect it without importing this module.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._api_key: str | None = os.environ.get("KOPITAR_API_KEY")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in _EXEMPT_PATHS or self._api_key is None:
            request.state.user = {"user_id": "anonymous", "authenticated": False}
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key", "")
        if provided_key == self._api_key:
            request.state.user = {"user_id": "api_key_user", "authenticated": True}
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "type": "unauthorized",
                    "message": "Invalid or missing API key.",
                    "status_code": 401,
                }
            },
        )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request/response logging middleware.

    Emits one log line per request containing: method, path,
    status_code, and duration_ms.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
