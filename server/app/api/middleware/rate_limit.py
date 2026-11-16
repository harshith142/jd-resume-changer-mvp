"""Rate limiting middleware for FastAPI."""
import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings

settings = get_settings()

# In-memory store for rate limiting (use Redis in production)
request_counts: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Create a key based on IP and path
        key = f"{client_ip}:{request.url.path}"

        current_time = time.time()
        window_start = current_time - settings.rate_limit_window_seconds

        # Clean old entries
        request_counts[key] = [
            timestamp for timestamp in request_counts[key]
            if timestamp > window_start
        ]

        # Check if limit exceeded
        if len(request_counts[key]) >= settings.rate_limit_requests:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(settings.rate_limit_window_seconds),
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + settings.rate_limit_window_seconds)),
                }
            )

        # Add current request
        request_counts[key].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.rate_limit_requests - len(request_counts[key]))
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + settings.rate_limit_window_seconds)
        )

        return response
