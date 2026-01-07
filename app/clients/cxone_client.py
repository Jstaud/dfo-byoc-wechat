"""CXone Digital Engagement API client."""
from typing import Dict, Any, Optional
from app.clients.base import BaseHTTPClient
from app.config import settings
from app.exceptions import CXoneAPIError, MessageProcessingError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CXoneClient(BaseHTTPClient):
    """Client for CXone Digital Engagement API."""
    
    def __init__(self):
        """Initialize CXone client."""
        super().__init__(
            base_url=settings.cxone_base_url,
            timeout=settings.http_timeout
        )
        self.channel_id = settings.cxone_channel_id
        self.bearer_token = settings.cxone_bearer_token
    
    async def post_message(self, openid: str, text: str) -> Dict[str, Any]:
        """
        Post an inbound message to CXone Digital Engagement.
        
        Args:
            openid: The WeChat user's openid (used as external platform ID)
            text: The message text content
            
        Returns:
            Response dict from CXone API
            
        Raises:
            CXoneAPIError: If posting fails
            MessageProcessingError: If message is invalid
        """
        if not openid:
            raise MessageProcessingError("openid is required")
        if not text:
            raise MessageProcessingError("message text is required")
        
        url = f"/channels/{self.channel_id}/messages"
        
        # Construct payload for CXone Digital Engagement API
        # TODO: Adjust payload structure based on actual CXone API requirements
        payload = {
            "thread": {
                "idOnExternalPlatform": openid
            },
            "message": {
                "text": text,
                "type": "text"
            },
            "direction": "inbound"
        }
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(
                "posting_message_to_cxone",
                openid=openid,
                channel_id=self.channel_id,
                text_length=len(text)
            )
            
            response = await self.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(
                "message_posted_to_cxone",
                openid=openid,
                response_id=result.get("id")
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "failed_to_post_to_cxone",
                openid=openid,
                error=str(e),
                error_type=type(e).__name__
            )
            
            if isinstance(e, CXoneAPIError):
                raise
            
            raise CXoneAPIError(
                f"Failed to post message to CXone: {str(e)}",
                status_code=502,
                details={"openid": openid, "error": str(e)}
            )


# Global client instance (will be initialized on startup)
_cxone_client: Optional[CXoneClient] = None


async def get_cxone_client() -> CXoneClient:
    """Get or create CXone client instance."""
    global _cxone_client
    if _cxone_client is None:
        _cxone_client = CXoneClient()
    return _cxone_client


async def close_cxone_client():
    """Close CXone client."""
    global _cxone_client
    if _cxone_client:
        await _cxone_client.close()
        _cxone_client = None

