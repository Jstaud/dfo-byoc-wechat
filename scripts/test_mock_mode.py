#!/usr/bin/env python3
"""Simple script to test the middleware in mock mode."""
import os
import sys
import requests
import json
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set mock mode before importing app modules
os.environ['MOCK_MODE'] = 'true'
os.environ['CLIENT_ID'] = 'test_client'
os.environ['CLIENT_SECRET'] = 'test_secret'
os.environ['JWT_SECRET'] = 'test_jwt_secret'
os.environ['WECHAT_APPID'] = 'test_appid'
os.environ['WECHAT_APPSECRET'] = 'test_secret'
os.environ['WECHAT_TOKEN'] = 'test_token'
os.environ['CXONE_BASE_URL'] = 'http://localhost:8001'
os.environ['CXONE_BEARER_TOKEN'] = 'test_token'
os.environ['CXONE_CHANNEL_ID'] = 'test_channel'

from app.mock_clients import reset_mock_clients, get_mock_wechat_client, get_mock_cxone_client
import asyncio


async def test_mock_mode():
    """Test mock mode functionality."""
    print("=" * 60)
    print("Testing Mock Mode")
    print("=" * 60)
    
    # Reset mocks
    reset_mock_clients()
    
    # Import after setting env vars
    from app.clients.wechat_client import send_text_message
    from app.clients.cxone_client import get_cxone_client
    
    print("\n1. Testing WeChat message sending (mock mode)...")
    result = await send_text_message("test_openid_123", "Hello from mock WeChat!")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    wechat_mock = get_mock_wechat_client("test_appid", "test_secret")
    print(f"   Messages sent: {len(wechat_mock.sent_messages)}")
    print(f"   Last message: {wechat_mock.sent_messages[-1]}")
    
    print("\n2. Testing CXone message posting (mock mode)...")
    cxone_client = await get_cxone_client()
    result = await cxone_client.post_message("test_openid_456", "Hello to mock CXone!")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    cxone_mock = get_mock_cxone_client("http://localhost:8001", "test_token", "test_channel")
    print(f"   Messages posted: {len(cxone_mock.posted_messages)}")
    print(f"   Last message: {cxone_mock.posted_messages[-1]}")
    
    print("\n" + "=" * 60)
    print("Mock mode test completed successfully!")
    print("=" * 60)
    print("\nAll messages were logged instead of being sent to real APIs.")
    print("You can inspect the mock clients to see captured messages.")


if __name__ == '__main__':
    asyncio.run(test_mock_mode())

