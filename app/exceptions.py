"""Custom exceptions for the application."""
from typing import Optional, Dict, Any


class ApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(ApplicationError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class ExternalAPIError(ApplicationError):
    """Raised when external API calls fail."""
    
    def __init__(self, message: str, service: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        self.service = service
        details = details or {}
        details["service"] = service
        super().__init__(message, status_code=status_code, details=details)


class CXoneAPIError(ExternalAPIError):
    """Raised when CXone API calls fail."""
    
    def __init__(self, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, service="CXone", status_code=status_code, details=details)


class WeChatAPIError(ExternalAPIError):
    """Raised when WeChat API calls fail."""
    
    def __init__(self, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, service="WeChat", status_code=status_code, details=details)


class MessageProcessingError(ApplicationError):
    """Raised when message processing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)

