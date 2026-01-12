# NICE CXone BYOC – External Messaging Middleware

This repository implements a Bring Your Own Channel (BYOC) middleware that bridges an external messaging platform (for example, a social or messaging app) with NICE CXone Digital Engagement.

The middleware is intentionally thin, stateless, and single-tenant, acting only as a transport layer between the external platform and CXone. All routing, skills, agent handling, and business logic are configured inside CXone, not in this service.

---

## Purpose & Design Principles

Primary goals:
- Enable external users to communicate with CXone agents
- Conform strictly to NICE CXone BYOC and Digital Engagement expectations
- Avoid unnecessary state, storage, or routing logic

Non-goals:
- Multi-tenant BYOC support
- Dynamic channel creation
- Customer or thread lifecycle management outside CXone
- Business-hours logic or routing in middleware

Design rule:
The middleware only moves messages. CXone owns everything else.

---

## High-Level Architecture

``` 
External User
   ↓
External Messaging Platform
   ↓
BYOC Middleware (this repository)
   ↓
NICE CXone Digital Engagement
   ↓
CXone Agent Console
```

Message flow is bidirectional:
- Inbound: External Platform → Middleware → CXone
- Outbound: CXone Agent → Middleware → External Platform

---

## Required BYOC Endpoints

This implementation supports only the minimum required endpoints for a single-channel BYOC integration.

### 1. OAuth Token Endpoint (CXone → Middleware)

``` 
POST /oauth/token
```

Used by CXone to exchange:
- `client_id`
- `client_secret`

The middleware returns a standard OAuth access token response.

Notes:
- The path must end in `/oauth/token`
- Token lifetime is short-lived
- No refresh token support is required
- API gateways or identity providers may front this endpoint

---

### 2. Outbound Message Callback (CXone → Middleware)

```
POST /channels/{channelId}/outbound
```

Invoked by CXone when:
- An agent sends a message
- An agent sends an attachment

The payload includes:
- `channelId`
- `thread.idOnExternalPlatform`
- Message content
- Attachment metadata

The middleware maps the CXone thread back to the correct external conversation and forwards the message to the external platform API.

---

## Sending Messages into CXone (External Platform → CXone)

All inbound messages are sent to CXone using one API only:

```
POST /channels/{channelId}/messages
```

CXone automatically:
- Creates customers
- Creates threads
- Associates messages correctly

The following APIs are not used:
- Threads API
- Customers API
- Inbound/outbound trigger APIs

---

## Identity & Threading Model

CXone distinguishes three separate external identifiers, all controlled by the middleware.

### Customer Identity
```
author.endUserIdentity.idOnExternalPlatform
```
- Stable identifier
- Represents the external user ID
- Used to associate conversations over time

### Thread Identity
```
thread.idOnExternalPlatform
```
- Represents a conversation session
- Controlled by the middleware
- Multiple messages may belong to one thread

### Message Identity
```
message.idOnExternalPlatform
```
- Unique per message
- Used only for message-level tracking

These identifiers are not interchangeable and must remain consistent.

---

## Message Direction

The `direction` field is informational only:
- `inbound` for messages from the external user
- `outbound` for messages from bots or agents

Direction does not affect routing behavior.

---

## Skills, Routing & Studio

- Routing queues in CXone are called Skills
- Skills are assigned per channel
- Messages are routed automatically when created
- No skill or queue identifier is passed in the API payload

Studio scripts may be used for:
- Business hours logic
- Auto-responses
- Advanced routing
- Menu-style interaction flows

All routing and business logic belongs in CXone, not the middleware.

---

## Attachments

- Maximum attachment size is approximately 40 MB
- Attachments are referenced using publicly accessible URLs
- CXone provides signed URLs valid for a short time window
- Middleware must download or forward immediately
- URLs must not be persisted

---

## Security Model

- OAuth token-based authentication only
- No HMAC
- No JWT callback signing
- No message-level encryption
- HTTPS/TLS is required

---

## Channel Creation & Configuration

- The BYOC channel is created once in the CXone admin UI
- The channel ID is static and reused
- Unused BYOC endpoints may be configured with placeholder URLs
- CXone does not periodically call channel-management endpoints in single-tenant setups

---

## FAQ & Clarifications

The following questions are intentionally collapsed by default.

<details>
<summary><strong>Messaging Model</strong></summary>

Q: Are we using real-time or threaded messaging?  
A: All Digital Engagement BYOC messaging is threaded. Even real-time chat experiences are backed by threads.

</details>

<details>
<summary><strong>Routing & Skills</strong></summary>

Q: How do we specify the routing queue or skill in the message payload?  
A: You do not. Routing is based on the channel’s assigned skill.

Q: Can routing change mid-conversation?  
A: Yes. Studio scripts can re-route conversations at any time.

</details>

<details>
<summary><strong>Studio Scripts & Business Hours</strong></summary>

Q: Do we need a Studio script?  
A: Recommended but not mandatory. Required for business hours, auto-replies, or advanced routing.

Q: Where should business hours logic live?  
A: In CXone (Studio or skill configuration), not in middleware.

</details>

<details>
<summary><strong>BYOC Channel Management</strong></summary>

Q: Do we need to implement POST/PATCH/DELETE channel endpoints?  
A: No. Single-tenant integrations use a manually created static channel.

Q: Is the channel ID permanent?  
A: Yes, unless the channel is deleted and recreated.

</details>

<details>
<summary><strong>Callbacks & URLs</strong></summary>

Q: How do we register the webhook for agent replies?  
A: Configure the outbound callback URL once in the CXone BYOC channel settings.

Q: Should the callback URL be global or channel-specific?  
A: Channel-specific. The channel ID is part of the path.

</details>

<details>
<summary><strong>Which APIs Should Be Used</strong></summary>

Q: Which endpoint should we use to send messages into CXone?  
A: Use `POST /channels/{channelId}/messages`.

Q: Should we use inbound or outbound endpoints to send messages?  
A: No. Those are used by CXone, not the middleware.

</details>

<details>
<summary><strong>Contacts, Threads & Identity</strong></summary>

Q: Do we need to pre-create contacts or threads?  
A: No. CXone auto-creates them on first inbound message.

Q: What happens if multiple messages use the same thread ID?  
A: CXone groups them into the same conversation.

Q: Should external IDs include a prefix?  
A: Either format is acceptable. Consistency is critical.

</details>

<details>
<summary><strong>Attachments & Rich Content</strong></summary>

Q: Do agent replies support images and files?  
A: Yes. Attachments are provided as signed URLs.

Q: Is there a file size limit?  
A: Approximately 40 MB.

</details>

<details>
<summary><strong>Security & Reliability</strong></summary>

Q: Does Digital Engagement support HMAC or JWT callbacks?  
A: No. OAuth and HTTPS only.

Q: Are idempotency keys supported?  
A: No explicit idempotency mechanism exists.

</details>

<details>
<summary><strong>Testing, Monitoring & Operations</strong></summary>

Q: Is there a sandbox environment?  
A: Yes, non-production environments are available.

Q: How can we test without real agents?  
A: Use the CXone Agent Emulator, test skills, and Studio script logging.

Q: What monitoring is available?  
A: Limited API visibility. Middleware logging is essential.

</details>

---

## Final Summary

This middleware is intentionally minimal.

Middleware responsibilities:
- Authenticate CXone
- Relay messages
- Map external identifiers
- Forward attachments

CXone responsibilities:
- Customer lifecycle
- Thread management
- Routing and skills
- Business logic
- Agent experience
