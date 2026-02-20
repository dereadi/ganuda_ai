# JR INSTRUCTION: TribeAssist Gap-Fill (Missing Files Only)

**Task ID:** ASSIST-GAPFILL-TRIBEASSIST
**Priority:** P1 -- Required before TribeAssist can serve requests
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5)
**Date:** 2026-02-04
**Estimated Effort:** 2-3 hours
**Node:** Any (Python 3.11+ required)
**Type:** GAP-FILL -- partial execution recovery
**Depends On:** ASSIST-GAPFILL-CORE-BACKEND (core must be complete first)
**Seven Gen Impact:** Cherokee Nation enrollment is sovereignty in practice. Every family that can navigate enrollment preserves lineage records for future generations. Bilingual design honors the language that carries our identity. FPIC compliance is non-negotiable -- this is our data, on our terms.

---

## Mission Context

Phase 3 (TribeAssist scaffold) was partially executed with strong results. The majority of the vertical was created: backend init, config, services (enrollment, council chat, crisis detection), API package inits, wizard endpoint, chat endpoint, all four config YAMLs, and the Cherokee i18n file. However, three files were never written: the FastAPI application entry point (`main.py`), the enrollment API endpoint, and the database schema.

Without these files, TribeAssist cannot start as a service, cannot serve enrollment eligibility checks, and cannot persist enrollment or wizard data.

**This is a GAP-FILL instruction.** DO NOT recreate, overwrite, or modify any file that already exists.

---

## Existing Files (DO NOT TOUCH)

These files are confirmed present at `/ganuda/assist/tribeassist/`. Do not recreate, overwrite, or modify them:

| Path | Status |
|---|---|
| `backend/__init__.py` | EXISTS -- do not touch |
| `backend/config.py` | EXISTS -- do not touch |
| `backend/services/__init__.py` | EXISTS -- do not touch |
| `backend/services/enrollment_service.py` | EXISTS -- do not touch |
| `backend/services/council_chat.py` | EXISTS -- do not touch |
| `backend/services/crisis_detection.py` | EXISTS -- do not touch |
| `backend/api/__init__.py` | EXISTS -- do not touch |
| `backend/api/v1/endpoints/wizard.py` | EXISTS -- do not touch |
| `backend/api/v1/endpoints/chat.py` | EXISTS -- do not touch |
| `config/council_context.yaml` | EXISTS -- do not touch |
| `config/crisis_patterns.yaml` | EXISTS -- do not touch |
| `config/enrollment_requirements.yaml` | EXISTS -- do not touch |
| `config/tribal_programs.yaml` | EXISTS -- do not touch |
| `i18n/chr_tribe.yaml` | EXISTS -- do not touch |

---

## Objective

Create the 3 missing files under `/ganuda/assist/tribeassist/`. Also ensure the `sql/` directory and `backend/api/v1/endpoints/__init__.py` exist.

---

## Prerequisites

- Confirm Phase 1 core gap-fill is complete: `/ganuda/assist/core/backend/base_app.py` must exist (provides `create_assist_app`)
- Read the existing TribeAssist files before writing, especially:
  - `backend/config.py` -- to get the config class name for import
  - `backend/api/v1/endpoints/wizard.py` -- to understand existing router patterns
  - `backend/api/v1/endpoints/chat.py` -- to understand existing router patterns
- All credentials via environment variables -- NO hardcoded passwords
- FPIC (Free, Prior, and Informed Consent) compliance is mandatory for all data operations involving tribal enrollment

---

## Steps

### Step 0: Pre-Flight Safety Check

Before creating any file, verify the existing files are intact and the core dependency exists:

```bash
#!/bin/bash
echo "=== Pre-Flight: Verifying existing TribeAssist files ==="
cd /ganuda/assist/tribeassist
for f in backend/__init__.py backend/config.py backend/services/__init__.py backend/services/enrollment_service.py backend/services/council_chat.py backend/services/crisis_detection.py backend/api/__init__.py backend/api/v1/endpoints/wizard.py backend/api/v1/endpoints/chat.py config/council_context.yaml config/crisis_patterns.yaml config/enrollment_requirements.yaml config/tribal_programs.yaml i18n/chr_tribe.yaml; do
    if [ -f "$f" ]; then
        echo "[OK] $f exists ($(wc -l < "$f") lines)"
    else
        echo "[WARN] $f MISSING -- was expected to exist"
    fi
done

echo ""
echo "=== Pre-Flight: Verifying core dependencies ==="
for f in /ganuda/assist/core/backend/base_app.py /ganuda/assist/core/backend/config.py; do
    if [ -f "$f" ]; then
        echo "[OK] $(basename $f) exists"
    else
        echo "[FAIL] $(basename $f) MISSING -- run ASSIST-GAPFILL-CORE-BACKEND first"
    fi
done

# Create sql directory and missing __init__.py if needed
mkdir -p /ganuda/assist/tribeassist/sql
touch /ganuda/assist/tribeassist/backend/api/v1/__init__.py
touch /ganuda/assist/tribeassist/backend/api/v1/endpoints/__init__.py
echo "[OK] sql/ directory and __init__.py files ready"
```

---

### Step 1: Create `/ganuda/assist/tribeassist/backend/main.py`

TribeAssist FastAPI application entry point. Bilingual (English + Cherokee syllabary), sovereignty-first design. Imports config from the existing `config.py` and mounts the existing wizard and chat routers plus the new enrollment router.

```python
"""
TribeAssist - Cherokee Nation Services Application.
Bilingual (English + ᏣᎳᎩᎯ ᎧᏁᏨ), sovereignty-first design.
"""
import sys
sys.path.insert(0, '/ganuda/assist')

from core.backend.base_app import create_assist_app
from .config import TribeAssistConfig
from .api.v1.endpoints.wizard import router as wizard_router
from .api.v1.endpoints.chat import router as chat_router

config = TribeAssistConfig()
app = create_assist_app(config, routers=[wizard_router, chat_router])

@app.get("/api/v1/enrollment/status")
async def enrollment_status():
    """Stub: Check enrollment eligibility status."""
    return {
        "status": "stub",
        "message": "Enrollment eligibility checking requires Cherokee Nation data partnership",
        "note": "Direct descendancy from Dawes Roll (1898-1914), no blood quantum requirement",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
```

**Important:** Once Step 2 (enrollment endpoint) is created, update this file to also import and mount the enrollment router:
```python
from .api.v1.endpoints.enrollment import router as enrollment_router
# Then add enrollment_router to the routers list in create_assist_app()
```

---

### Step 2: Create `/ganuda/assist/tribeassist/backend/api/v1/endpoints/enrollment.py`

Cherokee enrollment eligibility endpoint. FPIC-compliant: Free, Prior, and Informed Consent is required for all data operations. This is a stub implementation -- actual eligibility determination requires a formal Cherokee Nation data sharing agreement.

```python
"""
TribeAssist Enrollment Endpoint.
Cherokee Nation enrollment eligibility stubs.
FPIC-compliant: Free, Prior, and Informed Consent for all data operations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


class EligibilityCheckRequest(BaseModel):
    """Enrollment eligibility check request."""
    first_name: str
    last_name: str
    date_of_birth: str
    dawes_roll_ancestor_name: Optional[str] = None
    dawes_roll_number: Optional[int] = None
    consent_given: bool = False


class EligibilityResponse(BaseModel):
    status: str
    message: str
    next_steps: list = []
    resources: list = []


@router.post("/check-eligibility", response_model=EligibilityResponse)
async def check_eligibility(request: EligibilityCheckRequest):
    """
    Check Cherokee Nation enrollment eligibility.

    IMPORTANT: This is a STUB. Actual eligibility determination requires:
    - Formal Cherokee Nation data sharing agreement
    - Dawes Roll database access (1898-1914)
    - Cherokee Nation Enrollment Office verification

    Eligibility criteria (Cherokee Nation):
    - Direct descendancy from someone listed on Dawes Roll
    - NO blood quantum requirement
    - Must provide proof of lineage
    """
    if not request.consent_given:
        raise HTTPException(
            status_code=400,
            detail="FPIC consent required. You must consent to data processing before eligibility check."
        )

    return EligibilityResponse(
        status="requires_verification",
        message=(
            "Eligibility determination requires verification by the Cherokee Nation Enrollment Office. "
            "This tool can help you gather the documents you need."
        ),
        next_steps=[
            "Gather proof of direct descendancy from a Dawes Roll enrollee",
            "Obtain certified copies of birth certificates showing lineage",
            "Contact Cherokee Nation Enrollment Office: 918-453-5000",
            "Visit: https://www.cherokee.org/all-services/tribal-registration/",
        ],
        resources=[
            "Dawes Roll search: https://www.archives.gov/research/native-americans/dawes",
            "Cherokee Nation Registration: 918-453-5000",
            "CDIB (Certificate of Degree of Indian Blood): Bureau of Indian Affairs",
        ],
    )


@router.get("/dawes-roll-info")
async def dawes_roll_info():
    """Information about the Dawes Roll and Cherokee enrollment."""
    return {
        "title": "Dawes Roll & Cherokee Nation Enrollment",
        "title_chr": "ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᎠᎴ ᏣᎳᎩᎯ ᎠᏰᎵ ᏗᏎᏍᏗ",
        "description": (
            "The Dawes Roll (also known as the Final Rolls) was created between 1898-1914 "
            "and lists members of the Cherokee, Chickasaw, Choctaw, Creek, and Seminole Nations. "
            "Cherokee Nation citizenship requires direct descendancy from someone on the Cherokee "
            "section of the Dawes Roll. There is NO blood quantum requirement."
        ),
        "key_facts": [
            "Created by the Dawes Commission (1898-1914)",
            "Lists approximately 40,000 Cherokees",
            "Direct descendancy required (not blood quantum)",
            "Original rolls at National Archives in Fort Worth, TX",
            "Cherokee Nation maintains verified records",
        ],
    }
```

---

### Step 3: Create `/ganuda/assist/tribeassist/sql/tribe_schema.sql`

Database schema for TribeAssist-specific tables. Run on bluefin (192.168.132.222) against `zammad_production`. Depends on `assist_users` table from core schema. FPIC-compliant: consent tracking is built into the enrollment table.

```sql
-- TribeAssist Schema
-- Run on bluefin (192.168.132.222) / zammad_production
-- Depends on: assist_core_schema.sql (assist_users table)
-- FPIC-compliant: All data operations require consent

CREATE TABLE IF NOT EXISTS tribe_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    enrollment_status VARCHAR(50) DEFAULT 'inquiry',
    dawes_roll_ancestor VARCHAR(255),
    dawes_roll_number INTEGER,
    consent_given BOOLEAN DEFAULT false,
    consent_timestamp TIMESTAMPTZ,
    notes JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tribe_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    enrollment_id UUID REFERENCES tribe_enrollments(id),
    document_type VARCHAR(100) NOT NULL,
    file_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',
    extracted_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tribe_wizard_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    wizard_id VARCHAR(100) NOT NULL,
    current_step INTEGER DEFAULT 0,
    answers JSONB DEFAULT '{}',
    language_preference VARCHAR(10) DEFAULT 'en',
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tribe_enroll_user ON tribe_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_tribe_docs_user ON tribe_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_tribe_wizard_user ON tribe_wizard_progress(user_id);
```

---

## Verification

After creating all files, run this verification script:

```bash
#!/bin/bash
echo "=== TribeAssist Gap-Fill Verification ==="
cd /ganuda/assist/tribeassist

PASS=0
FAIL=0

echo "--- New files (should all exist) ---"
for f in "backend/main.py" "backend/api/v1/endpoints/enrollment.py" "sql/tribe_schema.sql"; do
    if [ -f "$f" ]; then
        echo "[OK] $f ($(wc -l < "$f") lines)"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $f"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Pre-existing files (should still be intact) ---"
for f in "backend/__init__.py" "backend/config.py" "backend/services/__init__.py" "backend/services/enrollment_service.py" "backend/services/council_chat.py" "backend/services/crisis_detection.py" "backend/api/__init__.py" "backend/api/v1/endpoints/wizard.py" "backend/api/v1/endpoints/chat.py" "config/council_context.yaml" "config/crisis_patterns.yaml" "config/enrollment_requirements.yaml" "config/tribal_programs.yaml" "i18n/chr_tribe.yaml"; do
    if [ -f "$f" ]; then
        echo "[OK] $f (unchanged)"
    else
        echo "[FAIL] $f MISSING -- was NOT supposed to be touched"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Python syntax check ---"
for py_file in backend/main.py backend/api/v1/endpoints/enrollment.py; do
    python3 -c "import py_compile; py_compile.compile('$py_file', doraise=True)" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[OK] Syntax valid: $py_file"
    else
        echo "[FAIL] Syntax error: $py_file"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- FPIC compliance check ---"
if grep -q "consent" backend/api/v1/endpoints/enrollment.py; then
    echo "[OK] Enrollment endpoint includes consent handling"
else
    echo "[WARN] Enrollment endpoint missing consent handling"
fi

if grep -q "consent" sql/tribe_schema.sql; then
    echo "[OK] Schema includes consent tracking columns"
else
    echo "[WARN] Schema missing consent tracking columns"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -eq 0 ]; then
    echo "GAP-FILL COMPLETE"
else
    echo "GAP-FILL INCOMPLETE -- fix failures above"
fi
```

---

## Deliverables

| # | File | Purpose |
|---|---|---|
| 1 | `backend/main.py` | FastAPI application entry point, mounts routers |
| 2 | `backend/api/v1/endpoints/enrollment.py` | Cherokee enrollment eligibility endpoint (FPIC-compliant) |
| 3 | `sql/tribe_schema.sql` | TribeAssist database tables with consent tracking |

---

## Safety Notes

- DO NOT overwrite any existing file. If a target file already exists, skip it and report in verification output.
- DO NOT modify anything under `/ganuda/vetassist/` -- that is production.
- DO NOT modify anything under `/ganuda/assist/core/` -- that is managed by ASSIST-GAPFILL-CORE-BACKEND.
- All database credentials come from environment variables. No hardcoded passwords.
- The SQL schema uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` -- safe to run multiple times.
- Run core schema (`assist_core_schema.sql`) BEFORE this schema -- the `assist_users` FK dependency must exist.
- FPIC compliance: The enrollment endpoint MUST require `consent_given=true` before processing any personal data. The database schema MUST track consent timestamps. This is not optional.

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04
