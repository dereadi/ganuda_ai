# JR Instruction: VetAssist Presidio PII Integration

## Date: January 15, 2026
## Priority: HIGH
## Assigned To: IT Triad (redfin)
## Depends On: goldfin Tailscale access (COMPLETE)

---

## Overview

Integrate Microsoft Presidio into VetAssist backend to detect and handle PII before storage. Veterans will be sharing sensitive information (SSN, medical conditions, service records) - we must protect this data.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PII FLOW ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Input (chat message)                                          │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────┐                                                    │
│  │  Presidio   │  Detect: SSN, DOB, names, addresses, medical      │
│  │  Analyzer   │                                                    │
│  └─────────────┘                                                    │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────┐                                                    │
│  │  Presidio   │  Action: Redact, mask, or tokenize                │
│  │  Anonymizer │                                                    │
│  └─────────────┘                                                    │
│       │                                                              │
│       ├──────────────────────┐                                      │
│       ▼                      ▼                                      │
│  ┌─────────────┐      ┌─────────────┐                              │
│  │  bluefin    │      │  goldfin    │                              │
│  │  (redacted) │      │  (PII vault)│                              │
│  │  Chat logs  │      │  via Tailsc │                              │
│  └─────────────┘      └─────────────┘                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## PII Types to Detect

| Type | Example | Action |
|------|---------|--------|
| SSN | 123-45-6789 | Tokenize → store in goldfin |
| DOB | 01/15/1985 | Redact in logs |
| Full Name | John Smith | Keep (needed for context) |
| Address | 123 Main St | Redact in logs |
| Phone | (555) 123-4567 | Redact in logs |
| Email | john@example.com | Redact in logs |
| Medical Condition | PTSD, TBI | Keep (needed for claims guidance) |
| Service Number | Varies | Tokenize |
| VA File Number | Varies | Tokenize |

## Implementation Steps

### Step 1: Install Presidio

```bash
# On redfin, in VetAssist backend venv
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg
```

### Step 2: Create PII Service Module

Create `/ganuda/vetassist/backend/app/services/pii_service.py`:

```python
"""
PII Detection and Protection Service for VetAssist
Uses Microsoft Presidio for entity recognition and anonymization
"""
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Dict, List, Tuple
import hashlib
import os

class PIIService:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Custom recognizers for VA-specific entities could be added here
        self.sensitive_entities = [
            "US_SSN",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "LOCATION",
            "DATE_TIME",  # For DOB
            "US_DRIVER_LICENSE",
        ]

        # Entities we detect but don't redact (needed for claims)
        self.preserve_entities = [
            "PERSON",  # Names needed for context
        ]

    def analyze(self, text: str) -> List[dict]:
        """
        Analyze text for PII entities.
        Returns list of detected entities with positions.
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities + self.preserve_entities
        )
        return [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text": text[r.start:r.end]
            }
            for r in results
        ]

    def redact_for_logging(self, text: str) -> str:
        """
        Redact PII for safe logging to bluefin.
        Replaces sensitive data with <ENTITY_TYPE> placeholders.
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities
        )

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})
            }
        )
        return anonymized.text

    def tokenize_for_vault(self, text: str, user_id: str) -> Tuple[str, Dict[str, str]]:
        """
        Tokenize PII for storage in goldfin vault.
        Returns (tokenized_text, token_mapping).
        Token mapping should be stored in goldfin only.
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.sensitive_entities
        )

        token_map = {}
        tokenized_text = text

        # Process in reverse order to maintain positions
        for result in sorted(results, key=lambda x: x.start, reverse=True):
            original = text[result.start:result.end]
            token = self._generate_token(original, user_id, result.entity_type)
            token_map[token] = {
                "original": original,
                "entity_type": result.entity_type
            }
            tokenized_text = (
                tokenized_text[:result.start] +
                f"<TOKEN:{token}>" +
                tokenized_text[result.end:]
            )

        return tokenized_text, token_map

    def _generate_token(self, value: str, user_id: str, entity_type: str) -> str:
        """Generate deterministic token for PII value."""
        # Same PII for same user = same token (allows deduplication)
        salt = os.environ.get("PII_TOKEN_SALT", "cherokee-ai-federation")
        token_input = f"{salt}:{user_id}:{entity_type}:{value}"
        return hashlib.sha256(token_input.encode()).hexdigest()[:16]


# Singleton instance
pii_service = PIIService()
```

### Step 3: Integrate with Chat Endpoint

Modify `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`:

```python
from app.services.pii_service import pii_service

@router.post("/message")
async def send_message(request: MessageRequest, db: Session = Depends(get_db)):
    # Analyze incoming message for PII
    pii_detected = pii_service.analyze(request.content)

    # Log redacted version to bluefin
    redacted_content = pii_service.redact_for_logging(request.content)

    # If PII detected, tokenize and store mapping in goldfin
    if pii_detected:
        tokenized_content, token_map = pii_service.tokenize_for_vault(
            request.content,
            str(request.session_id)
        )
        # TODO: Store token_map in goldfin via Tailscale
        # await store_pii_tokens(request.session_id, token_map)

    # Process with AI using original content (in memory only)
    # ... existing chat logic ...

    # Store redacted version in chat_messages
    # ... existing storage logic, but use redacted_content ...
```

### Step 4: goldfin PII Storage (Phase 2)

Create table on goldfin for PII token storage:

```sql
-- Run on goldfin PostgreSQL
CREATE TABLE pii_tokens (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    token VARCHAR(16) NOT NULL,
    encrypted_value BYTEA NOT NULL,  -- AES-256 encrypted original
    entity_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    UNIQUE(session_id, token)
);

CREATE INDEX idx_pii_session ON pii_tokens(session_id);
CREATE INDEX idx_pii_token ON pii_tokens(token);
```

### Step 5: Environment Configuration

Add to `/ganuda/vetassist/backend/.env`:

```bash
# PII Protection
PII_TOKEN_SALT=<generate-with-openssl-rand-hex-32>
PII_VAULT_HOST=<goldfin-tailscale-ip>
PII_VAULT_PORT=5432
PII_VAULT_DB=vetassist_pii
PII_ENCRYPTION_KEY=<generate-with-openssl-rand-hex-32>
```

## Validation Checklist

- [ ] Presidio installed and spacy model downloaded
- [ ] pii_service.py created and tested
- [ ] SSN detection working: "My SSN is 123-45-6789" → detected
- [ ] Phone detection working: "Call me at (555) 123-4567" → detected
- [ ] Redaction working: sensitive data replaced with <REDACTED>
- [ ] Tokenization working: deterministic tokens generated
- [ ] Chat endpoint integrated with PII service
- [ ] goldfin PostgreSQL accessible via Tailscale
- [ ] PII tokens table created on goldfin
- [ ] Token storage to goldfin working

## Testing

```python
# Quick test script
from app.services.pii_service import PIIService

pii = PIIService()

test_text = """
Hi, I'm John Smith. My SSN is 123-45-6789 and I was born on 01/15/1985.
You can reach me at (555) 123-4567 or john.smith@email.com.
I live at 123 Main Street, Anytown USA.
I'm filing for PTSD and tinnitus from my service in Iraq.
"""

# Test analysis
entities = pii.analyze(test_text)
print("Detected entities:", entities)

# Test redaction
redacted = pii.redact_for_logging(test_text)
print("Redacted:", redacted)

# Test tokenization
tokenized, tokens = pii.tokenize_for_vault(test_text, "test-user-123")
print("Tokenized:", tokenized)
print("Token map:", tokens)
```

## Security Notes

1. **Original PII stays in memory only** - never written to bluefin logs
2. **Redacted version** goes to bluefin chat_messages table
3. **Token mappings** go to goldfin (isolated VLAN 20)
4. **Encryption at rest** for goldfin PII storage
5. **Token salt** should be rotated periodically

## Success Criteria

1. A message containing "My SSN is 123-45-6789" should:
   - Be detected as containing PII
   - Store `<REDACTED>` in bluefin chat logs
   - Store encrypted original in goldfin with token reference
   - Still provide accurate AI response (using in-memory original)

2. Database query on bluefin should NEVER return raw SSN/phone/etc.

## Related Documentation

- KB: Isolated VLAN Tailscale Setup (`KB-ISOLATED-VLAN-TAILSCALE-VIA-SQUID-JAN15-2026.md`)
- VetAssist Deployment: `KB-VETASSIST-DEPLOYMENT-JAN15-2026.md`
- Presidio Docs: https://microsoft.github.io/presidio/

---

*Cherokee AI Federation - For the Seven Generations*
*"Protect the sacred - veteran data is entrusted to us."*
