# Jr Instruction: Fix PII Over-Redaction in VetAssist Chat (v2 — SEARCH/REPLACE format)

**Task ID:** VETASSIST-PII-FIX-002
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Replaces:** Task #515 (failed — wrong instruction format)

## Background

Veterans see `<REDACTED>` for military equipment names (M270), years of service ("12 years", "23 years"), and locations. The root cause is two-fold:

1. `chat.py` stores the REDACTED version as the user's message
2. `DATE_TIME` and `LOCATION` are in the default sensitive entities list

## Changes

### Change 1: Store original text in database, use redaction only for logs

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

<<<<<<< SEARCH
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
=======
    # Analyze message for PII — log detections but store original text
    pii_entities = pii_service.analyze(message_data.content)
    if pii_entities:
        entity_types = set(e['entity_type'] for e in pii_entities)
        # Redact ONLY for log output (never stored, never shown to user)
        log_redacted = pii_service.redact_for_logging(message_data.content)
        logger.info(f"PII detected in session {message_data.session_id}: {len(pii_entities)} entities of types {entity_types}")
        logger.debug(f"Redacted for log: {log_redacted[:100]}...")

    # Save user message with ORIGINAL content
    # Veterans need to see their own text (equipment names, service dates, etc.)
    # PII protection is handled by auth (JWT) — only the veteran sees their own messages
    user_message = ChatMessage(
        id=uuid.uuid4(),
        session_id=message_data.session_id,
        role="user",
        content=message_data.content  # Original text — user sees what they typed
    )
>>>>>>> REPLACE

### Change 2: Narrow the sensitive entities for VetAssist

**File:** `/ganuda/vetassist/backend/app/services/pii_service.py`

<<<<<<< SEARCH
class PIIService(CorePIIService):
    """
    VetAssist PII Service - extends core with veteran recognizers.

    Backward compatible with original interface:
    - analyze(text) -> List[dict]
    - redact_for_logging(text) -> str
    - tokenize_for_vault(text, user_id) -> Tuple[str, Dict]
    """

    def __init__(self):
        # Initialize core service
        super().__init__()

        # Add veteran-specific recognizers
        self.add_recognizers(veteran.get_recognizers())
=======
# VetAssist-specific entity list — narrower than core default
# Removes DATE_TIME (flags "12 years", "23 years" as PII)
# Removes LOCATION (flags city names veterans mention in service history)
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
>>>>>>> REPLACE

## Verification

1. Send a chat message: "I jumped out of M270s for years, and my knees hurt. I have been out 12 years after serving 23 years."
2. Verify the message displays WITHOUT redaction marks
3. Check backend logs — PII entities should still be detected and logged
4. Send a message with an SSN pattern: "My SSN is 123-45-6789" — verify it IS redacted in logs

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `app/api/v1/endpoints/chat.py` | MODIFY | Store original text, redact only for logs |
| `app/services/pii_service.py` | MODIFY | Use narrower entity list (no DATE_TIME, LOCATION) |
