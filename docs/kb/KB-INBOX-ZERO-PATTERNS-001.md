# KB-INBOX-ZERO-PATTERNS-001: Email Intelligence Patterns to Steal

**Created**: 2025-12-11
**Updated**: 2025-12-11
**Sources**:
- [elie222/inbox-zero](https://github.com/elie222/inbox-zero) - Full-featured AI email assistant (Next.js)
- [jonathan-warkentine/ai-email-assistant](https://github.com/jonathan-warkentine/ai-email-assistant) - Simple Python email assistant
**Status**: Reference for Cherokee Email Intelligence

---

## Overview

Inbox Zero is an open-source AI email assistant. Key patterns we can adapt for Cherokee's SAG dashboard email tab.

---

## Features to Steal

### 1. AI Rule-Based Email Processing

**How It Works:**
- Users define rules in plain English (e.g., "Archive newsletters", "Reply to urgent emails")
- Rules stored in database with priority ordering
- AI matches incoming emails against rules
- Actions: archive, label, forward, auto-reply, draft response

**Cherokee Adaptation:**
```python
# email_rules table
CREATE TABLE email_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255),
    rule_prompt TEXT,  -- Plain English: "If from Fidelity, mark as CRITICAL"
    action_type VARCHAR(50),  -- 'archive', 'label', 'reply', 'forward', 'escalate'
    action_params JSONB,  -- {"label": "financial", "forward_to": "xxx"}
    priority INT DEFAULT 50,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Gmail Send via API

**Key Pattern:**
```python
# Python equivalent of inbox-zero's mail.ts
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_reply(service, email_data, reply_text):
    """Send reply via Gmail API with proper threading"""
    message = MIMEMultipart('alternative')
    message['To'] = email_data['from']
    message['Subject'] = f"Re: {email_data['subject']}"
    message['In-Reply-To'] = email_data['message_id']
    message['References'] = email_data['message_id']

    # Plain text and HTML
    message.attach(MIMEText(reply_text, 'plain'))
    message.attach(MIMEText(f"<html><body>{reply_text}</body></html>", 'html'))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(
        userId='me',
        body={
            'raw': raw,
            'threadId': email_data['thread_id']
        }
    ).execute()
```

### 3. Smart Sender Categorization

**How It Works:**
- Track all unique senders
- AI categorizes: personal, work, newsletter, promotional, financial, receipts
- Build sender reputation over time
- Auto-apply labels based on sender category

**Cherokee Adaptation:**
```sql
CREATE TABLE email_senders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_address VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    category VARCHAR(50),  -- 'personal', 'work', 'newsletter', 'financial', 'promo'
    contact_frequency INT DEFAULT 0,  -- emails received count
    last_contact TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    thermal_importance DECIMAL(3,2) DEFAULT 0.5,  -- 0.0-1.0
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Cold Email Detection

**Pattern:**
```python
def is_cold_email(email_data, sender_history):
    """Detect unsolicited cold emails"""
    # Never sent to this sender before
    if sender_history['sent_count'] == 0:
        # Run through AI to detect cold email patterns
        prompt = f"""
        Analyze this email and determine if it's a cold/unsolicited email.

        From: {email_data['from']}
        Subject: {email_data['subject']}
        Body: {email_data['body'][:500]}

        Cold email indicators:
        - Unsolicited sales pitch
        - "I noticed you..." opener
        - Link to schedule meeting
        - Asking for time/call
        - Generic greeting

        Return: {"is_cold": true/false, "confidence": 0.0-1.0}
        """
        return ai_analyze(prompt)
    return {"is_cold": False}
```

### 5. Reply Tracking ("Reply Zero")

**Pattern:**
- Track emails that need responses
- Track emails awaiting responses from others
- Dashboard showing: "Needs Reply", "Awaiting Reply", "Completed"

**Cherokee Adaptation:**
```sql
ALTER TABLE emails ADD COLUMN reply_status VARCHAR(50);
-- Values: 'needs_reply', 'awaiting_reply', 'replied', 'no_reply_needed'

ALTER TABLE emails ADD COLUMN reply_due_date TIMESTAMP;
ALTER TABLE emails ADD COLUMN replied_at TIMESTAMP;
```

### 6. AI Draft Generation with Context

**Key Pattern (from architecture):**
- Pull thermal memory context about sender
- Include previous email thread
- Match user's writing style from past sent emails
- Generate contextual draft

**Cherokee Adaptation:**
```python
def generate_ai_draft(email_data, thermal_context):
    """Generate draft using Cherokee AI with thermal memory"""
    prompt = f"""
    Draft a reply to this email.

    === EMAIL ===
    From: {email_data['from']}
    Subject: {email_data['subject']}
    Body: {email_data['body']}

    === CONTEXT FROM THERMAL MEMORY ===
    {thermal_context}

    === INSTRUCTIONS ===
    - Be professional but warm
    - Reference any relevant context
    - Keep response concise
    - Sign off as "Darrell"
    """
    return cherokee_ai.generate(prompt)
```

### 7. Bulk Unsubscribe

**Pattern:**
- Identify newsletter/promotional senders
- One-click unsubscribe via List-Unsubscribe header
- Track unsubscribe status
- Archive all from sender

---

## Additional Patterns from jonathan-warkentine/ai-email-assistant

### 8. Polling Architecture (Simpler Alternative)
**Pattern:** Instead of webhooks, use continuous polling loop with configurable intervals:
```python
def main_loop():
    """Simple polling architecture"""
    while True:
        try:
            # Fetch new emails
            threads = gmail_client.fetch_threads_with_new_messages()

            # Filter threads needing response
            actionable = filter_threads_awaiting_response(threads)

            # Process each actionable email
            for thread in actionable:
                email_data = parse_email_thread(thread)
                ai_response = chatgpt_client.compose_response(email_data)
                gmail_client.save_draft(ai_response, thread)

            logger.info(f"Processed {len(actionable)} emails, sleeping...")
            time.sleep(config.poll_interval)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Error backoff
```

**Cherokee Adaptation:** Already using this in `gmail_sync_daemon.py`

### 9. Controller-Based Architecture
**Pattern:** Separate concerns into:
- `controllers/` - Request/event handlers
- `services/` - Business logic (Gmail, OpenAI)
- `models/` - Data structures
- `utils/` - Helper functions

**Cherokee Adaptation:** Could refactor `email_intelligence.py` into:
- `email_controller.py` - Flask routes
- `email_service.py` - Business logic
- `gmail_service.py` - Gmail API wrapper
- `ai_service.py` - LLM draft generation

### 10. Draft-First Workflow
**Pattern:** Generate drafts instead of auto-sending:
1. AI generates draft response
2. Save as Gmail draft (not sent)
3. User reviews and sends manually
4. Safer for business contexts

**Cherokee Adaptation:** Current implementation allows edit before send - good pattern to keep.

---

## Priority Implementation Order

### Phase 1: Core Fixes ✅ DONE
1. ✅ Display email body in detail view
2. ✅ Gmail send functionality via existing OAuth (using `send_reply()` method)

### Phase 2: AI Enhancement (Next)
3. AI draft generation with thermal context
4. Sender categorization table

### Phase 3: Smart Features
5. Reply tracking status
6. Cold email detection
7. Thread/conversation view

### Phase 4: Automation
8. AI rule-based processing
9. Bulk unsubscribe
10. Auto-archive/label

---

## Gmail API Scopes

Current token HAS all needed scopes:
```
✅ https://www.googleapis.com/auth/gmail.send
✅ https://www.googleapis.com/auth/gmail.modify
✅ https://www.googleapis.com/auth/gmail.readonly
✅ https://www.googleapis.com/auth/gmail.labels
```

---

## Related Files

- `/home/dereadi/sag_unified_interface/email_intelligence.py` - Current email module
- `/ganuda/email_daemon/gmail_sync_daemon.py` - Email sync daemon
- `~/.gmail_credentials/token.pickle` - OAuth token (may need re-auth for send scope)

---

## Sources

- [Inbox Zero GitHub](https://github.com/elie222/inbox-zero) - Complex, feature-rich (Next.js/TypeScript)
- [jonathan-warkentine/ai-email-assistant](https://github.com/jonathan-warkentine/ai-email-assistant) - Simple Python polling architecture
- [Architecture Doc](https://github.com/elie222/inbox-zero/blob/main/ARCHITECTURE.md)

---

## Comparison: Which to Steal From?

| Feature | inbox-zero | ai-email-assistant | Cherokee Choice |
|---------|------------|-------------------|-----------------|
| Language | TypeScript/Next.js | Python | **Python** (matches our stack) |
| Architecture | Complex, microservices | Simple polling | **Simple polling** (already using) |
| AI Integration | Multiple LLMs | OpenAI only | **Cherokee AI** (thermal context) |
| Gmail Auth | OAuth web flow | Service account | **OAuth** (already configured) |
| Features | Very comprehensive | Basic | **Steal ideas, build our own** |

**Bottom Line:** inbox-zero has better feature ideas (rules, categorization, reply tracking), but ai-email-assistant has simpler Python patterns closer to our implementation.

---

**For Seven Generations**: Learn from others, adapt for ourselves.
