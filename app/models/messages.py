"""Message models for request/response validation."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ThreadInfo(BaseModel):
    """Thread information model."""
    idOnExternalPlatform: Optional[str] = Field(None, description="External platform ID (WeChat openid)")
    
    @validator('idOnExternalPlatform')
    def validate_openid(cls, v):
        if v and len(v) > 128:
            raise ValueError('idOnExternalPlatform must be 128 characters or less')
        return v


class MessageContent(BaseModel):
    """Message content model."""
    text: Optional[str] = Field(None, description="Message text content")
    type: Optional[str] = Field("text", description="Message type")
    content: Optional[str] = Field(None, description="Alternative content field")
    
    @validator('text', 'content')
    def validate_text_length(cls, v):
        if v and len(v) > 10000:  # Reasonable limit for text messages
            raise ValueError('Message text must be 10000 characters or less')
        return v


class RecipientInfo(BaseModel):
    """Recipient information model."""
    idOnExternalPlatform: Optional[str] = None


class CXoneMessagePayload(BaseModel):
    """Validated model for CXone message payload."""
    thread: Optional[ThreadInfo] = None
    recipient: Optional[RecipientInfo] = None
    message: Optional[MessageContent] = None
    text: Optional[str] = Field(None, max_length=10000)
    content: Optional[str] = Field(None, max_length=10000)
    externalId: Optional[str] = None
    openid: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow additional fields for flexibility
    
    def get_openid(self) -> Optional[str]:
        """Extract WeChat openid from payload."""
        if self.thread and self.thread.idOnExternalPlatform:
            return self.thread.idOnExternalPlatform
        if self.recipient and self.recipient.idOnExternalPlatform:
            return self.recipient.idOnExternalPlatform
        if self.externalId:
            return self.externalId
        if self.metadata and isinstance(self.metadata, dict):
            openid = self.metadata.get('openid')
            if openid:
                return str(openid)
        if self.openid:
            return str(self.openid)
        return None
    
    def get_text(self) -> Optional[str]:
        """Extract message text from payload."""
        if self.message:
            if self.message.text:
                return self.message.text
            if self.message.content:
                return self.message.content
        if self.text:
            return self.text
        if self.content:
            return self.content
        return None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

