# DFO BYOC WeChat Integration

A FastAPI application that acts as a middleware bridge between CXone Digital Engagement and WeChat Service Accounts. The application handles OAuth client credentials flow for BYOC authentication and bidirectional message routing between WeChat and CXone.

This repository implements a Bring Your Own Channel (BYOC) middleware that bridges an external messaging platform (for example, a social or messaging app) with NICE CXone Digital Engagement. I made this so that others who need to integrate Wechat with the Bring Your Own Channel (BYOC) feature on the Nice CXOne platform would have a little more information and hopefully saves them time. 

The middleware is intentionally thin, stateless, and single-tenant, acting only as a transport layer between the external platform and CXone. All routing, skills, agent handling, and business logic are configured inside CXone, not in this service. The only exception is that I haven't implemented a channel create, update, delete endpoint set so you will have to manually create the channel once using the DFO api to get a channelid.

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads())

<a href="https://buymeacoffee.com/jamesstaud" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

## Features

- OAuth 2.0 client credentials grant endpoint for BYOC authentication
- Message posting endpoint with bearer token authentication
- WeChat webhook endpoints for receiving messages from WeChat users
- Bidirectional message routing:
  - **WeChat → CXone**: Receives WeChat messages and forwards to CXone Digital Engagement
  - **CXone → WeChat**: Receives CXone messages and sends to WeChat users
- UUID generation for message responses
- Request logging
- Support for encrypted WeChat messages (optional)

## Prerequisites

- Python 3.8 or higher
- CXone account with appropriate permissions
- WeChat Service Account (微信公众号) with API access
- (Optional) NGROK for local development

## CXone Configuration

### 1. Create BYOC Integration

1. Navigate to the CXone Admin Portal
2. Create a new BYOC integration with the following details:
   - Name: (Choose a descriptive name)
   - Integration Box URL: `<<your base URL>>/integration/box`
   - Authorization URL: `<<your base URL>>/integration/box/1.0/token`
   - Client ID: `2f52ebe1-45d0-4f36-a9d0-a94c788f53c6`
   - Client Secret: `a2051bd7-462e-4817-a28e-bedfb570d739`
   - Color: (Choose a color for the channel selector)
   - Icon: (Choose an icon for the channel selector)
   - Leave "Use DFO 3.0 Outbound API for replies" disabled

Note: The following URLs are not implemented in this sample app but may be needed in a production implementation:
- Action URL: `/integration/action`
- Reconnect URL: `/integration/reconnect`
- Remove URL: `/integration/remove`

Save the configuration and note the Integration ID provided.

### 2. Generate CXone JWT

1. Create Access Key/Secret:
   - Follow the instructions at [Manage Access Keys](https://help.nice-incontact.com/content/admin/security/manageaccesskeys.htm)

2. Authorize using the endpoint:
   - Follow the authentication process described in [Getting Started](https://developer.niceincontact.com/Documentation/GettingStarted)

### 3. Create Channel

Create a channel in your integration using the API:
- [Channel Create API](https://developer.niceincontact.com/API/DigitalEngagementAPI#/Channel%20(Point%20of%20Contact)/create-update-Channel)

### 4. Optional: NGROK Setup for Local Development

1. Install NGROK and configure with your token
2. Start the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
   ```
3. In a separate terminal, run:
   ```bash
   ngrok http 3000
   ```
4. Update the BYOC integration configuration and WeChat webhook URL with the NGROK URL

### 5. Test Message Flow

1. Create a new inbound message using the API:
   - [Create Message API](https://developer.niceincontact.com/API/DigitalEngagementAPI#/Message/channels-channelId-createmessage)
   - Use the Channel ID from step 3

2. In the agent application (CXA or MAX):
   - Search for the conversation
   - Send a reply

### Expected Flow

1. Initial message attempt (401 Unauthorized)
2. Token request to `/integration/box/1.0/token`
3. Second message attempt with valid token
4. Webhook delivery

Monitor the application console and NGROK monitor for request/response details.

## Installation

1. Clone the repository
2. Ensure you have Python 3.8 or higher installed
3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration values:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your actual values. See the Environment Variables section below for details.

   **Quick start for testing**: For testing without real APIs, set `MOCK_MODE=true` in your `.env` file. See the "Testing Without Real API Connectivity" section below for details.

5. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

For production deployment, use:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

The application will be available at `http://localhost:3000` with the following endpoints:
- `GET /health` - Health check endpoint
- `POST /integration/box/1.0/token` - OAuth token endpoint
- `POST /integration/box/1.0/posts/{id}/messages` - Message posting endpoint (CXone → WeChat)
- `GET /wechat/webhook` - WeChat webhook validation endpoint
- `POST /wechat/webhook` - WeChat message receiving endpoint (WeChat → CXone)

## Testing

### Running Unit Tests

Run the test suite with pytest:

```bash
pytest tests/
```

The test suite includes:
- WeChat webhook signature validation (success and failure cases)
- WeChat message processing with mocked CXone API calls
- Mock mode functionality

For more verbose output:
```bash
pytest tests/ -v
```

### Testing Without Real API Connectivity

The application supports **mock mode** which allows you to test the middleware without actual CXone or WeChat connectivity. This is useful for:
- Local development
- Testing message flow logic
- Debugging payload extraction
- Integration testing

#### Option 1: Built-in Mock Mode (Recommended)

The simplest way to test without real APIs is to enable mock mode using an environment variable:

1. Set `MOCK_MODE=true` in your `.env` file:
```bash
MOCK_MODE=true
# ... other settings still required but won't be used for API calls
WECHAT_APPID=test_appid
WECHAT_APPSECRET=test_secret
WECHAT_TOKEN=test_token
CLIENT_ID=test_client
CLIENT_SECRET=test_secret
JWT_SECRET=test_jwt_secret
CXONE_BASE_URL=http://localhost:8001
CXONE_BEARER_TOKEN=test_token
CXONE_CHANNEL_ID=test_channel
```

2. Start the application normally:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

3. In mock mode:
   - **WeChat messages**: Logged to console instead of being sent
   - **CXone messages**: Logged to console instead of being posted
   - All message data is captured and can be inspected

**Example mock mode output:**
```
[MOCK] Would send WeChat message to test_openid_123: Hello from agent
[MOCK] Would post to CXone for openid test_openid_456: Hello from user
```

#### Option 2: Mock HTTP Servers

For more realistic testing with actual HTTP requests, you can run mock servers:

1. Start the mock servers (in separate terminals):
```bash
# Terminal 1: Mock CXone server
python scripts/mock_servers.py cxone 8001

# Terminal 2: Mock WeChat server  
python scripts/mock_servers.py wechat 8002

# Or run both together:
python scripts/mock_servers.py
```

2. Configure your `.env` to point to mock servers:
```bash
MOCK_MODE=false  # Use real HTTP clients but point to mock servers
CXONE_BASE_URL=http://localhost:8001
# WeChat client will still need real credentials, but you can use mock mode
```

3. The mock servers will:
   - Accept POST requests and log them
   - Return realistic response structures
   - Allow you to inspect incoming payloads

#### Option 3: Manual Testing with curl/httpie

You can test individual endpoints without full integration:

**Test WeChat webhook validation:**
```bash
# Generate a valid signature (you'll need to implement this or use a test tool)
curl "http://localhost:3000/wechat/webhook?signature=test&timestamp=1234567890&nonce=test&echostr=hello"
```

**Test BYOC token endpoint:**
```bash
curl -X POST http://localhost:3000/integration/box/1.0/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "grant_type": "client_credentials"
  }'
```

**Test BYOC message endpoint (with mock mode enabled):**
```bash
# First get a token, then:
curl -X POST http://localhost:3000/integration/box/1.0/posts/test123/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "thread": {
      "idOnExternalPlatform": "test_wechat_openid"
    },
    "message": {
      "text": "Hello from CXone"
    }
  }'
```

**Test WeChat webhook with sample XML:**
```bash
curl -X POST "http://localhost:3000/wechat/webhook?signature=test&timestamp=1234567890&nonce=test" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<xml>
  <ToUserName><![CDATA[toUser]]></ToUserName>
  <FromUserName><![CDATA[fromUser]]></FromUserName>
  <CreateTime>1348831860</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[Hello WeChat]]></Content>
  <MsgId>1234567890123456</MsgId>
</xml>'
```

#### Inspecting Mock Messages

When using mock mode, you can inspect captured messages programmatically:

```python
from app.mock_clients import get_mock_wechat_client, get_mock_cxone_client

# Get mock clients and inspect messages
wechat_mock = get_mock_wechat_client("appid", "secret")
cxone_mock = get_mock_cxone_client("url", "token", "channel")

print("WeChat messages sent:", wechat_mock.sent_messages)
print("CXone messages posted:", cxone_mock.posted_messages)
```

#### Testing Tips

1. **Use mock mode for development**: Enable `MOCK_MODE=true` to avoid API rate limits and costs
2. **Test payload extraction**: Use mock mode to verify that openid and text extraction works with your expected CXone payload structure
3. **Test error handling**: Temporarily break mock servers or use invalid credentials to test error paths
4. **Use pytest fixtures**: The test suite includes fixtures for resetting mocks between tests
5. **Monitor logs**: All mock operations are logged, making it easy to trace message flow

## Environment Variables

All environment variables are configured in a `.env` file. A template is provided in `.env.example`.

**Quick Setup:**
```bash
cp .env.example .env
# Then edit .env with your actual values
```

The following environment variables are required:

### BYOC OAuth Settings (Required)
- `CLIENT_ID`: OAuth client ID for BYOC authentication (provided by CXone)
- `CLIENT_SECRET`: OAuth client secret for BYOC authentication (provided by CXone)
- `JWT_SECRET`: Secret key for JWT token signing (generate with: `openssl rand -hex 32`)
- `PORT`: The port the server will listen on (default: 3000)

### WeChat Service Account Settings (Required)
- `WECHAT_APPID`: WeChat Service Account AppID (from WeChat Official Account Platform)
- `WECHAT_APPSECRET`: WeChat Service Account AppSecret (from WeChat Official Account Platform)
- `WECHAT_TOKEN`: Token for WeChat webhook signature validation (configured in WeChat admin)
- `WECHAT_ENCODING_AES_KEY`: (Optional) Encoding AES key for encrypted messages

### CXone Digital Engagement Settings (Required)
- `CXONE_BASE_URL`: Base URL for CXone Digital Engagement API (e.g., `https://api.nice-incontact.com`)
- `CXONE_BEARER_TOKEN`: Bearer token for CXone API authentication (obtained via OAuth flow)
- `CXONE_CHANNEL_ID`: Channel ID in CXone Digital Engagement (created in your integration)

### Optional Settings
- `MOCK_MODE`: Set to `true` to enable mock mode for testing (default: `false`)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `INFO`)
- `JSON_LOGS`: Set to `true` for JSON log output (default: `false`)
- `HTTP_TIMEOUT`: HTTP request timeout in seconds (default: `30`)
- `HTTP_MAX_RETRIES`: Maximum retry attempts for failed requests (default: `3`)

See `.env.example` for a complete template with detailed comments and example values.

## WeChat Configuration

### 1. Configure WeChat Service Account Webhook

1. Log in to [WeChat Official Account Platform](https://mp.weixin.qq.com/)
2. Navigate to **Development** → **Basic Configuration**
3. Configure the server URL:
   - **URL**: `https://your-domain.com/wechat/webhook`
   - **Token**: Set this to match your `WECHAT_TOKEN` environment variable
   - **EncodingAESKey**: (Optional) Set if using encrypted messages
4. Enable **Message Encryption** if you want to use encrypted messages
5. Save the configuration

### 2. Test WeChat Webhook

WeChat will send a GET request to verify your webhook endpoint. The application automatically handles this validation.

## Message Flow

### WeChat → CXone Flow

When a WeChat user sends a message:

```mermaid
sequenceDiagram
    participant User as WeChat User
    participant WeChat as WeChat Platform
    participant App as Integration App
    participant CXone as CXone Digital Engagement

    User->>WeChat: Sends text message
    WeChat->>App: POST /wechat/webhook<br/>(with signature validation)
    App->>App: Validate signature
    App->>App: Parse XML message
    App->>App: Extract openid and text
    App->>CXone: POST /channels/{channelId}/messages<br/>(with Bearer token)
    CXone-->>App: Message created
    App-->>WeChat: HTTP 200 (success)
    WeChat-->>User: (No auto-reply by default)
```

### CXone → WeChat Flow

When an agent sends a message through CXone:

```mermaid
sequenceDiagram
    participant Agent as CXone Agent
    participant CXone as CXone Digital Engagement
    participant App as Integration App
    participant WeChat as WeChat Platform
    participant User as WeChat User

    Agent->>CXone: Sends message via agent interface
    CXone->>App: POST /integration/box/1.0/posts/{id}/messages<br/>(with Bearer JWT)
    App->>App: Validate JWT token
    App->>App: Extract openid and text from payload
    App->>WeChat: Send text message via WeChat API
    WeChat-->>App: Message sent confirmation
    App-->>CXone: { "idOnExternalPlatform": "<uuid>" }
    CXone-->>Agent: Message delivery confirmation
    WeChat->>User: Delivers message to user
```

## API Endpoints

### 1. Get OAuth Token
```
POST /integration/box/1.0/token
Content-Type: application/json

{
  "client_id": "2f52ebe1-45d0-4f36-a9d0-a94c788f53c6",
  "client_secret": "a2051bd7-462e-4817-a28e-bedfb570d739",
  "grant_type": "client_credentials"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### 2. Post Message (CXone → WeChat)
```
POST /integration/box/1.0/posts/{id}/messages
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "thread": {
    "idOnExternalPlatform": "wechat_openid_here"
  },
  "message": {
    "text": "Hello from CXone agent"
  }
}
```

**Note**: The exact payload structure depends on CXone's API. The application attempts to extract the openid and message text from various possible field locations (see Known Gaps section).

Response:
```json
{
  "idOnExternalPlatform": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. WeChat Webhook Validation (GET)
```
GET /wechat/webhook?signature={signature}&timestamp={timestamp}&nonce={nonce}&echostr={echostr}
```

Response (on success):
```
{echostr}
```

This endpoint is called by WeChat during webhook configuration to verify the endpoint.

### 4. WeChat Webhook Message Receiving (POST)
```
POST /wechat/webhook?signature={signature}&timestamp={timestamp}&nonce={nonce}
Content-Type: application/xml

<xml>
  <ToUserName><![CDATA[toUser]]></ToUserName>
  <FromUserName><![CDATA[fromUser]]></FromUserName>
  <CreateTime>1348831860</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[Hello WeChat]]></Content>
  <MsgId>1234567890123456</MsgId>
</xml>
```

Response:
```
HTTP 200 (empty body, no auto-reply)
```

The application parses the message, extracts the sender's openid and message text, and forwards it to CXone Digital Engagement.

## Error Responses

### Invalid Grant Type
```json
{
  "error": "unsupported_grant_type"
}
```

### Invalid Client Credentials
```json
{
  "error": "invalid_client"
}
```

### Invalid Token
```json
{
  "error": "Invalid token"
}
```

## Known Gaps and Limitations

This implementation includes several areas that require customization based on your specific CXone and WeChat configurations:

### 1. CXone Message Payload Structure

**Location**: `app/cxone_client.py` (line 27-38)

The payload structure for posting messages to CXone Digital Engagement is a placeholder. The current implementation assumes:
```json
{
  "thread": {
    "idOnExternalPlatform": "<openid>"
  },
  "message": {
    "text": "<message_text>",
    "type": "text"
  },
  "direction": "inbound"
}
```

**Action Required**: Verify the actual CXone Digital Engagement API payload structure and update accordingly.

### 2. OpenID Extraction from CXone Payload

**Location**: `app/routes/byoc.py` (line 101-133)

The function `get_wechat_openid_from_payload()` attempts to extract the WeChat openid from multiple possible field locations:
- `payload.thread.idOnExternalPlatform`
- `payload.recipient.idOnExternalPlatform`
- `payload.externalId`
- `payload.metadata.openid`
- `payload.openid`

**Action Required**: Determine the actual field name in CXone's message payload that contains the WeChat openid and update the extraction logic.

### 3. Message Text Extraction from CXone Payload

**Location**: `app/routes/byoc.py` (line 136-160)

The function `get_message_text_from_payload()` attempts to extract message text from:
- `payload.message.text`
- `payload.text`
- `payload.content`
- `payload.message.content`

**Action Required**: Determine the actual field name in CXone's message payload that contains the message text and update the extraction logic.

### 4. WeChat Encrypted Message Handling

**Location**: `app/routes/wechat.py` (line 78-95)

The implementation supports encrypted WeChat messages but includes a TODO regarding `msg_signature` extraction. Currently, it attempts to extract `msg_signature` from query parameters.

**Action Required**: Verify whether `msg_signature` is always in query parameters for encrypted messages or if it needs to be extracted from the XML body.

### 5. Error Handling and Retry Logic

- **CXone API failures**: Currently, if posting to CXone fails, the error is logged but the WeChat webhook still returns 200 to prevent retries. Consider implementing retry logic or a dead-letter queue.
- **WeChat API failures**: If sending to WeChat fails, the error is logged but the BYOC endpoint still returns success to CXone. Consider implementing retry logic or error responses.

### 6. Message Type Support

Currently, only **text messages** are supported:
- WeChat → CXone: Only text messages are processed
- CXone → WeChat: Only text messages are sent

**Action Required**: Extend support for other message types (images, videos, files, etc.) if needed.

### 7. BYOC Action/Reconnect/Remove Endpoints

The following BYOC endpoints are not implemented but may be needed:
- `/integration/action`
- `/integration/reconnect`
- `/integration/remove`

**Action Required**: Implement these endpoints if required by your CXone BYOC configuration.

### 8. Testing

Basic tests are included for WeChat webhook signature validation and message processing. Additional tests should be added for:
- CXone payload extraction logic
- Error handling scenarios
- Encrypted message handling
- End-to-end message flow

## Notes

- Tokens expire after 24 hours
- All requests are logged to the console
- No payload validation is performed beyond basic structure checks
- This is a sample application and should not be used in production without:
  - Addressing all known gaps listed above
  - Implementing proper error handling and retry logic
  - Adding comprehensive logging and monitoring
  - Implementing rate limiting and security measures
  - Adding input validation and sanitization 