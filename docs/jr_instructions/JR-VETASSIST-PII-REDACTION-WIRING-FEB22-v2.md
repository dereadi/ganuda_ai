# Jr Instruction: VetAssist PII Redaction — Wire Existing Service into Document Pipeline (v2)

**Task ID:** PII-REDACTION-WIRING-v2
**Kanban:** #1847
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

The PII service already exists at `/ganuda/vetassist/backend/app/services/pii_service.py` (Presidio-based, KB-VETASSIST-PII-PROTECTION-JAN16-2026). It was NOT wired into the document processing pipeline. This instruction adds PII redaction to OCR text BEFORE it gets stored in the database.

NOTE: Do NOT create a new PII service. Use the existing one.

---

## Step 1: Import PII service in wizard.py

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```python
<<<<<<< SEARCH
import json
import uuid
import os
import shutil
=======
import json
import uuid
import os
import shutil
from app.services.pii_service import pii_service
>>>>>>> REPLACE
```

---

## Step 2: Redact OCR text before database storage

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```python
<<<<<<< SEARCH
        # Step 5: Store results in vetassist_documents
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vetassist_documents
                    (session_id, document_type, classification_confidence,
                     parsed_data, ocr_text, processing_status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                doc_type,
                confidence,
                json.dumps(parsed_data),
                extracted_text[:10000],  # Cap stored OCR text
=======
        # Step 5: Redact PII from OCR text before storage (KB-VETASSIST-PII-PROTECTION)
        redacted_text = pii_service.redact_for_logging(extracted_text[:10000])
        pii_findings = pii_service.analyze(extracted_text[:5000])
        pii_types_found = list(set(f.get('entity_type', '') for f in pii_findings)) if pii_findings else []
        if pii_types_found:
            parsed_data['pii_types_detected'] = pii_types_found

        # Store results in vetassist_documents (with redacted OCR text)
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vetassist_documents
                    (session_id, document_type, classification_confidence,
                     parsed_data, ocr_text, processing_status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                doc_type,
                confidence,
                json.dumps(parsed_data),
                redacted_text,  # PII-redacted OCR text
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/vetassist/backend && python3 -c "from app.api.v1.endpoints.wizard import router; print('Wizard imports OK')"
```

## What NOT to Change

- Do NOT create a new PII service file — use existing pii_service.py
- Do NOT modify the PII service itself
- Do NOT change parsed_data structure beyond adding pii_types_detected
- Do NOT redact the in-memory extracted_text (only redact what goes to DB)
