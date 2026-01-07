"""CXone Digital Engagement API client utilities."""
import logging
import requests
from app.config import settings
from app.mock_clients import get_mock_cxone_client


logger = logging.getLogger(__name__)


def post_inbound_to_cxone(openid: str, text: str) -> dict:
    """
    Post an inbound message to CXone Digital Engagement.
    
    Args:
        openid: The WeChat user's openid (used as external platform ID)
        text: The message text content
        
    Returns:
        Response dict from CXone API or mock response
        
    Raises:
        Exception: If posting fails (only in non-mock mode)
    """
    if settings.mock_mode:
        # Mock mode: use mock client
        mock_client = get_mock_cxone_client(
            settings.cxone_base_url,
            settings.cxone_bearer_token,
            settings.cxone_channel_id
        )
        return mock_client.post_message(openid, text)
    
    # Real mode: use actual CXone API
    url = f"{settings.cxone_base_url}/channels/{settings.cxone_channel_id}/messages"
    
    # Construct payload for CXone Digital Engagement API
    # TODO: Adjust payload structure based on actual CXone API requirements
    # This is a placeholder structure - verify with CXone API documentation
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
        "Authorization": f"Bearer {settings.cxone_bearer_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Posted message to CXone for openid {openid}: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to post message to CXone for openid {openid}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}, body: {e.response.text}")
        raise

