# JR INSTRUCTION: Assist Platform Phase 1 — Core Framework Scaffold

**Task ID:** ASSIST-PHASE1-CORE
**Priority:** P1 — Foundation for all verticals
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5) + Council
**Date:** 2026-02-04

---

## Mission Context

VetAssist works. It runs on bluefin, it serves veterans, and it proves that the Cherokee AI Federation can build tools that make broken systems less broken — built by people who believe the world is worth fixing.

Now we generalize. The patterns inside VetAssist — auth, wizards, calculators, council chat, crisis detection, PII protection — are not veteran-specific. They are *people-helping* patterns. A benefits calculator is a benefits calculator whether it computes VA disability ratings or tribal housing assistance. A crisis detector must catch someone in danger whether they are a veteran or an elder.

Phase 1 extracts these patterns into `/ganuda/assist/core/` — a shared foundation that VetAssist (and every future vertical) can inherit from without duplicating code. We do NOT touch VetAssist. We build beside it.

Seven Generations framing: Every hour we spend making this core robust is an hour saved seven times over — once for each vertical that inherits it. The children of the next generation will not rewrite auth. They will build on ours.

---

## Objective

Build the shared Assist Platform core framework at `/ganuda/assist/core/`. This includes:

1. **Backend**: FastAPI application factory, base service classes (calculator, council chat, crisis detection, wizard engine, PII), auth/security/database/config modules
2. **Frontend**: Reusable React/Next.js components (wizard shell, calculator view, chat panel, header), base API client, auth context, core TypeScript types
3. **SQL**: Core schema for `assist_users`, `assist_sessions`, `assist_audit`
4. **Config**: YAML-driven crisis patterns, PII entities, council context, Cherokee i18n translations

---

## Prerequisites

- Read ALL VetAssist source files listed in the Reference Files section below BEFORE writing any code
- **DO NOT modify any file under `/ganuda/vetassist/`** — VetAssist is production
- Python 3.11+, Node.js 18+, PostgreSQL on bluefin (192.168.132.222)
- All credentials via environment variables prefixed with `ASSIST_` — NO hardcoded passwords, NO defaults for secrets
- Confirm access to bluefin database `zammad_production` before running SQL

### Reference Files (Read First, Do Not Modify)

| VetAssist File | Reuse % | What to Extract |
|---|---|---|
| `/ganuda/vetassist/backend/app/core/auth.py` | 100% | JWT decode, `get_current_user` dependency — copy and generalize table name |
| `/ganuda/vetassist/backend/app/core/database.py` | 100% | SQLAlchemy engine factory, `get_db` dependency — copy verbatim |
| `/ganuda/vetassist/backend/app/core/security.py` | 100% | Password hashing, JWT creation, email/password validation — copy verbatim |
| `/ganuda/vetassist/backend/app/core/config.py` | 80% | Pydantic BaseSettings pattern — remove all `VA_*` fields, remove hardcoded CORS origins |
| `/ganuda/vetassist/backend/app/services/council_chat.py` | 70% | Council integration, citation extraction, specialist priority — parameterize `va_context`, citation patterns, priority order |
| `/ganuda/vetassist/backend/app/services/crisis_detection.py` | 40% | Pattern-matching engine and `_build_response` structure — extract hardcoded patterns to YAML, make resources configurable |
| `/ganuda/vetassist/backend/app/services/pii_service.py` | 70% | `CorePIIService` wrapper pattern — parameterize entity lists via YAML |
| `/ganuda/vetassist/backend/app/services/va_calculator.py` | 20% | Only the ABC pattern: `calculate()`, `validate_inputs()`, `get_explanation()`, `get_test_cases()` |
| `/ganuda/vetassist/frontend/lib/auth-context.tsx` | 100% | AuthProvider, useAuth hook, withAuth HOC — copy verbatim |
| `/ganuda/vetassist/frontend/lib/api-client.ts` | 85% | ApiClient class, token management, request/response handling — remove VA-specific endpoints (linkVAAccount, admin, calculator, chat) |
| `/ganuda/vetassist/frontend/lib/types.ts` | 50% | User, Session, ChatMessage, LoginRequest, RegisterRequest — remove VA domain types (Condition, Dependents, EducationalContent) |
| `/ganuda/vetassist/frontend/app/layout.tsx` | 95% | RootLayout structure — parameterize title, description, footer text via props/env |
| `/ganuda/vetassist/backend/main.py` | 90% | FastAPI app creation, CORS setup, health check, router mounting — extract into factory function |

---

## Directory Structure

Create the following tree under `/ganuda/assist/core/`:

```
/ganuda/assist/
  core/
    README.md                          # Brief description only (3 lines max)
    backend/
      __init__.py                      # Package init with version
      base_app.py                      # FastAPI application factory
      base_calculator.py               # Abstract base calculator (ABC)
      base_council_chat.py             # Parameterized council chat service
      base_crisis.py                   # YAML-driven crisis detection
      base_pii.py                      # YAML-driven PII detection
      base_wizard.py                   # YAML-driven wizard engine
      auth.py                          # JWT auth (from VetAssist)
      database.py                      # SQLAlchemy setup (from VetAssist)
      security.py                      # Password/token utils (from VetAssist)
      config.py                        # Base AssistConfig (Pydantic)
    frontend/
      components/
        WizardShell.tsx                # Multi-step wizard renderer
        CalculatorView.tsx             # Calculator result display
        ChatPanel.tsx                  # Council chat interface
        Header.tsx                     # Branded header component
      lib/
        api-client.ts                  # Base API client
        auth-context.tsx               # Auth context provider
        types.ts                       # Core TypeScript types
    sql/
      assist_core_schema.sql           # Core database tables
    config/
      crisis_patterns.yaml             # Base crisis detection patterns
      pii_entities.yaml                # Base PII entity definitions
      council_context.yaml             # Council configuration template
    i18n/
      chr.yaml                         # Cherokee translations (shared)
      en.yaml                          # English translations (shared)
```

---

## File Specifications

### BACKEND FILES

---

### File 1: `/ganuda/assist/core/backend/__init__.py`

```python
"""
Assist Platform Core — Shared Framework
Cherokee AI Federation — For the Seven Generations

This package provides the shared foundation for all Assist verticals.
VetAssist was the first. It will not be the last.
"""

__version__ = "0.1.0"
__vertical__ = "core"
```

---

### File 2: `/ganuda/assist/core/backend/config.py`

Extract from VetAssist `app/core/config.py`. Remove ALL `VA_*` fields, remove hardcoded CORS origins, remove VetAssist-specific paths. Use `ASSIST_` env prefix.

```python
"""
Assist Platform Core Configuration
Loads from environment variables prefixed with ASSIST_
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class AssistConfig(BaseSettings):
    """
    Base configuration for all Assist verticals.
    Subclass this in your vertical and add domain-specific fields.

    Environment variables must be prefixed with ASSIST_
    Example: ASSIST_DB_HOST=192.168.132.222
    """

    # Application identity
    app_title: str = "Assist"
    app_version: str = "0.1.0"
    vertical_name: str = "base"

    # Database — bluefin PostgreSQL
    db_host: str = "192.168.132.222"
    db_port: str = "5432"
    db_name: str = "zammad_production"
    db_user: str = Field(
        ...,
        description="Database username — REQUIRED, no default"
    )
    db_password: str = Field(
        ...,
        description="Database password — REQUIRED, no default"
    )
    db_echo: bool = False

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "production"

    # Security — ALL REQUIRED, NO DEFAULTS
    secret_key: str = Field(
        ...,
        min_length=32,
        description="JWT signing key — REQUIRED, min 32 chars"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # PII Protection
    pii_token_salt: str = Field(
        default="",
        description="Salt for PII tokenization — set in environment"
    )

    # CORS — verticals override this
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_credentials: bool = True

    # LLM API (Redfin vLLM)
    vllm_api_url: str = "http://redfin:8000/v1"
    vllm_model: str = "ganuda-council-8b"
    vllm_timeout: int = 60

    # Council
    council_enabled: bool = True
    council_min_confidence: float = 0.70
    council_consensus_threshold: int = 5

    # File Storage — verticals override upload_dir
    upload_dir: str = "/ganuda/assist/uploads"
    max_upload_size_mb: int = 25
    allowed_extensions: List[str] = ["pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"]

    # Logging
    log_level: str = "INFO"
    log_file: str = "/ganuda/assist/logs/core.log"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # i18n
    default_language: str = "en"
    supported_languages: List[str] = ["en", "chr"]

    class Config:
        env_prefix = "ASSIST_"
        env_file = ".env"
        case_sensitive = False
```

**Key differences from VetAssist config.py:**
- `db_user`, `db_password`, `secret_key` are REQUIRED with NO defaults (the `...` sentinel)
- No `VA_LIGHTHOUSE_*`, `VA_OAUTH_*`, `VA_CCG_*`, `VETASSIST_*` fields
- No hardcoded CORS domains like `vetassist.ganuda.us`
- Added `vertical_name`, `default_language`, `supported_languages`
- Added `database_url` as a computed property instead of a separate field

---

### File 3: `/ganuda/assist/core/backend/database.py`

Copy from VetAssist `app/core/database.py` with one change: import config from the core package, not `app.core.config`. Use the computed `database_url` property.

```python
"""
Database connection and session management
SQLAlchemy setup for PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# These will be initialized by init_database()
engine = None
SessionLocal = None
Base = declarative_base()


def init_database(database_url: str, echo: bool = False):
    """
    Initialize database engine and session factory.
    Call this from your vertical's startup, passing config.database_url.

    Args:
        database_url: SQLAlchemy connection string
        echo: If True, log all SQL statements
    """
    global engine, SessionLocal

    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency to get database session.
    Usage: db: Session = Depends(get_db)
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Key difference from VetAssist:** Database is initialized explicitly via `init_database()` rather than at import time. This lets each vertical pass its own config without import-order coupling.

---

### File 4: `/ganuda/assist/core/backend/security.py`

Copy from VetAssist `app/core/security.py` verbatim, but change the import to use the core config. Remove the duplicate function definitions that exist in the VetAssist file (VetAssist has `decode_access_token` and `get_current_user` defined twice — take only one copy of each).

```python
"""
Security utilities — password hashing, JWT, validation
Extracted from VetAssist app/core/security.py (deduplicated)
"""

from fastapi import Header, HTTPException, status
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import hashlib
import re

# Module-level settings — set by init_security()
_secret_key: str = ""
_algorithm: str = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_security(secret_key: str, algorithm: str = "HS256"):
    """
    Initialize security module with secret key.
    Call during app startup.
    """
    global _secret_key, _algorithm
    if len(secret_key) < 32:
        raise ValueError("secret_key must be at least 32 characters")
    _secret_key = secret_key
    _algorithm = algorithm


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    if not _secret_key:
        raise RuntimeError("Security not initialized. Call init_security() first.")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _secret_key, algorithm=_algorithm)


def hash_token(token: str) -> str:
    """Create SHA-256 hash of a token (for storage/comparison)."""
    return hashlib.sha256(token.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple:
    """
    Validate password meets minimum requirements.
    Returns (is_valid: bool, message: str)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    return True, "Password meets requirements"


async def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token. Returns payload if valid, None otherwise."""
    if not _secret_key:
        raise RuntimeError("Security not initialized. Call init_security() first.")
    try:
        payload = jwt.decode(token, _secret_key, algorithms=[_algorithm])
        return payload
    except Exception:
        return None


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    FastAPI dependency: get current user if token present.
    Returns None for anonymous access.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        return None
    return {"user_id": payload.get("sub"), "email": payload.get("email")}


async def get_current_user(
    authorization: str = Header(..., description="JWT token")
) -> dict:
    """
    FastAPI dependency: get current user from JWT.
    Raises 401 if token is invalid or missing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    payload = await decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": payload.get("sub"), "email": payload.get("email")}
```

---

### File 5: `/ganuda/assist/core/backend/auth.py`

Thin wrapper that combines security functions with database user lookup. Generalized from VetAssist `app/core/auth.py` to use `assist_users` table instead of `users`.

```python
"""
Authentication module — JWT-based user authentication
Combines security.py JWT decoding with database user lookup
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import get_db
from .security import decode_access_token

security_scheme = HTTPBearer()


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    FastAPI dependency: decode JWT and look up user in assist_users table.
    Returns full user dict from database.
    Raises 401 if token invalid or user not found/inactive.
    """
    token = credentials.credentials
    payload = await decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    result = db.execute(
        text("SELECT * FROM assist_users WHERE id = :uid AND is_active = true"),
        {"uid": user_id}
    )
    user = result.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return dict(user._mapping)
```

---

### File 6: `/ganuda/assist/core/backend/base_app.py`

Application factory extracted from VetAssist `main.py`. Instead of hardcoding the title, CORS origins, and routers, accept them via `AssistConfig` and a list of routers.

```python
"""
Assist Platform — FastAPI Application Factory
Creates a configured FastAPI app for any vertical.
"""

import logging
from typing import List, Tuple
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .config import AssistConfig
from .database import init_database
from .security import init_security

logger = logging.getLogger(__name__)


def create_assist_app(
    config: AssistConfig,
    routers: List[Tuple[APIRouter, str, List[str]]] = None
) -> FastAPI:
    """
    Create a configured FastAPI application for an Assist vertical.

    Args:
        config: AssistConfig instance (or subclass)
        routers: List of (router, prefix, tags) tuples to mount
                 Example: [(wizard_router, "/api/v1/wizard", ["wizard"])]

    Returns:
        Configured FastAPI application

    Usage in a vertical:
        from assist.core.backend.base_app import create_assist_app
        from my_vertical.config import MyConfig
        from my_vertical.routers import wizard_router

        config = MyConfig()
        app = create_assist_app(config, [
            (wizard_router, "/api/v1/wizard", ["wizard"]),
        ])
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    # Initialize database
    init_database(config.database_url, echo=config.db_echo)
    logger.info(f"[{config.vertical_name}] Database initialized: {config.db_host}/{config.db_name}")

    # Initialize security
    init_security(config.secret_key, config.algorithm)
    logger.info(f"[{config.vertical_name}] Security initialized")

    # Create FastAPI app
    app = FastAPI(
        title=config.app_title,
        description=f"Cherokee AI Federation — {config.vertical_name} vertical",
        version=config.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check — every vertical gets this for free
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": config.app_title,
            "version": config.app_version,
            "vertical": config.vertical_name
        }

    # Mount vertical-specific routers
    if routers:
        for router, prefix, tags in routers:
            try:
                app.include_router(router, prefix=prefix, tags=tags)
                logger.info(f"[{config.vertical_name}] Router mounted: {prefix}")
            except Exception as e:
                logger.error(f"[{config.vertical_name}] Failed to mount router {prefix}: {e}")

    logger.info(
        f"[{config.vertical_name}] Application ready — "
        f"{config.app_title} v{config.app_version} on {config.host}:{config.port}"
    )

    return app
```

---

### File 7: `/ganuda/assist/core/backend/base_calculator.py`

Abstract base class. Only the ABC pattern from VetAssist `va_calculator.py` — none of the VA-specific logic.

```python
"""
Assist Platform — Abstract Base Calculator
Every vertical that computes something inherits from this.

VetAssist's VACalculatorService computes combined disability ratings.
A housing vertical might compute rental assistance eligibility.
The pattern is the same: inputs -> validation -> calculation -> explanation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CalculationResult:
    """Standard result from any Assist calculator."""
    value: float
    breakdown: Dict[str, Any]
    explanation: str
    warnings: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCalculator(ABC):
    """
    Abstract base for all Assist calculators.

    Subclass contract:
    1. Implement calculate() — the core computation
    2. Implement validate_inputs() — return list of error strings (empty = valid)
    3. Implement get_explanation() — human-readable explanation of result
    4. Optionally override get_test_cases() — built-in self-test data

    Example (from VetAssist pattern):
        class VADisabilityCalculator(BaseCalculator):
            def validate_inputs(self, inputs):
                errors = []
                if not inputs.get("conditions"):
                    errors.append("At least one condition is required")
                for c in inputs.get("conditions", []):
                    if c["rating"] < 0 or c["rating"] > 100:
                        errors.append(f"Invalid rating: {c['rating']}")
                return errors

            def calculate(self, inputs):
                # ... combined rating formula from 38 CFR 4.25 ...
                return CalculationResult(
                    value=rounded_rating,
                    breakdown={"steps": steps, "bilateral_factor": bf},
                    explanation=self.get_explanation(result)
                )
    """

    @abstractmethod
    def calculate(self, inputs: dict) -> CalculationResult:
        """
        Perform the calculation.

        Args:
            inputs: Dictionary of calculation inputs (vertical-specific)

        Returns:
            CalculationResult with value, breakdown, explanation

        Raises:
            ValueError: If inputs fail validation
        """
        ...

    @abstractmethod
    def validate_inputs(self, inputs: dict) -> List[str]:
        """
        Validate calculation inputs.

        Args:
            inputs: Dictionary of calculation inputs

        Returns:
            List of error strings. Empty list means inputs are valid.
        """
        ...

    @abstractmethod
    def get_explanation(self, result: CalculationResult) -> str:
        """
        Generate human-readable explanation of a calculation result.

        Args:
            result: The CalculationResult to explain

        Returns:
            Plain-English explanation string
        """
        ...

    def get_test_cases(self) -> List[dict]:
        """
        Return built-in test cases for self-validation.
        Override in subclass to provide vertical-specific test data.

        Each test case dict should have:
            - name: str — descriptive name
            - inputs: dict — calculator inputs
            - expected_value: float — expected result value
            - tolerance: float — acceptable deviation (default 0.5)

        Returns:
            List of test case dicts
        """
        return []

    def run_self_test(self) -> Dict[str, Any]:
        """
        Run built-in test cases and report results.
        Call this during startup or health checks.
        """
        test_cases = self.get_test_cases()
        if not test_cases:
            return {"status": "no_tests", "message": "No test cases defined"}

        results = []
        passed = 0
        failed = 0

        for tc in test_cases:
            name = tc.get("name", "unnamed")
            inputs = tc.get("inputs", {})
            expected = tc.get("expected_value")
            tolerance = tc.get("tolerance", 0.5)

            try:
                errors = self.validate_inputs(inputs)
                if errors:
                    results.append({"name": name, "status": "INVALID_INPUT", "errors": errors})
                    failed += 1
                    continue

                result = self.calculate(inputs)
                if abs(result.value - expected) <= tolerance:
                    results.append({"name": name, "status": "PASS", "got": result.value, "expected": expected})
                    passed += 1
                else:
                    results.append({"name": name, "status": "FAIL", "got": result.value, "expected": expected})
                    failed += 1
            except Exception as e:
                results.append({"name": name, "status": "ERROR", "error": str(e)})
                failed += 1

        return {
            "status": "pass" if failed == 0 else "fail",
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "results": results
        }
```

---

### File 8: `/ganuda/assist/core/backend/base_council_chat.py`

Parameterized version of VetAssist `council_chat.py`. The domain context, citation patterns, and specialist priority are constructor parameters instead of hardcoded VA text.

```python
"""
Assist Platform — Base Council Chat Service
Parameterized integration with Ganuda 7-specialist Council.
Extracted from VetAssist council_chat.py — domain made configurable.
"""

import re
import yaml
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Import Ganuda Council (same path as VetAssist uses)
import importlib.util

_council_path = "/ganuda/lib/specialist_council.py"
_spec = importlib.util.spec_from_file_location("specialist_council", _council_path)
_council_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_council_module)
SpecialistCouncil = _council_module.SpecialistCouncil
council_vote = _council_module.council_vote

logger = logging.getLogger(__name__)


class BaseCouncilChatService:
    """
    Domain-agnostic Council chat service.

    Constructor takes:
      - domain_context: str — prepended to every query (replaces VetAssist va_context)
      - citation_patterns: list — regex patterns to extract citations from responses
      - specialist_priority: dict — {specialist_name: weight} for ranking responses
      - config_path: str — optional path to council_context.yaml

    VetAssist set domain_context to "You are assisting a veteran with VA disability claims..."
    A housing vertical would set it to "You are assisting with tribal housing assistance..."
    """

    # Specialist badge colors — shared across all verticals
    SPECIALIST_COLORS = {
        "crawdad": "#E63946",
        "gecko": "#06FFA5",
        "turtle": "#4A7C59",
        "eagle_eye": "#457B9D",
        "spider": "#A8DADC",
        "peace_chief": "#F1FAEE",
        "raven": "#1D3557"
    }

    def __init__(
        self,
        domain_context: str = None,
        citation_patterns: List[str] = None,
        specialist_priority: Dict[str, float] = None,
        config_path: str = None,
        max_tokens: int = 400
    ):
        """
        Initialize the council chat service.

        Args:
            domain_context: Context string prepended to all queries.
            citation_patterns: List of regex patterns to extract citations.
            specialist_priority: Dict mapping specialist name to priority weight.
            config_path: Path to council_context.yaml — overrides above params if set.
            max_tokens: Max tokens for council response.
        """
        self.council = SpecialistCouncil(max_tokens=max_tokens)

        # Load from YAML if config_path provided
        if config_path:
            self._load_from_yaml(config_path)
        else:
            self.domain_context = domain_context or (
                "CONTEXT: You are an AI assistant.\n"
                "RULES:\n"
                "1. Be helpful and accurate\n"
                "2. Cite regulations when applicable\n"
                "3. Include appropriate disclaimers\n"
            )
            self.citation_patterns = citation_patterns or []
            self.specialist_priority = specialist_priority or {
                "turtle": 1.0,
                "gecko": 1.0,
                "spider": 1.0,
                "raven": 1.0,
                "eagle_eye": 1.0,
                "crawdad": 1.0,
                "peace_chief": 1.0
            }

        self.disclaimer = ""  # Verticals set their own disclaimer

    def _load_from_yaml(self, config_path: str):
        """Load council configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Council config not found: {config_path}")

        with open(path, 'r') as f:
            cfg = yaml.safe_load(f)

        self.domain_context = (
            f"CONTEXT: {cfg.get('domain', 'General Assistance')}\n"
            f"{cfg.get('description', '')}\n"
        )

        # Build citation patterns from regulations list
        self.citation_patterns = []
        for reg in cfg.get('regulations', []):
            if 'pattern' in reg:
                self.citation_patterns.append(reg['pattern'])

        self.specialist_priority = cfg.get('specialist_priority', {})

    def format_question(
        self,
        user_question: str,
        session_history: List[Dict] = None
    ) -> str:
        """
        Format user question with domain context and session history.
        Mirrors VetAssist format_question_for_council().
        """
        formatted = self.domain_context

        if session_history and len(session_history) > 0:
            formatted += "\nRECENT CONVERSATION:\n"
            for msg in session_history[-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted += f"{role.upper()}: {content[:200]}\n"
            formatted += "\n"

        formatted += f"QUESTION: {user_question}\n\n"
        formatted += "Provide a helpful, accurate response."

        return formatted

    def extract_citations(self, text: str) -> List[str]:
        """
        Extract citations using configured regex patterns.
        VetAssist extracted "38 CFR 4.25", "38 U.S.C. 1110", "M21-1" refs.
        Other verticals define their own patterns.
        """
        citations = []
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        return list(set([c.strip() for c in citations]))

    def get_primary_specialist(self, council_responses: List[Dict]) -> str:
        """
        Determine primary specialist based on configured priority weights.
        Higher weight = higher priority.
        """
        if not council_responses:
            return "Council"

        # Sort by priority weight (descending)
        sorted_priority = sorted(
            self.specialist_priority.items(),
            key=lambda x: x[1],
            reverse=True
        )
        priority_order = [name for name, _ in sorted_priority]

        for specialist_id in priority_order:
            for response in council_responses:
                if response.get("name", "").lower() == specialist_id:
                    return response.get("name", "Council")

        return council_responses[0].get("name", "Council")

    def ask_council(
        self,
        user_question: str,
        session_history: List[Dict] = None
    ) -> Dict:
        """
        Ask the Ganuda Council a question with domain context.
        Returns same structure as VetAssist ask_council().
        """
        formatted_question = self.format_question(user_question, session_history)

        council_result = council_vote(
            question=formatted_question,
            max_tokens=400,
            include_responses=True
        )

        consensus = council_result.get(
            "consensus",
            "I don't have enough information to answer that question."
        )

        # Append disclaimer if set
        if self.disclaimer and self.disclaimer.lower() not in consensus.lower():
            consensus += f"\n\n*{self.disclaimer}*"

        citations = self.extract_citations(consensus)
        all_responses = council_result.get("responses", [])
        primary_specialist = self.get_primary_specialist(all_responses)

        return {
            "response": consensus,
            "specialist": primary_specialist,
            "confidence": float(council_result.get("confidence", 0.75)),
            "citations": citations,
            "concerns": council_result.get("concerns", []),
            "recommendation": council_result.get("recommendation", "PROCEED"),
            "all_responses": all_responses,
            "audit_hash": council_result.get("audit_hash", "")
        }

    def get_specialist_badge_color(self, specialist_name: str) -> str:
        """Get hex color for specialist badge in UI."""
        return self.SPECIALIST_COLORS.get(
            specialist_name.lower().replace(" ", "_"), "#6B7280"
        )
```

---

### File 9: `/ganuda/assist/core/backend/base_crisis.py`

YAML-driven crisis detection. Extracts the pattern-matching engine from VetAssist `crisis_detection.py` but loads patterns from `config/crisis_patterns.yaml` instead of hardcoding them.

```python
"""
Assist Platform — YAML-Driven Crisis Detection
Extracted from VetAssist crisis_detection.py.

Base patterns (suicide, self-harm, abuse) are ALWAYS active.
Verticals add domain-specific patterns via YAML.

SAFETY CRITICAL: This module detects when users may be in danger.
"""

import re
import yaml
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CrisisResult:
    """Result of crisis detection check."""
    is_crisis: bool
    severity: str = "none"       # none, medium, high, critical
    category: str = ""           # e.g., "immediate_danger", "self_harm", "abuse"
    matched_patterns: List[str] = field(default_factory=list)
    recommended_action: str = "" # e.g., "988_referral", "crisis_counselor"
    response_text: str = ""      # Text to show the user
    resources: Dict[str, str] = field(default_factory=dict)
    detected_at: str = ""


class BaseCrisisDetector:
    """
    YAML-driven crisis detection.

    Loads patterns from a YAML config file. Base patterns are always present.
    Verticals add domain-specific patterns (e.g., VetAssist adds MST, veteran substance patterns).

    Usage:
        detector = BaseCrisisDetector("/ganuda/assist/core/config/crisis_patterns.yaml")
        result = detector.detect("I want to end it all")
        if result.is_crisis:
            # Show result.response_text and result.resources
    """

    def __init__(
        self,
        config_path: str,
        default_resources: Dict[str, str] = None,
        response_templates: Dict[str, str] = None
    ):
        """
        Args:
            config_path: Path to crisis_patterns.yaml
            default_resources: Default crisis resources dict
                Example: {"phone": "988", "text": "741741", "chat": "988lifeline.org"}
            response_templates: Dict of category -> response text template
                If not provided, a generic response is used.
        """
        self.config_path = config_path
        self.default_resources = default_resources or {
            "phone": "988 Suicide & Crisis Lifeline",
            "text": "Text HOME to 741741",
            "chat": "988lifeline.org"
        }
        self.response_templates = response_templates or {}
        self.compiled_patterns: Dict[str, List] = {}

        self._load_patterns()

    def _load_patterns(self):
        """Load and compile patterns from YAML config."""
        path = Path(self.config_path)
        if not path.exists():
            logger.error(f"Crisis patterns config not found: {self.config_path}")
            # Load hardcoded minimum safety patterns as fallback
            self._load_safety_fallback()
            return

        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        all_patterns = config.get("base_patterns", []) + config.get("vertical_patterns", [])

        for entry in all_patterns:
            category = entry.get("category", "unknown")
            severity = entry.get("severity", "medium")
            keywords = entry.get("keywords", [])
            action = entry.get("action", "crisis_referral")

            if category not in self.compiled_patterns:
                self.compiled_patterns[category] = []

            for kw in keywords:
                # Compile keyword as regex (escape if plain text, keep if regex)
                try:
                    pattern = re.compile(re.escape(kw), re.IGNORECASE)
                except re.error:
                    pattern = re.compile(kw, re.IGNORECASE)

                self.compiled_patterns[category].append({
                    "pattern": pattern,
                    "keyword": kw,
                    "severity": severity,
                    "action": action
                })

        logger.info(
            f"Crisis detector loaded: {sum(len(v) for v in self.compiled_patterns.values())} "
            f"patterns across {len(self.compiled_patterns)} categories"
        )

    def _load_safety_fallback(self):
        """
        Hardcoded minimum patterns — ALWAYS present even if YAML fails.
        These must never be removed or disabled.
        """
        fallback_keywords = {
            "immediate_danger": {
                "severity": "critical",
                "action": "988_referral",
                "keywords": ["kill myself", "end my life", "suicide", "want to die"]
            },
            "self_harm": {
                "severity": "high",
                "action": "crisis_counselor",
                "keywords": ["hurt myself", "self harm", "cutting"]
            }
        }

        for category, data in fallback_keywords.items():
            self.compiled_patterns[category] = []
            for kw in data["keywords"]:
                self.compiled_patterns[category].append({
                    "pattern": re.compile(re.escape(kw), re.IGNORECASE),
                    "keyword": kw,
                    "severity": data["severity"],
                    "action": data["action"]
                })

        logger.warning("Crisis detector using FALLBACK patterns — YAML config not loaded")

    def detect(self, message: str) -> CrisisResult:
        """
        Check a message for crisis indicators.

        Args:
            message: User's message text

        Returns:
            CrisisResult — always returned. Check is_crisis to determine if crisis was found.
        """
        if not message:
            return CrisisResult(is_crisis=False)

        message_lower = message.lower()
        matched = []

        for category, pattern_entries in self.compiled_patterns.items():
            for entry in pattern_entries:
                if entry["pattern"].search(message_lower):
                    matched.append({
                        "category": category,
                        "keyword": entry["keyword"],
                        "severity": entry["severity"],
                        "action": entry["action"]
                    })

        if not matched:
            return CrisisResult(is_crisis=False)

        # Use the highest severity match
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        matched.sort(key=lambda m: severity_order.get(m["severity"], 0), reverse=True)
        top_match = matched[0]

        # Build response text
        response_text = self.response_templates.get(
            top_match["category"],
            self._default_response(top_match["category"])
        )

        logger.info(f"Crisis detected: category={top_match['category']}, severity={top_match['severity']}")

        return CrisisResult(
            is_crisis=True,
            severity=top_match["severity"],
            category=top_match["category"],
            matched_patterns=[m["keyword"] for m in matched],
            recommended_action=top_match["action"],
            response_text=response_text,
            resources=self.default_resources,
            detected_at=datetime.utcnow().isoformat()
        )

    def _default_response(self, category: str) -> str:
        """Default crisis response when no template is configured."""
        resources_str = "\n".join(
            f"  {k}: {v}" for k, v in self.default_resources.items()
        )
        return (
            f"It sounds like you may be going through a difficult time. "
            f"Please reach out for help:\n\n{resources_str}\n\n"
            f"These services are free, confidential, and available 24/7."
        )


# Convenience function
def check_message(
    message: str,
    config_path: str = None
) -> CrisisResult:
    """
    Quick check for crisis indicators.
    Uses default config path if not specified.
    """
    if config_path is None:
        config_path = str(Path(__file__).parent.parent / "config" / "crisis_patterns.yaml")
    detector = BaseCrisisDetector(config_path)
    return detector.detect(message)
```

---

### File 10: `/ganuda/assist/core/backend/base_pii.py`

YAML-driven PII detection. Mirrors VetAssist's `pii_service.py` wrapper pattern but loads entity definitions from YAML.

```python
"""
Assist Platform — YAML-Driven PII Detection
Wraps ganuda_pii core with configurable entity lists per vertical.
"""

import sys
import yaml
import logging
from typing import List, Dict, Optional
from pathlib import Path

sys.path.insert(0, '/ganuda/lib')

from ganuda_pii import PIIService as CorePIIService

logger = logging.getLogger(__name__)


class BasePIIService:
    """
    YAML-configurable PII detection service.

    Loads entity definitions from pii_entities.yaml.
    Base entities (SSN, phone, email) are always active.
    Verticals add domain-specific entities via YAML vertical_entities section.

    Usage:
        pii = BasePIIService("/ganuda/assist/core/config/pii_entities.yaml")
        findings = pii.analyze("My SSN is 123-45-6789")
        redacted = pii.redact("My SSN is 123-45-6789")
    """

    def __init__(self, config_path: str = None, additional_recognizers: list = None):
        """
        Args:
            config_path: Path to pii_entities.yaml
            additional_recognizers: Optional list of presidio recognizer objects
        """
        self.config_path = config_path
        self.entities = []
        self.patterns = {}

        if config_path:
            self._load_config(config_path)

        # Build entity list for core service
        entity_names = [e["type"] for e in self.entities if e.get("action") == "redact"]
        flag_entities = [e["type"] for e in self.entities if e.get("action") == "flag"]

        # Initialize core PII service
        # Map YAML entity types to Presidio entity names
        presidio_entities = self._map_to_presidio(entity_names + flag_entities)
        self.core = CorePIIService(sensitive_entities=presidio_entities)

        if additional_recognizers:
            self.core.add_recognizers(additional_recognizers)

        logger.info(f"PII service initialized: {len(self.entities)} entity types loaded")

    def _load_config(self, config_path: str):
        """Load PII entity definitions from YAML."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"PII config not found: {config_path}, using defaults")
            self._load_defaults()
            return

        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        self.entities = config.get("base_entities", []) + config.get("vertical_entities", [])

        # Store regex patterns for custom detection
        for entity in self.entities:
            if "pattern" in entity:
                self.patterns[entity["type"]] = entity["pattern"]

    def _load_defaults(self):
        """Default PII entities if YAML not available."""
        self.entities = [
            {"type": "US_SSN", "action": "redact"},
            {"type": "PHONE_NUMBER", "action": "flag"},
            {"type": "EMAIL_ADDRESS", "action": "flag"},
        ]

    def _map_to_presidio(self, entity_types: list) -> list:
        """Map YAML entity type names to Presidio recognizer names."""
        mapping = {
            "ssn": "US_SSN",
            "phone": "PHONE_NUMBER",
            "email": "EMAIL_ADDRESS",
            "dob": "DATE_TIME",
            "credit_card": "CREDIT_CARD",
            "driver_license": "US_DRIVER_LICENSE",
            "bank_number": "US_BANK_NUMBER",
        }
        result = []
        for t in entity_types:
            mapped = mapping.get(t.lower(), t.upper())
            result.append(mapped)
        return list(set(result))

    def analyze(self, text: str) -> List[Dict]:
        """Analyze text for PII. Returns list of findings."""
        return self.core.analyze(text)

    def redact(self, text: str) -> str:
        """Redact PII from text for logging."""
        return self.core.redact_for_logging(text)
```

---

### File 11: `/ganuda/assist/core/backend/base_wizard.py`

YAML-driven wizard engine. No hardcoded steps — everything loaded from YAML files.

```python
"""
Assist Platform — YAML-Driven Wizard Engine
Multi-step guided workflows with conditional branching.

Wizard definitions live in YAML files. Each vertical provides its own
wizard YAML files (e.g., VetAssist has claims-wizard.yaml).
The engine just runs them.
"""

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class WizardStep:
    """A single step in a wizard flow."""
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.title: str = data.get("title", "")
        self.description: str = data.get("description", "")
        self.input_type: str = data.get("input_type", "text")  # text, select, multi_select, number, date, boolean, file
        self.options: List[Dict] = data.get("options", [])      # For select/multi_select
        self.required: bool = data.get("required", True)
        self.validation: Dict = data.get("validation", {})      # {min, max, pattern, etc.}
        self.next_step: str = data.get("next_step", "")         # Default next step ID
        self.conditional_next: List[Dict] = data.get("conditional_next", [])  # [{if_value: X, then_step: Y}]
        self.help_text: str = data.get("help_text", "")
        self.i18n_key: str = data.get("i18n_key", "")           # For Cherokee translations


class WizardDefinition:
    """A complete wizard loaded from YAML."""
    def __init__(self, yaml_path: str):
        self.path = yaml_path
        self.steps: Dict[str, WizardStep] = {}
        self.first_step_id: str = ""
        self.title: str = ""
        self.description: str = ""
        self.version: str = "1.0"

        self._load(yaml_path)

    def _load(self, yaml_path: str):
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Wizard definition not found: {yaml_path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        self.title = data.get("title", "Wizard")
        self.description = data.get("description", "")
        self.version = data.get("version", "1.0")
        self.first_step_id = data.get("first_step", "")

        for step_data in data.get("steps", []):
            step = WizardStep(step_data)
            self.steps[step.id] = step

        if not self.first_step_id and self.steps:
            self.first_step_id = list(self.steps.keys())[0]

        logger.info(f"Wizard loaded: '{self.title}' with {len(self.steps)} steps")


class WizardEngine:
    """
    Runs a wizard for a user session.

    Manages:
    - Current step tracking
    - Input validation per step
    - Conditional branching (show step X if answer to step Y equals Z)
    - Save/resume progress via session_data dict (stored in assist_sessions)

    Usage:
        definition = WizardDefinition("/ganuda/assist/verticals/vetassist/wizards/claims.yaml")
        engine = WizardEngine(definition)

        # Start or resume
        session_data = {}  # Load from assist_sessions.session_data
        current = engine.get_current_step(session_data)

        # User submits answer
        result = engine.submit_step(session_data, step_id="step_1", value="PTSD")

        # Save session_data back to assist_sessions
    """

    def __init__(self, definition: WizardDefinition):
        self.definition = definition

    def get_current_step(self, session_data: dict) -> Optional[Dict[str, Any]]:
        """
        Get the current step for this session.

        Args:
            session_data: Session data dict (from assist_sessions.session_data)

        Returns:
            Dict with step info: {id, title, description, input_type, options, required, help_text}
            Returns None if wizard is complete.
        """
        current_id = session_data.get("current_step", self.definition.first_step_id)

        if current_id == "__complete__":
            return None

        step = self.definition.steps.get(current_id)
        if not step:
            logger.error(f"Step not found: {current_id}")
            return None

        return {
            "id": step.id,
            "title": step.title,
            "description": step.description,
            "input_type": step.input_type,
            "options": step.options,
            "required": step.required,
            "help_text": step.help_text,
            "i18n_key": step.i18n_key,
            "progress": self._calculate_progress(session_data),
            "total_steps": len(self.definition.steps)
        }

    def validate_step_input(self, step_id: str, value: Any) -> List[str]:
        """
        Validate input for a given step.

        Returns list of error strings (empty = valid).
        """
        step = self.definition.steps.get(step_id)
        if not step:
            return [f"Unknown step: {step_id}"]

        errors = []

        if step.required and (value is None or value == ""):
            errors.append(f"{step.title} is required")
            return errors

        if not step.required and (value is None or value == ""):
            return []  # Optional and empty is fine

        validation = step.validation

        if step.input_type == "number":
            try:
                num_val = float(value)
                if "min" in validation and num_val < validation["min"]:
                    errors.append(f"Minimum value is {validation['min']}")
                if "max" in validation and num_val > validation["max"]:
                    errors.append(f"Maximum value is {validation['max']}")
            except (ValueError, TypeError):
                errors.append("Must be a number")

        if step.input_type == "select" and step.options:
            valid_values = [opt.get("value") for opt in step.options]
            if value not in valid_values:
                errors.append(f"Invalid selection. Choose from: {valid_values}")

        if "pattern" in validation:
            import re
            if not re.match(validation["pattern"], str(value)):
                errors.append(validation.get("pattern_message", "Invalid format"))

        return errors

    def submit_step(
        self,
        session_data: dict,
        step_id: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Submit an answer for a step and advance to the next.

        Args:
            session_data: Session data dict (MUTATED in place)
            step_id: The step being answered
            value: The user's answer

        Returns:
            Dict with:
                - valid: bool
                - errors: list (if invalid)
                - next_step: dict or None (if wizard complete)
                - session_data: updated session data
        """
        # Validate
        errors = self.validate_step_input(step_id, value)
        if errors:
            return {"valid": False, "errors": errors, "next_step": None, "session_data": session_data}

        # Record answer
        if "answers" not in session_data:
            session_data["answers"] = {}
        session_data["answers"][step_id] = value
        session_data["last_updated"] = datetime.utcnow().isoformat()

        # Determine next step
        step = self.definition.steps.get(step_id)
        next_step_id = self._resolve_next_step(step, value)

        session_data["current_step"] = next_step_id
        session_data["completed_steps"] = session_data.get("completed_steps", [])
        if step_id not in session_data["completed_steps"]:
            session_data["completed_steps"].append(step_id)

        # Get next step info
        next_step_info = self.get_current_step(session_data)

        return {
            "valid": True,
            "errors": [],
            "next_step": next_step_info,
            "session_data": session_data
        }

    def _resolve_next_step(self, step: WizardStep, value: Any) -> str:
        """Resolve next step using conditional branching rules."""
        if not step:
            return "__complete__"

        # Check conditional rules first
        for rule in step.conditional_next:
            if_value = rule.get("if_value")
            then_step = rule.get("then_step")
            if str(value) == str(if_value) and then_step:
                return then_step

        # Default next step
        if step.next_step:
            return step.next_step

        return "__complete__"

    def _calculate_progress(self, session_data: dict) -> float:
        """Calculate wizard completion progress (0.0 to 1.0)."""
        total = len(self.definition.steps)
        if total == 0:
            return 1.0
        completed = len(session_data.get("completed_steps", []))
        return min(completed / total, 1.0)

    def get_summary(self, session_data: dict) -> Dict[str, Any]:
        """Get a summary of all answers for review before submission."""
        answers = session_data.get("answers", {})
        summary = []
        for step_id, step in self.definition.steps.items():
            value = answers.get(step_id)
            summary.append({
                "step_id": step_id,
                "title": step.title,
                "value": value,
                "answered": value is not None
            })
        return {
            "title": self.definition.title,
            "version": self.definition.version,
            "steps": summary,
            "complete": session_data.get("current_step") == "__complete__",
            "progress": self._calculate_progress(session_data)
        }
```

---

### FRONTEND FILES

---

### File 12: `/ganuda/assist/core/frontend/lib/types.ts`

Core types only. Extracted from VetAssist `frontend/lib/types.ts`. Removed VA-specific types (Condition, Dependents, EducationalContent). Kept: User, Session, ChatMessage, WizardStep, CalculationResult.

```typescript
/**
 * Assist Platform Core TypeScript Types
 * Shared across all verticals.
 * Domain-specific types belong in the vertical, not here.
 */

// === Auth Types ===

export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  preferred_language?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
  expires_in: number;
}

// === Session Types ===

export interface AssistSession {
  id: string;
  user_id: string;
  vertical: string;
  session_type: string;
  session_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// === Wizard Types ===

export interface WizardStepOption {
  value: string;
  label: string;
  description?: string;
}

export interface WizardStep {
  id: string;
  title: string;
  description: string;
  input_type: 'text' | 'select' | 'multi_select' | 'number' | 'date' | 'boolean' | 'file';
  options: WizardStepOption[];
  required: boolean;
  help_text: string;
  i18n_key: string;
  progress: number;
  total_steps: number;
}

export interface WizardSubmitResult {
  valid: boolean;
  errors: string[];
  next_step: WizardStep | null;
}

export interface WizardSummary {
  title: string;
  steps: Array<{
    step_id: string;
    title: string;
    value: any;
    answered: boolean;
  }>;
  complete: boolean;
  progress: number;
}

// === Calculator Types ===

export interface CalculationResult {
  value: number;
  breakdown: Record<string, any>;
  explanation: string;
  warnings: string[];
  confidence: number;
  metadata?: Record<string, any>;
}

// === Chat Types ===

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  specialist?: string;
  confidence_score?: number;
  citations?: string[];
  created_at: string;
}

export interface ChatMessageRequest {
  session_id: string | null;
  message: string;
}

export interface ChatMessageResponse {
  message: ChatMessage;
  session: AssistSession;
}

// === API Error ===

export interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

// === Crisis Detection ===

export interface CrisisAlert {
  is_crisis: boolean;
  severity: string;
  category: string;
  response_text: string;
  resources: Record<string, string>;
}
```

---

### File 13: `/ganuda/assist/core/frontend/lib/api-client.ts`

Base API client extracted from VetAssist. Removed: `linkVAAccount`, all admin endpoints, `calculateRating`, `sendChatMessage`. Kept: core HTTP methods, token management, auth endpoints. Verticals extend this class.

```typescript
/**
 * Assist Platform — Base API Client
 * Extracted from VetAssist api-client.ts.
 * Verticals extend this class to add domain-specific endpoints.
 */

import type { User, LoginRequest, RegisterRequest, AuthResponse, ApiError } from './types';

export type { ApiError, User, LoginRequest, RegisterRequest };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class BaseApiClient {
  protected baseUrl: string;
  protected token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;

    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  protected getHeaders(): HeadersInit {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  protected async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = { message: response.statusText, status: response.status };
      try {
        const data = await response.json();
        error.detail = data.detail || data.message;
      } catch { /* not JSON */ }
      throw error;
    }
    return response.json();
  }

  protected async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: { ...this.getHeaders(), ...options.headers },
    };
    const response = await fetch(url, config);
    return this.handleResponse<T>(response);
  }

  // === Auth Endpoints (shared by all verticals) ===

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(response.access_token);
    return response;
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me', { method: 'GET' });
  }

  // === Health Check ===

  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/health', { method: 'GET' });
  }
}

// Default singleton — verticals create their own
export const apiClient = new BaseApiClient();
export default BaseApiClient;
```

---

### File 14: `/ganuda/assist/core/frontend/lib/auth-context.tsx`

Copy from VetAssist `frontend/lib/auth-context.tsx` verbatim. It is already generic enough. Only change the import path to use the core api-client.

```tsx
'use client';

/**
 * Authentication Context Provider
 * Manages user authentication state across the application.
 * Copied from VetAssist auth-context.tsx — already fully generic.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, User, LoginRequest, RegisterRequest, ApiError } from './api-client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const loadUser = async () => {
      const token = apiClient.getToken();
      if (!token) { setLoading(false); return; }
      try {
        const userData = await apiClient.getCurrentUser();
        setUser(userData);
      } catch (err) {
        apiClient.setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiClient.login(credentials);
      setUser(response.user);
      router.push('/dashboard');
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || apiError.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    setError(null);
    setLoading(true);
    try {
      const response = await apiClient.register(data);
      setUser(response.user);
      router.push('/dashboard');
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || apiError.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    try { await apiClient.logout(); } catch (err) { console.error('Logout error:', err); }
    finally { setUser(null); router.push('/login'); }
  };

  const clearError = () => setError(null);

  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.error('Failed to refresh user:', err);
      setUser(null);
      apiClient.setToken(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, clearError, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function withAuth<P extends object>(Component: React.ComponentType<P>): React.FC<P> {
  return function ProtectedRoute(props: P) {
    const { user, loading } = useAuth();
    const router = useRouter();
    useEffect(() => { if (!loading && !user) { router.push('/login'); } }, [user, loading, router]);
    if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="text-lg">Loading...</div></div>;
    if (!user) return null;
    return <Component {...props} />;
  };
}
```

---

### File 15: `/ganuda/assist/core/frontend/components/Header.tsx`

Parameterized header. VetAssist hardcodes "Ganuda VetAssist". This takes props.

```tsx
'use client';

/**
 * Assist Platform — Branded Header Component
 * Props control title and logo — no hardcoded branding.
 */

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../lib/auth-context';

interface HeaderProps {
  title: string;
  logoUrl?: string;
  homeHref?: string;
  navItems?: Array<{ label: string; href: string }>;
}

export default function Header({
  title,
  logoUrl,
  homeHref = '/',
  navItems = []
}: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link href={homeHref} className="flex items-center gap-2">
          {logoUrl && <img src={logoUrl} alt={title} className="h-8 w-8" />}
          <span className="text-xl font-bold">{title}</span>
        </Link>

        <nav className="flex items-center gap-4">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="text-sm hover:underline">
              {item.label}
            </Link>
          ))}

          {user ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <button
                onClick={() => logout()}
                className="text-sm px-3 py-1 rounded border hover:bg-muted"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link href="/login" className="text-sm px-3 py-1 rounded border hover:bg-muted">
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
```

---

### File 16: `/ganuda/assist/core/frontend/components/WizardShell.tsx`

Multi-step wizard renderer. Consumes the WizardStep type from the backend.

```tsx
'use client';

/**
 * Assist Platform — Wizard Shell Component
 * Renders any YAML-driven wizard from the backend.
 */

import React, { useState } from 'react';
import type { WizardStep, WizardSubmitResult } from '../lib/types';

interface WizardShellProps {
  currentStep: WizardStep | null;
  onSubmitStep: (stepId: string, value: any) => Promise<WizardSubmitResult>;
  onComplete?: () => void;
  title?: string;
}

export default function WizardShell({
  currentStep,
  onSubmitStep,
  onComplete,
  title
}: WizardShellProps) {
  const [value, setValue] = useState<any>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  if (!currentStep) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-4">Complete</h2>
        <p className="text-muted-foreground">All steps have been completed.</p>
        {onComplete && (
          <button onClick={onComplete} className="mt-4 px-6 py-2 rounded bg-primary text-white">
            Continue
          </button>
        )}
      </div>
    );
  }

  const handleSubmit = async () => {
    setSubmitting(true);
    setErrors([]);
    try {
      const result = await onSubmitStep(currentStep.id, value);
      if (!result.valid) {
        setErrors(result.errors);
      } else {
        setValue('');
        if (!result.next_step && onComplete) {
          onComplete();
        }
      }
    } catch (err) {
      setErrors(['An unexpected error occurred']);
    } finally {
      setSubmitting(false);
    }
  };

  const renderInput = () => {
    switch (currentStep.input_type) {
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full p-3 border rounded"
          >
            <option value="">Select...</option>
            {currentStep.options.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        );
      case 'boolean':
        return (
          <div className="flex gap-4">
            <button
              onClick={() => setValue(true)}
              className={`px-6 py-3 rounded border ${value === true ? 'bg-primary text-white' : ''}`}
            >
              Yes
            </button>
            <button
              onClick={() => setValue(false)}
              className={`px-6 py-3 rounded border ${value === false ? 'bg-primary text-white' : ''}`}
            >
              No
            </button>
          </div>
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => setValue(parseFloat(e.target.value))}
            className="w-full p-3 border rounded"
          />
        );
      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full p-3 border rounded"
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full p-3 border rounded"
            placeholder={currentStep.help_text || ''}
          />
        );
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {title && <h1 className="text-2xl font-bold mb-6">{title}</h1>}

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-muted-foreground mb-1">
          <span>Step {Math.round(currentStep.progress * currentStep.total_steps) + 1} of {currentStep.total_steps}</span>
          <span>{Math.round(currentStep.progress * 100)}%</span>
        </div>
        <div className="w-full bg-muted rounded-full h-2">
          <div
            className="bg-primary h-2 rounded-full transition-all"
            style={{ width: `${currentStep.progress * 100}%` }}
          />
        </div>
      </div>

      {/* Step content */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="text-xl font-semibold mb-2">{currentStep.title}</h2>
        {currentStep.description && (
          <p className="text-muted-foreground mb-4">{currentStep.description}</p>
        )}

        <div className="mb-4">{renderInput()}</div>

        {errors.length > 0 && (
          <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded">
            {errors.map((e, i) => <p key={i}>{e}</p>)}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="px-6 py-2 rounded bg-primary text-white disabled:opacity-50"
        >
          {submitting ? 'Submitting...' : 'Next'}
        </button>
      </div>
    </div>
  );
}
```

---

### File 17: `/ganuda/assist/core/frontend/components/CalculatorView.tsx`

Displays calculation results with breakdown. Generic — works for any calculator output.

```tsx
'use client';

/**
 * Assist Platform — Calculator Result Display
 * Shows value, breakdown, explanation, and warnings for any calculator.
 */

import React from 'react';
import type { CalculationResult } from '../lib/types';

interface CalculatorViewProps {
  result: CalculationResult | null;
  title?: string;
  valueLabel?: string;
  valueFormatter?: (value: number) => string;
}

export default function CalculatorView({
  result,
  title = 'Calculation Result',
  valueLabel = 'Result',
  valueFormatter = (v) => v.toString()
}: CalculatorViewProps) {
  if (!result) return null;

  return (
    <div className="bg-card rounded-lg border p-6">
      <h2 className="text-xl font-bold mb-4">{title}</h2>

      {/* Primary value */}
      <div className="text-center py-6 bg-primary/5 rounded-lg mb-4">
        <p className="text-sm text-muted-foreground">{valueLabel}</p>
        <p className="text-4xl font-bold">{valueFormatter(result.value)}</p>
        {result.confidence < 1.0 && (
          <p className="text-sm text-muted-foreground mt-1">
            Confidence: {Math.round(result.confidence * 100)}%
          </p>
        )}
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="font-medium text-yellow-800 mb-1">Warnings:</p>
          {result.warnings.map((w, i) => (
            <p key={i} className="text-sm text-yellow-700">- {w}</p>
          ))}
        </div>
      )}

      {/* Explanation */}
      {result.explanation && (
        <div className="mb-4">
          <h3 className="font-semibold mb-1">Explanation</h3>
          <p className="text-muted-foreground text-sm">{result.explanation}</p>
        </div>
      )}

      {/* Breakdown */}
      {result.breakdown && Object.keys(result.breakdown).length > 0 && (
        <details className="mb-4">
          <summary className="cursor-pointer font-semibold text-sm">View Breakdown</summary>
          <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto">
            {JSON.stringify(result.breakdown, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
```

---

### File 18: `/ganuda/assist/core/frontend/components/ChatPanel.tsx`

Council chat interface. Generic — works with any BaseCouncilChatService backend.

```tsx
'use client';

/**
 * Assist Platform — Chat Panel Component
 * Council-powered chat interface. Domain-agnostic.
 */

import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage, ChatMessageRequest, ChatMessageResponse, CrisisAlert } from '../lib/types';

interface ChatPanelProps {
  sessionId: string | null;
  onSendMessage: (request: ChatMessageRequest) => Promise<ChatMessageResponse>;
  onCrisisDetected?: (alert: CrisisAlert) => void;
  placeholder?: string;
  disclaimer?: string;
}

export default function ChatPanel({
  sessionId,
  onSendMessage,
  onCrisisDetected,
  placeholder = 'Type your question...',
  disclaimer
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId || '',
      role: 'user',
      content: input,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await onSendMessage({
        session_id: currentSessionId,
        message: input,
      });

      if (response.session) {
        setCurrentSessionId(response.session.id);
      }

      setMessages((prev) => [...prev, response.message]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          session_id: currentSessionId || '',
          role: 'system',
          content: 'An error occurred. Please try again.',
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full border rounded-lg">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-muted-foreground py-8">{placeholder}</p>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : msg.role === 'system'
                ? 'bg-destructive/10 text-destructive'
                : 'bg-muted'
            }`}>
              {msg.specialist && (
                <p className="text-xs font-medium mb-1 opacity-75">{msg.specialist}</p>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-current/10">
                  <p className="text-xs opacity-75">Citations: {msg.citations.join(', ')}</p>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-2 animate-pulse">Thinking...</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Disclaimer */}
      {disclaimer && (
        <div className="px-4 py-1 text-xs text-muted-foreground text-center border-t">
          {disclaimer}
        </div>
      )}

      {/* Input area */}
      <div className="border-t p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={placeholder}
          className="flex-1 p-2 border rounded"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded bg-primary text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

---

## Database Schema

### File: `/ganuda/assist/core/sql/assist_core_schema.sql`

Run on bluefin (192.168.132.222), database `zammad_production`. **DO NOT run in a transaction that touches VetAssist tables.** This creates NEW tables only.

```sql
-- Assist Platform Core Schema
-- Run on bluefin (192.168.132.222) database: zammad_production
-- Created: 2026-02-04 by TPM (Claude Opus 4.5) + Council
--
-- SAFETY: These are NEW tables. They do NOT touch existing VetAssist tables.

-- Core user table for all Assist verticals
CREATE TABLE IF NOT EXISTS assist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session storage for wizards, chat, and vertical state
CREATE TABLE IF NOT EXISTS assist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id) ON DELETE CASCADE,
    vertical VARCHAR(50) NOT NULL,
    session_type VARCHAR(50) DEFAULT 'wizard',
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit trail for all actions across all verticals
CREATE TABLE IF NOT EXISTS assist_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    vertical VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_assist_users_email ON assist_users(email);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_user ON assist_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_vertical ON assist_sessions(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_type ON assist_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_assist_audit_user ON assist_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_audit_vertical ON assist_audit(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_audit_created ON assist_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_assist_audit_action ON assist_audit(action);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION assist_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_assist_users_updated
    BEFORE UPDATE ON assist_users
    FOR EACH ROW EXECUTE FUNCTION assist_update_timestamp();

CREATE OR REPLACE TRIGGER trg_assist_sessions_updated
    BEFORE UPDATE ON assist_sessions
    FOR EACH ROW EXECUTE FUNCTION assist_update_timestamp();
```

---

## YAML Configurations

### File: `/ganuda/assist/core/config/crisis_patterns.yaml`

```yaml
# Assist Platform — Base Crisis Detection Patterns
# These base_patterns are ALWAYS active across all verticals.
# Verticals add domain-specific patterns in vertical_patterns section
# or in their own YAML that extends this one.
#
# SAFETY CRITICAL: Do not remove base patterns.
# They catch people in immediate danger.

base_patterns:
  - category: "immediate_danger"
    severity: "critical"
    keywords:
      - "kill myself"
      - "end my life"
      - "suicide"
      - "want to die"
      - "end it all"
      - "no reason to live"
      - "better off dead"
    action: "988_referral"

  - category: "self_harm"
    severity: "high"
    keywords:
      - "hurt myself"
      - "cutting"
      - "self harm"
      - "self-harm"
    action: "crisis_counselor"

  - category: "abuse"
    severity: "high"
    keywords:
      - "being abused"
      - "domestic violence"
      - "being hurt"
      - "someone is hurting me"
    action: "hotline_referral"

  - category: "danger_to_others"
    severity: "critical"
    keywords:
      - "want to hurt someone"
      - "going to kill"
      - "voices telling me"
    action: "988_referral"

# Verticals add their patterns here or in a separate file.
# Example for VetAssist:
#   vertical_patterns:
#     - category: "mst"
#       severity: "high"
#       keywords: ["military sexual trauma", "MST"]
#       action: "mst_coordinator"
vertical_patterns: []
```

---

### File: `/ganuda/assist/core/config/pii_entities.yaml`

```yaml
# Assist Platform — Base PII Entity Definitions
# These are always detected. Verticals add domain-specific entities.

base_entities:
  - type: "ssn"
    pattern: "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    action: "redact"
    description: "Social Security Number"

  - type: "dob"
    pattern: "\\b\\d{2}/\\d{2}/\\d{4}\\b"
    action: "redact"
    description: "Date of birth"

  - type: "phone"
    pattern: "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b"
    action: "flag"
    description: "Phone number"

  - type: "email"
    pattern: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
    action: "flag"
    description: "Email address"

  - type: "credit_card"
    pattern: "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b"
    action: "redact"
    description: "Credit card number"

# Verticals add domain-specific entities here.
# Example for VetAssist:
#   vertical_entities:
#     - type: "va_file_number"
#       pattern: "\\b\\d{8,9}\\b"
#       action: "redact"
vertical_entities: []
```

---

### File: `/ganuda/assist/core/config/council_context.yaml`

```yaml
# Assist Platform — Council Configuration Template
# Each vertical overrides this with domain-specific context.

domain: "General Assistance"
description: "Base council context — override per vertical"

# Regulations the council should cite (with regex extraction patterns)
regulations: []
# Example for VetAssist:
#   regulations:
#     - name: "CFR"
#       pattern: "38\\s+CFR\\s+\\d+\\.\\d+"
#     - name: "USC"
#       pattern: "38\\s+U\\.?S\\.?C\\.?\\s+\\d+"

# Specialist priority weights (higher = more authoritative for this domain)
specialist_priority:
  turtle: 1.0      # Seven Generations wisdom
  gecko: 1.0       # Performance
  spider: 1.0      # Integration
  raven: 1.0       # Strategy
  eagle_eye: 1.0   # Monitoring
  crawdad: 1.0     # Security
  peace_chief: 1.0 # Consensus

# Citation format: standard, legal, medical, academic
citation_format: "standard"

# Disclaimer appended to council responses
disclaimer: "This is for informational purposes only."
```

---

### File: `/ganuda/assist/core/i18n/chr.yaml`

```yaml
# Cherokee (chr) translations — shared across all Assist verticals
# Cherokee language is a first-class citizen, not an afterthought.
# ᎠᏂᏴᏫᏰ ᏗᎦᎵᏍᏙᏗ — For the Seven Generations

common:
  welcome: "ᎣᏏᏲ"                    # Osiyo — Hello
  help: "ᎠᎵᏍᏕᎸᏙᏗ"                # Help
  submit: "ᎠᏓᏅᏖᏍᏗ"                # Submit
  cancel: "ᎠᏍᏓᏩᏗᏎᏍᏗ"              # Cancel
  next: "ᎢᏴᏛ"                      # Next
  back: "ᎤᏔᎾ"                      # Back
  save: "ᎠᏍᏆᎵ"                    # Save
  error: "ᎤᏲᎱᏒ"                    # Error
  loading: "ᎠᏓᎾᏅᎢ..."              # Loading...
  seven_generations: "ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ"  # Seven Generations
  yes: "ᎥᎥ"                        # Yes
  no: "ᎥᏝ"                         # No
  thank_you: "ᏩᏙᎢ"                  # Thank you

navigation:
  home: "ᎤᏪᏘ"                      # Home
  dashboard: "ᎠᏓᎴᏂᏍᎬ"              # Dashboard
  calculator: "ᏗᏎᏍᏗ"                # Calculator
  chat: "ᎠᏬᏂᏍᏗ"                    # Chat
  settings: "ᎠᏍᏓᏩᏗᏎᏍᏗ"              # Settings
  profile: "ᎤᏙᏢᏒ"                  # Profile
  logout: "ᎠᏓᏍᏕᎸᏗ"                # Logout

messages:
  crisis_detected: "ᎠᎵᏍᏕᎸᏙᏗ ᎤᏲᎯ ᎨᏒ"  # Help is available
  session_saved: "ᎠᏍᏆᎵ ᎣᏍᏓ"          # Session saved
  calculation_complete: "ᏗᏎᏍᏗ ᎤᎵᏍᏔᏅ"  # Calculation complete
  login_success: "ᎣᏏᏲ ᏕᏣᏓᎢ"          # Welcome back
  registration_complete: "ᎠᏓᎾᏅ ᎣᏍᏓ"    # Registration complete

wizard:
  step_of: "ᏗᎬᏙᏗ {current} ᎠᎴ {total}"  # Step X of Y
  complete: "ᎤᎵᏍᏔᏅ"                      # Complete
  review: "ᎠᏓᏲᎵᏍᏔᏅ"                      # Review
```

---

### File: `/ganuda/assist/core/i18n/en.yaml`

```yaml
# English (en) translations — shared across all Assist verticals

common:
  welcome: "Welcome"
  help: "Help"
  submit: "Submit"
  cancel: "Cancel"
  next: "Next"
  back: "Back"
  save: "Save"
  error: "Error"
  loading: "Loading..."
  seven_generations: "Seven Generations"
  yes: "Yes"
  no: "No"
  thank_you: "Thank you"

navigation:
  home: "Home"
  dashboard: "Dashboard"
  calculator: "Calculator"
  chat: "Chat"
  settings: "Settings"
  profile: "Profile"
  logout: "Logout"

messages:
  crisis_detected: "Help is available"
  session_saved: "Session saved"
  calculation_complete: "Calculation complete"
  login_success: "Welcome back"
  registration_complete: "Registration complete"

wizard:
  step_of: "Step {current} of {total}"
  complete: "Complete"
  review: "Review"
```

---

## Verification Steps

The Jr must confirm ALL of the following before marking this task complete.

### 1. Directory Structure Exists

```bash
# Run from any node
ls -la /ganuda/assist/core/backend/
ls -la /ganuda/assist/core/frontend/components/
ls -la /ganuda/assist/core/frontend/lib/
ls -la /ganuda/assist/core/sql/
ls -la /ganuda/assist/core/config/
ls -la /ganuda/assist/core/i18n/
```

All directories and files listed in the Directory Structure section must exist.

### 2. Python Imports Succeed

```bash
cd /ganuda/assist/core
python3 -c "
from backend.config import AssistConfig
from backend.database import init_database, get_db, Base
from backend.security import init_security, hash_password, verify_password, create_access_token
from backend.base_calculator import BaseCalculator, CalculationResult
from backend.base_crisis import BaseCrisisDetector, CrisisResult, check_message
from backend.base_wizard import WizardDefinition, WizardEngine
print('All imports successful')
"
```

This MUST print "All imports successful" with zero errors.

### 3. Config Validation

```bash
cd /ganuda/assist/core
ASSIST_DB_USER=test ASSIST_DB_PASSWORD=test ASSIST_SECRET_KEY=test_key_that_is_at_least_32_characters python3 -c "
from backend.config import AssistConfig
config = AssistConfig()
assert config.db_host == '192.168.132.222'
assert config.db_name == 'zammad_production'
assert config.vertical_name == 'base'
assert 'postgresql://' in config.database_url
print('Config validation passed')
"
```

Also verify that config FAILS without required fields:

```bash
cd /ganuda/assist/core
python3 -c "
from backend.config import AssistConfig
try:
    config = AssistConfig()
    print('FAIL: Should have raised validation error')
except Exception as e:
    print(f'PASS: Config correctly requires credentials: {type(e).__name__}')
"
```

### 4. Crisis Detection Works

```bash
cd /ganuda/assist/core
python3 -c "
from backend.base_crisis import BaseCrisisDetector
detector = BaseCrisisDetector('config/crisis_patterns.yaml')
result = detector.detect('I want to kill myself')
assert result.is_crisis == True
assert result.severity == 'critical'
print(f'Crisis detection: category={result.category}, severity={result.severity}')

safe = detector.detect('I want to check my benefits')
assert safe.is_crisis == False
print('Safe message correctly not flagged')
print('Crisis detection verification PASSED')
"
```

### 5. YAML Configs Load

```bash
cd /ganuda/assist/core
python3 -c "
import yaml
for f in ['config/crisis_patterns.yaml', 'config/pii_entities.yaml', 'config/council_context.yaml', 'i18n/chr.yaml', 'i18n/en.yaml']:
    with open(f) as fh:
        data = yaml.safe_load(fh)
    print(f'{f}: OK ({len(str(data))} chars)')
print('All YAML configs valid')
"
```

### 6. No Hardcoded Credentials

```bash
# This must return ZERO matches
grep -rn "password" /ganuda/assist/core/backend/ | grep -v "password_hash" | grep -v "db_password" | grep -v "validate_password" | grep -v "hash_password" | grep -v "verify_password" | grep -v "plain_password" | grep -v "hashed_password" | grep -v '""' | grep -v "Field(" | grep -v "# " | grep -v "def " | grep -v "str  #"
```

If any match shows an actual hardcoded password value, the task FAILS.

### 7. VetAssist Untouched

```bash
cd /ganuda/vetassist
git diff --stat
# Must show NO changes to VetAssist files
```

### 8. SQL Syntax Valid

```bash
# Parse-check only — do NOT execute against production without TPM approval
cd /ganuda/assist/core
python3 -c "
with open('sql/assist_core_schema.sql') as f:
    sql = f.read()
assert 'CREATE TABLE IF NOT EXISTS assist_users' in sql
assert 'CREATE TABLE IF NOT EXISTS assist_sessions' in sql
assert 'CREATE TABLE IF NOT EXISTS assist_audit' in sql
assert 'gen_random_uuid' in sql
assert 'ON DELETE CASCADE' in sql
print('SQL schema syntax check PASSED')
"
```

---

## Security Requirements

**Crawdad-approved constraints — these are non-negotiable:**

1. **No hardcoded credentials.** `db_user`, `db_password`, `secret_key` use Pydantic `Field(...)` which REQUIRES environment variables. There are NO defaults for these fields.

2. **No plaintext passwords in logs.** The PII service redacts before logging. The audit table stores `ip_hash` (SHA-256), never raw IPs.

3. **JWT tokens expire.** Default 24 hours, configurable via `access_token_expire_minutes`.

4. **Password strength enforced.** Minimum 8 chars, must contain letter + number.

5. **CORS locked down.** Default is `["http://localhost:3000"]` only. Verticals explicitly add their domains — no wildcards in production.

6. **Crisis detection has hardcoded fallback.** Even if the YAML file is missing or corrupt, the `_load_safety_fallback()` method ensures suicide/self-harm patterns are ALWAYS active. This is a safety invariant that must never be removed.

7. **SQL uses `IF NOT EXISTS`.** Schema creation is idempotent. Running it twice does not break anything.

8. **Session data is JSONB.** No schema assumptions about what verticals store in sessions. The core just provides the container.

---

## Dependencies

### What Phase 2 Needs From This (VetAssist Migration)

Phase 2 will make VetAssist inherit from this core. It needs:

- `AssistConfig` to subclass with VA-specific fields (`VA_LIGHTHOUSE_API_KEY`, etc.)
- `BaseCalculator` to subclass for `VADisabilityCalculator`
- `BaseCouncilChatService` to subclass with VA context, CFR citation patterns, raven-first priority
- `BaseCrisisDetector` loaded with VetAssist-specific patterns (MST, veteran substance abuse)
- `BasePIIService` loaded with VetAssist entity list (minus DATE_TIME and LOCATION)
- `WizardEngine` loaded with VetAssist claims wizard YAML
- `BaseApiClient` extended with VA-specific endpoints
- `assist_users` table (VetAssist may migrate from its own `users` table or use dual-read)

### What Phase 3 Needs From This (New Vertical Scaffold)

Phase 3 creates a new vertical (e.g., HousingAssist, ElderAssist). It needs:

- `create_assist_app()` to build a ready-to-run FastAPI app
- `AssistConfig` subclass with vertical-specific fields
- `BaseCalculator` subclass for the vertical's computation
- YAML wizard definitions for the vertical's guided workflow
- YAML crisis patterns extended with domain-specific triggers
- Cherokee i18n translations from `core/i18n/chr.yaml` plus vertical additions
- `base_app.py` router mounting for vertical-specific API endpoints

---

## Estimated Effort

- **Backend files**: 10 files, ~900 lines total
- **Frontend files**: 7 files, ~700 lines total
- **SQL**: 1 file, ~50 lines
- **YAML configs**: 5 files, ~150 lines total
- **Estimated time**: 4-6 hours for an experienced Jr

---

## Notes for the Jr

1. **Read the VetAssist source files FIRST.** Every backend file in this instruction was designed by reading the VetAssist equivalent and asking: "What is VA-specific and what is universal?" If you skip reading the source, you will miss context.

2. **The `base_` prefix means abstract/configurable.** `base_calculator.py` is NOT a calculator — it is the template all calculators inherit from. `base_crisis.py` is NOT a crisis detector — it is the engine that loads patterns from YAML.

3. **Cherokee i18n is NOT optional.** The `chr.yaml` file ships with core. Every vertical inherits it. If you are building UI, check for the `i18n_key` field on wizard steps and render the Cherokee translation when `preferred_language === 'chr'`.

4. **Test with missing env vars.** The config MUST fail loudly if `ASSIST_DB_USER`, `ASSIST_DB_PASSWORD`, or `ASSIST_SECRET_KEY` are not set. This is intentional. Never add defaults to work around it.

5. **Do not run the SQL against production without TPM approval.** Parse-check it. Validate the syntax. But the actual `psql` execution happens in a separate, supervised step.

---

*Tools that make broken systems less broken, built by people who believe the world is worth fixing.*

*ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ — For the Seven Generations*
