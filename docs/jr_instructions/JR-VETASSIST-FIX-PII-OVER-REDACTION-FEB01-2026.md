# Jr Instruction: Fix PII Over-Redaction in VetAssist Chat

**Task ID:** VETASSIST-PII-REDACT-FIX-001
**Priority:** P1 (High — user-facing data loss)
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)

## Problem

When veterans type messages in the VetAssist chat, the PII redaction system incorrectly flags service-related information as PII and replaces it with `<REDACTED>` before storing in the database. The user then sees their own message with key details removed.

**Example:**
- User types: `I jumped out of M270s for years, and my knees hurt. I have been out 12 years after serving 23 years`
- User sees: `I jumped out of <REDACTED> for <REDACTED>, and my knees hurt. I have been out <REDACTED> after serving <REDACTED>`

Equipment model numbers (`M270`), years of service (`23 years`), and time since discharge (`12 years`) are essential claim information, not PII.

## Root Cause

Two problems:

1. **`chat.py` stores REDACTED content as the user's message** — the original text is sent to the Council but lost for display purposes
2. **`DATE_TIME` is in the default sensitive entities list** — Presidio flags service durations as temporal PII

## Changes Required

### Change 1: Store original content for user display

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

**Find this block (approximately lines 236-252):**
```python
    # Analyze message for PII before storage
    pii_entities = pii_service.analyze(message_data.content)
    if pii_entities:
        entity_types = set(e['entity_type'] for e in pii_entities)
        logger.info(f"PII detected in session {message_data.session_id}: {len(pii_entities)} entities of types {entity_types}")

    # Create redacted version for database storage
    storage_content = pii_service.redact_for_logging(message_data.content)

    # Save user message with REDACTED content (for storage)
    # Note: We send the original unsanitized content to Council for processing
    user_message = ChatMessage(
        id=uuid.uuid4(),
        session_id=message_data.session_id,
        role="user",
        content=storage_content  # REDACTED for PII protection
    )
```

**Replace with:**
```python
    # Analyze message for PII — log only, do NOT redact user-visible content
    # Veterans need to see their own service details (equipment, dates, durations)
    pii_entities = pii_service.analyze(message_data.content)
    if pii_entities:
        entity_types = set(e['entity_type'] for e in pii_entities)
        redacted_log = pii_service.redact_for_logging(message_data.content)
        logger.info(f"PII detected in session {message_data.session_id}: {len(pii_entities)} entities of types {entity_types} (redacted for log: {redacted_log})")

    # Save user message with ORIGINAL content — user must see their own input
    user_message = ChatMessage(
        id=uuid.uuid4(),
        session_id=message_data.session_id,
        role="user",
        content=message_data.content  # Original text — user's own data
    )
```

**Key difference:** `content=message_data.content` instead of `content=storage_content`. PII analysis still runs for logging/monitoring, but the user sees their original text.

### Change 2: Remove DATE_TIME from VetAssist sensitive entities

**File:** `/ganuda/vetassist/backend/app/services/pii_service.py`

**Replace the entire file with:**
```python
"""
PII Detection and Protection Service for VetAssist
Cherokee AI Federation - For the Seven Generations

This module now uses the CORE ganuda-pii package with
veteran-specific recognizers as a plugin.

REFACTORED: January 16, 2026
- Extracted core PII logic to /ganuda/lib/ganuda_pii/
- Veteran recognizers now in ganuda_pii.recognizers.veteran
- This file is now a thin wrapper for backward compatibility

UPDATED: February 1, 2026
- Removed DATE_TIME from sensitive entities (service durations are not PII)
- Removed LOCATION from sensitive entities (duty stations are claim-relevant)
"""

import sys
sys.path.insert(0, '/ganuda/lib')

from ganuda_pii import PIIService as CorePIIService
from ganuda_pii.recognizers import veteran


# VetAssist-specific entity list — narrower than the core default
# Excludes DATE_TIME (service durations) and LOCATION (duty stations)
# which are essential for disability claims
VETASSIST_SENSITIVE_ENTITIES = [
    "US_SSN",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "US_DRIVER_LICENSE",
    "CREDIT_CARD",
    "US_BANK_NUMBER",
]


class PIIService(CorePIIService):
    """
    VetAssist PII Service - extends core with veteran recognizers.

    Backward compatible with original interface:
    - analyze(text) -> List[dict]
    - redact_for_logging(text) -> str
    - tokenize_for_vault(text, user_id) -> Tuple[str, Dict]
    """

    def __init__(self):
        # Initialize core service with VetAssist-specific entity list
        super().__init__(sensitive_entities=VETASSIST_SENSITIVE_ENTITIES)

        # Add veteran-specific recognizers
        self.add_recognizers(veteran.get_recognizers())


# Singleton instance (backward compatible)
pii_service = PIIService()
```

**Key difference:** The `PIIService` constructor now passes `sensitive_entities=VETASSIST_SENSITIVE_ENTITIES` which excludes `DATE_TIME` and `LOCATION`. The core ganuda_pii service constructor already accepts this parameter (see `/ganuda/lib/ganuda_pii/service.py` line 69-72).

### No other files need changes

- The frontend displays `message.content` as-is — no frontend changes needed
- The `ChatMessage` model already has a `Text` content column — no schema changes needed
- The core `ganuda_pii` service is not modified — only the VetAssist wrapper

## Verification

After applying changes, restart the backend:
```bash
# The systemd service will auto-restart, or:
sudo systemctl restart vetassist-backend
```

### Test Cases

**Test 1 — Military equipment and service dates (should NOT be redacted):**
```
Input: "I jumped out of M270s for 23 years, and my knees hurt. I have been out 12 years."
Expected: User sees their full original text, no <REDACTED> tags
```

**Test 2 — Actual SSN (SHOULD be redacted in logs):**
```
Input: "My SSN is 123-45-6789"
Expected: User sees original text. Server log shows: "PII detected... (redacted for log: My SSN is <REDACTED>)"
```

**Test 3 — Service location and duration (should NOT be redacted):**
```
Input: "I was stationed at Fort Bragg from 2001 to 2012 and developed tinnitus."
Expected: User sees full text. Locations and dates preserved.
```

## Security Notes

- SSNs, credit cards, bank numbers, and driver's licenses are still detected and redacted in **server logs**
- User-visible storage now shows original text — this is the user's own data, they have a right to see it
- The PII service `analyze()` still runs on every message for monitoring/alerting
- Admin-facing dashboards should use `redact_for_logging()` if they display user messages to non-owners

## Files Modified

| File | Change |
|------|--------|
| `app/api/v1/endpoints/chat.py` | Store original content, redact only for logs |
| `app/services/pii_service.py` | Remove DATE_TIME and LOCATION from sensitive entities |
