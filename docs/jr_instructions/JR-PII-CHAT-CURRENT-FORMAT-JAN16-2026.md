# JR Instruction: VetAssist Chat PII Integration

## Overview

Run the PII integration script to add PIIService to chat.py.

## Tasks

### Task 1: Run Integration

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python integrate_pii.py
```

### Task 2: Verify Integration

```bash
grep -n "pii_service" /ganuda/vetassist/backend/app/api/v1/endpoints/chat.py
```

```bash
cd /ganuda/vetassist/backend && source venv/bin/activate && python -c "from app.api.v1.endpoints.chat import router; print('Import OK')"
```

---

*Cherokee AI Federation - For the Seven Generations*
