"""Tests for mock mode functionality."""
import pytest
from unittest.mock import patch, AsyncMock
from app.mock_clients import reset_mock_clients, get_mock_wechat_client, get_mock_cxone_client


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mock clients before each test."""
    reset_mock_clients()
    yield
    reset_mock_clients()


@pytest.mark.asyncio
async def test_mock_mode_wechat_sending():
    """Test that mock mode logs WeChat messages instead of sending."""
    from app.clients.wechat_client import send_text_message
    
    # Mock mode should be enabled via settings
    with patch('app.config.settings.mock_mode', True):
        # Send a message in mock mode
        result = await send_text_message("test_openid_123", "Hello from mock")
        
        # Verify mock response
        assert result["errcode"] == 0
        assert result["errmsg"] == "ok"
        assert "msgid" in result
        
        # Verify message was logged in mock client
        mock_client = get_mock_wechat_client("test_appid", "test_secret")
        assert len(mock_client.sent_messages) == 1
        assert mock_client.sent_messages[0]["openid"] == "test_openid_123"
        assert mock_client.sent_messages[0]["content"] == "Hello from mock"


@pytest.mark.asyncio
async def test_mock_mode_cxone_posting():
    """Test that mock mode logs CXone messages instead of posting."""
    from app.clients.cxone_client import get_cxone_client
    
    # Mock mode should be enabled via settings
    with patch('app.config.settings.mock_mode', True):
        cxone_client = await get_cxone_client()
        
        # Post a message in mock mode
        result = await cxone_client.post_message("test_openid_456", "Hello to CXone")
        
        # Verify mock response
        assert result["status"] == "created"
        assert "id" in result
