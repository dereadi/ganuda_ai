# JR Instruction: VetAssist Chat PII Integration (Phase 2)

## Metadata
```yaml
task_id: vetassist_pii_chat_integration
priority: P1_CRITICAL
council_vote: 6700b2d88464ab8b
assigned_to: it_triad_jr
estimated_duration: 30_minutes
requires_sudo: false
requires_restart: true
target_node: redfin
depends_on: presidio_pii_integration_v2
```

## Overview

Integrate the PIIService into VetAssist chat endpoint so that:
1. User messages are scanned for PII before storage
2. REDACTED versions are stored in the database (bluefin)
3. Original messages are used for AI processing (in memory only)
4. PII detection events are logged for audit

**Sacred Fire Priority:** Veterans trust us with SSNs, medical data, and personal information. We protect their data as we would protect the sacred fire.

---

## Current State

The chat endpoint at `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`:
- Uses `sanitize_message()` for XSS/injection protection (line 227)
- Stores sanitized content to database
- Sends original content to Council (line 250)

**Gap:** No PII detection or redaction before database storage.

---

## Tasks

### Task 1: Add PIIService Import

Add to the imports section of `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`:

```python
from app.services.pii_service import pii_service
import logging

logger = logging.getLogger(__name__)
```

### Task 2: Modify send_message Endpoint

In the `send_message` function (around line 187), after verifying the session exists but BEFORE saving the user message:

```python
# Analyze message for PII (BEFORE storage)
pii_entities = pii_service.analyze(message_data.content)

# Log PII detection (entity types only, NOT the actual values)
if pii_entities:
    entity_types = set(e['entity_type'] for e in pii_entities)
    logger.info(
        f"PII detected in chat session {message_data.session_id}: "
        f"{len(pii_entities)} entities of types {entity_types}"
    )

# Create REDACTED version for database storage
# Original content is still used for Council processing
storage_content = pii_service.redact_for_logging(
    sanitize_message(message_data.content)
)
```

### Task 3: Update User Message Storage

Change line 223-228 from:

```python
user_message = ChatMessage(
    id=uuid.uuid4(),
    session_id=message_data.session_id,
    role="user",
    content=sanitize_message(message_data.content)  # OLD
)
```

To:

```python
user_message = ChatMessage(
    id=uuid.uuid4(),
    session_id=message_data.session_id,
    role="user",
    content=storage_content  # REDACTED version
)
```

### Task 4: Ensure Original Used for AI

Verify line 250 still uses `message_data.content` (original):

```python
council_response = council_service.ask_council(
    user_question=message_data.content,  # Original for AI
    session_history=history
)
```

This is already correct - no change needed.

---

## Verification

After making changes, restart the backend and test:

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate

# Kill existing process
pkill -f "uvicorn app.main:app" || true
sleep 2

# Start backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/vetassist_backend.log 2>&1 &
sleep 5

# Test endpoint with PII
curl -s -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "00000000-0000-0000-0000-000000000001",
    "content": "Hi, my SSN is 123-45-6789 and I need help with my claim"
  }' | python3 -m json.tool

# Check what was stored in database
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c \
  "SELECT content FROM vetassist_chat_messages ORDER BY created_at DESC LIMIT 1;"
```

Expected: Database should show `<REDACTED>` instead of the actual SSN.

---

## Security Notes

1. **NEVER log actual PII values** - only log entity types and counts
2. **Original content stays in memory** - Python garbage collection handles cleanup
3. **Database only gets redacted** - this is the security boundary
4. **AI sees original** - required for accurate responses

---

## Rollback Plan

If issues occur:

```bash
# Restore backup
cp /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py.backup_* \
   /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py

# Restart
pkill -f "uvicorn app.main:app" && \
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
```

---

*Cherokee AI Federation - For the Seven Generations*
*"The sacred fire protects the tribe. PII protection protects our veterans."*
