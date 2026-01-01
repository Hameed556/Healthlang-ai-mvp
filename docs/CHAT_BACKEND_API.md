# Chat Backend API (for Frontend Integration)

This document describes the endpoints your frontend can call to implement a full ChatGPT‑style experience: multiple conversations per user, message history, and server‑side memory.

All endpoints require an authenticated user (JWT) using the existing auth flow (`/api/v1/auth/login`).

## Authentication

- Login: `POST /api/v1/auth/login`
  - Request: `{ "username": "...", "password": "..." }`
  - Response: `{ "access_token": "...", "token_type": "bearer" }`
  - Use header: `Authorization: Bearer <token>` on all chat endpoints

---

## Conversations

### Create a conversation
- `POST /api/v1/chat/conversations`
- Optional body: `{ "title": "My chat" }`
- Response: `{ "conversation_id": "uuid", "title": "My chat" }`

### List conversations (most recent first)
- `GET /api/v1/chat/conversations?limit=50&offset=0`
- Response:
```json
[
  {
    "id": "uuid",
    "title": "Trip to clinic",
    "archived": false,
    "created_at": "2025-10-31T10:00:00Z",
    "updated_at": "2025-10-31T10:05:00Z"
  }
]
```

### Rename / archive
- `PATCH /api/v1/chat/conversations/{conversation_id}`
- Body can include one or both:
```json
{ "title": "New title", "archived": true }
```
- Response: `{ "id": "uuid", "title": "New title", "archived": true }`

### Delete conversation
- `DELETE /api/v1/chat/conversations/{conversation_id}`
- Response: 204 No Content

---

## Messages

### Get messages
- `GET /api/v1/chat/conversations/{conversation_id}/messages?limit=50&offset=0`
- Response:
```json
[
  { "id": "uuid", "role": "user", "content": "Hi", "created_at": "..." },
  { "id": "uuid", "role": "assistant", "content": "Hello!", "created_at": "..." }
]
```

### Send a message and get assistant reply
- `POST /api/v1/chat/conversations/{conversation_id}/messages`
- Body: `{ "text": "What are the symptoms of diabetes?" }`
- Response:
```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Key symptoms include...",
    "created_at": "..."
  }
}
```

Notes:
- The backend uses a compact rolling summary + last ~10 messages to keep context like ChatGPT.
- Safety disclaimers are included for medical content.
- Sources from RAG/MCP are appended when available.

---

## Data model (relevant tables)

- `conversations(id, user_id, title, archived, metadata, created_at, updated_at)`
- `messages(id, conversation_id, user_id, role, content, created_at, model, tokens, latency, tool_calls, attachments)`
- `conversation_summaries(id, conversation_id, summary_text, token_count, last_message_id, updated_at, created_at)`
- `users(...)` (existing)

The older `queries` table remains for analytics/auditing. `translations` is present but not used.

---

## Frontend flow

1. User logs in → store JWT
2. Fetch conversation list → show in sidebar
3. Create conversation or open an existing one
4. Send message → POST message; render assistant reply from response
5. Repeat; the backend maintains memory and summaries
6. Allow rename, archive, delete via respective endpoints

---

## Status and limits

- Rate limits: configured in middleware; adjust as needed
- Context window: last ~10 messages + rolling summary
- Titles: frontend can generate a title from the first turn, or call `PATCH` later

---

## Next steps (optional)

- Add typing indicators with SSE or WebSocket (separate endpoint)
- Add feedback endpoint to rate assistant replies
- Add export (download conversation as JSON/markdown)
- Add pinned notes per conversation
