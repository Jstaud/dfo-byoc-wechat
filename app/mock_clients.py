"""Mock implementations of WeChat and CXone clients for testing."""
import logging
from typing import Dict, Any
import json


logger = logging.getLogger(__name__)


class MockWeChatClient:
    """Mock WeChat client that logs messages instead of sending them."""
    
    def __init__(self, appid: str, appsecret: str):
        self.appid = appid
        self.appsecret = appsecret
        self.sent_messages: list = []
    
    def send_text_message(self, openid: str, content: str) -> Dict[str, Any]:
        """
        Mock implementation that logs the message instead of sending.
        
        Args:
            openid: The WeChat user's openid
            content: The text message content
            
        Returns:
            Mock response dict
        """
        message_record = {
            "openid": openid,
            "content": content,
            "type": "text"
        }
        self.sent_messages.append(message_record)
        logger.info(f"[MOCK] Would send WeChat message to {openid}: {content}")
        return {
            "errcode": 0,
            "errmsg": "ok",
            "msgid": f"mock_msgid_{len(self.sent_messages)}"
        }


class MockCXoneClient:
    """Mock CXone client that logs messages instead of posting them."""
    
    def __init__(self, base_url: str, bearer_token: str, channel_id: str):
        self.base_url = base_url
        self.bearer_token = bearer_token
        self.channel_id = channel_id
        self.posted_messages: list = []
    
    def post_message(self, openid: str, text: str) -> Dict[str, Any]:
        """
        Mock implementation that logs the message instead of posting.
        
        Args:
            openid: The WeChat user's openid
            text: The message text content
            
        Returns:
            Mock response dict
        """
        message_record = {
            "openid": openid,
            "text": text,
            "channel_id": self.channel_id
        }
        self.posted_messages.append(message_record)
        logger.info(f"[MOCK] Would post to CXone for openid {openid}: {text}")
        return {
            "id": f"mock_cxone_msg_{len(self.posted_messages)}",
            "status": "created",
            "thread": {
                "idOnExternalPlatform": openid
            }
        }


# Global mock instances (for testing/debugging)
_mock_wechat_client: MockWeChatClient = None
_mock_cxone_client: MockCXoneClient = None


def get_mock_wechat_client(appid: str, appsecret: str) -> MockWeChatClient:
    """Get or create a mock WeChat client instance."""
    global _mock_wechat_client
    if _mock_wechat_client is None:
        _mock_wechat_client = MockWeChatClient(appid, appsecret)
    return _mock_wechat_client


def get_mock_cxone_client(base_url: str, bearer_token: str, channel_id: str) -> MockCXoneClient:
    """Get or create a mock CXone client instance."""
    global _mock_cxone_client
    if _mock_cxone_client is None:
        _mock_cxone_client = MockCXoneClient(base_url, bearer_token, channel_id)
    return _mock_cxone_client


def reset_mock_clients():
    """Reset mock clients (useful for testing)."""
    global _mock_wechat_client, _mock_cxone_client
    _mock_wechat_client = None
    _mock_cxone_client = None

