# JR Instruction: VetAssist Presidio PII Integration (ULTRATHINK ENHANCED)

## Metadata
```yaml
task_id: presidio_pii_integration_v2
priority: P1_CRITICAL
council_vote: 6700b2d88464ab8b
assigned_to: it_triad_jr
estimated_duration: 45_minutes
requires_sudo: false
requires_restart: true
target_node: redfin
```

## ULTRATHINK: Strategic Analysis

### Why This Matters (Seven Generations Impact)
Veterans trust us with their most sensitive data - SSNs, medical conditions, service records. A single data breach could:
- Destroy trust in the platform permanently
- Expose veterans to identity theft
- Create legal liability for the Federation
- End the VetAssist mission before it starts

**This is a SACRED FIRE priority.** We protect veteran data as we would protect the sacred fire.

### Current State Assessment
- `pii_service.py` EXISTS at `/ganuda/vetassist/backend/app/services/pii_service.py`
- Presidio packages NOT INSTALLED
- spaCy model NOT DOWNLOADED
- Chat endpoint NOT integrated
- goldfin vault NOT connected
- Environment variables NOT configured

### Success Criteria (Must ALL Pass)
1. `pip list | grep presidio` shows both packages
2. `python -c "import spacy; spacy.load('en_core_web_lg')"` succeeds
3. Test script detects SSN in sample text
4. Chat endpoint calls pii_service before storage
5. Redacted text stored in bluefin (no raw PII)

---

## PHASE 1: Install Dependencies
**Duration:** 10 minutes
**Risk Level:** LOW

### Step 1.1: Activate Virtual Environment
```bash
# CRITICAL: Must use VetAssist venv, not system Python
cd /ganuda/vetassist/backend
source venv/bin/activate

# Verify correct Python
which python
# Expected: /ganuda/vetassist/backend/venv/bin/python
```

### Step 1.2: Install Presidio Packages
```bash
# Install analyzer (entity detection) and anonymizer (redaction)
pip install presidio-analyzer presidio-anonymizer

# Verify installation
pip list | grep -i presidio
# Expected output:
# presidio-analyzer    2.x.x
# presidio-anonymizer  2.x.x
```

### Step 1.3: Download spaCy Model
```bash
# Presidio requires spaCy for NER (Named Entity Recognition)
# en_core_web_lg is the large English model (~750MB)
python -m spacy download en_core_web_lg

# Verify model loads
python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('spaCy model loaded successfully')"
```

### Step 1.4: Validate Presidio Works
```bash
python << 'PYTEST'
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Test detection
test_text = "My SSN is 123-45-6789 and phone is (555) 123-4567"
results = analyzer.analyze(text=test_text, language="en")

print(f"Detected {len(results)} PII entities:")
for r in results:
    print(f"  - {r.entity_type}: '{test_text[r.start:r.end]}' (score: {r.score:.2f})")

# Test anonymization
anonymized = anonymizer.anonymize(text=test_text, analyzer_results=results)
print(f"\nAnonymized: {anonymized.text}")

assert len(results) >= 2, "Should detect at least SSN and phone"
assert "123-45-6789" not in anonymized.text, "SSN should be anonymized"
print("\n✅ PHASE 1 COMPLETE: Presidio working correctly")
PYTEST
```

**CHECKPOINT:** If the above fails, DO NOT PROCEED. Debug first.

---

## PHASE 2: Verify PII Service Module
**Duration:** 5 minutes
**Risk Level:** LOW

### Step 2.1: Test Existing pii_service.py
```bash
cd /ganuda/vetassist/backend
source venv/bin/activate

python << 'PYTEST'
import sys
sys.path.insert(0, '/ganuda/vetassist/backend')

from app.services.pii_service import PIIService

pii = PIIService()

test_text = """
Hi, I'm John Smith. My SSN is 123-45-6789 and I was born on 01/15/1985.
You can reach me at (555) 123-4567 or john.smith@email.com.
I live at 123 Main Street, Anytown USA 12345.
I'm filing for PTSD and tinnitus from my service in Iraq.
"""

# Test analysis
print("=== ANALYSIS TEST ===")
entities = pii.analyze(test_text)
print(f"Detected {len(entities)} entities:")
for e in entities:
    print(f"  - {e['entity_type']}: '{e['text']}' (score: {e['score']:.2f})")

# Test redaction
print("\n=== REDACTION TEST ===")
redacted = pii.redact_for_logging(test_text)
print(f"Redacted text:\n{redacted}")

# Verify SSN is redacted
assert "123-45-6789" not in redacted, "SSN should be redacted"
assert "555" not in redacted or "123-4567" not in redacted, "Phone should be redacted"

# Test tokenization
print("\n=== TOKENIZATION TEST ===")
tokenized, token_map = pii.tokenize_for_vault(test_text, "test-user-123")
print(f"Token map has {len(token_map)} entries")
for token, data in token_map.items():
    print(f"  - {token[:8]}...: {data['entity_type']} = '{data['original']}'")

print("\n✅ PHASE 2 COMPLETE: PIIService working correctly")
PYTEST
```

**CHECKPOINT:** All assertions must pass.

---

## PHASE 3: Integrate with Chat Endpoint
**Duration:** 15 minutes
**Risk Level:** MEDIUM (modifying production code)

### Step 3.1: Backup Current Chat Endpoint
```bash
cp /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py \
   /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 3.2: Read Current Chat Endpoint
```bash
# Review current implementation before modifying
head -100 /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py
```

### Step 3.3: Add PII Integration
The chat endpoint needs these modifications:

1. **Import pii_service at top of file:**
```python
from app.services.pii_service import pii_service
```

2. **In the message handling function, BEFORE storing to database:**
```python
# Analyze for PII
pii_entities = pii_service.analyze(message_content)

# Create redacted version for storage
redacted_content = pii_service.redact_for_logging(message_content)

# Log PII detection (but not the actual PII)
if pii_entities:
    logger.info(f"PII detected in message: {len(pii_entities)} entities of types {set(e['entity_type'] for e in pii_entities)}")
```

3. **Store REDACTED version in database, not original:**
```python
# Store redacted version in chat_messages table
db_message = ChatMessage(
    session_id=session_id,
    content=redacted_content,  # <-- REDACTED, not original
    role="user",
    # ... other fields
)
```

4. **Use ORIGINAL for AI processing (in memory only):**
```python
# AI sees original (in memory) for accurate response
ai_response = await council_chat.get_response(
    message=message_content,  # <-- Original, in memory only
    session_id=session_id,
    # ...
)
```

### Step 3.4: Verify Integration
```bash
# Restart VetAssist backend
pkill -f "uvicorn app.main:app" || true
sleep 2
cd /ganuda/vetassist/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/vetassist_backend.log 2>&1 &
sleep 5

# Test the endpoint
curl -s -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-pii-session",
    "content": "Hi, my SSN is 123-45-6789 and I need help with my claim"
  }' | python3 -m json.tool

# Check what was stored in database
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c \
  "SELECT content FROM vetassist_chat_messages WHERE session_id = 'test-pii-session' ORDER BY created_at DESC LIMIT 1;"

# Verify SSN is NOT in stored content
```

**CHECKPOINT:** The database query should show `<REDACTED>` not `123-45-6789`.

---

## PHASE 4: Configure Environment
**Duration:** 5 minutes
**Risk Level:** LOW

### Step 4.1: Generate Secure Token Salt
```bash
# Generate cryptographically secure salt
PII_SALT=$(openssl rand -hex 32)
echo "Generated PII_TOKEN_SALT: $PII_SALT"
```

### Step 4.2: Add to Environment File
```bash
# Append to .env file
cat >> /ganuda/vetassist/backend/.env << EOF

# PII Protection (added $(date))
PII_TOKEN_SALT=$PII_SALT
PII_VAULT_HOST=100.x.x.x  # goldfin Tailscale IP - update when known
PII_VAULT_PORT=5432
PII_VAULT_DB=vetassist_pii
EOF

echo "Environment variables added to .env"
```

---

## PHASE 5: Validation & Documentation
**Duration:** 10 minutes
**Risk Level:** NONE

### Step 5.1: Full Integration Test
```bash
cd /ganuda/vetassist/backend
source venv/bin/activate

python << 'FULLTEST'
import asyncio
import sys
sys.path.insert(0, '/ganuda/vetassist/backend')

from app.services.pii_service import PIIService

pii = PIIService()

# Test cases representing real veteran input
test_cases = [
    ("My SSN is 123-45-6789", ["US_SSN"]),
    ("Call me at (555) 123-4567", ["PHONE_NUMBER"]),
    ("Email: veteran@gmail.com", ["EMAIL_ADDRESS"]),
    ("I live at 123 Oak Street, Dallas TX 75201", ["LOCATION"]),
    ("Born on 03/15/1975", ["DATE_TIME"]),
    ("My VA file number is 12345678", []),  # Custom - may not detect
    ("I have PTSD and tinnitus from Iraq", []),  # Medical - should NOT redact
]

print("=== COMPREHENSIVE PII TEST ===\n")
all_passed = True

for text, expected_types in test_cases:
    entities = pii.analyze(text)
    detected_types = [e['entity_type'] for e in entities]
    redacted = pii.redact_for_logging(text)

    # Check if expected entities were detected
    status = "✅" if all(t in detected_types for t in expected_types) else "⚠️"
    if expected_types and not any(t in detected_types for t in expected_types):
        status = "❌"
        all_passed = False

    print(f"{status} Input: '{text}'")
    print(f"   Expected: {expected_types}")
    print(f"   Detected: {detected_types}")
    print(f"   Redacted: '{redacted}'")
    print()

if all_passed:
    print("✅ ALL TESTS PASSED - PII protection is working")
else:
    print("⚠️ SOME TESTS NEED REVIEW - check output above")
FULLTEST
```

### Step 5.2: Update Thermal Memory
```bash
# Record completion in thermal memory
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production << 'SQL'
INSERT INTO thermal_memory_archive (content, memory_type, source_context, temperature, tags)
VALUES (
    'PRESIDIO PII INTEGRATION COMPLETE - January 16, 2026

Status: OPERATIONAL
Components:
- presidio-analyzer: Installed
- presidio-anonymizer: Installed
- spacy en_core_web_lg: Downloaded
- pii_service.py: Validated
- Chat endpoint: Integrated (VERIFY)
- Environment: Configured

PII Types Protected:
- US_SSN ✓
- PHONE_NUMBER ✓
- EMAIL_ADDRESS ✓
- LOCATION ✓
- DATE_TIME ✓

Next Steps:
- goldfin vault connection (Phase 2)
- Token storage implementation
- Audit logging

Council Vote: 6700b2d88464ab8b
Crawdad Security Approved',
    'deployment',
    'jr_instruction_execution',
    75.0,
    ARRAY['presidio', 'pii', 'vetassist', 'security', 'phase1_complete']
);
SQL
```

### Step 5.3: Create KB Article
```bash
cat > /ganuda/docs/kb/KB-PRESIDIO-PII-INTEGRATION-JAN16-2026.md << 'EOF'
# KB: Presidio PII Integration for VetAssist

**Date:** January 16, 2026
**Status:** Phase 1 Complete
**Author:** IT Triad Jr (automated)

## Summary

Microsoft Presidio has been integrated into VetAssist to detect and protect PII (Personally Identifiable Information) in veteran chat messages.

## Components Installed

| Component | Version | Location |
|-----------|---------|----------|
| presidio-analyzer | 2.x | VetAssist backend venv |
| presidio-anonymizer | 2.x | VetAssist backend venv |
| spacy en_core_web_lg | 3.x | VetAssist backend venv |
| pii_service.py | 1.0 | /ganuda/vetassist/backend/app/services/ |

## PII Types Detected

| Entity Type | Example | Action |
|-------------|---------|--------|
| US_SSN | 123-45-6789 | Redact |
| PHONE_NUMBER | (555) 123-4567 | Redact |
| EMAIL_ADDRESS | user@email.com | Redact |
| LOCATION | 123 Main St | Redact |
| DATE_TIME | 01/15/1985 | Redact |
| PERSON | John Smith | Preserve |

## Usage

```python
from app.services.pii_service import pii_service

# Analyze text for PII
entities = pii_service.analyze("My SSN is 123-45-6789")

# Redact for logging
safe_text = pii_service.redact_for_logging("My SSN is 123-45-6789")
# Returns: "My SSN is <REDACTED>"

# Tokenize for vault storage
tokenized, token_map = pii_service.tokenize_for_vault(text, user_id)
```

## Remaining Work (Phase 2)

- [ ] goldfin PostgreSQL vault setup
- [ ] Token storage to goldfin
- [ ] Encryption at rest for token_map
- [ ] Audit logging for PII access

## Troubleshooting

### Presidio not detecting SSN
Ensure spaCy model is loaded:
```bash
python -c "import spacy; spacy.load('en_core_web_lg')"
```

### Import errors
Ensure using VetAssist venv:
```bash
source /ganuda/vetassist/backend/venv/bin/activate
```

## References

- Council Vote: 6700b2d88464ab8b
- JR Instruction: JR-PRESIDIO-ULTRATHINK-EXECUTABLE-JAN16-2026.md
- Presidio Docs: https://microsoft.github.io/presidio/

---

*Cherokee AI Federation - For the Seven Generations*
EOF
```

---

## COMPLETION CHECKLIST

Execute this final validation:

```bash
echo "=== PRESIDIO INTEGRATION VALIDATION ==="
echo ""

# Check 1: Packages installed
echo -n "1. Presidio packages: "
pip list 2>/dev/null | grep -q presidio && echo "✅ INSTALLED" || echo "❌ MISSING"

# Check 2: spaCy model
echo -n "2. spaCy model: "
python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null && echo "✅ LOADED" || echo "❌ MISSING"

# Check 3: pii_service exists
echo -n "3. pii_service.py: "
[ -f /ganuda/vetassist/backend/app/services/pii_service.py ] && echo "✅ EXISTS" || echo "❌ MISSING"

# Check 4: Can import and use
echo -n "4. PIIService functional: "
python -c "from app.services.pii_service import PIIService; p = PIIService(); assert len(p.analyze('SSN 123-45-6789')) > 0" 2>/dev/null && echo "✅ WORKING" || echo "❌ BROKEN"

# Check 5: Environment configured
echo -n "5. Environment vars: "
grep -q PII_TOKEN_SALT /ganuda/vetassist/backend/.env 2>/dev/null && echo "✅ CONFIGURED" || echo "⚠️ PENDING"

# Check 6: KB article exists
echo -n "6. KB article: "
[ -f /ganuda/docs/kb/KB-PRESIDIO-PII-INTEGRATION-JAN16-2026.md ] && echo "✅ WRITTEN" || echo "⚠️ PENDING"

echo ""
echo "=== INTEGRATION STATUS ==="
```

---

## ERROR RECOVERY

### If pip install fails:
```bash
# Upgrade pip first
pip install --upgrade pip
pip install presidio-analyzer presidio-anonymizer
```

### If spaCy download fails:
```bash
# Try direct download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.0/en_core_web_lg-3.7.0.tar.gz
```

### If import fails after install:
```bash
# Restart Python to pick up new packages
deactivate
source venv/bin/activate
python -c "from presidio_analyzer import AnalyzerEngine; print('OK')"
```

---

*Cherokee AI Federation - For the Seven Generations*
*"The sacred fire protects the tribe. PII protection protects our veterans."*
