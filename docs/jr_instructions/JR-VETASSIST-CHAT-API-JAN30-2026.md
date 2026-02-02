# JR-VETASSIST-CHAT-API-JAN30-2026
## Build VetAssist Chat API Module (Specialist Council Integration)

**Priority:** P0 - Core Feature
**Target Node:** bluefin (192.168.132.222)
**File to Create:** `/ganuda/vetassist/backend/app/api/chat_routes.py`
**Wire into:** `/ganuda/vetassist/backend/main.py`
**Depends on:** Auth API (JR-VETASSIST-AUTH-API-JAN30-2026)

### Context

The VetAssist chat connects veterans to the 7-Specialist Council via the LLM Gateway on redfin. The frontend manages chat sessions and messages. Database tables already exist.

**`chat_sessions` table:**
- id (uuid), user_id (uuid FK->users), title (varchar)
- created_at (timestamptz), updated_at (timestamptz), is_archived (boolean)

**`chat_messages` table:**
- id (uuid), session_id (uuid FK->chat_sessions), role (varchar: user/assistant/system)
- content (text), specialist (varchar), confidence_score (numeric)
- citations (jsonb), created_at (timestamptz)

**LLM Gateway:** http://192.168.132.223:8080/v1/chat/completions
- API Key: `ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5`
- Supports system prompts for veteran-specific context

### Endpoints to Implement

#### 1. GET /api/v1/chat/sessions
**Query params:** `user_id` (required), `limit` (default 50)
**Headers:** `Authorization: Bearer <token>`
**Response:**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "PTSD Rating Question",
      "created_at": "2026-01-30T10:00:00Z",
      "updated_at": "2026-01-30T10:05:00Z",
      "is_archived": false
    }
  ]
}
```
**Logic:** SELECT from chat_sessions WHERE user_id = ? AND is_archived = false ORDER BY updated_at DESC LIMIT ?

#### 2. POST /api/v1/chat/sessions
**Headers:** `Authorization: Bearer <token>`
**Request:** `{"user_id": "uuid", "title": "New conversation"}`
**Response:** Created session object (201)
**Logic:** INSERT into chat_sessions with new UUID

#### 3. GET /api/v1/chat/sessions/{session_id}/messages
**Headers:** `Authorization: Bearer <token>`
**Response:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "role": "user",
      "content": "What rating should I expect for PTSD?",
      "specialist": null,
      "confidence_score": null,
      "citations": null,
      "created_at": "2026-01-30T10:00:00Z"
    },
    {
      "id": "uuid",
      "session_id": "uuid",
      "role": "assistant",
      "content": "Based on 38 CFR 4.130...",
      "specialist": "Gecko",
      "confidence_score": 0.92,
      "citations": ["38 CFR 4.130", "38 CFR 4.126"],
      "created_at": "2026-01-30T10:00:05Z"
    }
  ]
}
```
**Logic:** SELECT from chat_messages WHERE session_id = ? ORDER BY created_at ASC

#### 4. POST /api/v1/chat/message
**Headers:** `Authorization: Bearer <token>`
**Request:**
```json
{
  "session_id": "uuid-or-null",
  "message": "What rating should I expect for PTSD with nightmares and hypervigilance?"
}
```
**Response (matches frontend ChatMessageResponse):**
```json
{
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Based on the VA rating criteria...",
    "specialist": "Gecko",
    "confidence_score": 0.92,
    "citations": ["38 CFR 4.130", "Diagnostic Code 9411"],
    "created_at": "2026-01-30T10:00:05Z"
  },
  "session": {
    "id": "uuid",
    "user_id": "uuid",
    "title": "PTSD Rating Question",
    "created_at": "2026-01-30T10:00:00Z",
    "updated_at": "2026-01-30T10:00:05Z",
    "is_archived": false
  }
}
```
**Logic:**
1. If session_id is null, create new session (auto-title from first message)
2. INSERT user message into chat_messages
3. Build system prompt with veteran context
4. Call LLM Gateway with conversation history
5. Parse response for specialist info, citations, confidence
6. INSERT assistant message into chat_messages
7. UPDATE chat_sessions SET updated_at = now()
8. Return both message and session objects

#### 5. DELETE /api/v1/chat/sessions/{session_id}
**Headers:** `Authorization: Bearer <token>`
**Response:** `{"message": "Session archived"}`
**Logic:** UPDATE chat_sessions SET is_archived = true (soft delete)

### LLM Gateway Integration

```python
import httpx

LLM_GATEWAY_URL = "http://192.168.132.223:8080/v1/chat/completions"
LLM_API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

VETASSIST_SYSTEM_PROMPT = """You are VetAssist, a VA disability claims specialist AI assistant.
You help veterans understand their benefits, navigate the claims process, and prepare evidence.

Key guidelines:
- Cite specific 38 CFR sections when discussing ratings
- Always recommend veterans consult with an accredited VSO
- Never guarantee specific rating outcomes
- Be empathetic but factual
- Flag crisis situations (mention of self-harm, homelessness, substance abuse)

You have access to 38 CFR Parts 3 and 4 (Schedule of Ratings).
"""

async def call_llm_gateway(messages: list) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            LLM_GATEWAY_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "default",
                "messages": [
                    {"role": "system", "content": VETASSIST_SYSTEM_PROMPT},
                    *messages
                ],
                "max_tokens": 1024,
                "temperature": 0.3
            }
        )
        return response.json()
```

### Dependencies

```bash
pip install httpx
```

### RAG Enhancement (Optional Phase 2)

Before calling the LLM, query ChromaDB for relevant regulations:
```python
# Query RAG for context
rag_results = collection.query(query_texts=[user_message], n_results=3)
# Inject into system prompt as additional context
context = "\n".join(rag_results["documents"][0])
enhanced_prompt = VETASSIST_SYSTEM_PROMPT + f"\n\nRelevant regulations:\n{context}"
```

### Wire into main.py

```python
from app.api.chat_routes import router as chat_router
app.include_router(chat_router)
```

### Verification

```bash
# Create session
curl -X POST http://192.168.132.222:8001/api/v1/chat/sessions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<USER_UUID>","title":"Test Chat"}'

# Send message
curl -X POST http://192.168.132.222:8001/api/v1/chat/message \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id":null,"message":"What is the rating criteria for PTSD?"}'

# List sessions
curl http://192.168.132.222:8001/api/v1/chat/sessions?user_id=<USER_UUID>&limit=10 \
  -H "Authorization: Bearer <TOKEN>"
```
