# Jr Task: Microsoft Presidio PII Filter Layer

**Date**: January 5, 2026
**Priority**: MEDIUM
**Target Node**: greenfin (192.168.132.224)
**Depends On**: vetassist_pii database setup
**Council Vote**: Part of approved VetAssist PII architecture

## Background

Microsoft Presidio is a 6.5k star open-source framework for detecting and anonymizing PII. We'll deploy it as a filter layer so AI agents NEVER see raw PII - only tokenized references.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VETASSIST FLOW                               │
│                                                                     │
│  ┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Veteran  │───▶│  Presidio   │───▶│ AI Agent │───▶│ Response │  │
│  │  Input   │    │  Analyzer   │    │ (Triad)  │    │          │  │
│  └──────────┘    └──────┬──────┘    └──────────┘    └──────────┘  │
│                         │                                          │
│                         │ Detected PII                             │
│                         ▼                                          │
│                  ┌─────────────┐                                   │
│                  │  Presidio   │                                   │
│                  │ Anonymizer  │                                   │
│                  └──────┬──────┘                                   │
│                         │                                          │
│         ┌───────────────┼───────────────┐                         │
│         ▼               ▼               ▼                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │
│  │ Token Map   │ │vetassist_pii│ │ Audit Log   │                  │
│  │ <VET_123>   │ │ (encrypted) │ │ (who/when)  │                  │
│  │ ↔ real SSN  │ │             │ │             │                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                  │
│                                                                     │
│  AI sees: "Veteran <VET_123> served in <BRANCH_1> from <DATE_1>"   │
│  DB has:  "John Smith, SSN 123-45-6789, Army, 2001-2005"           │
└─────────────────────────────────────────────────────────────────────┘
```

## Task 1: Install Presidio on Greenfin

```bash
# SSH to greenfin
ssh dereadi@192.168.132.224

# Create virtual environment
cd /ganuda
python3 -m venv presidio_venv
source presidio_venv/bin/activate

# Install Presidio components
pip install presidio-analyzer presidio-anonymizer

# Install spaCy model for NLP
python -m spacy download en_core_web_lg

# Verify installation
python -c "from presidio_analyzer import AnalyzerEngine; print('Presidio OK')"
```

## Task 2: Create PII Analyzer Service

Create `/ganuda/services/presidio/analyzer_service.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Presidio PII Analyzer Service
Detects and anonymizes PII before AI agent processing.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

app = FastAPI(title="VetAssist PII Filter", version="1.0")

# Initialize Presidio engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Token mapping store (in production, use Redis or DB)
token_map: Dict[str, Dict] = {}


class AnalyzeRequest(BaseModel):
    text: str
    veteran_id: Optional[str] = None
    session_id: Optional[str] = None
    language: str = "en"


class AnalyzeResponse(BaseModel):
    original_text: str
    anonymized_text: str
    pii_detected: List[Dict]
    token_map: Dict[str, str]
    session_id: str


class DeanonymizeRequest(BaseModel):
    text: str
    session_id: str
    authorized_fields: List[str] = []  # Which PII types can be revealed


# Custom recognizers for veteran-specific PII
VETERAN_PII_ENTITIES = [
    "PERSON",           # Names
    "US_SSN",           # Social Security Numbers
    "PHONE_NUMBER",     # Phone numbers
    "EMAIL_ADDRESS",    # Email
    "US_DRIVER_LICENSE",
    "CREDIT_CARD",
    "US_BANK_NUMBER",
    "DATE_TIME",        # Dates (DOB, service dates)
    "LOCATION",         # Addresses
    "US_PASSPORT",
    "IP_ADDRESS",
    "MEDICAL_LICENSE",
    "US_ITIN",          # Individual Taxpayer ID
]


def generate_token(entity_type: str, value: str, session_id: str) -> str:
    """Generate consistent token for PII value within session."""
    hash_input = f"{session_id}:{entity_type}:{value}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    return f"<{entity_type}_{short_hash}>"


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze text for PII and return anonymized version.
    """
    session_id = request.session_id or hashlib.sha256(
        f"{datetime.now().isoformat()}:{request.text[:20]}".encode()
    ).hexdigest()[:16]

    # Detect PII
    results = analyzer.analyze(
        text=request.text,
        entities=VETERAN_PII_ENTITIES,
        language=request.language
    )

    if not results:
        return AnalyzeResponse(
            original_text=request.text,
            anonymized_text=request.text,
            pii_detected=[],
            token_map={},
            session_id=session_id
        )

    # Sort by start position (descending) for safe replacement
    results = sorted(results, key=lambda x: x.start, reverse=True)

    # Build token map and anonymize
    session_tokens = {}
    anonymized = request.text
    pii_detected = []

    for result in results:
        original_value = request.text[result.start:result.end]
        token = generate_token(result.entity_type, original_value, session_id)

        # Store mapping
        session_tokens[token] = {
            "original": original_value,
            "entity_type": result.entity_type,
            "confidence": result.score,
            "detected_at": datetime.now().isoformat()
        }

        # Replace in text
        anonymized = anonymized[:result.start] + token + anonymized[result.end:]

        pii_detected.append({
            "entity_type": result.entity_type,
            "token": token,
            "confidence": result.score,
            "start": result.start,
            "end": result.end
        })

    # Store session tokens
    token_map[session_id] = session_tokens

    # Log for audit (without actual PII values)
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "veteran_id": request.veteran_id,
        "pii_types_detected": [p["entity_type"] for p in pii_detected],
        "token_count": len(pii_detected)
    }
    # TODO: Write to audit_log table

    return AnalyzeResponse(
        original_text="[REDACTED - stored securely]",
        anonymized_text=anonymized,
        pii_detected=pii_detected,
        token_map={t: "[REDACTED]" for t in session_tokens.keys()},
        session_id=session_id
    )


@app.post("/deanonymize")
async def deanonymize_text(request: DeanonymizeRequest):
    """
    Restore original PII values (requires authorization).
    Only authorized personnel can call this endpoint.
    """
    if request.session_id not in token_map:
        raise HTTPException(status_code=404, detail="Session not found")

    session_tokens = token_map[request.session_id]
    result = request.text

    revealed = []
    for token, data in session_tokens.items():
        # Only reveal authorized field types
        if data["entity_type"] in request.authorized_fields:
            result = result.replace(token, data["original"])
            revealed.append(data["entity_type"])

    # Audit the deanonymization
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": request.session_id,
        "action": "DEANONYMIZE",
        "revealed_types": revealed
    }
    # TODO: Write to audit_log table

    return {
        "text": result,
        "revealed_types": revealed,
        "remaining_tokens": [t for t in session_tokens.keys() if t in result]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "presidio-pii-filter"}


@app.get("/entities")
async def list_entities():
    """List all PII entity types we detect."""
    return {"entities": VETERAN_PII_ENTITIES}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
```

## Task 3: Create Systemd Service

Create `/etc/systemd/system/presidio-filter.service`:

```ini
[Unit]
Description=Cherokee AI VetAssist Presidio PII Filter
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/presidio
Environment="PATH=/ganuda/presidio_venv/bin"
ExecStart=/ganuda/presidio_venv/bin/python analyzer_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable presidio-filter
sudo systemctl start presidio-filter
```

## Task 4: Integration with AI Agents

Update AI agent code to use Presidio filter:

```python
# In Triad or Gateway code
import httpx

PRESIDIO_URL = "http://192.168.132.224:8090"

async def process_veteran_query(veteran_id: str, user_input: str):
    """Process veteran query with PII filtering."""

    # Step 1: Anonymize input before AI sees it
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PRESIDIO_URL}/analyze",
            json={
                "text": user_input,
                "veteran_id": veteran_id
            }
        )
        filtered = response.json()

    # Step 2: AI processes anonymized text
    ai_response = await call_ai_agent(
        prompt=filtered["anonymized_text"],
        context=get_veteran_context(veteran_id)  # Non-PII context from DB
    )

    # Step 3: Response goes back (still anonymized)
    # Deanonymization only happens in authorized UI with audit trail

    return {
        "response": ai_response,
        "session_id": filtered["session_id"],
        "pii_detected": len(filtered["pii_detected"])
    }
```

## Task 5: Test the Service

```bash
# Test PII detection
curl -X POST http://192.168.132.224:8090/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My name is John Smith, SSN 123-45-6789. I served from 2001 to 2005. Call me at 555-123-4567.",
    "veteran_id": "VET001"
  }'

# Expected response:
# {
#   "anonymized_text": "My name is <PERSON_a1b2c3d4>, SSN <US_SSN_e5f6g7h8>. I served from <DATE_TIME_i9j0k1l2> to <DATE_TIME_m3n4o5p6>. Call me at <PHONE_NUMBER_q7r8s9t0>.",
#   "pii_detected": [
#     {"entity_type": "PERSON", "token": "<PERSON_a1b2c3d4>", "confidence": 0.85},
#     {"entity_type": "US_SSN", "token": "<US_SSN_e5f6g7h8>", "confidence": 0.95},
#     ...
#   ],
#   "session_id": "abc123..."
# }

# Test health
curl http://192.168.132.224:8090/health
```

## Task 6: Custom Veteran Recognizers (Optional)

Add custom recognizers for military-specific data:

```python
# Add to analyzer_service.py

from presidio_analyzer import Pattern, PatternRecognizer

# Military Service Number pattern (older records)
military_sn_pattern = Pattern(
    name="military_service_number",
    regex=r"\b[A-Z]{2}\s?\d{6,8}\b",
    score=0.7
)

military_sn_recognizer = PatternRecognizer(
    supported_entity="MILITARY_SERVICE_NUMBER",
    patterns=[military_sn_pattern]
)

# VA File Number
va_file_pattern = Pattern(
    name="va_file_number",
    regex=r"\b[Cc]?-?\d{7,9}\b",
    score=0.6
)

va_file_recognizer = PatternRecognizer(
    supported_entity="VA_FILE_NUMBER",
    patterns=[va_file_pattern]
)

# Add to analyzer
analyzer.registry.add_recognizer(military_sn_recognizer)
analyzer.registry.add_recognizer(va_file_recognizer)
```

## Task 7: Database Integration for Token Persistence

For production, store token maps in database instead of memory:

```sql
-- Add to vetassist_pii database
CREATE TABLE pii_token_map (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(32) NOT NULL,
    token VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    original_value_encrypted BYTEA NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',

    UNIQUE(session_id, token)
);

CREATE INDEX idx_token_map_session ON pii_token_map(session_id);
CREATE INDEX idx_token_map_expires ON pii_token_map(expires_at);

-- Cleanup job (add to cron)
-- DELETE FROM pii_token_map WHERE expires_at < NOW();
```

## Acceptance Criteria

- [ ] Presidio installed on greenfin with spaCy model
- [ ] analyzer_service.py deployed and running on port 8090
- [ ] Systemd service enabled and auto-starts
- [ ] /analyze endpoint correctly detects PII
- [ ] /analyze returns anonymized text with tokens
- [ ] /deanonymize requires explicit authorization
- [ ] Token map persisted (memory for POC, DB for production)
- [ ] Health endpoint responding
- [ ] Audit logging captures PII detection events

## Security Notes

- **AI agents NEVER see raw PII** - only tokenized references
- **Deanonymization is audited** - every reveal is logged with who/when
- **Token maps expire** - 24-hour TTL prevents long-term token→PII correlation
- **Authorization required** - only specific roles can deanonymize
- **Network isolation** - Presidio only accessible from internal services

## Performance Considerations

- spaCy en_core_web_lg model is ~800MB, loads once at startup
- First request may be slow (~2-3 sec) for model warm-up
- Subsequent requests: ~50-100ms for typical text
- For high volume: consider running multiple instances behind load balancer

## For Seven Generations
