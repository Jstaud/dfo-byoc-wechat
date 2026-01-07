"""Pytest configuration and fixtures."""
import pytest
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings for tests."""
    # Set minimal required env vars
    test_env = {
        "CLIENT_ID": "test_client_id",
        "CLIENT_SECRET": "test_client_secret",
        "JWT_SECRET": "test_jwt_secret",
        "WECHAT_APPID": "test_wechat_appid",
        "WECHAT_APPSECRET": "test_wechat_secret",
        "WECHAT_TOKEN": "test_wechat_token",
        "CXONE_BASE_URL": "http://localhost:8001",
        "CXONE_BEARER_TOKEN": "test_cxone_token",
        "CXONE_CHANNEL_ID": "test_channel_id",
        "MOCK_MODE": "true",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    # Reload settings
    from app.config import Settings
    import importlib
    import app.config
    importlib.reload(app.config)
    
    yield
    
    # Cleanup
    for key in test_env.keys():
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def mock_cxone_client():
    """Mock CXone client for tests."""
    mock_client = AsyncMock()
    mock_client.post_message = AsyncMock(return_value={"id": "test_message_id", "status": "created"})
    return mock_client


@pytest.fixture
def mock_wechat_client():
    """Mock WeChat client for tests."""
    mock_client = AsyncMock()
    mock_client.send_text_message = AsyncMock(return_value={"errcode": 0, "errmsg": "ok", "msgid": "test_msgid"})
    return mock_client

