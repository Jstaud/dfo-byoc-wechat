"""Tests for BYOC endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.auth import create_access_token


client = TestClient(app)


def test_token_endpoint_success():
    """Test successful token generation."""
    response = client.post(
        "/integration/box/1.0/token",
        json={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "grant_type": "client_credentials"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 86400


def test_token_endpoint_invalid_grant_type():
    """Test token endpoint with invalid grant type."""
    response = client.post(
        "/integration/box/1.0/token",
        json={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "grant_type": "invalid_grant"
        }
    )
    assert response.status_code == 422  # Validation error


def test_token_endpoint_invalid_credentials():
    """Test token endpoint with invalid credentials."""
    response = client.post(
        "/integration/box/1.0/token",
        json={
            "client_id": "wrong_client",
            "client_secret": "wrong_secret",
            "grant_type": "client_credentials"
        }
    )
    assert response.status_code == 401


def test_post_message_with_valid_token():
    """Test posting a message with valid token."""
    # First get a token
    token_response = client.post(
        "/integration/box/1.0/token",
        json={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "grant_type": "client_credentials"
        }
    )
    token = token_response.json()["access_token"]
    
    # Mock WeChat client
    mock_wechat = AsyncMock()
    mock_wechat.send_text_message = AsyncMock(return_value={"errcode": 0, "msgid": "test_msgid"})
    
    with patch('app.routes.byoc.send_text_message', mock_wechat.send_text_message):
        response = client.post(
            "/integration/box/1.0/posts/test123/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "thread": {
                    "idOnExternalPlatform": "test_openid"
                },
                "message": {
                    "text": "Hello from CXone"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "idOnExternalPlatform" in data


def test_post_message_invalid_token():
    """Test posting a message with invalid token."""
    response = client.post(
        "/integration/box/1.0/posts/test123/messages",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "thread": {"idOnExternalPlatform": "test_openid"},
            "message": {"text": "Hello"}
        }
    )
    assert response.status_code == 401


def test_post_message_missing_openid():
    """Test posting a message without openid."""
    # Get a valid token
    token_response = client.post(
        "/integration/box/1.0/token",
        json={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "grant_type": "client_credentials"
        }
    )
    token = token_response.json()["access_token"]
    
    response = client.post(
        "/integration/box/1.0/posts/test123/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": {
                "text": "Hello"
            }
        }
    )
    # Should fail validation - missing openid
    assert response.status_code in [422, 400]

