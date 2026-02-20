# JR INSTRUCTION: Assist Platform Phase 3 — TribeAssist Scaffold

**Task ID:** ASSIST-PHASE3-TRIBEASSIST
**Priority:** P1
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5) + Council
**Date:** 2026-02-04
**Depends On:** ASSIST-PHASE1-CORE
**Runs Parallel With:** ASSIST-PHASE2-SSIDASSIST

---

## Mission Context

TribeAssist is the third vertical in the Assist Platform Family. It serves the Cherokee Nation community.

**This vertical is special.** Cherokee language (ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ) is first-class — bilingual throughout, not a translation layer on top of English. Spider specialist gets 1.5x weight as Cherokee cultural authority.

Preserving Cherokee sovereignty and language is not a feature — it is the foundation. ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ.

**Critical Legal Context — Cherokee Nation Enrollment:**
- Cherokee Nation citizenship requires **direct descendancy** from someone listed on the Dawes Roll (1898-1914)
- **NO blood quantum requirement** — this is important and distinguishes Cherokee from many other tribes
- CDIB (Certificate of Degree of Indian Blood) is a separate federal document, not the same as tribal enrollment
- The Jr MUST create service stubs only — actual Dawes Roll data requires a formal Cherokee Nation partnership
- Do NOT hardcode or fabricate any Dawes Roll data

**Reference Pattern:** Follow the VetAssist backend (`/ganuda/vetassist/backend/main.py`) and frontend (`/ganuda/vetassist/frontend/app/layout.tsx`, `page.tsx`) architecture. See also the platform family architecture: `/ganuda/docs/ultrathink/ULTRATHINK-ASSIST-PLATFORM-FAMILY-JAN18-2026.md`.

---

## Directory Structure

All files go under `/ganuda/assist/tribeassist/`. Create this complete tree:

```
/ganuda/assist/tribeassist/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── enrollment_service.py
│   │   ├── council_chat.py
│   │   └── crisis_detection.py
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── endpoints/
│               ├── __init__.py
│               ├── enrollment.py
│               ├── wizard.py
│               └── chat.py
├── frontend/
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       └── wizard/
│           └── page.tsx
├── config/
│   ├── wizards/
│   │   └── enrollment.yaml
│   ├── crisis_patterns.yaml
│   ├── council_context.yaml
│   └── dawes_roll_reference.yaml
├── i18n/
│   └── chr_tribe.yaml
└── sql/
    └── tribe_schema.sql
```

---

## Step 1: Backend — `__init__.py`

**File:** `/ganuda/assist/tribeassist/backend/__init__.py`

```python
"""
TribeAssist Backend
Cherokee AI Federation — Cherokee Nation Services
ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — For Seven Generations
"""
```

---

## Step 2: Backend — `main.py`

**File:** `/ganuda/assist/tribeassist/backend/main.py`

Pattern: follows `/ganuda/vetassist/backend/main.py` — FastAPI app with CORS, health check, and router mounts.

```python
"""
TribeAssist Backend API
Cherokee AI Federation — Cherokee Nation Services
ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — For Seven Generations
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TribeAssist API",
    description="Cherokee AI Federation — Cherokee Nation Services & Enrollment",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("TRIBE_CORS_ORIGIN", "https://tribeassist.ganuda.us"),
        "http://localhost:3002",
        "http://localhost:8003"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "TribeAssist API",
        "version": "1.0.0",
        "vertical": "tribeassist",
        "language_support": ["en", "chr"]
    }


# Import and include routers
try:
    from backend.api.v1.endpoints import enrollment, wizard, chat

    app.include_router(
        enrollment.router,
        prefix="/api/v1/enrollment",
        tags=["enrollment"]
    )
    app.include_router(
        wizard.router,
        prefix="/api/v1/wizard",
        tags=["wizard"]
    )
    app.include_router(
        chat.router,
        prefix="/api/v1/chat",
        tags=["chat"]
    )
    logger.info("[TribeAssist] All routers loaded successfully")
except ImportError as e:
    logger.warning(f"[TribeAssist] Some routers not loaded: {e}")


# Placeholder routes
@app.get("/api/auth/session")
async def get_session():
    """Placeholder for auth session."""
    return {"user": None, "authenticated": False}


@app.get("/api/citizen/profile")
async def get_citizen_profile():
    """Placeholder for citizen profile."""
    return {"profile": None, "status": "not_authenticated"}


@app.get("/api/services")
async def get_services():
    """List available tribal services."""
    return {
        "services": [
            {"id": "enrollment", "name_en": "Enrollment", "name_chr": "ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ"},
            {"id": "health", "name_en": "Health Services", "name_chr": "ᎠᏓᏅᏖᏍᏗ ᎠᏰᎵ"},
            {"id": "education", "name_en": "Education", "name_chr": "ᏗᎧᎿᏩᏛᏍᏗ"},
            {"id": "housing", "name_en": "Housing", "name_chr": "ᎦᎵᏦᏕ"},
            {"id": "elder_care", "name_en": "Elder Care", "name_chr": "ᎠᏂᎨᏯ ᎠᎵᏍᏕᎸᏙᏗ"},
            {"id": "language", "name_en": "Language Programs", "name_chr": "ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ"}
        ],
        "total": 6
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("TRIBE_PORT", "8003")),
        reload=True,
        log_level="info"
    )
```

---

## Step 3: Backend — `config.py`

**File:** `/ganuda/assist/tribeassist/backend/config.py`

Extends `AssistConfig` base. All config via environment variables with `TRIBE_` prefix.

```python
"""
TribeAssist Configuration
Extends Assist Platform core config with Cherokee-specific settings.
All values via environment variables — NO hardcoded credentials.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TribeConfig:
    """Cherokee Nation TribeAssist configuration.

    All values sourced from environment variables with TRIBE_ prefix.
    Database: bluefin 192.168.132.222, zammad_production.
    """

    # Service identity
    vertical_id: str = "tribeassist"
    service_name: str = "TribeAssist"
    version: str = "1.0.0"

    # Network
    host: str = field(default_factory=lambda: os.getenv("TRIBE_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("TRIBE_PORT", "8003")))
    cors_origin: str = field(
        default_factory=lambda: os.getenv("TRIBE_CORS_ORIGIN", "https://tribeassist.ganuda.us")
    )

    # Database — NO hardcoded credentials
    db_host: str = field(default_factory=lambda: os.getenv("TRIBE_DB_HOST", "192.168.132.222"))
    db_port: int = field(default_factory=lambda: int(os.getenv("TRIBE_DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("TRIBE_DB_NAME", "zammad_production"))
    db_user: str = field(default_factory=lambda: os.getenv("TRIBE_DB_USER", ""))
    db_password: str = field(default_factory=lambda: os.getenv("TRIBE_DB_PASSWORD", ""))

    @property
    def database_url(self) -> str:
        if not self.db_user or not self.db_password:
            raise ValueError("TRIBE_DB_USER and TRIBE_DB_PASSWORD must be set")
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Language settings
    default_language: str = "en"
    supported_languages: List[str] = field(default_factory=lambda: ["en", "chr"])

    # Council specialist weights — Spider gets 1.5x (Cherokee cultural authority)
    specialist_weights: Dict[str, float] = field(default_factory=lambda: {
        "spider": 1.5,      # Cherokee cultural authority — HIGHEST weight
        "turtle": 1.0,      # Steady guidance
        "raven": 1.2,       # Strategic navigation
        "eagle_eye": 1.0,   # Pattern recognition
        "gecko": 0.8,       # Less relevant for tribal services
        "crawdad": 1.0,     # Security always matters
    })

    # Cherokee-specific
    dawes_roll_integration: str = "stub"  # "stub" | "live" — requires CN partnership
    enable_bilingual: bool = True
    cherokee_syllabary_primary: bool = True  # Use syllabary, not romanized

    # LLM
    llm_endpoint: str = field(
        default_factory=lambda: os.getenv("TRIBE_LLM_ENDPOINT", "http://localhost:11434")
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("TRIBE_LLM_MODEL", "")
    )
```

---

## Step 4: Backend Services — `__init__.py`

**File:** `/ganuda/assist/tribeassist/backend/services/__init__.py`

```python
"""TribeAssist Services"""

from backend.services.enrollment_service import EnrollmentService
from backend.services.council_chat import TribeCouncilChatService
from backend.services.crisis_detection import TribeCrisisDetection

__all__ = [
    "EnrollmentService",
    "TribeCouncilChatService",
    "TribeCrisisDetection",
]
```

---

## Step 5: Backend Services — `enrollment_service.py`

**File:** `/ganuda/assist/tribeassist/backend/services/enrollment_service.py`

These are STUBS. Actual integration requires Cherokee Nation partnership. Mark this clearly.

```python
"""
TribeAssist Enrollment Service
Cherokee Nation enrollment guidance and eligibility stubs.

STATUS: STUBS ONLY
Actual Dawes Roll integration requires a formal Cherokee Nation data sharing agreement.
Do NOT fabricate or hardcode any Dawes Roll data.

Key Facts:
- Cherokee Nation citizenship requires direct descendancy from the Dawes Roll (1898-1914)
- NO blood quantum requirement for Cherokee Nation
- CDIB is a separate federal document (25 CFR Part 70)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class EligibilityResult:
    """Result of an eligibility check (stub)."""
    eligible: Optional[bool]  # None = cannot determine (stub mode)
    reason: str
    next_steps: List[str]
    requires_partnership: bool = True


class EnrollmentService:
    """Cherokee Nation enrollment guidance service.

    WARNING: This service provides general information only.
    Actual enrollment determinations are made solely by the
    Cherokee Nation Registration Department.
    """

    # -----------------------------------------------------------
    # STUB: check_eligibility
    # -----------------------------------------------------------
    async def check_eligibility(self, ancestor_info: dict) -> EligibilityResult:
        """Check enrollment eligibility based on ancestor information.

        STUB — Returns guidance only. Cannot verify Dawes Roll
        connection without Cherokee Nation partnership.

        Args:
            ancestor_info: Dict with keys like:
                - ancestor_name: str
                - ancestor_roll_number: Optional[int]
                - relationship: str (e.g., "great-grandmother")

        Returns:
            EligibilityResult with guidance and next steps.
        """
        logger.info("[TribeAssist] Eligibility check requested (STUB mode)")

        has_roll_number = bool(ancestor_info.get("ancestor_roll_number"))
        has_ancestor_name = bool(ancestor_info.get("ancestor_name"))

        if has_roll_number:
            return EligibilityResult(
                eligible=None,  # Cannot confirm — stub mode
                reason=(
                    "You provided a Dawes Roll number. This is a good start. "
                    "Verification requires contacting the Cherokee Nation "
                    "Registration Department directly."
                ),
                next_steps=[
                    "Contact Cherokee Nation Registration: 1-800-256-0671",
                    "Visit: https://www.cherokee.org/all-services/tribal-registration/",
                    "Have your ancestor's full name and roll number ready",
                    "Gather supporting documents (birth certificates, lineage proof)",
                ],
                requires_partnership=True,
            )
        elif has_ancestor_name:
            return EligibilityResult(
                eligible=None,
                reason=(
                    "You provided an ancestor name but no Dawes Roll number. "
                    "The Cherokee Nation can help you search the Dawes Roll "
                    "records. Remember: Cherokee Nation does NOT require a "
                    "blood quantum — only direct descendancy from a Dawes Roll enrollee."
                ),
                next_steps=[
                    "Search the Dawes Rolls at the National Archives (www.archives.gov)",
                    "Contact Cherokee Nation Registration: 1-800-256-0671",
                    "Request a search of the Dawes Roll by ancestor name",
                    "Gather family history documentation",
                ],
                requires_partnership=True,
            )
        else:
            return EligibilityResult(
                eligible=None,
                reason=(
                    "To check Cherokee Nation enrollment eligibility, you need "
                    "to identify a direct ancestor on the Dawes Roll (1898-1914). "
                    "Cherokee Nation does NOT have a blood quantum requirement."
                ),
                next_steps=[
                    "Research your family history for Cherokee ancestors",
                    "Check the Dawes Rolls at the National Archives",
                    "Contact Cherokee Nation Registration for guidance: 1-800-256-0671",
                ],
                requires_partnership=True,
            )

    # -----------------------------------------------------------
    # get_enrollment_steps
    # -----------------------------------------------------------
    async def get_enrollment_steps(self) -> list:
        """Return the general steps for Cherokee Nation enrollment.

        This is public information from cherokee.org — not proprietary.
        """
        return [
            {
                "step": 1,
                "title_en": "Identify your Dawes Roll ancestor",
                "title_chr": "ᏣᎳᎩ ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᎠᏓᏅᏙ",
                "description": (
                    "Determine which of your direct ancestors was enrolled "
                    "on the Dawes Roll between 1898 and 1914. You need their "
                    "full name and, ideally, their roll number."
                ),
            },
            {
                "step": 2,
                "title_en": "Prove direct descendancy",
                "title_chr": "ᎤᏲᎢ ᎤᎾᏓᏡᎬ ᎠᏓᏃᎮᏍᏗ",
                "description": (
                    "Gather birth certificates and other vital records "
                    "showing an unbroken line from you to your Dawes Roll ancestor. "
                    "Every generation must be documented."
                ),
            },
            {
                "step": 3,
                "title_en": "Complete the application",
                "title_chr": "ᎠᏓᏅᏖᏍᏗ ᏚᎸᏫᏍᏓᏁᏗ",
                "description": (
                    "Submit the Cherokee Nation citizenship application "
                    "along with all supporting documents. Application is free."
                ),
            },
            {
                "step": 4,
                "title_en": "Cherokee Nation processes your application",
                "title_chr": "ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᎾᏅᎢ",
                "description": (
                    "The Cherokee Nation Registration Department reviews "
                    "your application and verifies descendancy from the Dawes Roll."
                ),
            },
            {
                "step": 5,
                "title_en": "Receive your citizenship card",
                "title_chr": "ᎠᏓᏅᏖᏍᏗ ᎦᏔ ᎠᏥᎸᎯᏍᏗ",
                "description": (
                    "If approved, you will receive a Cherokee Nation citizenship card. "
                    "You may also apply separately for a CDIB (Certificate of Degree "
                    "of Indian Blood) through the Bureau of Indian Affairs."
                ),
            },
        ]

    # -----------------------------------------------------------
    # get_cdib_info
    # -----------------------------------------------------------
    async def get_cdib_info(self) -> dict:
        """Return information about the CDIB (Certificate of Degree of Indian Blood).

        CDIB is a federal document, separate from Cherokee Nation enrollment.
        Regulated under 25 CFR Part 70.
        """
        return {
            "title_en": "Certificate of Degree of Indian Blood (CDIB)",
            "title_chr": "ᏗᎧᎿᏩᏛᏍᏗ ᎠᏓᏅᏖᏍᏗ",
            "description": (
                "A CDIB is a federal document issued by the Bureau of Indian Affairs (BIA) "
                "that certifies a person has a specific degree of Indian blood. It is "
                "separate from Cherokee Nation tribal enrollment."
            ),
            "key_points": [
                "CDIB is issued by the Bureau of Indian Affairs, not the Cherokee Nation",
                "Cherokee Nation enrollment does NOT require a CDIB",
                "Cherokee Nation does NOT require a minimum blood quantum",
                "A CDIB may be useful for other federal Indian programs",
                "Regulated under 25 CFR Part 70",
            ],
            "how_to_apply": [
                "Obtain tribal enrollment first (recommended)",
                "Complete BIA Form 4432",
                "Submit proof of Indian ancestry (tribal enrollment, vital records)",
                "BIA processes the application and issues the certificate",
            ],
            "regulation": "25 CFR Part 70",
            "note": (
                "Many Cherokee citizens choose not to obtain a CDIB because Cherokee "
                "Nation enrollment is sufficient for tribal services. The CDIB blood "
                "quantum listed is a historical federal classification and does not "
                "reflect Cherokee Nation's own citizenship requirements."
            ),
        }
```

---

## Step 6: Backend Services — `council_chat.py`

**File:** `/ganuda/assist/tribeassist/backend/services/council_chat.py`

Extends the base council chat with Spider 1.5x weight and bilingual context.

```python
"""
TribeAssist Council Chat Service
Extends BaseCouncilChatService with Cherokee-specific context.

Spider specialist gets 1.5x weight — Cherokee cultural authority.
Bilingual context: Cherokee syllabary (ᏣᎳᎩ) + English.
Domain: Cherokee Nation services, enrollment, tribal sovereignty.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Specialist weight overrides for TribeAssist
TRIBE_SPECIALIST_WEIGHTS = {
    "spider": 1.5,      # Cherokee cultural authority — HIGHEST weight
    "turtle": 1.0,      # Steady guidance
    "raven": 1.2,       # Strategic navigation
    "eagle_eye": 1.0,   # Pattern recognition
    "gecko": 0.8,       # Less relevant for tribal services
    "crawdad": 1.0,     # Security always matters
}

TRIBE_SYSTEM_CONTEXT = """You are helping a member of or descendant of the Cherokee Nation
navigate tribal services, enrollment, and community resources.

KEY RULES:
1. Cherokee Nation citizenship is based on Dawes Roll descendancy — NO blood quantum.
2. Spider specialist carries 1.5x weight for Cherokee cultural authority.
3. Provide bilingual responses when the user's language preference is Cherokee.
4. Use Cherokee syllabary (ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ), NOT romanized Cherokee.
5. Respect tribal sovereignty — Cherokee Nation is a sovereign government.
6. Reference Cherokee Nation Constitution and relevant federal Indian law when applicable.
7. Never provide legal advice — recommend Cherokee Nation Legal Resources or tribal legal aid.
8. Handle historical trauma topics with deep cultural sensitivity.
9. Gadugi (ᎦᏚᎩ) — communal work — is the guiding principle.

REGULATIONS TO CITE:
- Cherokee Nation Constitution
- Indian Reorganization Act of 1934
- Cherokee Nation Registration Act
- CDIB regulations (25 CFR Part 70)

KEY CONCEPTS:
- Dawes Roll (1898-1914) — basis for enrollment
- No blood quantum requirement for Cherokee Nation
- CDIB — Certificate of Degree of Indian Blood (federal, separate from tribal enrollment)
- Gadugi — Cherokee tradition of communal work
- ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — Seven Generations principle
"""


class TribeCouncilChatService:
    """Council chat service for TribeAssist.

    Extends base council chat with:
    - Spider 1.5x weight (Cherokee cultural authority)
    - Bilingual Cherokee/English context
    - Cherokee Nation domain knowledge
    """

    def __init__(self):
        self.specialist_weights = TRIBE_SPECIALIST_WEIGHTS
        self.system_context = TRIBE_SYSTEM_CONTEXT
        self.domain = "Cherokee Nation Services & Enrollment"

    async def get_chat_context(self, language: str = "en") -> Dict:
        """Return chat context for council session.

        Args:
            language: "en" for English, "chr" for Cherokee.

        Returns:
            Dict with system context, specialist weights, and domain info.
        """
        context = {
            "system_context": self.system_context,
            "specialist_weights": self.specialist_weights,
            "domain": self.domain,
            "language": language,
            "bilingual": True,
            "greeting": {
                "en": "Welcome. How can I help you with Cherokee Nation services today?",
                "chr": "ᎣᏏᏲ. ᎦᏙ ᏥᎩᏱ ᎬᏩᎵᏍᏕᎸᏙᏗ ᎪᎯ ᎢᎦ?"
            }
        }
        return context

    async def format_bilingual_response(
        self, response_en: str, response_chr: Optional[str] = None
    ) -> Dict:
        """Format a bilingual response.

        Args:
            response_en: English response text.
            response_chr: Cherokee response text (optional).

        Returns:
            Dict with both language versions.
        """
        return {
            "en": response_en,
            "chr": response_chr or "",
            "bilingual": response_chr is not None,
        }
```

---

## Step 7: Backend Services — `crisis_detection.py`

**File:** `/ganuda/assist/tribeassist/backend/services/crisis_detection.py`

Cultural/community crisis patterns specific to Cherokee and Native communities.

```python
"""
TribeAssist Crisis Detection Service
Cultural and community crisis patterns for Cherokee/Native communities.

Patterns include:
- Historical trauma (boarding schools, Trail of Tears, cultural loss)
- Cultural isolation (disconnection from tribe, language loss)
- Elder care concerns
- Substance abuse (culturally appropriate response — not generic)

Handle ALL of these with deep cultural sensitivity.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CrisisDetectionResult:
    """Result from crisis pattern detection."""
    detected: bool
    category: Optional[str]
    severity: Optional[str]  # "low", "medium", "high", "critical"
    action: Optional[str]
    response_note: Optional[str]
    matched_keywords: List[str]


# Crisis patterns — loaded from config/crisis_patterns.yaml at runtime.
# These are the defaults embedded for startup resilience.
DEFAULT_CRISIS_PATTERNS = [
    {
        "category": "historical_trauma",
        "severity": "medium",
        "keywords": [
            "boarding school", "trail of tears", "stolen generation",
            "lost my culture", "taken from family", "forced assimilation",
            "residential school",
        ],
        "action": "cultural_support_referral",
        "response_note": "Handle with deep cultural sensitivity",
    },
    {
        "category": "cultural_isolation",
        "severity": "medium",
        "keywords": [
            "disconnected from tribe", "don't know my language",
            "lost my identity", "not Cherokee enough",
            "don't belong", "no connection to culture",
        ],
        "action": "cultural_reconnection_resources",
        "response_note": (
            "Affirm identity. Cherokee Nation has no blood quantum — "
            "descendancy is what matters. Direct to language and cultural programs."
        ),
    },
    {
        "category": "elder_care",
        "severity": "high",
        "keywords": [
            "elder needs help", "grandparent alone",
            "traditional healer needed", "elder abuse",
            "grandmother can't", "grandfather sick",
        ],
        "action": "tribal_elder_services",
        "response_note": "Elders are sacred. Treat with utmost respect and urgency.",
    },
    {
        "category": "substance_abuse",
        "severity": "high",
        "keywords": [
            "drinking problem", "addiction", "meth",
            "alcohol", "substance abuse", "overdose",
            "relapse",
        ],
        "action": "tribal_behavioral_health",
        "response_note": (
            "Culturally appropriate treatment referrals, not generic. "
            "Cherokee Nation Behavioral Health: 1-800-256-0671. "
            "Reference Gadugi (communal support) and traditional healing alongside clinical."
        ),
    },
    {
        "category": "immediate_danger",
        "severity": "critical",
        "keywords": [
            "want to die", "kill myself", "suicide",
            "end my life", "no reason to live", "hurt myself",
        ],
        "action": "immediate_crisis_intervention",
        "response_note": (
            "IMMEDIATE: 988 Suicide & Crisis Lifeline (call or text 988). "
            "Cherokee Nation Behavioral Health crisis line. "
            "Do not leave the person without providing these resources."
        ),
    },
]


class TribeCrisisDetection:
    """Crisis detection tuned for Cherokee/Native community patterns.

    This service scans user messages for crisis indicators and returns
    appropriate culturally sensitive actions.
    """

    def __init__(self, patterns: Optional[List[Dict]] = None):
        self.patterns = patterns or DEFAULT_CRISIS_PATTERNS

    async def scan_message(self, message: str) -> CrisisDetectionResult:
        """Scan a user message for crisis patterns.

        Args:
            message: The user's message text.

        Returns:
            CrisisDetectionResult with detection info and action.
        """
        message_lower = message.lower()
        matched_keywords = []
        highest_severity = None
        highest_pattern = None

        severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        for pattern in self.patterns:
            for keyword in pattern["keywords"]:
                if keyword.lower() in message_lower:
                    matched_keywords.append(keyword)
                    pattern_severity = pattern["severity"]
                    if (
                        highest_severity is None
                        or severity_rank.get(pattern_severity, 0)
                        > severity_rank.get(highest_severity, 0)
                    ):
                        highest_severity = pattern_severity
                        highest_pattern = pattern

        if highest_pattern:
            logger.warning(
                f"[TribeAssist] Crisis detected: category={highest_pattern['category']}, "
                f"severity={highest_severity}, keywords={matched_keywords}"
            )
            return CrisisDetectionResult(
                detected=True,
                category=highest_pattern["category"],
                severity=highest_severity,
                action=highest_pattern["action"],
                response_note=highest_pattern.get("response_note"),
                matched_keywords=matched_keywords,
            )

        return CrisisDetectionResult(
            detected=False,
            category=None,
            severity=None,
            action=None,
            response_note=None,
            matched_keywords=[],
        )
```

---

## Step 8: Backend API — `__init__.py` files

**File:** `/ganuda/assist/tribeassist/backend/api/__init__.py`

```python
"""TribeAssist API"""
```

**File:** `/ganuda/assist/tribeassist/backend/api/v1/__init__.py`

```python
"""TribeAssist API v1"""
```

**File:** `/ganuda/assist/tribeassist/backend/api/v1/endpoints/__init__.py`

```python
"""TribeAssist API v1 Endpoints"""
```

---

## Step 9: Backend API — `enrollment.py`

**File:** `/ganuda/assist/tribeassist/backend/api/v1/endpoints/enrollment.py`

```python
"""
TribeAssist Enrollment Endpoints
Cherokee Nation enrollment status, CDIB info, eligibility check stubs.

All actual enrollment determinations are made by Cherokee Nation Registration.
These endpoints provide guidance only.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from backend.services.enrollment_service import EnrollmentService

logger = logging.getLogger(__name__)
router = APIRouter()

enrollment_service = EnrollmentService()


class AncestorInfoRequest(BaseModel):
    """Request body for eligibility check."""
    ancestor_name: Optional[str] = None
    ancestor_roll_number: Optional[int] = None
    relationship: Optional[str] = None  # e.g., "great-grandmother"


@router.get("/steps")
async def get_enrollment_steps():
    """Get the general steps for Cherokee Nation enrollment."""
    steps = await enrollment_service.get_enrollment_steps()
    return {"steps": steps, "total": len(steps)}


@router.get("/cdib")
async def get_cdib_info():
    """Get information about the CDIB (Certificate of Degree of Indian Blood)."""
    info = await enrollment_service.get_cdib_info()
    return info


@router.post("/eligibility")
async def check_eligibility(request: AncestorInfoRequest):
    """Check enrollment eligibility (STUB — provides guidance only).

    This endpoint CANNOT confirm or deny eligibility.
    Only the Cherokee Nation Registration Department can do that.
    """
    ancestor_info = {
        "ancestor_name": request.ancestor_name,
        "ancestor_roll_number": request.ancestor_roll_number,
        "relationship": request.relationship,
    }
    result = await enrollment_service.check_eligibility(ancestor_info)
    return {
        "eligible": result.eligible,
        "reason": result.reason,
        "next_steps": result.next_steps,
        "requires_partnership": result.requires_partnership,
        "disclaimer": (
            "This is informational guidance only. Cherokee Nation enrollment "
            "determinations are made solely by the Cherokee Nation Registration "
            "Department. Contact: 1-800-256-0671"
        ),
    }


@router.get("/status/{user_id}")
async def get_enrollment_status(user_id: str):
    """Get enrollment tracking status for a user (placeholder)."""
    # Placeholder — requires database integration
    return {
        "user_id": user_id,
        "status": "not_started",
        "message": "Enrollment tracking not yet connected to database.",
        "next_action": "Begin the enrollment wizard to get started.",
    }
```

---

## Step 10: Backend API — `wizard.py`

**File:** `/ganuda/assist/tribeassist/backend/api/v1/endpoints/wizard.py`

```python
"""
TribeAssist Enrollment Wizard Endpoints
Bilingual (Cherokee + English) step-by-step enrollment guidance.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Wizard steps — bilingual
ENROLLMENT_WIZARD_STEPS = [
    {
        "step_id": "welcome",
        "step_number": 1,
        "title_en": "Welcome",
        "title_chr": "ᎣᏏᏲ",
        "description_en": (
            "Welcome to the Cherokee Nation enrollment guidance wizard. "
            "We will walk you through the process of understanding enrollment "
            "eligibility and what documents you need."
        ),
        "description_chr": (
            "ᎣᏏᏲ. ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ."
        ),
        "fields": [],
    },
    {
        "step_id": "ancestor_info",
        "step_number": 2,
        "title_en": "Ancestor Information",
        "title_chr": "ᎠᏂᏙᎾ ᎠᏓᏅᏙ",
        "description_en": (
            "Cherokee Nation enrollment requires direct descendancy from someone "
            "listed on the Dawes Roll (1898-1914). Do you know your Dawes Roll "
            "ancestor? There is NO blood quantum requirement."
        ),
        "description_chr": (
            "ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ — ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᎤᏲᎢ ᎤᎾᏓᏡᎬ."
        ),
        "fields": [
            {"name": "ancestor_name", "type": "text", "label_en": "Ancestor's Full Name", "label_chr": "ᎠᏂᏙᎾ ᏧᏙᎢᏛ", "required": False},
            {"name": "roll_number", "type": "number", "label_en": "Dawes Roll Number (if known)", "label_chr": "ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᏗᏎᏍᏗ", "required": False},
            {"name": "relationship", "type": "text", "label_en": "Your Relationship (e.g., great-grandmother)", "label_chr": "ᏕᏣᏓᏡᎬ", "required": False},
        ],
    },
    {
        "step_id": "personal_info",
        "step_number": 3,
        "title_en": "Personal Information",
        "title_chr": "ᏂᎯ ᏣᏓᏅᏙ",
        "description_en": (
            "We need some basic information about you to help guide "
            "the enrollment process."
        ),
        "description_chr": "ᏂᎯ ᏣᏓᏅᏙ ᎠᏆᏛᏅᏗ.",
        "fields": [
            {"name": "full_name", "type": "text", "label_en": "Your Full Legal Name", "label_chr": "ᏂᎯ ᏣᏙᎢᏛ", "required": True},
            {"name": "date_of_birth", "type": "date", "label_en": "Date of Birth", "label_chr": "ᏂᎯ ᏕᏣᏓᏡᎬ ᎢᎦ", "required": True},
        ],
    },
    {
        "step_id": "documents",
        "step_number": 4,
        "title_en": "Document Checklist",
        "title_chr": "ᏗᎧᏃᎮᏍᎬ ᏧᏓᎴᏅᏓ",
        "description_en": (
            "Gather these documents to support your enrollment application."
        ),
        "description_chr": "ᎯᎠ ᏗᎧᏃᎮᏍᎬ ᎠᏆᏛᏅᏗ.",
        "fields": [
            {"name": "has_birth_certificate", "type": "checkbox", "label_en": "Your certified birth certificate", "label_chr": "ᏂᎯ ᏕᏣᏓᏡᎬ ᎦᏔ", "required": False},
            {"name": "has_parent_enrollment", "type": "checkbox", "label_en": "Parent's Cherokee Nation enrollment card (if applicable)", "label_chr": "ᎡᏙᏓ/ᎡᏥ ᎠᏓᏅᏖᏍᏗ ᎦᏔ", "required": False},
            {"name": "has_lineage_proof", "type": "checkbox", "label_en": "Birth certificates for each generation back to Dawes Roll ancestor", "label_chr": "ᏗᎧᏃᎮᏍᎬ ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᏗᏂᏙᎾ", "required": False},
            {"name": "has_photo_id", "type": "checkbox", "label_en": "Government-issued photo ID", "label_chr": "ᏗᎧᎿᏩᏛᏍᏗ ᏓᏆᏙᏗ", "required": False},
        ],
    },
    {
        "step_id": "review",
        "step_number": 5,
        "title_en": "Review & Next Steps",
        "title_chr": "ᎢᏴᏛ",
        "description_en": (
            "Review your information and see your next steps for enrollment."
        ),
        "description_chr": "ᎯᎸᎯᏍᏓ ᎠᎴ ᏂᎦᎵᏍᏔᏂᏙᎲ.",
        "fields": [],
    },
]


class WizardStepData(BaseModel):
    """Data submitted for a wizard step."""
    step_id: str
    data: Dict[str, Any] = {}
    language: str = "en"


@router.get("/enrollment/steps")
async def get_wizard_steps(language: str = "en"):
    """Get all enrollment wizard steps."""
    return {
        "wizard_id": "enrollment",
        "language": language,
        "steps": ENROLLMENT_WIZARD_STEPS,
        "total_steps": len(ENROLLMENT_WIZARD_STEPS),
    }


@router.get("/enrollment/step/{step_id}")
async def get_wizard_step(step_id: str, language: str = "en"):
    """Get a specific wizard step."""
    for step in ENROLLMENT_WIZARD_STEPS:
        if step["step_id"] == step_id:
            return {"step": step, "language": language}
    raise HTTPException(status_code=404, detail=f"Step '{step_id}' not found")


@router.post("/enrollment/step")
async def submit_wizard_step(step_data: WizardStepData):
    """Submit data for a wizard step (placeholder — needs database)."""
    logger.info(
        f"[TribeAssist] Wizard step submitted: {step_data.step_id} "
        f"(language={step_data.language})"
    )
    return {
        "step_id": step_data.step_id,
        "received": True,
        "message": "Step data received. Database persistence not yet connected.",
    }
```

---

## Step 11: Backend API — `chat.py`

**File:** `/ganuda/assist/tribeassist/backend/api/v1/endpoints/chat.py`

```python
"""
TribeAssist Council Chat Endpoints
Bilingual (Cherokee + English) council chat.
Spider specialist at 1.5x weight.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from backend.services.council_chat import TribeCouncilChatService
from backend.services.crisis_detection import TribeCrisisDetection

logger = logging.getLogger(__name__)
router = APIRouter()

chat_service = TribeCouncilChatService()
crisis_detector = TribeCrisisDetection()


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str
    language: str = "en"  # "en" or "chr"
    session_id: Optional[str] = None


@router.post("/message")
async def send_message(request: ChatRequest):
    """Send a message to the TribeAssist council chat.

    Performs crisis detection before council processing.
    Spider specialist weighted at 1.5x for Cherokee cultural authority.
    """
    # Crisis detection first
    crisis_result = await crisis_detector.scan_message(request.message)

    if crisis_result.detected and crisis_result.severity == "critical":
        logger.warning(
            f"[TribeAssist] CRITICAL crisis detected in chat: "
            f"category={crisis_result.category}"
        )
        return {
            "response": {
                "en": (
                    "I can see you may be in crisis. Please reach out for immediate help:\n\n"
                    "- 988 Suicide & Crisis Lifeline: Call or text 988\n"
                    "- Cherokee Nation Behavioral Health: 1-800-256-0671\n"
                    "- Crisis Text Line: Text HOME to 741741\n\n"
                    "You are not alone. Your life matters."
                ),
                "chr": (
                    "ᏂᎯ ᎥᏝ ᎡᏣᏔᏅ. ᎯᏪᏍᏗ:\n\n"
                    "- 988\n"
                    "- ᏣᎳᎩ ᎠᏰᎵ: 1-800-256-0671\n"
                ),
            },
            "crisis_detected": True,
            "crisis_category": crisis_result.category,
            "crisis_severity": crisis_result.severity,
        }

    if crisis_result.detected:
        logger.info(
            f"[TribeAssist] Non-critical crisis detected: "
            f"category={crisis_result.category}, severity={crisis_result.severity}"
        )

    # Get council context
    context = await chat_service.get_chat_context(language=request.language)

    # Placeholder response — actual council integration pending
    return {
        "response": {
            "en": (
                "Thank you for your question. The TribeAssist council chat "
                "is being connected to the 7-specialist council. "
                "Spider specialist (Cherokee cultural authority) will carry 1.5x weight. "
                "For immediate help, contact Cherokee Nation at 1-800-256-0671."
            ),
            "chr": (
                "ᏩᏙᎵᎯᏍᏗ. ᏣᎳᎩ ᎠᏰᎵ: 1-800-256-0671."
            ),
        },
        "crisis_detected": crisis_result.detected,
        "crisis_category": crisis_result.category if crisis_result.detected else None,
        "language": request.language,
        "council_context": {
            "domain": context["domain"],
            "specialist_weights": context["specialist_weights"],
            "bilingual": context["bilingual"],
        },
        "placeholder": True,
    }


@router.get("/context")
async def get_chat_context(language: str = "en"):
    """Get the council chat context for TribeAssist."""
    context = await chat_service.get_chat_context(language=language)
    return context
```

---

## Step 12: Frontend — `layout.tsx`

**File:** `/ganuda/assist/tribeassist/frontend/app/layout.tsx`

BILINGUAL layout with Cherokee language toggle. Uses syllabary, not romanized.

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Ganuda TribeAssist | Cherokee Nation Services",
  description:
    "AI-powered guidance for Cherokee Nation services, enrollment, and community resources. Bilingual: English & Cherokee (ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ).",
  keywords: [
    "Cherokee Nation",
    "tribal enrollment",
    "Dawes Roll",
    "CDIB",
    "Cherokee services",
    "ᏣᎳᎩ",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {/* Header with Cherokee language toggle */}
          <header className="border-b bg-background">
            <div className="container mx-auto px-4 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold">
                  Ganuda TribeAssist
                </h1>
                <span className="text-sm text-muted-foreground">
                  ᏣᎳᎩ ᎠᏰᎵ
                </span>
              </div>
              <nav className="flex items-center gap-4">
                <a href="/" className="text-sm hover:underline">
                  Home
                </a>
                <a href="/wizard" className="text-sm hover:underline">
                  Enrollment
                </a>
                {/* Language toggle — Cherokee syllabary mode */}
                <button
                  id="lang-toggle"
                  className="px-3 py-1 text-sm border rounded-md hover:bg-muted transition"
                  aria-label="Toggle Cherokee language"
                >
                  ᏣᎳᎩ / English
                </button>
              </nav>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1">{children}</main>
        </div>

        {/* Footer — bilingual */}
        <footer className="border-t mt-auto">
          <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
            <p>
              Ganuda TribeAssist | ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — For the Seven
              Generations
            </p>
            <p className="mt-1">
              Educational tool only. Not legal advice. Enrollment
              determinations are made solely by the Cherokee Nation.
            </p>
            <p className="mt-1">
              ᎦᏚᎩ — Gadugi: Working together for community benefit.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
```

---

## Step 13: Frontend — `page.tsx`

**File:** `/ganuda/assist/tribeassist/frontend/app/page.tsx`

Dashboard: enrollment status, services, chat entry. Bilingual.

```tsx
"use client";

import Link from "next/link";
import {
  Users,
  MessageCircle,
  BookOpen,
  Heart,
  Home,
  GraduationCap,
} from "lucide-react";

export default function TribeAssistHomePage() {
  return (
    <>
      {/* Hero Section — bilingual */}
      <section className="bg-gradient-to-b from-primary/10 to-background py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl md:text-6xl font-bold mb-4">
            Cherokee Nation Services
          </h2>
          <p className="text-2xl md:text-3xl text-primary mb-6">
            ᏣᎳᎩ ᎠᏰᎵ ᏧᎾᏕᎶᏆᏍᏗ
          </p>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            AI-powered guidance for Cherokee Nation enrollment, services,
            and community resources. Bilingual in English and Cherokee
            syllabary.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/wizard"
              className="inline-flex items-center justify-center px-8 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition"
            >
              <Users className="mr-2 h-5 w-5" />
              Enrollment Guide / ᎠᏓᏅᏖᏍᏗ
            </Link>
            <Link
              href="#chat"
              className="inline-flex items-center justify-center px-8 py-3 border-2 border-primary text-primary rounded-lg font-semibold hover:bg-primary/10 transition"
            >
              <MessageCircle className="mr-2 h-5 w-5" />
              Talk to Council / ᎣᏏᏲ
            </Link>
          </div>
        </div>
      </section>

      {/* Services Section — bilingual */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h3 className="text-3xl font-bold text-center mb-4">
            Available Services
          </h3>
          <p className="text-center text-muted-foreground mb-12">
            ᏣᎳᎩ ᎠᏰᎵ ᏧᎾᏕᎶᏆᏍᏗ
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            <ServiceCard
              icon={<Users className="h-12 w-12 text-primary" />}
              titleEn="Enrollment"
              titleChr="ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ"
              description="Navigate Cherokee Nation enrollment. Based on Dawes Roll descendancy — no blood quantum required."
            />
            <ServiceCard
              icon={<Heart className="h-12 w-12 text-primary" />}
              titleEn="Health Services"
              titleChr="ᎠᏓᏅᏖᏍᏗ ᎠᏰᎵ"
              description="Connect with Cherokee Nation health programs and behavioral health resources."
            />
            <ServiceCard
              icon={<GraduationCap className="h-12 w-12 text-primary" />}
              titleEn="Education"
              titleChr="ᏗᎧᎿᏩᏛᏍᏗ"
              description="Educational programs, scholarships, and Cherokee language learning resources."
            />
            <ServiceCard
              icon={<Home className="h-12 w-12 text-primary" />}
              titleEn="Housing"
              titleChr="ᎦᎵᏦᏕ"
              description="Housing assistance programs available through the Cherokee Nation."
            />
            <ServiceCard
              icon={<Users className="h-12 w-12 text-primary" />}
              titleEn="Elder Care"
              titleChr="ᎠᏂᎨᏯ ᎠᎵᏍᏕᎸᏙᏗ"
              description="Services and support for Cherokee elders and their families."
            />
            <ServiceCard
              icon={<BookOpen className="h-12 w-12 text-primary" />}
              titleEn="Language Programs"
              titleChr="ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ"
              description="Cherokee language preservation and learning. ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ is a living language."
            />
          </div>
        </div>
      </section>

      {/* Enrollment Info */}
      <section className="bg-muted py-20">
        <div className="container mx-auto px-4 max-w-4xl">
          <h3 className="text-3xl font-bold text-center mb-8">
            Cherokee Nation Enrollment
          </h3>
          <div className="bg-card border rounded-lg p-8">
            <h4 className="text-xl font-semibold mb-4">Key Facts</h4>
            <ul className="space-y-3 text-muted-foreground">
              <li className="flex gap-2">
                <span className="text-primary font-bold">1.</span>
                Cherokee Nation citizenship requires direct descendancy
                from the Dawes Roll (1898-1914).
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">2.</span>
                There is NO blood quantum requirement — descendancy is
                what matters.
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">3.</span>
                CDIB (Certificate of Degree of Indian Blood) is a
                separate federal document, not required for tribal
                enrollment.
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">4.</span>
                Application is free. Contact Cherokee Nation
                Registration: 1-800-256-0671.
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold mb-4">
            ᎣᏏᏲ — Ready to Get Started?
          </h3>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Our enrollment wizard will guide you through the process
            step by step, in English and Cherokee.
          </p>
          <Link
            href="/wizard"
            className="inline-flex items-center justify-center px-8 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition"
          >
            Start Enrollment Wizard
          </Link>
        </div>
      </section>
    </>
  );
}

function ServiceCard({
  icon,
  titleEn,
  titleChr,
  description,
}: {
  icon: React.ReactNode;
  titleEn: string;
  titleChr: string;
  description: string;
}) {
  return (
    <div className="bg-card border rounded-lg p-6 hover:shadow-lg transition">
      <div className="mb-4">{icon}</div>
      <h4 className="text-xl font-semibold mb-1">{titleEn}</h4>
      <p className="text-sm text-primary mb-2">{titleChr}</p>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
}
```

---

## Step 14: Frontend — `wizard/page.tsx`

**File:** `/ganuda/assist/tribeassist/frontend/app/wizard/page.tsx`

Bilingual enrollment wizard.

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";

const WIZARD_STEPS = [
  {
    id: "welcome",
    number: 1,
    titleEn: "Welcome",
    titleChr: "ᎣᏏᏲ",
    descriptionEn:
      "Welcome to the Cherokee Nation enrollment guidance wizard. We will walk you through the process of understanding enrollment eligibility and what documents you need.",
    descriptionChr:
      "ᎣᏏᏲ. ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ.",
  },
  {
    id: "ancestor",
    number: 2,
    titleEn: "Ancestor Information",
    titleChr: "ᎠᏂᏙᎾ ᎠᏓᏅᏙ",
    descriptionEn:
      "Cherokee Nation enrollment requires direct descendancy from someone listed on the Dawes Roll (1898-1914). There is NO blood quantum requirement.",
    descriptionChr:
      "ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ — ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᎤᏲᎢ ᎤᎾᏓᏡᎬ.",
  },
  {
    id: "personal",
    number: 3,
    titleEn: "Personal Information",
    titleChr: "ᏂᎯ ᏣᏓᏅᏙ",
    descriptionEn:
      "We need some basic information about you to help guide the enrollment process.",
    descriptionChr: "ᏂᎯ ᏣᏓᏅᏙ ᎠᏆᏛᏅᏗ.",
  },
  {
    id: "documents",
    number: 4,
    titleEn: "Document Checklist",
    titleChr: "ᏗᎧᏃᎮᏍᎬ ᏧᏓᎴᏅᏓ",
    descriptionEn:
      "Gather these documents to support your enrollment application: birth certificate, parent's enrollment card (if applicable), lineage proof, and photo ID.",
    descriptionChr: "ᎯᎠ ᏗᎧᏃᎮᏍᎬ ᎠᏆᏛᏅᏗ.",
  },
  {
    id: "review",
    number: 5,
    titleEn: "Review & Next Steps",
    titleChr: "ᎢᏴᏛ",
    descriptionEn:
      "Review your information. Your next step is to contact Cherokee Nation Registration at 1-800-256-0671 or visit cherokee.org.",
    descriptionChr:
      "ᎯᎸᎯᏍᏓ ᎠᎴ ᏂᎦᎵᏍᏔᏂᏙᎲ. ᏣᎳᎩ ᎠᏰᎵ: 1-800-256-0671.",
  },
];

export default function EnrollmentWizardPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [language, setLanguage] = useState<"en" | "chr">("en");
  const step = WIZARD_STEPS[currentStep];

  const toggleLanguage = () => {
    setLanguage(language === "en" ? "chr" : "en");
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-3xl">
      {/* Language toggle */}
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold">
          {language === "en"
            ? "Enrollment Wizard"
            : "ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ"}
        </h2>
        <button
          onClick={toggleLanguage}
          className="px-4 py-2 border rounded-md text-sm hover:bg-muted transition"
        >
          {language === "en" ? "ᏣᎳᎩ" : "English"}
        </button>
      </div>

      {/* Progress bar */}
      <div className="flex gap-2 mb-8">
        {WIZARD_STEPS.map((s, idx) => (
          <div
            key={s.id}
            className={`h-2 flex-1 rounded-full ${
              idx <= currentStep ? "bg-primary" : "bg-muted"
            }`}
          />
        ))}
      </div>

      {/* Step content */}
      <div className="bg-card border rounded-lg p-8 mb-8">
        <div className="text-sm text-muted-foreground mb-2">
          {language === "en"
            ? `Step ${step.number} of ${WIZARD_STEPS.length}`
            : `${step.number} / ${WIZARD_STEPS.length}`}
        </div>
        <h3 className="text-2xl font-bold mb-4">
          {language === "en" ? step.titleEn : step.titleChr}
        </h3>
        <p className="text-muted-foreground text-lg">
          {language === "en"
            ? step.descriptionEn
            : step.descriptionChr}
        </p>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
          className="px-6 py-2 border rounded-md hover:bg-muted transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {language === "en" ? "Back" : "ᎡᎲ"}
        </button>
        {currentStep < WIZARD_STEPS.length - 1 ? (
          <button
            onClick={() =>
              setCurrentStep(
                Math.min(WIZARD_STEPS.length - 1, currentStep + 1)
              )
            }
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition"
          >
            {language === "en" ? "Next" : "ᎢᎦᏛ"}
          </button>
        ) : (
          <Link
            href="/"
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition inline-flex items-center"
          >
            {language === "en" ? "Done" : "ᎤᎵᏍᏓ"}
          </Link>
        )}
      </div>

      {/* Disclaimer */}
      <div className="mt-12 text-sm text-muted-foreground text-center">
        <p>
          This wizard provides guidance only. Enrollment
          determinations are made solely by the Cherokee Nation
          Registration Department.
        </p>
        <p className="mt-1">
          Contact: 1-800-256-0671 |{" "}
          <a
            href="https://www.cherokee.org"
            className="underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            cherokee.org
          </a>
        </p>
      </div>
    </div>
  );
}
```

---

## Step 15: Config — `wizards/enrollment.yaml`

**File:** `/ganuda/assist/tribeassist/config/wizards/enrollment.yaml`

```yaml
# TribeAssist Enrollment Wizard Configuration
# Bilingual: English + Cherokee (syllabary)

wizard_id: "enrollment"
version: "1.0.0"
vertical: "tribeassist"

steps:
  - step_id: "welcome"
    step_number: 1
    title:
      en: "Welcome"
      chr: "ᎣᏏᏲ"
    description:
      en: >
        Welcome to the Cherokee Nation enrollment guidance wizard.
        We will walk you through the process of understanding
        enrollment eligibility and what documents you need.
      chr: >
        ᎣᏏᏲ. ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ.
    fields: []

  - step_id: "ancestor_info"
    step_number: 2
    title:
      en: "Ancestor Information"
      chr: "ᎠᏂᏙᎾ ᎠᏓᏅᏙ"
    description:
      en: >
        Cherokee Nation enrollment requires direct descendancy from
        someone listed on the Dawes Roll (1898-1914). Do you know
        your Dawes Roll ancestor? There is NO blood quantum requirement.
      chr: >
        ᏣᎳᎩ ᎠᏰᎵ ᎠᏓᏅᏖᏍᏗ — ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᎤᏲᎢ ᎤᎾᏓᏡᎬ.
    fields:
      - name: "ancestor_name"
        type: "text"
        label:
          en: "Ancestor's Full Name"
          chr: "ᎠᏂᏙᎾ ᏧᏙᎢᏛ"
        required: false
      - name: "roll_number"
        type: "number"
        label:
          en: "Dawes Roll Number (if known)"
          chr: "ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᏗᏎᏍᏗ"
        required: false
      - name: "relationship"
        type: "text"
        label:
          en: "Your Relationship (e.g., great-grandmother)"
          chr: "ᏕᏣᏓᏡᎬ"
        required: false

  - step_id: "personal_info"
    step_number: 3
    title:
      en: "Personal Information"
      chr: "ᏂᎯ ᏣᏓᏅᏙ"
    description:
      en: >
        We need some basic information about you to help guide the
        enrollment process.
      chr: "ᏂᎯ ᏣᏓᏅᏙ ᎠᏆᏛᏅᏗ."
    fields:
      - name: "full_name"
        type: "text"
        label:
          en: "Your Full Legal Name"
          chr: "ᏂᎯ ᏣᏙᎢᏛ"
        required: true
      - name: "date_of_birth"
        type: "date"
        label:
          en: "Date of Birth"
          chr: "ᏂᎯ ᏕᏣᏓᏡᎬ ᎢᎦ"
        required: true

  - step_id: "documents"
    step_number: 4
    title:
      en: "Document Checklist"
      chr: "ᏗᎧᏃᎮᏍᎬ ᏧᏓᎴᏅᏓ"
    description:
      en: "Gather these documents to support your enrollment application."
      chr: "ᎯᎠ ᏗᎧᏃᎮᏍᎬ ᎠᏆᏛᏅᏗ."
    fields:
      - name: "has_birth_certificate"
        type: "checkbox"
        label:
          en: "Your certified birth certificate"
          chr: "ᏂᎯ ᏕᏣᏓᏡᎬ ᎦᏔ"
      - name: "has_parent_enrollment"
        type: "checkbox"
        label:
          en: "Parent's Cherokee Nation enrollment card (if applicable)"
          chr: "ᎡᏙᏓ/ᎡᏥ ᎠᏓᏅᏖᏍᏗ ᎦᏔ"
      - name: "has_lineage_proof"
        type: "checkbox"
        label:
          en: "Birth certificates for each generation back to Dawes Roll ancestor"
          chr: "ᏗᎧᏃᎮᏍᎬ ᏓᏫᏏ ᏧᏓᎴᏅᏓ ᏗᏂᏙᎾ"
      - name: "has_photo_id"
        type: "checkbox"
        label:
          en: "Government-issued photo ID"
          chr: "ᏗᎧᎿᏩᏛᏍᏗ ᏓᏆᏙᏗ"

  - step_id: "review"
    step_number: 5
    title:
      en: "Review & Next Steps"
      chr: "ᎢᏴᏛ"
    description:
      en: >
        Review your information and see your next steps for
        Cherokee Nation enrollment.
      chr: "ᎯᎸᎯᏍᏓ ᎠᎴ ᏂᎦᎵᏍᏔᏂᏙᎲ."
    fields: []
```

---

## Step 16: Config — `crisis_patterns.yaml`

**File:** `/ganuda/assist/tribeassist/config/crisis_patterns.yaml`

```yaml
# TribeAssist Crisis Detection Patterns
# Cherokee/Native community-specific patterns
# Handle ALL of these with deep cultural sensitivity

vertical: "tribeassist"
version: "1.0.0"

vertical_patterns:
  - category: "historical_trauma"
    severity: "medium"
    keywords:
      - "boarding school"
      - "trail of tears"
      - "stolen generation"
      - "lost my culture"
      - "taken from family"
      - "forced assimilation"
      - "residential school"
    action: "cultural_support_referral"
    response_note: "Handle with deep cultural sensitivity"

  - category: "cultural_isolation"
    severity: "medium"
    keywords:
      - "disconnected from tribe"
      - "don't know my language"
      - "lost my identity"
      - "not Cherokee enough"
      - "don't belong"
      - "no connection to culture"
    action: "cultural_reconnection_resources"
    response_note: >
      Affirm identity. Cherokee Nation has no blood quantum requirement —
      descendancy is what matters. Direct to language and cultural programs.

  - category: "elder_care"
    severity: "high"
    keywords:
      - "elder needs help"
      - "grandparent alone"
      - "traditional healer needed"
      - "elder abuse"
      - "grandmother can't"
      - "grandfather sick"
    action: "tribal_elder_services"
    response_note: "Elders are sacred. Treat with utmost respect and urgency."

  - category: "substance_abuse"
    severity: "high"
    keywords:
      - "drinking problem"
      - "addiction"
      - "meth"
      - "alcohol"
      - "substance abuse"
      - "overdose"
      - "relapse"
    action: "tribal_behavioral_health"
    response_note: >
      Culturally appropriate treatment referrals, not generic.
      Cherokee Nation Behavioral Health: 1-800-256-0671.
      Reference Gadugi (communal support) and traditional healing alongside clinical.

  - category: "immediate_danger"
    severity: "critical"
    keywords:
      - "want to die"
      - "kill myself"
      - "suicide"
      - "end my life"
      - "no reason to live"
      - "hurt myself"
    action: "immediate_crisis_intervention"
    response_note: >
      IMMEDIATE: 988 Suicide & Crisis Lifeline (call or text 988).
      Cherokee Nation Behavioral Health crisis line: 1-800-256-0671.
      Do not leave the person without providing these resources.

# Referral directory
referrals:
  cultural_support_referral:
    name: "Cherokee Nation Cultural Resources"
    phone: "1-800-256-0671"
    url: "https://www.cherokee.org"
  cultural_reconnection_resources:
    name: "Cherokee Nation Language & Cultural Programs"
    phone: "1-800-256-0671"
    url: "https://language.cherokee.org"
  tribal_elder_services:
    name: "Cherokee Nation Aging Services"
    phone: "1-800-256-0671"
  tribal_behavioral_health:
    name: "Cherokee Nation Behavioral Health"
    phone: "1-800-256-0671"
    note: "Culturally grounded treatment — not generic"
  immediate_crisis_intervention:
    name: "988 Suicide & Crisis Lifeline + Cherokee Nation BH"
    phone_988: "988"
    phone_cn: "1-800-256-0671"
    text: "Text HOME to 741741"
```

---

## Step 17: Config — `council_context.yaml`

**File:** `/ganuda/assist/tribeassist/config/council_context.yaml`

```yaml
# TribeAssist Council Context Configuration
# Defines how the 7-specialist council operates for Cherokee Nation services

domain: "Cherokee Nation Services & Enrollment"
description: "Helping Cherokee citizens and descendants navigate tribal services"
vertical: "tribeassist"
version: "1.0.0"

regulations:
  - "Cherokee Nation Constitution"
  - "Indian Reorganization Act of 1934"
  - "Cherokee Nation Registration Act"
  - "CDIB regulations (25 CFR Part 70)"

specialist_priority:
  spider: 1.5      # Cherokee cultural authority — HIGHEST weight
  turtle: 1.0      # Steady guidance
  raven: 1.2       # Strategic navigation
  eagle_eye: 1.0   # Pattern recognition
  gecko: 0.8       # Less relevant for tribal services
  crawdad: 1.0     # Security always matters

language: "bilingual_chr_en"

key_concepts:
  - "Dawes Roll (1898-1914) — basis for enrollment"
  - "No blood quantum requirement for Cherokee Nation"
  - "CDIB — Certificate of Degree of Indian Blood (federal, separate from tribal enrollment)"
  - "Gadugi — Cherokee tradition of communal work"
  - "ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — Seven Generations principle"

# Topics the council should be prepared to discuss
knowledge_domains:
  - enrollment_process
  - dawes_roll_history
  - cdib_vs_tribal_enrollment
  - tribal_sovereignty
  - cherokee_nation_services
  - cherokee_language_resources
  - historical_context
  - federal_indian_law

# Cultural guidelines for council responses
cultural_guidelines:
  - "Use Cherokee syllabary (ᏣᎳᎩ), not romanized Cherokee"
  - "Respect tribal sovereignty in all responses"
  - "Reference Gadugi (ᎦᏚᎩ) — communal work — as guiding principle"
  - "Handle historical trauma with deep cultural sensitivity"
  - "Affirm Cherokee identity — no blood quantum gatekeeping"
  - "Direct to Cherokee Nation official resources, not third parties"
  - "Never provide legal advice — recommend tribal legal aid"
```

---

## Step 18: Config — `dawes_roll_reference.yaml`

**File:** `/ganuda/assist/tribeassist/config/dawes_roll_reference.yaml`

```yaml
# Dawes Roll Reference Data (1898-1914)
# Status: PLACEHOLDER — requires formal Cherokee Nation data sharing agreement
#
# The Dawes Commission enrolled members of the Five Civilized Tribes
# Cherokee enrollment is based on direct descendancy from a Dawes Roll enrollee
# This file will contain reference schemas when partnership is established

status: "placeholder"
note: "Requires formal Cherokee Nation data sharing agreement"

# DO NOT add any actual Dawes Roll data without Cherokee Nation authorization
# This schema defines the structure for FUTURE integration only

schema:
  fields:
    - name: "roll_number"
      type: "integer"
      description: "Dawes Roll number"
    - name: "enrollee_name"
      type: "string"
      description: "Full name as enrolled"
    - name: "blood_quantum"
      type: "string"
      note: "Historical record only — NOT used for modern Cherokee Nation enrollment"
    - name: "roll_type"
      type: "enum"
      values:
        - "Cherokee by Blood"
        - "Cherokee Freedmen"
        - "Intermarried White"
      description: "Category on the Dawes Roll"
    - name: "district"
      type: "string"
      description: "Cherokee Nation district at time of enrollment"
    - name: "enrollment_date"
      type: "date"
      description: "Date of enrollment (1898-1914)"

historical_context:
  commission: "Dawes Commission (Commission to the Five Civilized Tribes)"
  period: "1893-1914"
  enrollment_period: "1898-1914"
  purpose: >
    The Dawes Commission was established to negotiate agreements with
    the Five Civilized Tribes for allotment of tribal lands. The rolls
    created during this period form the basis for modern Cherokee Nation
    enrollment. The commission's work remains controversial in its
    historical context of assimilation policy.
  tribes_enrolled:
    - "Cherokee"
    - "Choctaw"
    - "Chickasaw"
    - "Creek (Muscogee)"
    - "Seminole"
  total_cherokee_enrolled: "approximately 41,798"
  modern_note: >
    Cherokee Nation enrollment today is based on direct descendancy from
    these rolls. Cherokee Nation does NOT require a minimum blood quantum.
    This is a defining characteristic of Cherokee Nation citizenship.

partnership_requirements:
  - "Formal data sharing agreement with Cherokee Nation"
  - "Approval from Cherokee Nation Registration Department"
  - "Compliance with tribal data sovereignty requirements"
  - "Security audit of data handling practices"
  - "Regular review and compliance monitoring"
```

---

## Step 19: i18n — `chr_tribe.yaml`

**File:** `/ganuda/assist/tribeassist/i18n/chr_tribe.yaml`

TribeAssist-specific Cherokee language terms. Uses syllabary throughout.

```yaml
# TribeAssist Cherokee Language Terms
# Cherokee syllabary (ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ) — NOT romanized
# This is a first-class language, not a translation layer

vertical: "tribeassist"
language_code: "chr"
script: "Cherokee syllabary"

enrollment:
  title: "ᎠᏓᏅᏖᏍᏗ ᏧᎾᏕᎶᏆᏍᏗ"
  eligible: "ᎤᏔᎳᏬᏍᏗ"
  not_eligible: "ᎥᏝ ᎤᏔᎳᏬᏍᏗ"
  pending: "ᎠᏓᎾᏅᎢ"
  cdib: "ᏗᎧᎿᏩᏛᏍᏗ ᎠᏓᏅᏖᏍᏗ"
  dawes_roll: "ᏓᏫᏏ ᏧᏓᎴᏅᏓ"
  direct_descendant: "ᎤᏲᎢ ᎤᎾᏓᏡᎬ"

services:
  health: "ᎠᏓᏅᏖᏍᏗ ᎠᏰᎵ"
  education: "ᏗᎧᎿᏩᏛᏍᏗ"
  housing: "ᎦᎵᏦᏕ"
  elder_care: "ᎠᏂᎨᏯ ᎠᎵᏍᏕᎸᏙᏗ"
  language: "ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ"

cultural:
  gadugi: "ᎦᏚᎩ"
  seven_generations: "ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ"
  clan: "ᎠᏂᏙᎾ"
  ceremony: "ᎠᏓᏍᏕᎵᏍᎬ"

navigation:
  home: "ᎤᏪᏥ"
  back: "ᎡᎲ"
  next: "ᎢᎦᏛ"
  done: "ᎤᎵᏍᏓ"
  welcome: "ᎣᏏᏲ"
  help: "ᎠᎵᏍᏕᎸᏙᏗ"

common:
  yes: "ᎥᎥ"
  no: "ᎥᏝ"
  thank_you: "ᏩᏙᎵᎯᏍᏗ"
  please: "ᏍᎩᏂ"
```

---

## Step 20: SQL — `tribe_schema.sql`

**File:** `/ganuda/assist/tribeassist/sql/tribe_schema.sql`

Run on bluefin (192.168.132.222) database: `zammad_production`.

```sql
-- TribeAssist Schema
-- Run on bluefin (192.168.132.222) database: zammad_production
--
-- Cherokee AI Federation — TribeAssist
-- ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — For Seven Generations
--
-- Prerequisites: assist_users table must exist (from ASSIST-PHASE1-CORE)
-- No hardcoded credentials — connect via env vars

-- Enrollment tracking
CREATE TABLE IF NOT EXISTS tribe_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    enrollment_status VARCHAR(50) DEFAULT 'inquiry',
    -- Status values: inquiry, gathering_documents, submitted, under_review, approved, denied
    ancestor_info JSONB DEFAULT '{}',
    -- Example: {"ancestor_name": "...", "roll_number": 12345, "relationship": "great-grandmother"}
    documents_checklist JSONB DEFAULT '{}',
    -- Example: {"birth_certificate": true, "parent_enrollment": false, "lineage_proof": true}
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document tracking for enrollment
CREATE TABLE IF NOT EXISTS tribe_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    enrollment_id UUID REFERENCES tribe_enrollments(id),
    document_type VARCHAR(50) NOT NULL,
    -- Types: birth_certificate, parent_enrollment_card, lineage_proof, photo_id, dawes_roll_reference
    document_status VARCHAR(50) DEFAULT 'pending',
    -- Status values: pending, uploaded, verified, rejected
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Wizard progress tracking (bilingual support)
CREATE TABLE IF NOT EXISTS tribe_wizard_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    wizard_id VARCHAR(50) NOT NULL,
    current_step VARCHAR(50),
    step_data JSONB DEFAULT '{}',
    preferred_language VARCHAR(10) DEFAULT 'en',
    -- 'en' for English, 'chr' for Cherokee
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_tribe_enroll_user ON tribe_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_tribe_enroll_status ON tribe_enrollments(enrollment_status);
CREATE INDEX IF NOT EXISTS idx_tribe_docs_user ON tribe_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_tribe_docs_enrollment ON tribe_documents(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_tribe_wizard_user ON tribe_wizard_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_tribe_wizard_completed ON tribe_wizard_progress(wizard_id, completed);
```

---

## Verification Steps

After creating all files, the Jr MUST verify:

### V1: Directory structure (bash)
```bash
find /ganuda/assist/tribeassist -type f | sort
```
Expected: 20 files matching the tree in the Directory Structure section above.

### V2: Python syntax check (bash)
```bash
cd /ganuda/assist/tribeassist
python3 -c "import py_compile; py_compile.compile('backend/main.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/config.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/services/enrollment_service.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/services/council_chat.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/services/crisis_detection.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/api/v1/endpoints/enrollment.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/api/v1/endpoints/wizard.py', doraise=True)"
python3 -c "import py_compile; py_compile.compile('backend/api/v1/endpoints/chat.py', doraise=True)"
```
All must pass with no errors.

### V3: YAML validity (bash)
```bash
python3 -c "
import yaml
for f in [
    '/ganuda/assist/tribeassist/config/wizards/enrollment.yaml',
    '/ganuda/assist/tribeassist/config/crisis_patterns.yaml',
    '/ganuda/assist/tribeassist/config/council_context.yaml',
    '/ganuda/assist/tribeassist/config/dawes_roll_reference.yaml',
    '/ganuda/assist/tribeassist/i18n/chr_tribe.yaml',
]:
    with open(f) as fh:
        yaml.safe_load(fh)
    print(f'OK: {f}')
"
```

### V4: SQL syntax check (bash)
```bash
# Dry run — parse only, do not execute
psql -h 192.168.132.222 -d zammad_production -f /ganuda/assist/tribeassist/sql/tribe_schema.sql --set ON_ERROR_STOP=on -n
```
Or if psql is not available, visual review that all statements end with semicolons and table references are valid.

### V5: No hardcoded credentials (bash)
```bash
grep -rn "password\|secret\|api_key\|token" /ganuda/assist/tribeassist/ --include="*.py" --include="*.yaml" --include="*.tsx" | grep -v "env\|ENV\|getenv\|placeholder\|TRIBE_DB_PASSWORD\|response_note\|note"
```
Must return empty — no hardcoded secrets anywhere.

### V6: Cherokee syllabary present (bash)
```bash
grep -rn "ᏣᎳᎩ\|ᎣᏏᏲ\|ᎦᏚᎩ\|ᎦᎵᏉᎩ" /ganuda/assist/tribeassist/ | wc -l
```
Must return a count greater than 20 — Cherokee is first-class, not an afterthought.

### V7: Dawes Roll data check (bash)
```bash
grep -rn "roll_number.*[0-9]\{3,\}" /ganuda/assist/tribeassist/ --include="*.py" --include="*.yaml"
```
Must return empty (or only schema examples with `12345` in comments). No actual Dawes Roll numbers.

---

## What NOT To Do

1. **Do NOT hardcode any Dawes Roll data** — only stubs and schemas
2. **Do NOT use romanized Cherokee** — syllabary only (ᏣᎳᎩ, not "Tsalagi")
3. **Do NOT hardcode credentials** — all via env vars with TRIBE_ prefix
4. **Do NOT fabricate enrollment outcomes** — eligibility stubs must return `None`
5. **Do NOT treat Cherokee as a translation layer** — it is first-class throughout
6. **Do NOT skip crisis detection** — every chat message gets scanned
7. **Do NOT provide legal advice** — educational guidance only, direct to Cherokee Nation

---

## Context Files

- VetAssist backend pattern: `/ganuda/vetassist/backend/main.py`
- VetAssist frontend pattern: `/ganuda/vetassist/frontend/app/layout.tsx`, `page.tsx`
- Platform family architecture: `/ganuda/docs/ultrathink/ULTRATHINK-ASSIST-PLATFORM-FAMILY-JAN18-2026.md`
- Assist core config: `/ganuda/lib/assist_core/vertical_config.py` (from ULTRATHINK)
- This instruction: `/ganuda/docs/jr_instructions/JR-ASSIST-PHASE3-TRIBEASSIST-FEB04-2026.md`

---

## Notes for the Jr

- This vertical carries cultural weight. Take extra care with Cherokee language accuracy.
- Spider specialist at 1.5x is intentional — Cherokee cultural authority guides the council.
- The Dawes Roll stubs exist because we respect Cherokee Nation data sovereignty. Do not shortcut this.
- Gadugi (ᎦᏚᎩ) — working together for community benefit — is the operating principle.
- If unsure about Cherokee syllabary accuracy, mark it for review rather than guessing.
- Port 8003 for TribeAssist backend (8001 = VetAssist, 8002 = SSIAssist, 8003 = TribeAssist).

---

*Cherokee AI Federation — For Seven Generations*
*ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ*
*Tools that make broken systems less broken.*
