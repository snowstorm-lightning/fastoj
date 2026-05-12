from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.services.queue_service import queue_service


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed based on rate limit."""
        try:
            queue_service.connect()
            redis = queue_service.redis_client
            if redis is None:
                return True

            current = redis.get(f"rate_limit:{key}")  # type: ignore[union-attr]
            if current is None:
                redis.setex(f"rate_limit:{key}", self.window_seconds, 1)  # type: ignore[union-attr]
                return True

            if int(current) >= self.max_requests:  # type: ignore[arg-type]
                return False

            redis.incr(f"rate_limit:{key}")  # type: ignore[union-attr]
            return True
        except Exception:
            # If Redis is unavailable, allow the request
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/api/v1/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        if not self.limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        response = await call_next(request)
        return response
