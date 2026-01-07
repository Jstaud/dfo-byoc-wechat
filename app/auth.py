"""JWT authentication helpers."""
from datetime import datetime, timedelta
from typing import Optional
import jwt  # PyJWT
from app.config import settings


def create_access_token(client_id: str) -> str:
    """
    Create a JWT access token for the given client_id.
    
    Args:
        client_id: The client ID to include in the token payload
        
    Returns:
        A signed JWT token string
    """
    payload = {
        "client_id": client_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string to verify
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

