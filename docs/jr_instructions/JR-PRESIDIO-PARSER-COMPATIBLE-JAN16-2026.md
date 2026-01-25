# JR Instruction: Presidio PII Integration

## Overview

Install and validate Microsoft Presidio for VetAssist PII detection.

## Tasks

### Task 1: Create Installation Script

Create `/ganuda/vetassist/backend/install_presidio.sh`:

```bash
#!/bin/bash
# Presidio Installation Script for VetAssist
# Cherokee AI Federation - January 2026

set -e
echo "=== PRESIDIO PII INSTALLATION ==="

cd /ganuda/vetassist/backend
source venv/bin/activate

echo "1. Installing presidio packages..."
pip install presidio-analyzer presidio-anonymizer

echo "2. Downloading spaCy model..."
python -m spacy download en_core_web_lg

echo "3. Generating PII token salt..."
if ! grep -q PII_TOKEN_SALT .env 2>/dev/null; then
    PII_SALT=$(openssl rand -hex 32)
    echo "PII_TOKEN_SALT=$PII_SALT" >> .env
    echo "   Added PII_TOKEN_SALT to .env"
else
    echo "   PII_TOKEN_SALT already exists in .env"
fi

echo "4. Testing Presidio..."
python -c "
from presidio_analyzer import AnalyzerEngine
from app.services.pii_service import PIIService

# Test analyzer
a = AnalyzerEngine()
r = a.analyze('SSN 123-45-6789', 'en')
assert len(r) >= 1, 'Should detect SSN'
print('   Presidio analyzer: OK')

# Test PIIService
p = PIIService()
e = p.analyze('My SSN is 123-45-6789')
assert len(e) >= 1, 'PIIService should detect SSN'
print('   PIIService: OK')

# Test redaction
redacted = p.redact_for_logging('My SSN is 123-45-6789')
assert '123-45-6789' not in redacted, 'SSN should be redacted'
print('   Redaction: OK')

print('ALL TESTS PASSED')
"

echo ""
echo "=== PRESIDIO INSTALLATION COMPLETE ==="
```

## Verification

```bash
cd /ganuda/vetassist/backend && chmod +x install_presidio.sh && ./install_presidio.sh
```

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && pip list | grep -E "presidio|spacy"
```

---

*Cherokee AI Federation - For the Seven Generations*
