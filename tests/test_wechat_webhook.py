"""Tests for WeChat webhook endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


client = TestClient(app)


def test_wechat_webhook_get_success():
    """Test GET /wechat/webhook with valid signature."""
    # Mock check_signature to return True
    with patch('wechatpy.utils.check_signature', return_value=True):
        response = client.get(
            "/wechat/webhook",
            params={
                "signature": "test_signature",
                "timestamp": "1234567890",
                "nonce": "test_nonce",
                "echostr": "test_echo"
            }
        )
        assert response.status_code == 200
        assert response.text == "test_echo"


def test_wechat_webhook_get_invalid_signature():
    """Test GET /wechat/webhook with invalid signature."""
    # Mock check_signature to return False
    with patch('wechatpy.utils.check_signature', return_value=False):
        response = client.get(
            "/wechat/webhook",
            params={
                "signature": "invalid_signature",
                "timestamp": "1234567890",
                "nonce": "test_nonce",
                "echostr": "test_echo"
            }
        )
        assert response.status_code == 400


def test_wechat_webhook_post_text_message():
    """Test POST /wechat/webhook with a plaintext text message."""
    # Mock signature validation
    with patch('wechatpy.utils.check_signature', return_value=True):
        # Sample WeChat text message XML (plaintext, no encryption)
        xml_message = """<?xml version="1.0" encoding="UTF-8"?>
<xml>
    <ToUserName><![CDATA[toUser]]></ToUserName>
    <FromUserName><![CDATA[fromUser]]></FromUserName>
    <CreateTime>1348831860</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[Hello WeChat]]></Content>
    <MsgId>1234567890123456</MsgId>
</xml>"""
        
        # Mock the CXone client
        mock_cxone = AsyncMock()
        mock_cxone.post_message = AsyncMock(return_value={"id": "test_message_id"})
        
        with patch('app.routes.wechat.get_cxone_client', return_value=mock_cxone):
            response = client.post(
                "/wechat/webhook",
                params={
                    "signature": "test_signature",
                    "timestamp": "1234567890",
                    "nonce": "test_nonce"
                },
                content=xml_message,
                headers={"Content-Type": "application/xml"}
            )
            
            assert response.status_code == 200
            # Verify that post_message was called with correct arguments
            mock_cxone.post_message.assert_called_once()
            call_args = mock_cxone.post_message.call_args
            assert call_args[0][0] == "fromUser"  # openid
            assert call_args[0][1] == "Hello WeChat"  # text content


def test_wechat_webhook_post_invalid_signature():
    """Test POST /wechat/webhook with invalid signature."""
    with patch('wechatpy.utils.check_signature', return_value=False):
        response = client.post(
            "/wechat/webhook",
            params={
                "signature": "invalid_signature",
                "timestamp": "1234567890",
                "nonce": "test_nonce"
            },
            content="<xml></xml>",
            headers={"Content-Type": "application/xml"}
        )
        assert response.status_code == 400
