# JR INSTRUCTION: SSIDAssist Gap-Fill (Missing Files Only)

**Task ID:** ASSIST-GAPFILL-SSIDASSIST
**Priority:** P1 -- Required before SSIDAssist can serve requests
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5)
**Date:** 2026-02-04
**Estimated Effort:** 2-3 hours
**Node:** Any (Python 3.11+ required)
**Type:** GAP-FILL -- partial execution recovery
**Depends On:** ASSIST-GAPFILL-CORE-BACKEND (core must be complete first)
**Seven Gen Impact:** Accessible Social Security guidance reduces suffering for disabled Americans waiting 18+ months for adjudication. Every correct PIA estimate prevents a family from making catastrophic financial decisions based on bad math.

---

## Mission Context

Phase 2 (SSIDAssist scaffold) was partially executed. The following files were created successfully during the initial run: the FastAPI application entry point, config, PIA calculator service, calculator endpoint, SSDI wizard YAML, crisis patterns YAML, and council context YAML. However, five critical files were never written: the council chat service, crisis detection module, wizard endpoint, chat endpoint, and database schema.

Without these files, SSIDAssist cannot serve wizard flows, council chat, or persist calculation history.

**This is a GAP-FILL instruction.** DO NOT recreate, overwrite, or modify any file that already exists.

---

## Existing Files (DO NOT TOUCH)

These files are confirmed present at `/ganuda/assist/ssidassist/`. Do not recreate, overwrite, or modify them:

| Path | Status |
|---|---|
| `backend/main.py` | EXISTS -- do not touch |
| `backend/config.py` | EXISTS -- do not touch |
| `backend/services/pia_calculator.py` | EXISTS -- do not touch |
| `backend/api/v1/endpoints/calculator.py` | EXISTS -- do not touch |
| `frontend/config/wizards/ssdi_application.yaml` | EXISTS -- do not touch |
| `config/crisis_patterns.yaml` | EXISTS -- do not touch |
| `config/council_context.yaml` | EXISTS -- do not touch |

---

## Objective

Create the 5 missing files under `/ganuda/assist/ssidassist/`. Also ensure the `sql/` directory exists.

---

## Prerequisites

- Confirm Phase 1 core gap-fill is complete: `/ganuda/assist/core/backend/base_council_chat.py` must exist
- Confirm Phase 1 core gap-fill is complete: `/ganuda/assist/core/backend/base_crisis.py` must exist
- Confirm Phase 1 core gap-fill is complete: `/ganuda/assist/core/backend/base_wizard.py` must exist
- Read the existing SSIDAssist files to understand naming conventions already in use
- All credentials via environment variables -- NO hardcoded passwords

---

## Steps

### Step 0: Pre-Flight Safety Check

Before creating any file, verify the existing files are intact and the core dependencies exist:

```bash
#!/bin/bash
echo "=== Pre-Flight: Verifying existing SSIDAssist files ==="
cd /ganuda/assist/ssidassist
for f in backend/main.py backend/config.py backend/services/pia_calculator.py backend/api/v1/endpoints/calculator.py frontend/config/wizards/ssdi_application.yaml config/crisis_patterns.yaml config/council_context.yaml; do
    if [ -f "$f" ]; then
        echo "[OK] $f exists ($(wc -l < "$f") lines)"
    else
        echo "[WARN] $f MISSING -- was expected to exist"
    fi
done

echo ""
echo "=== Pre-Flight: Verifying core dependencies ==="
for f in /ganuda/assist/core/backend/base_council_chat.py /ganuda/assist/core/backend/base_crisis.py /ganuda/assist/core/backend/base_wizard.py /ganuda/assist/core/backend/config.py; do
    if [ -f "$f" ]; then
        echo "[OK] $(basename $f) exists"
    else
        echo "[FAIL] $(basename $f) MISSING -- run ASSIST-GAPFILL-CORE-BACKEND first"
    fi
done

# Create sql directory if needed
mkdir -p /ganuda/assist/ssidassist/sql
echo "[OK] sql/ directory ready"
```

---

### Step 1: Create `/ganuda/assist/ssidassist/backend/services/council_chat.py`

SSDI council chat extending base. 20 CFR 404/416 context, Turtle specialist weighted higher for methodical benefit calculations.

```python
"""
SSIDAssist Council Chat Service.
Extends BaseCouncilChatService with Social Security regulatory context.
"""
import sys
sys.path.insert(0, '/ganuda/assist')
from core.backend.base_council_chat import BaseCouncilChatService, ChatResponse
from core.backend.config import AssistConfig


class SSIDCouncilChat(BaseCouncilChatService):
    """SSDI-specific council chat with 20 CFR context."""

    def __init__(self, config: AssistConfig):
        super().__init__(
            config=config,
            domain_context=(
                "Social Security Disability Insurance (SSDI) and Supplemental Security Income (SSI). "
                "Primary regulations: 20 CFR Part 404 (SSDI) and 20 CFR Part 416 (SSI). "
                "Covers PIA calculations, work credits, disability determination process, "
                "Blue Book listings, RFC assessments, and appeals procedures."
            ),
            citation_patterns=[
                r'20\s*CFR\s*§?\s*\d+\.\d+',
                r'SSR\s+\d{2}-\d+p?',
                r'POMS\s+[A-Z]{2}\s*\d+\.\d+',
            ],
            specialist_priority={
                "turtle": 1.3,     # Methodical benefit calculations
                "gecko": 1.2,      # Technical regulatory interpretation
                "spider": 0.8,     # Less relevant for SSDI
                "raven": 1.0,      # Strategic planning
                "eagle_eye": 1.0,  # Pattern recognition
            },
        )

    def build_system_prompt(self) -> str:
        return (
            "You are a knowledgeable Social Security benefits counselor. "
            "You help people understand SSDI and SSI eligibility, the application process, "
            "PIA calculations, and appeals. Always cite specific CFR sections or SSA rulings. "
            "Never guarantee outcomes. If unsure, recommend consulting with a disability attorney "
            "or accredited claims agent."
        )
```

---

### Step 2: Create `/ganuda/assist/ssidassist/backend/services/crisis_detection.py`

SSDI-specific crisis detection -- financial distress patterns relevant to SSDI applicants who are often in dire economic circumstances while waiting for adjudication.

```python
"""
SSIDAssist Crisis Detection.
Extends base crisis with financial distress patterns relevant to SSDI applicants.
"""
import sys
sys.path.insert(0, '/ganuda/assist')
from core.backend.base_crisis import detect_crisis_enhanced


SSID_FINANCIAL_CRISIS_PATTERNS = [
    "can't pay rent",
    "about to be evicted",
    "losing my home",
    "can't afford medication",
    "rationing medication",
    "can't feed my family",
    "utilities shut off",
    "going to lose everything",
    "no money for food",
    "disability check didn't come",
    "denied again",
    "appeal denied",
    "can't work anymore",
]


def detect_ssid_crisis(text: str, context: dict = None) -> dict:
    """
    SSDI-specific crisis detection.
    Combines base C-SSRS with financial distress patterns.
    """
    if context is None:
        context = {"user_type": "general"}

    # Run base crisis detection (C-SSRS + keyword)
    base_result = detect_crisis_enhanced(text, context)

    # Check financial distress patterns
    text_lower = text.lower()
    financial_matches = [p for p in SSID_FINANCIAL_CRISIS_PATTERNS if p in text_lower]

    if financial_matches:
        base_result["has_financial_distress"] = True
        base_result["financial_patterns"] = financial_matches

        # Financial distress alone is not suicide crisis, but flag for support
        if not base_result["is_crisis"]:
            base_result["recommended_action"] = "financial_support_referral"
            base_result["financial_resources"] = [
                "211 - Local social services referral",
                "SNAP/EBT - Food assistance: 1-800-221-5689",
                "LIHEAP - Utility assistance: contact local CAA",
                "SSA direct: 1-800-772-1213",
            ]
    else:
        base_result["has_financial_distress"] = False

    return base_result
```

---

### Step 3: Create `/ganuda/assist/ssidassist/backend/api/v1/endpoints/wizard.py`

SSDI application wizard endpoint. Loads the wizard definition from the YAML that already exists at `frontend/config/wizards/ssdi_application.yaml`.

```python
"""
SSIDAssist Wizard Endpoint.
Serves the SSDI application wizard steps.
"""
import sys
sys.path.insert(0, '/ganuda/assist')

from fastapi import APIRouter, HTTPException, Depends
from core.backend.base_wizard import BaseWizard, WizardProgress

router = APIRouter(prefix="/wizard", tags=["wizard"])

# Load wizard definition
SSDI_WIZARD = None

def get_wizard():
    global SSDI_WIZARD
    if SSDI_WIZARD is None:
        SSDI_WIZARD = BaseWizard("/ganuda/assist/ssidassist/frontend/config/wizards/ssdi_application.yaml")
    return SSDI_WIZARD


@router.get("/steps")
async def get_wizard_steps(wizard: BaseWizard = Depends(get_wizard)):
    """Get all wizard steps."""
    return {
        "metadata": wizard.metadata,
        "steps": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "fields": s.fields,
                "help_text": s.help_text,
            }
            for s in wizard.steps
        ],
        "total_steps": len(wizard.steps),
    }


@router.post("/validate/{step_id}")
async def validate_step(step_id: str, data: dict, wizard: BaseWizard = Depends(get_wizard)):
    """Validate a wizard step's data."""
    errors = wizard.validate_step(step_id, data)
    return {"valid": len(errors) == 0, "errors": errors}


@router.post("/progress")
async def get_progress(answers: dict, wizard: BaseWizard = Depends(get_wizard)):
    """Get visible steps and progress given current answers."""
    visible = wizard.get_visible_steps(answers)
    return {
        "visible_steps": [{"id": s.id, "title": s.title} for s in visible],
        "total_visible": len(visible),
    }
```

---

### Step 4: Create `/ganuda/assist/ssidassist/backend/api/v1/endpoints/chat.py`

SSDI council chat endpoint. Currently a stub that will be wired to the council chat service once the LLM gateway is confirmed accessible.

```python
"""
SSIDAssist Chat Endpoint.
Council chat with SSDI domain expertise.
"""
import sys
sys.path.insert(0, '/ganuda/assist')

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponseModel(BaseModel):
    message: str
    specialist: str
    citations: list = []
    session_id: str


@router.post("/", response_model=ChatResponseModel)
async def send_message(request: ChatRequest):
    """Send a message to the SSDI council chat."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id or "new"

    # Stub response - will be wired to actual council chat service
    return ChatResponseModel(
        message=f"[SSDI Council] I received your question about Social Security benefits. This is a stub response.",
        specialist="turtle",
        citations=[],
        session_id=session_id,
    )
```

---

### Step 5: Create `/ganuda/assist/ssidassist/sql/ssid_schema.sql`

Database schema for SSIDAssist-specific tables. Run on bluefin (192.168.132.222) against `zammad_production`. Depends on `assist_users` table from core schema.

```sql
-- SSIDAssist Schema
-- Run on bluefin (192.168.132.222) / zammad_production
-- Depends on: assist_core_schema.sql (assist_users table)

CREATE TABLE IF NOT EXISTS ssid_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    calculation_type VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ssid_earnings_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    year INTEGER NOT NULL,
    earnings DECIMAL(12,2),
    indexed_earnings DECIMAL(12,2),
    is_computation_year BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ssid_wizard_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    wizard_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ssid_calc_user ON ssid_calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_ssid_earnings_user ON ssid_earnings_records(user_id);
```

---

## Verification

After creating all files, run this verification script:

```bash
#!/bin/bash
echo "=== SSIDAssist Gap-Fill Verification ==="
cd /ganuda/assist/ssidassist

PASS=0
FAIL=0

echo "--- New files (should all exist) ---"
for f in "backend/services/council_chat.py" "backend/services/crisis_detection.py" "backend/api/v1/endpoints/wizard.py" "backend/api/v1/endpoints/chat.py" "sql/ssid_schema.sql"; do
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
for f in "backend/main.py" "backend/config.py" "backend/services/pia_calculator.py" "backend/api/v1/endpoints/calculator.py" "frontend/config/wizards/ssdi_application.yaml" "config/crisis_patterns.yaml" "config/council_context.yaml"; do
    if [ -f "$f" ]; then
        echo "[OK] $f (unchanged)"
    else
        echo "[FAIL] $f MISSING -- was NOT supposed to be touched"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Python syntax check ---"
for py_file in backend/services/council_chat.py backend/services/crisis_detection.py backend/api/v1/endpoints/wizard.py backend/api/v1/endpoints/chat.py; do
    python3 -c "import py_compile; py_compile.compile('$py_file', doraise=True)" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[OK] Syntax valid: $py_file"
    else
        echo "[FAIL] Syntax error: $py_file"
        FAIL=$((FAIL + 1))
    fi
done

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
| 1 | `backend/services/council_chat.py` | SSDI council chat with 20 CFR context, Turtle priority |
| 2 | `backend/services/crisis_detection.py` | Financial distress detection layered on C-SSRS base |
| 3 | `backend/api/v1/endpoints/wizard.py` | SSDI application wizard API endpoints |
| 4 | `backend/api/v1/endpoints/chat.py` | Council chat API endpoint (stub, to be wired) |
| 5 | `sql/ssid_schema.sql` | SSIDAssist database tables and indexes |

---

## Safety Notes

- DO NOT overwrite any existing file. If a target file already exists, skip it and report in verification output.
- DO NOT modify anything under `/ganuda/vetassist/` -- that is production.
- DO NOT modify anything under `/ganuda/assist/core/` -- that is managed by ASSIST-GAPFILL-CORE-BACKEND.
- All database credentials come from environment variables. No hardcoded passwords.
- The SQL schema uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` -- safe to run multiple times.
- Run core schema (`assist_core_schema.sql`) BEFORE this schema -- the `assist_users` FK dependency must exist.

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04
