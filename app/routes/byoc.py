"""BYOC integration endpoints."""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from app.auth import create_access_token, verify_token
from app.config import settings
from app.clients.wechat_client import send_text_message
from app.models.messages import CXoneMessagePayload, ErrorResponse
from app.exceptions import AuthenticationError, ValidationError, WeChatAPIError, MessageProcessingError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TokenRequest(BaseModel):
    """Request model for OAuth token endpoint."""
    client_id: str = Field(..., min_length=1, max_length=128)
    client_secret: str = Field(..., min_length=1, max_length=256)
    grant_type: str = Field(..., min_length=1, max_length=50)
    
    @validator('grant_type')
    def validate_grant_type(cls, v):
        if v != "client_credentials":
            raise ValueError("grant_type must be 'client_credentials'")
        return v


class TokenResponse(BaseModel):
    """Response model for OAuth token endpoint."""
    access_token: str
    token_type: str
    expires_in: int


class MessageResponse(BaseModel):
    """Response model for message posting endpoint."""
    idOnExternalPlatform: str


def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate Bearer token from Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The token string
        
    Raises:
        AuthenticationError: If token is missing or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    if not token:
        raise AuthenticationError("Token is empty")
    
    payload = verify_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    return token


@router.post("/1.0/token", response_model=TokenResponse)
async def get_token(request: Request, token_request: TokenRequest):
    """
    OAuth2 client credentials token endpoint.
    
    Validates client credentials and returns a JWT access token.
    """
    # Validate client credentials
    if token_request.client_id != settings.client_id or token_request.client_secret != settings.client_secret:
        raise AuthenticationError("Invalid client credentials")
    
    # Generate JWT token
    access_token = create_access_token(token_request.client_id)
    
    logger.info("token_generated", client_id=token_request.client_id)
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=24 * 60 * 60  # 24 hours in seconds
    )


@router.post("/1.0/posts/{id}/messages", response_model=MessageResponse)
async def post_message(
    id: str,
    request: Request,
    token: str = Depends(get_bearer_token)
):
    """
    Post a message to a specific post.
    
    Requires Bearer token authentication, validates payload,
    and forwards the message to WeChat.
    """
    # Validate post ID
    if not id or len(id) > 128:
        raise ValidationError("Invalid post ID")
    
    # Get and validate request body
    try:
        body = await request.json()
        payload = CXoneMessagePayload(**body)
    except Exception as e:
        raise ValidationError(
            "Invalid request payload",
            details={"error": str(e)}
        )
    
    logger.info(
        "received_cxone_message",
        post_id=id,
        payload_keys=list(payload.dict().keys()),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    # Extract WeChat openid and message text using validated model
    openid = payload.get_openid()
    text = payload.get_text()
    
    # Validate required fields
    if not openid:
        raise MessageProcessingError(
            "Could not extract openid from payload",
            details={"payload": payload.dict()}
        )
    
    if not text:
        raise MessageProcessingError(
            "Could not extract message text from payload",
            details={"payload": payload.dict()}
        )
    
    # Send to WeChat
    try:
        result = await send_text_message(openid, text)
        logger.info(
            "message_sent_to_wechat",
            openid=openid,
            post_id=id,
            msgid=result.get("msgid")
        )
    except WeChatAPIError as e:
        # Log error but don't fail the request - CXone expects success
        # In production, you might want to queue for retry
        logger.error(
            "failed_to_send_to_wechat",
            openid=openid,
            post_id=id,
            error=str(e),
            error_details=e.details
        )
        # Still return success to CXone to avoid retries
        # TODO: Implement message queue for retry
    
    # Generate and return UUID (preserve existing behavior)
    message_id = str(uuid.uuid4())
    logger.info("message_processed", post_id=id, message_id=message_id)
    
    return MessageResponse(idOnExternalPlatform=message_id)
