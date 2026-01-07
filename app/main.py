"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routes import byoc, wechat
from app.exceptions import ApplicationError
from app.config import settings
from app.utils.logging import setup_logging, get_logger
from app.clients.cxone_client import close_cxone_client

# Setup structured logging
setup_logging(
    log_level=getattr(settings, 'log_level', 'INFO'),
    json_logs=getattr(settings, 'json_logs', False)
)
logger = get_logger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info("application_starting", version="1.0.0", mock_mode=settings.mock_mode)
    yield
    # Shutdown
    logger.info("application_shutting_down")
    # Close HTTP clients
    await close_cxone_client()


app = FastAPI(
    title="DFO BYOC Integration Box",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        "rate_limit_exceeded",
        client_ip=get_remote_address(request),
        path=request.url.path
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "RateLimitExceeded",
            "message": "Too many requests. Please try again later."
        }
    )

# Include BYOC router
app.include_router(byoc.router, prefix="/integration/box")

# Include WeChat router
app.include_router(wechat.router, prefix="/wechat")

# Include health check router
from app.api import health
app.include_router(health.router)


# Global exception handlers
@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError):
    """Handle custom application errors."""
    logger.error(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(
        "unexpected_error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )



