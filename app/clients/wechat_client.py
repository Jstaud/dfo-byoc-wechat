"""WeChat Service Account API client."""
import asyncio
from typing import Dict, Any, Optional
from wechatpy import WeChatClient
from app.config import settings
from app.exceptions import WeChatAPIError, MessageProcessingError
from app.utils.logging import get_logger
from app.mock_clients import get_mock_wechat_client

logger = get_logger(__name__)


class WeChatClientWrapper:
    """Wrapper for WeChat client to support async operations."""
    
    def __init__(self, appid: str, appsecret: str):
        """Initialize WeChat client wrapper."""
        self.appid = appid
        self.appsecret = appsecret
        self._client: Optional[WeChatClient] = None
    
    @property
    def client(self) -> WeChatClient:
        """Get or create WeChat client instance."""
        if self._client is None:
            self._client = WeChatClient(self.appid, self.appsecret)
        return self._client
    
    async def send_text_message(self, openid: str, content: str) -> Dict[str, Any]:
        """
        Send a plain text message to a WeChat user (async wrapper).
        
        Args:
            openid: The WeChat user's openid
            content: The text message content to send
            
        Returns:
            Response dict from WeChat API
            
        Raises:
            WeChatAPIError: If message sending fails
            MessageProcessingError: If message is invalid
        """
        if not openid:
            raise MessageProcessingError("openid is required")
        if not content:
            raise MessageProcessingError("message content is required")
        
        if len(content) > 10000:
            raise MessageProcessingError("message content exceeds 10000 characters")
        
        try:
            logger.info(
                "sending_wechat_message",
                openid=openid,
                content_length=len(content)
            )
            
            # Run synchronous wechatpy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.message.send_text(openid, content)
            )
            
            logger.info(
                "wechat_message_sent",
                openid=openid,
                msgid=result.get("msgid")
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "failed_to_send_wechat_message",
                openid=openid,
                error=str(e),
                error_type=type(e).__name__
            )
            
            if isinstance(e, WeChatAPIError):
                raise
            
            raise WeChatAPIError(
                f"Failed to send message to WeChat: {str(e)}",
                status_code=502,
                details={"openid": openid, "error": str(e)}
            )


# Global client instance (will be initialized on startup)
_wechat_client: Optional[WeChatClientWrapper] = None


async def get_wechat_client() -> WeChatClientWrapper:
    """Get or create WeChat client instance."""
    global _wechat_client
    
    if settings.mock_mode:
        # Return mock client wrapper
        mock_client = get_mock_wechat_client(settings.wechat_appid, settings.wechat_appsecret)
        
        class MockWeChatClientWrapper:
            async def send_text_message(self, openid: str, content: str) -> Dict[str, Any]:
                return mock_client.send_text_message(openid, content)
        
        return MockWeChatClientWrapper()
    
    if _wechat_client is None:
        _wechat_client = WeChatClientWrapper(settings.wechat_appid, settings.wechat_appsecret)
    
    return _wechat_client


async def send_text_message(openid: str, content: str) -> Dict[str, Any]:
    """
    Send a plain text message to a WeChat user.
    
    Args:
        openid: The WeChat user's openid
        content: The text message content to send
        
    Returns:
        Response dict from WeChat API or mock response
        
    Raises:
        WeChatAPIError: If message sending fails
    """
    client = await get_wechat_client()
    return await client.send_text_message(openid, content)

