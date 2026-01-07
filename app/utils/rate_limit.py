"""Rate limiting utilities."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_handler():
    """Get rate limit exceeded handler."""
    @_rate_limit_exceeded_handler
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        logger.warning(
            "rate_limit_exceeded",
            client_ip=get_remote_address(request),
            path=request.url.path
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "error": "RateLimitExceeded",
                "message": "Too many requests. Please try again later."
            }
        )
    return rate_limit_handler

