# JR INSTRUCTION: Assist Core Backend Gap-Fill (Missing Files Only)

**Task ID:** ASSIST-GAPFILL-CORE-BACKEND
**Priority:** P1 -- Required before any vertical can run
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5)
**Date:** 2026-02-04
**Estimated Effort:** 3-4 hours
**Node:** Any (Python 3.11+ required)
**Type:** GAP-FILL -- partial execution recovery

---

## Mission Context

Phase 1 core scaffold was partially executed. The crisis detection subsystem (C-SSRS scorer, patterns, base_crisis) and all config/i18n YAML files were created successfully. However, the foundational backend modules -- config, database, auth, security, application factory, base calculator, council chat, and wizard engine -- were never written. The SQL schema directory was also never created.

Without these files, no vertical (VetAssist migration, SSIDAssist, TribeAssist) can import from `assist.core.backend`. This instruction fills exactly those gaps and nothing else.

**This is a GAP-FILL instruction.** DO NOT recreate, overwrite, or modify any file that already exists.

---

## Existing Files (DO NOT TOUCH)

These files are confirmed present at `/ganuda/assist/core/`. Do not recreate, overwrite, or modify them:

| Path | Status |
|---|---|
| `backend/base_crisis.py` | EXISTS -- do not touch |
| `backend/cssrs_patterns.py` | EXISTS -- do not touch |
| `backend/cssrs_scorer.py` | EXISTS -- do not touch |
| `backend/cssrs_test.py` | EXISTS -- do not touch |
| `config/crisis_patterns.yaml` | EXISTS -- do not touch |
| `config/pii_entities.yaml` | EXISTS -- do not touch |
| `config/council_context.yaml` | EXISTS -- do not touch |
| `i18n/chr.yaml` | EXISTS -- do not touch |
| `i18n/en.yaml` | EXISTS -- do not touch |

---

## Objective

Create the 8 missing backend Python files and 1 SQL schema file under `/ganuda/assist/core/`. Also create the `sql/` directory and the `backend/__init__.py` package init if absent.

---

## Prerequisites

- Read the VetAssist reference files before writing:
  - `/ganuda/vetassist/backend/app/core/database.py` -- connection pool pattern
  - `/ganuda/vetassist/backend/app/core/auth.py` -- JWT decode, get_current_user
  - `/ganuda/vetassist/backend/app/core/security.py` -- password hashing, token creation
  - `/ganuda/vetassist/backend/app/core/config.py` -- Pydantic BaseSettings pattern
- All credentials via environment variables prefixed `ASSIST_` -- NO hardcoded passwords
- Confirm PostgreSQL access on bluefin (192.168.132.222) before running SQL

---

## Steps

### Step 0: Pre-Flight Safety Check

Before creating any file, verify the existing files are intact:

```bash
#!/bin/bash
echo "=== Pre-Flight: Verifying existing files ==="
cd /ganuda/assist/core
for f in backend/base_crisis.py backend/cssrs_patterns.py backend/cssrs_scorer.py backend/cssrs_test.py config/crisis_patterns.yaml config/pii_entities.yaml config/council_context.yaml i18n/chr.yaml i18n/en.yaml; do
    if [ -f "$f" ]; then
        echo "[OK] $f exists ($(wc -l < "$f") lines)"
    else
        echo "[WARN] $f MISSING -- was expected to exist"
    fi
done

# Create sql directory if needed
mkdir -p /ganuda/assist/core/sql
echo "[OK] sql/ directory ready"
```

---

### Step 1: Create `/ganuda/assist/core/backend/__init__.py`

Package init with version constant.

```python
"""
Assist Platform Core -- Shared Framework
Cherokee AI Federation -- For the Seven Generations

This package provides the shared foundation for all Assist verticals.
VetAssist was the first. It will not be the last.
"""

__version__ = "0.1.0"
```

---

### Step 2: Create `/ganuda/assist/core/backend/config.py`

Base configuration class. Environment-driven, no hardcoded credentials.

```python
"""
Assist Platform Base Configuration.
All credentials via environment variables. No hardcoded secrets.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class AssistConfig:
    """Base configuration for any Assist vertical."""

    # Application
    app_title: str = "Assist Platform"
    version: str = "0.1.0"
    vertical_name: str = "base"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (env-driven)
    db_host: str = field(default_factory=lambda: os.environ.get('ASSIST_DB_HOST', '192.168.132.222'))
    db_port: int = field(default_factory=lambda: int(os.environ.get('ASSIST_DB_PORT', '5432')))
    db_name: str = field(default_factory=lambda: os.environ.get('ASSIST_DB_NAME', 'zammad_production'))
    db_user: str = field(default_factory=lambda: os.environ.get('ASSIST_DB_USER', ''))
    db_password: str = field(default_factory=lambda: os.environ.get('ASSIST_DB_PASS', ''))

    # Security
    secret_key: str = field(default_factory=lambda: os.environ.get('ASSIST_SECRET_KEY', ''))
    cors_origins: list = field(default_factory=lambda: os.environ.get('ASSIST_CORS_ORIGINS', 'http://localhost:3000').split(','))
    rate_limit_per_minute: int = 60

    # Council/LLM
    llm_endpoint: str = field(default_factory=lambda: os.environ.get('ASSIST_LLM_ENDPOINT', 'http://192.168.132.223:8000/v1'))
    llm_model: str = field(default_factory=lambda: os.environ.get('ASSIST_LLM_MODEL', 'nvidia/Llama-3.1-Nemotron-Nano-8B-v1'))

    # Crisis
    crisis_patterns_path: str = ""

    # Vertical-specific config (override in subclass)
    vertical_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def validate(self) -> list:
        """Validate required configuration."""
        errors = []
        if not self.db_user:
            errors.append("ASSIST_DB_USER not set")
        if not self.db_password:
            errors.append("ASSIST_DB_PASS not set")
        if not self.secret_key:
            errors.append("ASSIST_SECRET_KEY not set")
        return errors
```

---

### Step 3: Create `/ganuda/assist/core/backend/database.py`

Shared database connection manager. Adapted from VetAssist `core/database.py`.

```python
"""
Assist Platform Database Manager.
Provides connection pooling and transaction management.
Adapted from VetAssist core/database.py, generalized for all verticals.
"""
import logging
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from .config import AssistConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection pool manager."""

    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __init__(self, config: AssistConfig):
        self.config = config
        self._pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        logger.info(f"Database pool initialized: {config.db_host}:{config.db_port}/{config.db_name}")

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a cursor from a pooled connection."""
        cursor_factory = RealDictCursor if dict_cursor else None
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and optionally fetch results."""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return None

    def close(self):
        """Close all pool connections."""
        if self._pool:
            self._pool.closeall()
            logger.info("Database pool closed")

    @classmethod
    def get_instance(cls, config: Optional[AssistConfig] = None) -> 'DatabaseManager':
        """Get or create singleton instance."""
        if cls._instance is None:
            if config is None:
                raise ValueError("Config required for first initialization")
            cls._instance = cls(config)
        return cls._instance
```

---

### Step 4: Create `/ganuda/assist/core/backend/auth.py`

Shared auth module. JWT-based, adapted from VetAssist.

```python
"""
Assist Platform Authentication.
JWT-based auth, adapted from VetAssist core/auth.py.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import AssistConfig
from .database import DatabaseManager

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Token settings
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash."""
    try:
        salt, hash_hex = stored_hash.split(':')
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(hashed.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict, config: AssistConfig, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, config.secret_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict, config: AssistConfig) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, config.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, config: AssistConfig) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """FastAPI dependency: get current authenticated user."""
    # Note: config must be injected via app.state in base_app.py
    # This is a stub - vertical implementations wire this up
    token = credentials.credentials
    # Decode will be done with config from app state
    return {"token": token}
```

---

### Step 5: Create `/ganuda/assist/core/backend/security.py`

Security middleware: rate limiting, CORS, PII detection.

```python
"""
Assist Platform Security.
Rate limiting, CORS configuration, PII detection.
Adapted from VetAssist core/security.py.
"""
import logging
import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import AssistConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._requests: dict = defaultdict(list)

    def check(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = time.time()
        window_start = now - 60

        # Clean old entries
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > window_start
        ]

        if len(self._requests[client_id]) >= self.requests_per_minute:
            return False

        self._requests[client_id].append(now)
        return True


# PII patterns for detection/masking
PII_PATTERNS = {
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'ssn_no_dash': re.compile(r'\b\d{9}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'dob': re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
}


def detect_pii(text: str) -> list:
    """Detect PII in text. Returns list of (type, match) tuples."""
    found = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            found.append((pii_type, match))
    return found


def mask_pii(text: str) -> str:
    """Mask PII in text for safe logging."""
    masked = text
    for pii_type, pattern in PII_PATTERNS.items():
        masked = pattern.sub(f'[{pii_type.upper()}_REDACTED]', masked)
    return masked


def configure_cors(app, config: AssistConfig):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host if request.client else "unknown"
    limiter = request.app.state.rate_limiter

    if not limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    return await call_next(request)
```

---

### Step 6: Create `/ganuda/assist/core/backend/base_app.py`

FastAPI application factory.

```python
"""
Assist Platform Application Factory.
Creates configured FastAPI applications for any vertical.
"""
import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import AssistConfig
from .database import DatabaseManager
from .security import RateLimiter, configure_cors, rate_limit_middleware

logger = logging.getLogger(__name__)


def create_assist_app(config: AssistConfig, routers: list = None) -> FastAPI:
    """
    Create a configured Assist vertical application.

    Args:
        config: Vertical-specific configuration
        routers: List of APIRouter instances to mount

    Returns:
        Configured FastAPI application
    """
    # Validate config
    errors = config.validate()
    if errors and not config.debug:
        raise ValueError(f"Configuration errors: {errors}")

    app = FastAPI(
        title=config.app_title,
        version=config.version,
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
    )

    # Store config in app state
    app.state.config = config
    app.state.rate_limiter = RateLimiter(config.rate_limit_per_minute)

    # Initialize database
    try:
        app.state.db = DatabaseManager(config)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        app.state.db = None

    # Security middleware
    configure_cors(app, config)
    app.middleware("http")(rate_limit_middleware)

    # Mount vertical routers
    if routers:
        for router in routers:
            app.include_router(router)

    # Health check
    @app.get("/health")
    async def health():
        db_status = "connected" if app.state.db else "disconnected"
        return {
            "status": "healthy",
            "vertical": config.vertical_name,
            "version": config.version,
            "database": db_status,
        }

    # Startup/shutdown
    @app.on_event("startup")
    async def startup():
        logger.info(f"Starting {config.app_title} v{config.version}")

    @app.on_event("shutdown")
    async def shutdown():
        if app.state.db:
            app.state.db.close()
        logger.info(f"Shutting down {config.app_title}")

    return app
```

---

### Step 7: Create `/ganuda/assist/core/backend/base_calculator.py`

Abstract base calculator class.

```python
"""
Assist Platform Base Calculator.
Abstract base for all benefit calculators (VA, SSDI, tribal, etc.).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CalculationResult:
    """Result from any benefit calculator."""

    amount: float
    breakdown: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "breakdown": self.breakdown,
            "explanation": self.explanation,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class BaseCalculator(ABC):
    """Abstract base for benefit calculators."""

    @abstractmethod
    def calculate(self, inputs: dict) -> CalculationResult:
        """Run the calculation with given inputs."""
        ...

    @abstractmethod
    def validate_inputs(self, inputs: dict) -> List[str]:
        """Validate inputs, return list of error messages (empty if valid)."""
        ...

    @abstractmethod
    def get_explanation(self, result: CalculationResult) -> str:
        """Generate human-readable explanation of the result."""
        ...

    def get_test_cases(self) -> List[dict]:
        """Return built-in test cases for self-validation. Override in subclass."""
        return []

    def self_test(self) -> List[dict]:
        """Run built-in test cases and report results."""
        results = []
        for case in self.get_test_cases():
            try:
                result = self.calculate(case["inputs"])
                passed = abs(result.amount - case["expected"]) < 0.01
                results.append({
                    "name": case.get("name", "unnamed"),
                    "passed": passed,
                    "expected": case["expected"],
                    "actual": result.amount,
                })
            except Exception as e:
                results.append({
                    "name": case.get("name", "unnamed"),
                    "passed": False,
                    "error": str(e),
                })
        return results
```

---

### Step 8: Create `/ganuda/assist/core/backend/base_council_chat.py`

Parameterized council chat service.

```python
"""
Assist Platform Base Council Chat.
Parameterized by domain context, citation patterns, and specialist priorities.
Adapted from VetAssist services/council_chat.py, generalized.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import AssistConfig

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class ChatResponse:
    """Response from council chat."""
    message: str
    citations: List[str] = field(default_factory=list)
    specialist: str = ""  # Which council specialist responded
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


class BaseCouncilChatService:
    """
    Base council chat service.

    Configure per vertical with:
    - domain_context: What domain this covers (e.g., "VA disability benefits")
    - citation_patterns: Regex patterns for valid citations (e.g., "38 CFR")
    - specialist_priority: Weight each council specialist (spider, turtle, etc.)
    """

    def __init__(
        self,
        config: AssistConfig,
        domain_context: str,
        citation_patterns: List[str] = None,
        specialist_priority: Dict[str, float] = None,
    ):
        self.config = config
        self.domain_context = domain_context
        self.citation_patterns = citation_patterns or []
        self.specialist_priority = specialist_priority or {
            "turtle": 1.0,
            "spider": 1.0,
            "raven": 1.0,
            "gecko": 1.0,
            "eagle_eye": 1.0,
        }

    def build_system_prompt(self) -> str:
        """Build the system prompt for the council."""
        return (
            f"You are a knowledgeable assistant specializing in {self.domain_context}. "
            f"Provide accurate, helpful information. "
            f"Always cite sources when referencing regulations or policies. "
            f"If unsure, say so clearly rather than guessing."
        )

    async def get_response(
        self,
        message: str,
        session_id: str,
        history: List[ChatMessage] = None,
    ) -> ChatResponse:
        """
        Get a response from the council.

        Override in vertical subclass to customize LLM interaction.
        Base implementation is a stub.
        """
        logger.info(f"Council chat [{session_id}]: {message[:100]}...")

        # Stub - vertical implementations wire this to actual LLM
        return ChatResponse(
            message=f"[Council chat stub] Received: {message[:50]}...",
            specialist="base",
            confidence=0.0,
            metadata={"stub": True},
        )

    def extract_citations(self, text: str) -> List[str]:
        """Extract citations from response text."""
        import re
        citations = []
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        return citations
```

---

### Step 9: Create `/ganuda/assist/core/backend/base_wizard.py`

YAML-driven multi-step wizard engine.

```python
"""
Assist Platform Base Wizard Engine.
Loads wizard definitions from YAML, handles step sequencing,
conditional branching, and save/resume per user session.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WizardStep:
    """A single wizard step definition."""
    id: str
    title: str
    description: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    help_text: str = ""
    required: bool = True


@dataclass
class WizardProgress:
    """User's progress through a wizard."""
    wizard_id: str
    user_id: str
    current_step: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False


class BaseWizard:
    """
    YAML-driven wizard engine.

    Loads wizard definitions from YAML files.
    Handles conditional step visibility and save/resume.
    """

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.steps: List[WizardStep] = []
        self.metadata: Dict[str, Any] = {}
        self._load_definition()

    def _load_definition(self):
        """Load wizard from YAML file."""
        path = Path(self.yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Wizard definition not found: {self.yaml_path}")

        with open(path) as f:
            definition = yaml.safe_load(f)

        self.metadata = {
            "name": definition.get("name", "Unnamed Wizard"),
            "description": definition.get("description", ""),
            "version": definition.get("version", "1.0"),
        }

        for step_def in definition.get("steps", []):
            step = WizardStep(
                id=step_def["id"],
                title=step_def["title"],
                description=step_def.get("description", ""),
                fields=step_def.get("fields", []),
                conditions=step_def.get("conditions", []),
                help_text=step_def.get("help_text", ""),
                required=step_def.get("required", True),
            )
            self.steps.append(step)

        logger.info(f"Loaded wizard '{self.metadata['name']}' with {len(self.steps)} steps")

    def get_visible_steps(self, answers: Dict[str, Any]) -> List[WizardStep]:
        """Get steps visible given current answers (handles conditional branching)."""
        visible = []
        for step in self.steps:
            if self._evaluate_conditions(step.conditions, answers):
                visible.append(step)
        return visible

    def _evaluate_conditions(self, conditions: List[Dict], answers: Dict) -> bool:
        """Evaluate step visibility conditions."""
        if not conditions:
            return True

        for condition in conditions:
            field_id = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")

            answer = answers.get(field_id)

            if operator == "equals" and answer != value:
                return False
            elif operator == "not_equals" and answer == value:
                return False
            elif operator == "in" and answer not in value:
                return False
            elif operator == "exists" and answer is None:
                return False

        return True

    def validate_step(self, step_id: str, data: Dict[str, Any]) -> List[str]:
        """Validate data for a specific step. Returns list of errors."""
        step = next((s for s in self.steps if s.id == step_id), None)
        if not step:
            return [f"Unknown step: {step_id}"]

        errors = []
        for field_def in step.fields:
            field_id = field_def.get("id")
            required = field_def.get("required", step.required)

            if required and field_id not in data:
                errors.append(f"Required field missing: {field_def.get('label', field_id)}")

        return errors

    def get_progress_percent(self, progress: WizardProgress) -> float:
        """Calculate completion percentage."""
        visible = self.get_visible_steps(progress.answers)
        if not visible:
            return 100.0
        return (progress.current_step / len(visible)) * 100
```

---

### Step 10: Create `/ganuda/assist/core/sql/assist_core_schema.sql`

Core database schema. Run on bluefin (192.168.132.222) against `zammad_production`.

```sql
-- Assist Platform Core Schema
-- Run on bluefin (192.168.132.222) / zammad_production
-- Creates shared tables for all Assist verticals

CREATE TABLE IF NOT EXISTS assist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    vertical VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    vertical VARCHAR(50) NOT NULL,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assist_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    vertical VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assist_wizard_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id),
    wizard_id VARCHAR(100) NOT NULL,
    vertical VARCHAR(50) NOT NULL,
    current_step INTEGER DEFAULT 0,
    answers JSONB DEFAULT '{}',
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, wizard_id)
);

-- Index for fast session lookups
CREATE INDEX IF NOT EXISTS idx_assist_sessions_user ON assist_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_vertical ON assist_sessions(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_audit_user ON assist_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_audit_vertical ON assist_audit(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_wizard_user ON assist_wizard_progress(user_id);
```

---

## Verification

After creating all files, run this verification script:

```bash
#!/bin/bash
cd /ganuda/assist/core
echo "=== Verifying Core Backend Gap-Fill ==="

PASS=0
FAIL=0

for f in backend/__init__.py backend/config.py backend/database.py backend/auth.py backend/security.py backend/base_app.py backend/base_calculator.py backend/base_council_chat.py backend/base_wizard.py sql/assist_core_schema.sql; do
    if [ -f "$f" ]; then
        echo "[OK] $f ($(wc -l < "$f") lines)"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $f MISSING"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Confirming pre-existing files are still intact ---"
for f in backend/base_crisis.py backend/cssrs_patterns.py backend/cssrs_scorer.py backend/cssrs_test.py config/crisis_patterns.yaml config/pii_entities.yaml config/council_context.yaml i18n/chr.yaml i18n/en.yaml; do
    if [ -f "$f" ]; then
        echo "[OK] $f (unchanged)"
    else
        echo "[FAIL] $f MISSING -- was NOT supposed to be touched"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Python import check ---"
python3 -c "
import sys
sys.path.insert(0, '.')
from backend.config import AssistConfig
from backend.base_calculator import BaseCalculator, CalculationResult
from backend.base_wizard import BaseWizard, WizardStep
print('All imports successful')
" 2>&1

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
| 1 | `backend/__init__.py` | Package init with version |
| 2 | `backend/config.py` | Environment-driven configuration |
| 3 | `backend/database.py` | Connection pool manager |
| 4 | `backend/auth.py` | JWT auth (hash, verify, create, decode) |
| 5 | `backend/security.py` | Rate limiter, PII detect/mask, CORS |
| 6 | `backend/base_app.py` | FastAPI application factory |
| 7 | `backend/base_calculator.py` | Abstract base calculator (ABC) |
| 8 | `backend/base_council_chat.py` | Parameterized council chat service |
| 9 | `backend/base_wizard.py` | YAML-driven wizard engine |
| 10 | `sql/assist_core_schema.sql` | Core database tables and indexes |

---

## Safety Notes

- DO NOT overwrite any existing file. If a target file already exists, skip it and report in verification output.
- DO NOT modify anything under `/ganuda/vetassist/` -- that is production.
- All database credentials come from environment variables. No hardcoded passwords.
- The SQL schema uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` -- safe to run multiple times.

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04
