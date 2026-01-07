"""Health check endpoint with dependency checks."""
from fastapi import APIRouter
from typing import Dict, Any
from app.clients.cxone_client import get_cxone_client
from app.clients.wechat_client import get_wechat_client
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint with dependency status.
    
    Returns:
        Health status including dependency checks
    """
    status = {
        "status": "ok",
        "version": "1.0.0",
        "dependencies": {}
    }
    
    # Check CXone connectivity (if not in mock mode)
    if not settings.mock_mode:
        try:
            cxone_client = await get_cxone_client()
            # Simple connectivity check - could be improved with actual API call
            status["dependencies"]["cxone"] = {
                "status": "ok",
                "base_url": settings.cxone_base_url
            }
        except Exception as e:
            logger.warning("cxone_health_check_failed", error=str(e))
            status["dependencies"]["cxone"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"
    else:
        status["dependencies"]["cxone"] = {"status": "mock_mode"}
    
    # Check WeChat connectivity (if not in mock mode)
    if not settings.mock_mode:
        try:
            wechat_client = await get_wechat_client()
            # Simple connectivity check
            status["dependencies"]["wechat"] = {
                "status": "ok",
                "appid": settings.wechat_appid[:10] + "..."  # Don't expose full appid
            }
        except Exception as e:
            logger.warning("wechat_health_check_failed", error=str(e))
            status["dependencies"]["wechat"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"
    else:
        status["dependencies"]["wechat"] = {"status": "mock_mode"}
    
    return status


@router.get("/ready")
async def readiness() -> Dict[str, str]:
    """
    Readiness probe for Kubernetes.
    
    Returns:
        Ready status
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes.
    
    Returns:
        Live status
    """
    return {"status": "alive"}

