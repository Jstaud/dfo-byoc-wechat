"""WeChat Service Account client utilities."""
from wechatpy import WeChatClient
from app.config import settings
from app.mock_clients import get_mock_wechat_client


def get_wechat_client():
    """
    Construct and return a WeChatClient instance (real or mock).
    
    Returns:
        Configured WeChatClient or MockWeChatClient using app settings
    """
    if settings.mock_mode:
        return get_mock_wechat_client(settings.wechat_appid, settings.wechat_appsecret)
    return WeChatClient(settings.wechat_appid, settings.wechat_appsecret)


def send_text_message(openid: str, content: str) -> dict:
    """
    Send a plain text message to a WeChat user.
    
    Args:
        openid: The WeChat user's openid
        content: The text message content to send
        
    Returns:
        Response dict from WeChat API or mock response
        
    Raises:
        Exception: If message sending fails (only in non-mock mode)
    """
    client = get_wechat_client()
    
    if settings.mock_mode:
        # Mock mode: use mock client's send_text_message method
        return client.send_text_message(openid, content)
    else:
        # Real mode: use actual WeChat API
        result = client.message.send_text(openid, content)
        return result

