# Jr Instruction: VetAssist Chat Database Migration

**Date:** January 30, 2026
**Priority:** High
**Assigned To:** Software Engineer Jr.
**Council Vote:** 23589699dd7b4a97

## Problem

`POST /api/v1/chat/sessions` returns HTTP 500 internal server error. The SQLAlchemy ORM models (`ChatSession`, `ChatMessage`, `CouncilValidation`) likely don't have corresponding tables in the database.

## Investigation Steps

### Step 1 (bash): Check which database VetAssist connects to

```bash
cd /ganuda/vetassist/backend && grep -r "DATABASE_URL\|SQLALCHEMY_DATABASE_URL\|postgresql" app/core/database.py app/core/config.py app/core/database_config.py .env 2>/dev/null | head -20
```

### Step 2 (sql): Check if chat tables exist

Connect to the database identified in Step 1 and run:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('chat_sessions', 'chat_messages', 'council_validations', 'chatsession', 'chatmessage', 'councilvalidation')
ORDER BY table_name;
```

### Step 3 (python): Read the ORM models to get table schema

```bash
cat /ganuda/vetassist/backend/app/models/chat.py
```

This file defines `ChatSession`, `ChatMessage`, `CouncilValidation` models. Extract the column definitions to build the CREATE TABLE statements.

### Step 4 (sql): Create missing tables

Based on the ORM model definitions from Step 3, create the tables. Expected schema pattern:

```sql
-- Only create if they don't exist
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(200),
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    specialist VARCHAR(50),
    confidence_score FLOAT,
    citations JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS council_validations (
    id UUID PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    specialist VARCHAR(50) NOT NULL,
    vote VARCHAR(20) NOT NULL,
    confidence FLOAT,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_council_validations_message ON council_validations(message_id);
```

**IMPORTANT:** Match column names and types exactly to the ORM model definitions in `app/models/chat.py`. The SQL above is an approximation — verify against the actual model.

### Step 5 (bash): Verify by testing session creation

```bash
curl -s -X POST http://192.168.132.223:8001/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "title": "Migration Test"}' | python3 -m json.tool
```

Expected: HTTP 201 with session UUID returned.

### Step 6 (bash): Test full chat flow

```bash
# Use the session_id from Step 5
SESSION_ID="<session_id_from_step_5>"
curl -s -X POST http://192.168.132.223:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"content\": \"What is the rating criteria for PTSD?\"}" | python3 -m json.tool
```

Expected: Response with user_message, assistant_message, specialist, confidence, citations.

## Context

- Backend runs on redfin (192.168.132.223:8001), app entry at `app/main.py`
- ORM models at `app/models/chat.py`
- Database config at `app/core/database.py` and `app/core/config.py`
- The chat endpoint (`app/api/v1/endpoints/chat.py`) also uses PII service and crisis detection
- See KB article: `KB-VETASSIST-TIER1-DEPLOYMENT-JAN30-2026.md` lesson #8

---
*Cherokee AI Federation — For Seven Generations*
