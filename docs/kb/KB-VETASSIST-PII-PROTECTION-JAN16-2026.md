# KB: VetAssist PII Protection System

**Date:** January 16, 2026
**Status:** Phase 1 Complete, Phase 2 In Progress
**Council Vote:** 6700b2d88464ab8b
**Author:** TPM (Cherokee AI Federation)

---

## Overview

VetAssist protects veteran PII (Personally Identifiable Information) using Microsoft Presidio with custom veteran-specific recognizers. This multi-phase implementation ensures sensitive data like SSNs, phone numbers, and VA file numbers are detected and protected before storage.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     VetAssist Chat Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Message ─────┬──────────────────────────────────────────► │
│                    │                                            │
│                    ▼                                            │
│            ┌─────────────┐                                      │
│            │ PIIService  │──── Analyze ────► Entity Detection   │
│            │  (Phase 1)  │                                      │
│            └──────┬──────┘                                      │
│                   │                                             │
│         ┌────────┴────────┐                                     │
│         ▼                 ▼                                     │
│   [REDACTED]         [ORIGINAL]                                 │
│         │                 │                                     │
│         ▼                 ▼                                     │
│   ┌──────────┐     ┌───────────┐                               │
│   │ bluefin  │     │  Council  │──► AI Processing              │
│   │ Database │     │  (vLLM)   │    (in memory only)           │
│   │ (Phase 2)│     └───────────┘                               │
│   └────┬─────┘                                                 │
│        │                                                        │
│        ▼                                                        │
│   ┌──────────┐                                                  │
│   │ goldfin  │──► Token Vault (Phase 3 - Future)               │
│   │  Vault   │                                                  │
│   └──────────┘                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Presidio installation, custom recognizers | COMPLETE |
| **Phase 2** | Chat endpoint integration | IN PROGRESS |
| **Phase 3** | goldfin token vault | PLANNED |

---

## Phase 1: Presidio Installation (COMPLETE)

### Components Installed

| Component | Version | Purpose |
|-----------|---------|---------|
| presidio-analyzer | 2.x | Entity detection engine |
| presidio-anonymizer | 2.x | Redaction engine |
| spacy en_core_web_lg | 3.x | NER model (750MB) |

### Custom Recognizers

**VeteranSSNRecognizer** - Enhanced SSN detection with higher confidence scores:
- Pattern: `\b([0-9]{3})-([0-9]{2})-([0-9]{4})\b` (score: 0.85)
- Pattern: `\b([0-9]{3}) ([0-9]{2}) ([0-9]{4})\b` (score: 0.85)
- Pattern: `\b([0-9]{9})\b` (score: 0.4)
- Context words: ssn, social, security, number, veteran, va

**VAFileNumberRecognizer** - VA claim file number detection:
- Pattern: `\b[Cc]?[0-9]{7,9}\b` (score: 0.6)
- Context words: va, file, number, claim, veteran

### PII Types Protected

| Entity Type | Example | Score | Action |
|-------------|---------|-------|--------|
| US_SSN | 123-45-6789 | 1.00 | Redact |
| PHONE_NUMBER | (555) 123-4567 | 0.75 | Redact |
| EMAIL_ADDRESS | user@email.com | 0.85 | Redact |
| VA_FILE_NUMBER | C12345678 | 0.60 | Redact |
| LOCATION | 123 Main St | varies | Redact |
| DATE_TIME | 01/15/1985 | varies | Redact |
| PERSON | John Smith | varies | Preserve |

### Key Files

- **PIIService**: `/ganuda/vetassist/backend/app/services/pii_service.py`
- **JR Instruction**: `/ganuda/docs/jr_instructions/JR-PRESIDIO-ULTRATHINK-EXECUTABLE-JAN16-2026.md`

---

## Phase 2: Chat Integration (IN PROGRESS)

### Changes Required

1. Import `pii_service` in chat endpoint
2. Analyze messages for PII before storage
3. Store REDACTED version in database
4. Use ORIGINAL for AI processing (in memory)
5. Log PII detection events (types only, not values)

### JR Instruction

`/ganuda/docs/jr_instructions/JR-VETASSIST-PII-CHAT-INTEGRATION-JAN16-2026.md`

---

## Phase 3: goldfin Vault (PLANNED)

### Purpose

Store reversible PII tokens in secure goldfin PostgreSQL:
- Tokenized PII maps to original values
- Enables re-identification for authorized requests
- Encrypted at rest
- Audit logging for all access

---

## Usage Examples

### Analyze Text for PII
```python
from app.services.pii_service import pii_service

entities = pii_service.analyze("My SSN is 123-45-6789")
# Returns: [{'entity_type': 'US_SSN', 'text': '123-45-6789', 'score': 1.00, ...}]
```

### Redact for Logging/Storage
```python
safe_text = pii_service.redact_for_logging("My SSN is 123-45-6789")
# Returns: "My SSN is <REDACTED>"
```

### Tokenize for Vault (Phase 3)
```python
tokenized, token_map = pii_service.tokenize_for_vault(text, user_id)
# Returns: ("My SSN is <TOKEN:a1b2c3d4>", {"a1b2c3d4": {"original": "123-45-6789", "entity_type": "US_SSN"}})
```

---

## Troubleshooting

### Presidio Not Detecting SSN

**Symptom:** `pii_service.analyze()` returns empty list for SSN

**Cause:** Default Presidio SSN patterns have low scores (0.05) that get filtered

**Solution:** Verify custom VeteranSSNRecognizer is loaded:
```python
from app.services.pii_service import PIIService
p = PIIService()
print(p.analyzer.registry.recognizers)
# Should show VeteranSSNRecognizer in list
```

### Import Errors

**Symptom:** `ModuleNotFoundError: presidio_analyzer`

**Solution:** Ensure using VetAssist venv:
```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip list | grep presidio
```

### spaCy Model Not Found

**Symptom:** `OSError: [E050] Can't find model 'en_core_web_lg'`

**Solution:** Download the model:
```bash
python -m spacy download en_core_web_lg
```

---

## Security Considerations

1. **Never log actual PII values** - Only log entity types and counts
2. **Original content is ephemeral** - Only exists in memory during request
3. **Database gets redacted version** - Security boundary at storage layer
4. **Token salt is secret** - Stored in `.env`, not committed to git
5. **Audit logging** - Track who accessed what PII (Phase 3)

---

## References

- Council Vote: `6700b2d88464ab8b`
- Microsoft Presidio: https://microsoft.github.io/presidio/
- JR Instructions:
  - Phase 1: `JR-PRESIDIO-ULTRATHINK-EXECUTABLE-JAN16-2026.md`
  - Phase 2: `JR-VETASSIST-PII-CHAT-INTEGRATION-JAN16-2026.md`

---

*Cherokee AI Federation - For the Seven Generations*
*"The sacred fire protects the tribe. PII protection protects our veterans."*
