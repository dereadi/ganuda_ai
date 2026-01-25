# JR Instruction: Presidio PII Integration (Executable Format)

## Overview

Install Microsoft Presidio for PII detection in VetAssist.

## Tasks

### Task 1: Install Presidio Packages

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && pip install presidio-analyzer presidio-anonymizer
```

### Task 2: Download spaCy Model

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -m spacy download en_core_web_lg
```

### Task 3: Generate PII Token Salt

```bash
PII_SALT=$(openssl rand -hex 32) && echo "PII_TOKEN_SALT=$PII_SALT" >> /ganuda/vetassist/backend/.env
```

## Verification

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && pip list | grep presidio
```

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -c "from presidio_analyzer import AnalyzerEngine; a = AnalyzerEngine(); r = a.analyze('SSN 123-45-6789', 'en'); print(f'Detected {len(r)} entities: {[x.entity_type for x in r]}')"
```

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -c "from app.services.pii_service import PIIService; p = PIIService(); print('PIIService loaded OK'); e = p.analyze('My SSN is 123-45-6789'); print(f'Detected: {e}')"
```

---

*Cherokee AI Federation - For the Seven Generations*
