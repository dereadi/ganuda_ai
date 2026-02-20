# JR INSTRUCTION: Assist Platform Phase 4 — Vertical Registry & Generator

**Task ID:** ASSIST-PHASE4-REGISTRY
**Priority:** P2
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5) + Council
**Date:** 2026-02-04
**Depends On:** ASSIST-PHASE1-CORE, ASSIST-PHASE2-SSIDASSIST, ASSIST-PHASE3-TRIBEASSIST

---

## Background

Phases 1-3 established the Assist Platform core framework, the SSIDAssist vertical scaffold, and the TribeAssist vertical scaffold. Each vertical follows a common directory structure, shares the core library at `/ganuda/assist/core/`, and connects to the `zammad_production` database on bluefin (192.168.132.222).

Phase 4 introduces the **meta-tooling layer**: a machine-readable registry of all verticals and shell scripts that generate, validate, and list verticals. This eliminates manual scaffold creation and ensures every vertical starts from a consistent, tested template.

### Why This Matters

Without registry and generator tooling, each new vertical requires manual directory creation, copy-paste from existing verticals, and ad-hoc validation. This leads to drift between verticals, missing files, and inconsistent config. The generator script encodes the conventions established in Phases 1-3 into an executable template. The validation script catches problems before they reach production.

---

## Files to Create

| # | File | Purpose |
|---|------|---------|
| 1 | `/ganuda/assist/verticals.yaml` | Source of truth registry for all Assist verticals |
| 2 | `/ganuda/assist/scripts/new_vertical.sh` | Generator script — creates new vertical from template |
| 3 | `/ganuda/assist/scripts/validate_vertical.sh` | Pre-launch validation — checks vertical integrity |
| 4 | `/ganuda/assist/scripts/list_verticals.sh` | Quick status listing of all registered verticals |

---

## File 1: `/ganuda/assist/verticals.yaml`

This file is the authoritative registry. All scripts read from it. When a new vertical is generated, it is appended here automatically.

```yaml
# Assist Platform Vertical Registry
# Cherokee AI Federation — For Seven Generations
#
# This file is the source of truth for all Assist platform verticals.
# Each vertical is a standalone application that shares the core framework.
#
# Status values: scaffold | development | staging | production | deprecated
# Ports: 8000-8099 reserved for Assist verticals

verticals:
  vetassist:
    display_name: "VetAssist"
    description: "VA disability claims assistance for veterans"
    path: /ganuda/vetassist
    status: production
    port: 8000
    database: zammad_production
    table_prefix: ""
    created: "2025-12-01"
    council_priority:
      gecko: 1.2
      turtle: 1.0

  ssidassist:
    display_name: "SSIDAssist"
    description: "Social Security Disability Insurance navigation"
    path: /ganuda/assist/ssidassist
    status: scaffold
    port: 8001
    database: zammad_production
    table_prefix: "ssid_"
    created: "2026-02-04"
    council_priority:
      turtle: 1.0
      gecko: 1.2
      spider: 0.8

  tribeassist:
    display_name: "TribeAssist"
    description: "Cherokee Nation services and enrollment guidance"
    path: /ganuda/assist/tribeassist
    status: scaffold
    port: 8002
    database: zammad_production
    table_prefix: "tribe_"
    created: "2026-02-04"
    council_priority:
      spider: 1.5
      raven: 1.2
      turtle: 1.0
    language: "bilingual_chr_en"
```

---

## File 2: `/ganuda/assist/scripts/new_vertical.sh`

This is the generator script. It must be a **complete, working bash script** — not pseudocode. Every file it creates uses heredoc with proper template substitution. Mark it executable after creation (`chmod +x`).

```bash
#!/bin/bash
# Assist Platform — New Vertical Generator
# Usage: ./new_vertical.sh <vertical_name> [display_name] [port]
#
# Creates a new vertical scaffold from the core template.
# Cherokee AI Federation — For Seven Generations
# ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ

set -euo pipefail

ASSIST_ROOT="/ganuda/assist"
REGISTRY="${ASSIST_ROOT}/verticals.yaml"
DB_HOST="192.168.132.222"
DB_NAME="zammad_production"

# ──────────────────────────────────────────────
# Helper: find the next available port in 8000-8099
# ──────────────────────────────────────────────
next_available_port() {
    local used_ports
    used_ports=$(python3 -c "
import yaml, sys
try:
    with open('${REGISTRY}') as f:
        data = yaml.safe_load(f)
    ports = sorted([v.get('port', 0) for v in data.get('verticals', {}).values()])
    print(' '.join(str(p) for p in ports))
except Exception:
    print('8000')
")
    local next_port=8000
    for p in $used_ports; do
        if [[ "$next_port" -le "$p" ]]; then
            next_port=$((p + 1))
        fi
    done
    # Stay within reserved range
    if [[ "$next_port" -gt 8099 ]]; then
        echo "ERROR: No available ports in 8000-8099 range" >&2
        exit 1
    fi
    echo "$next_port"
}

# ──────────────────────────────────────────────
# Argument parsing
# ──────────────────────────────────────────────
VERTICAL_NAME="${1:?Usage: $0 <vertical_name> [display_name] [port]}"
DISPLAY_NAME="${2:-${VERTICAL_NAME^}Assist}"
PORT="${3:-$(next_available_port)}"

VERTICAL_DIR="${ASSIST_ROOT}/${VERTICAL_NAME}"
CORE_DIR="${ASSIST_ROOT}/core"
TABLE_PREFIX="${VERTICAL_NAME}_"
CREATED_DATE="$(date +%Y-%m-%d)"

# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────
if [[ -d "$VERTICAL_DIR" ]]; then
    echo "ERROR: Directory already exists: $VERTICAL_DIR"
    exit 1
fi

if ! [[ "$VERTICAL_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "ERROR: Vertical name must start with a lowercase letter and contain only lowercase alphanumeric characters and underscores"
    exit 1
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 8000 ]] || [[ "$PORT" -gt 8099 ]]; then
    echo "ERROR: Port must be a number between 8000 and 8099"
    exit 1
fi

if ! [[ -f "$REGISTRY" ]]; then
    echo "ERROR: Registry file not found: $REGISTRY"
    echo "Phase 4 requires verticals.yaml to exist. Create it first."
    exit 1
fi

# Check name not already registered
if python3 -c "
import yaml, sys
with open('${REGISTRY}') as f:
    data = yaml.safe_load(f)
if '${VERTICAL_NAME}' in data.get('verticals', {}):
    sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
    echo "ERROR: Vertical '${VERTICAL_NAME}' is already registered in ${REGISTRY}"
    exit 1
fi

# Check port not already in use
if python3 -c "
import yaml, sys
with open('${REGISTRY}') as f:
    data = yaml.safe_load(f)
for name, v in data.get('verticals', {}).items():
    if v.get('port') == ${PORT}:
        print(f'Port ${PORT} already used by {name}', file=sys.stderr)
        sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
    echo "ERROR: Port ${PORT} is already assigned to another vertical"
    exit 1
fi

echo "========================================"
echo "Creating Assist vertical: $DISPLAY_NAME"
echo "  Name:      $VERTICAL_NAME"
echo "  Directory: $VERTICAL_DIR"
echo "  Port:      $PORT"
echo "  Prefix:    $TABLE_PREFIX"
echo "  Date:      $CREATED_DATE"
echo "========================================"
echo ""

# ──────────────────────────────────────────────
# Create directory structure
# ──────────────────────────────────────────────
echo "[1/8] Creating directory structure..."
mkdir -p "$VERTICAL_DIR"/{backend/{services,api/v1/endpoints},frontend/app,config/wizards,sql}

# ──────────────────────────────────────────────
# Backend __init__.py files
# ──────────────────────────────────────────────
echo "[2/8] Creating Python package init files..."

cat > "$VERTICAL_DIR/backend/__init__.py" << 'INITEOF'
# Assist Platform Vertical — Backend Package
INITEOF

cat > "$VERTICAL_DIR/backend/services/__init__.py" << 'INITEOF'
# Assist Platform Vertical — Services Package
INITEOF

cat > "$VERTICAL_DIR/backend/api/__init__.py" << 'INITEOF'
# Assist Platform Vertical — API Package
INITEOF

cat > "$VERTICAL_DIR/backend/api/v1/__init__.py" << 'INITEOF'
# Assist Platform Vertical — API v1 Package
INITEOF

cat > "$VERTICAL_DIR/backend/api/v1/endpoints/__init__.py" << 'INITEOF'
# Assist Platform Vertical — Endpoints Package
INITEOF

# ──────────────────────────────────────────────
# Backend main.py
# ──────────────────────────────────────────────
echo "[3/8] Creating backend main.py..."

cat > "$VERTICAL_DIR/backend/main.py" << MAINEOF
"""
${DISPLAY_NAME} — Assist Platform Vertical
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add core to path
sys.path.insert(0, "${CORE_DIR}")

app = FastAPI(
    title="${DISPLAY_NAME}",
    description="${DISPLAY_NAME} — Assist Platform Vertical",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "vertical": "${VERTICAL_NAME}",
        "display_name": "${DISPLAY_NAME}",
        "version": "0.1.0",
    }


@app.get("/api/v1/info")
async def vertical_info():
    return {
        "vertical": "${VERTICAL_NAME}",
        "display_name": "${DISPLAY_NAME}",
        "port": ${PORT},
        "database": "${DB_NAME}",
        "table_prefix": "${TABLE_PREFIX}",
    }


# Import and include endpoint routers here as the vertical grows:
# from api.v1.endpoints import claims, chat, documents
# app.include_router(claims.router, prefix="/api/v1/claims", tags=["claims"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=${PORT})
MAINEOF

# ──────────────────────────────────────────────
# Backend config.py
# ──────────────────────────────────────────────
echo "[4/8] Creating backend config.py..."

cat > "$VERTICAL_DIR/backend/config.py" << CONFEOF
"""
${DISPLAY_NAME} — Configuration
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
"""
import os

# Vertical identity
VERTICAL_NAME = "${VERTICAL_NAME}"
DISPLAY_NAME = "${DISPLAY_NAME}"
TABLE_PREFIX = "${TABLE_PREFIX}"

# Server
HOST = os.getenv("${VERTICAL_NAME^^}_HOST", "0.0.0.0")
PORT = int(os.getenv("${VERTICAL_NAME^^}_PORT", "${PORT}"))
DEBUG = os.getenv("${VERTICAL_NAME^^}_DEBUG", "false").lower() == "true"

# Database — credentials loaded from environment, never hardcoded
DB_HOST = os.getenv("ASSIST_DB_HOST", "${DB_HOST}")
DB_PORT = int(os.getenv("ASSIST_DB_PORT", "5432"))
DB_NAME = os.getenv("ASSIST_DB_NAME", "${DB_NAME}")
DB_USER = os.getenv("ASSIST_DB_USER", "")
DB_PASS = os.getenv("ASSIST_DB_PASS", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Core framework path
CORE_DIR = "${CORE_DIR}"

# Crisis detection — all Assist verticals must support this
CRISIS_DETECTION_ENABLED = True
CRISIS_PATTERNS_FILE = os.path.join(
    "${VERTICAL_DIR}", "config", "crisis_patterns.yaml"
)

# Council context
COUNCIL_CONTEXT_FILE = os.path.join(
    "${VERTICAL_DIR}", "config", "council_context.yaml"
)
CONFEOF

# ──────────────────────────────────────────────
# Backend service stubs
# ──────────────────────────────────────────────
echo "[5/8] Creating service and endpoint stubs..."

cat > "$VERTICAL_DIR/backend/services/claims_service.py" << SVCEOF
"""
${DISPLAY_NAME} — Claims Service Stub
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
Implement domain-specific claims logic here.
"""
import sys
sys.path.insert(0, "${CORE_DIR}")


class ClaimsService:
    """Handle claims processing for ${DISPLAY_NAME}."""

    def __init__(self):
        self.table_prefix = "${TABLE_PREFIX}"

    async def get_claim(self, claim_id: int) -> dict:
        """Retrieve a single claim by ID."""
        raise NotImplementedError("Implement in vertical-specific service")

    async def list_claims(self, user_id: int, limit: int = 50) -> list:
        """List claims for a user."""
        raise NotImplementedError("Implement in vertical-specific service")

    async def create_claim(self, user_id: int, data: dict) -> dict:
        """Create a new claim."""
        raise NotImplementedError("Implement in vertical-specific service")
SVCEOF

cat > "$VERTICAL_DIR/backend/services/chat_service.py" << CHATEOF
"""
${DISPLAY_NAME} — Chat Service Stub
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
Implement AI chat and crisis detection logic here.
"""
import os
import sys
import yaml

sys.path.insert(0, "${CORE_DIR}")


class ChatService:
    """Handle AI-assisted chat for ${DISPLAY_NAME}."""

    def __init__(self):
        self.table_prefix = "${TABLE_PREFIX}"
        self.crisis_patterns = self._load_crisis_patterns()

    def _load_crisis_patterns(self) -> list:
        """Load crisis detection patterns from config."""
        config_path = os.path.join(
            "${VERTICAL_DIR}", "config", "crisis_patterns.yaml"
        )
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return data.get("patterns", [])
        except FileNotFoundError:
            return []

    async def process_message(self, user_id: int, message: str) -> dict:
        """Process an incoming chat message."""
        # Crisis detection runs FIRST on every message
        crisis_check = self._check_crisis(message)
        if crisis_check["is_crisis"]:
            return {
                "response": crisis_check["response"],
                "is_crisis": True,
                "crisis_type": crisis_check["type"],
            }

        raise NotImplementedError("Implement AI chat in vertical-specific service")

    def _check_crisis(self, message: str) -> dict:
        """Check message for crisis indicators. This is a safety-critical function."""
        message_lower = message.lower()
        for pattern in self.crisis_patterns:
            for trigger in pattern.get("triggers", []):
                if trigger.lower() in message_lower:
                    return {
                        "is_crisis": True,
                        "type": pattern.get("type", "unknown"),
                        "response": pattern.get("response", "If you are in crisis, please call 988 (Suicide & Crisis Lifeline) or 911."),
                    }
        return {"is_crisis": False, "type": None, "response": None}
CHATEOF

# Endpoint stub
cat > "$VERTICAL_DIR/backend/api/v1/endpoints/health.py" << HEALTHEOF
"""
${DISPLAY_NAME} — Health Endpoint
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "vertical": "${VERTICAL_NAME}",
        "display_name": "${DISPLAY_NAME}",
    }
HEALTHEOF

cat > "$VERTICAL_DIR/backend/api/v1/endpoints/claims.py" << CLAIMEOF
"""
${DISPLAY_NAME} — Claims Endpoints Stub
Cherokee AI Federation — For Seven Generations

Auto-generated by new_vertical.sh on ${CREATED_DATE}
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def list_claims():
    """List claims — implement with ClaimsService."""
    return {"claims": [], "message": "Not yet implemented"}


@router.get("/{claim_id}")
async def get_claim(claim_id: int):
    """Get a single claim — implement with ClaimsService."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
CLAIMEOF

# ──────────────────────────────────────────────
# Frontend files
# ──────────────────────────────────────────────
echo "[6/8] Creating frontend templates..."

cat > "$VERTICAL_DIR/frontend/app/layout.tsx" << LAYOUTEOF
/**
 * ${DISPLAY_NAME} — Root Layout
 * Cherokee AI Federation — For Seven Generations
 *
 * Auto-generated by new_vertical.sh on ${CREATED_DATE}
 */
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "${DISPLAY_NAME}",
  description: "${DISPLAY_NAME} — Assist Platform Vertical",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
LAYOUTEOF

cat > "$VERTICAL_DIR/frontend/app/page.tsx" << PAGEEOF
/**
 * ${DISPLAY_NAME} — Home Page
 * Cherokee AI Federation — For Seven Generations
 *
 * Auto-generated by new_vertical.sh on ${CREATED_DATE}
 */
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">${DISPLAY_NAME}</h1>
      <p className="text-lg text-gray-600 mb-8">
        Assist Platform Vertical — Scaffold
      </p>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-md">
        <p className="text-sm text-blue-800">
          This vertical was generated on ${CREATED_DATE}.
          Implement your domain-specific UI here.
        </p>
      </div>
    </main>
  );
}
PAGEEOF

# ──────────────────────────────────────────────
# Config files
# ──────────────────────────────────────────────
echo "[7/8] Creating config files..."

cat > "$VERTICAL_DIR/config/crisis_patterns.yaml" << 'CRISISEOF'
# Crisis Detection Patterns
# Cherokee AI Federation — For Seven Generations
#
# These patterns trigger immediate crisis intervention responses.
# This is a SAFETY-CRITICAL file. Changes require council review.
#
# Every Assist vertical MUST have crisis detection active.
# If you are unsure whether a pattern belongs here, ADD IT.

patterns:
  - type: suicidal_ideation
    severity: critical
    triggers:
      - "want to kill myself"
      - "want to die"
      - "end my life"
      - "better off dead"
      - "no reason to live"
      - "suicide"
      - "suicidal"
    response: >-
      I hear you, and I want you to know that help is available right now.
      Please contact the 988 Suicide & Crisis Lifeline by calling or texting 988.
      Veterans can press 1 for the Veterans Crisis Line.
      You can also chat at 988lifeline.org.
      If you are in immediate danger, please call 911.

  - type: self_harm
    severity: critical
    triggers:
      - "hurt myself"
      - "harm myself"
      - "cutting myself"
      - "self harm"
      - "self-harm"
    response: >-
      I am concerned about your safety. Please reach out to the 988 Suicide
      & Crisis Lifeline by calling or texting 988. You deserve support right now.

  - type: domestic_violence
    severity: high
    triggers:
      - "being abused"
      - "hitting me"
      - "domestic violence"
      - "afraid of my partner"
      - "spouse is violent"
    response: >-
      Your safety matters. Please contact the National Domestic Violence Hotline
      at 1-800-799-7233 (SAFE) or text START to 88788.
      If you are in immediate danger, please call 911.

  - type: homelessness_crisis
    severity: high
    triggers:
      - "sleeping outside"
      - "about to be homeless"
      - "living in my car"
      - "nowhere to go"
      - "eviction tomorrow"
    response: >-
      I understand this is an urgent situation. Please contact 211 (dial 2-1-1)
      for immediate shelter and housing assistance in your area.
      Veterans can also call the National Call Center for Homeless Veterans
      at 1-877-4AID-VET (1-877-424-3838).
CRISISEOF

cat > "$VERTICAL_DIR/config/council_context.yaml" << COUNCILEOF
# Council Context for ${DISPLAY_NAME}
# Cherokee AI Federation — For Seven Generations
#
# This file defines how the AI Council weights decisions for this vertical.
# Auto-generated by new_vertical.sh on ${CREATED_DATE}

vertical: ${VERTICAL_NAME}
display_name: "${DISPLAY_NAME}"

# Council member priority weights for this vertical
# Higher weight = more influence on decisions in this domain
council_priority:
  turtle: 1.0    # Deliberation, caution
  gecko: 1.0     # Adaptation, pattern recognition
  spider: 0.8    # Connection, network thinking
  raven: 0.8     # Communication, translation

# Domain-specific context the council should consider
domain_context:
  description: "${DISPLAY_NAME} vertical for the Assist Platform"
  regulatory_framework: "TBD — configure for your vertical's regulatory domain"
  sensitivity_level: "high"
  requires_audit_trail: true

# Safety constraints — these cannot be overridden by the council
safety:
  crisis_detection: required
  pii_protection: required
  audit_logging: required
  max_ai_confidence_for_action: 0.85
COUNCILEOF

cat > "$VERTICAL_DIR/config/wizards/.gitkeep" << 'KEEPEOF'
KEEPEOF

# ──────────────────────────────────────────────
# SQL schema
# ──────────────────────────────────────────────
echo "[8/8] Creating SQL schema..."

cat > "$VERTICAL_DIR/sql/${VERTICAL_NAME}_schema.sql" << SQLEOF
-- ${DISPLAY_NAME} Database Schema
-- Cherokee AI Federation — For Seven Generations
--
-- Auto-generated by new_vertical.sh on ${CREATED_DATE}
-- Database: ${DB_NAME} on ${DB_HOST}
-- Table prefix: ${TABLE_PREFIX}
--
-- Run: psql -h ${DB_HOST} -d ${DB_NAME} -f ${VERTICAL_DIR}/sql/${VERTICAL_NAME}_schema.sql

-- Users / Profiles
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}users_email ON ${TABLE_PREFIX}users(email);

-- Claims
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}claims (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES ${TABLE_PREFIX}users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}claims_user ON ${TABLE_PREFIX}claims(user_id);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}claims_status ON ${TABLE_PREFIX}claims(status);

-- Documents
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}documents (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER REFERENCES ${TABLE_PREFIX}claims(id),
    user_id INTEGER REFERENCES ${TABLE_PREFIX}users(id),
    filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    ocr_text TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}docs_claim ON ${TABLE_PREFIX}documents(claim_id);

-- Chat History
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES ${TABLE_PREFIX}users(id),
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    is_crisis BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}chat_user ON ${TABLE_PREFIX}chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}chat_session ON ${TABLE_PREFIX}chat_history(session_id);

-- Educational Content
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}educational_content (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}edu_slug ON ${TABLE_PREFIX}educational_content(slug);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}edu_category ON ${TABLE_PREFIX}educational_content(category);

-- Audit Trail (required by council safety policy)
CREATE TABLE IF NOT EXISTS ${TABLE_PREFIX}audit_trail (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}audit_user ON ${TABLE_PREFIX}audit_trail(user_id);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}audit_action ON ${TABLE_PREFIX}audit_trail(action);
CREATE INDEX IF NOT EXISTS idx_${TABLE_PREFIX}audit_time ON ${TABLE_PREFIX}audit_trail(created_at);
SQLEOF

# ──────────────────────────────────────────────
# Register in verticals.yaml
# ──────────────────────────────────────────────
echo ""
echo "Registering in ${REGISTRY}..."

python3 << REGEOF
import yaml

registry_path = "${REGISTRY}"
with open(registry_path) as f:
    data = yaml.safe_load(f)

if "verticals" not in data:
    data["verticals"] = {}

data["verticals"]["${VERTICAL_NAME}"] = {
    "display_name": "${DISPLAY_NAME}",
    "description": "${DISPLAY_NAME} — Assist Platform Vertical",
    "path": "${VERTICAL_DIR}",
    "status": "scaffold",
    "port": ${PORT},
    "database": "${DB_NAME}",
    "table_prefix": "${TABLE_PREFIX}",
    "created": "${CREATED_DATE}",
    "council_priority": {
        "turtle": 1.0,
        "gecko": 1.0,
    },
}

with open(registry_path, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"  Registered '${VERTICAL_NAME}' in {registry_path}")
REGEOF

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
echo ""
echo "========================================"
echo "Vertical '${VERTICAL_NAME}' created successfully."
echo "========================================"
echo ""
echo "Directory structure:"
find "$VERTICAL_DIR" -type f | sort | while read -r filepath; do
    echo "  $filepath"
done
echo ""
echo "Next steps:"
echo "  1. Edit config files in ${VERTICAL_DIR}/config/"
echo "  2. Implement services in ${VERTICAL_DIR}/backend/services/"
echo "  3. Design frontend in ${VERTICAL_DIR}/frontend/app/"
echo "  4. Run SQL schema:"
echo "     psql -h ${DB_HOST} -d ${DB_NAME} -f ${VERTICAL_DIR}/sql/${VERTICAL_NAME}_schema.sql"
echo "  5. Validate:"
echo "     ${ASSIST_ROOT}/scripts/validate_vertical.sh ${VERTICAL_NAME}"
echo ""
echo "For Seven Generations — ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ"
```

**Important:** After creating this file, run `chmod +x /ganuda/assist/scripts/new_vertical.sh`.

---

## File 3: `/ganuda/assist/scripts/validate_vertical.sh`

This is the validation script. It must be a **complete, working bash script** with all checks implemented. Mark it executable after creation (`chmod +x`).

```bash
#!/bin/bash
# Assist Platform — Vertical Validation Script
# Usage: ./validate_vertical.sh <vertical_name>
#
# Checks that a vertical is properly configured and ready for development/deployment.
# Cherokee AI Federation — For Seven Generations

set -euo pipefail

VERTICAL_NAME="${1:?Usage: $0 <vertical_name>}"
ASSIST_ROOT="/ganuda/assist"
VERTICAL_DIR="${ASSIST_ROOT}/${VERTICAL_NAME}"
REGISTRY="${ASSIST_ROOT}/verticals.yaml"
ERRORS=0
WARNINGS=0
CHECKS=0

# Colors for output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

pass_check() {
    CHECKS=$((CHECKS + 1))
    echo -e "  ${GREEN}PASS${NC}: $1"
}

fail_check() {
    CHECKS=$((CHECKS + 1))
    ERRORS=$((ERRORS + 1))
    echo -e "  ${RED}FAIL${NC}: $1"
}

warn_check() {
    CHECKS=$((CHECKS + 1))
    WARNINGS=$((WARNINGS + 1))
    echo -e "  ${YELLOW}WARN${NC}: $1"
}

echo "========================================"
echo "Validating vertical: $VERTICAL_NAME"
echo "Directory: $VERTICAL_DIR"
echo "========================================"
echo ""

# ──────────────────────────────────────────────
# Check 1: Directory exists
# ──────────────────────────────────────────────
echo "Check 1: Directory structure"
if [[ -d "$VERTICAL_DIR" ]]; then
    pass_check "Vertical directory exists: $VERTICAL_DIR"
else
    fail_check "Vertical directory does not exist: $VERTICAL_DIR"
    echo ""
    echo "Cannot continue validation without the directory."
    exit 1
fi

for subdir in backend backend/services backend/api backend/api/v1 backend/api/v1/endpoints frontend frontend/app config sql; do
    if [[ -d "$VERTICAL_DIR/$subdir" ]]; then
        pass_check "Subdirectory exists: $subdir/"
    else
        fail_check "Missing subdirectory: $subdir/"
    fi
done

# ──────────────────────────────────────────────
# Check 2: Required files exist
# ──────────────────────────────────────────────
echo ""
echo "Check 2: Required files"

required_files=(
    "backend/main.py"
    "backend/config.py"
)

for rfile in "${required_files[@]}"; do
    if [[ -f "$VERTICAL_DIR/$rfile" ]]; then
        pass_check "Required file exists: $rfile"
    else
        fail_check "Missing required file: $rfile"
    fi
done

# At least one service
service_count=$(find "$VERTICAL_DIR/backend/services" -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)
if [[ "$service_count" -gt 0 ]]; then
    pass_check "At least one service file found ($service_count)"
else
    fail_check "No service files in backend/services/"
fi

# At least one endpoint
endpoint_count=$(find "$VERTICAL_DIR/backend/api/v1/endpoints" -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)
if [[ "$endpoint_count" -gt 0 ]]; then
    pass_check "At least one endpoint file found ($endpoint_count)"
else
    fail_check "No endpoint files in backend/api/v1/endpoints/"
fi

# ──────────────────────────────────────────────
# Check 3: Config YAML files are valid
# ──────────────────────────────────────────────
echo ""
echo "Check 3: Config YAML validation"

for yaml_file in "$VERTICAL_DIR"/config/*.yaml; do
    if [[ -f "$yaml_file" ]]; then
        basename_file=$(basename "$yaml_file")
        if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            pass_check "Valid YAML: config/$basename_file"
        else
            fail_check "Invalid YAML: config/$basename_file"
        fi
    fi
done

# Check crisis_patterns.yaml specifically
if [[ -f "$VERTICAL_DIR/config/crisis_patterns.yaml" ]]; then
    pattern_count=$(python3 -c "
import yaml
with open('$VERTICAL_DIR/config/crisis_patterns.yaml') as f:
    data = yaml.safe_load(f)
patterns = data.get('patterns', [])
print(len(patterns))
" 2>/dev/null || echo "0")
    if [[ "$pattern_count" -gt 0 ]]; then
        pass_check "Crisis patterns loaded: $pattern_count pattern(s)"
    else
        fail_check "Crisis patterns file exists but contains no patterns"
    fi
else
    fail_check "Missing critical file: config/crisis_patterns.yaml"
fi

# Check council_context.yaml
if [[ -f "$VERTICAL_DIR/config/council_context.yaml" ]]; then
    pass_check "Council context file exists"
else
    warn_check "Missing config/council_context.yaml (recommended)"
fi

# ──────────────────────────────────────────────
# Check 4: SQL schema file exists
# ──────────────────────────────────────────────
echo ""
echo "Check 4: SQL schema"

schema_file="$VERTICAL_DIR/sql/${VERTICAL_NAME}_schema.sql"
if [[ -f "$schema_file" ]]; then
    pass_check "Schema file exists: sql/${VERTICAL_NAME}_schema.sql"
    # Check it has CREATE TABLE statements
    table_count=$(grep -c "CREATE TABLE" "$schema_file" 2>/dev/null || echo "0")
    if [[ "$table_count" -gt 0 ]]; then
        pass_check "Schema defines $table_count table(s)"
    else
        warn_check "Schema file exists but contains no CREATE TABLE statements"
    fi
else
    fail_check "Missing schema file: sql/${VERTICAL_NAME}_schema.sql"
fi

# ──────────────────────────────────────────────
# Check 5: Database tables exist (if schema was applied)
# ──────────────────────────────────────────────
echo ""
echo "Check 5: Database tables (non-blocking)"

# Read table_prefix from registry
TABLE_PREFIX=$(python3 -c "
import yaml
with open('${REGISTRY}') as f:
    data = yaml.safe_load(f)
v = data.get('verticals', {}).get('${VERTICAL_NAME}', {})
print(v.get('table_prefix', '${VERTICAL_NAME}_'))
" 2>/dev/null || echo "${VERTICAL_NAME}_")

# Attempt database check — this is non-blocking since schema may not be applied yet
DB_CHECK=$(python3 << DBEOF 2>/dev/null || echo "SKIP"
import os
try:
    import psycopg2
    db_user = os.environ.get("ASSIST_DB_USER", "")
    db_pass = os.environ.get("ASSIST_DB_PASS", "")
    if not db_user or not db_pass:
        print("SKIP")
    else:
        conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            dbname="zammad_production",
            user=db_user,
            password=db_pass,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE %s",
            ("${TABLE_PREFIX}%",)
        )
        tables = [row[0] for row in cur.fetchall()]
        conn.close()
        if tables:
            print("FOUND:" + ",".join(tables))
        else:
            print("NONE")
except ImportError:
    print("SKIP")
except Exception as e:
    print(f"ERROR:{e}")
DBEOF
)

if [[ "$DB_CHECK" == "SKIP" ]]; then
    warn_check "Database check skipped (no credentials or psycopg2 not available)"
elif [[ "$DB_CHECK" == FOUND:* ]]; then
    tables="${DB_CHECK#FOUND:}"
    table_list_count=$(echo "$tables" | tr ',' '\n' | wc -l)
    pass_check "Database has $table_list_count table(s) with prefix '${TABLE_PREFIX}'"
elif [[ "$DB_CHECK" == "NONE" ]]; then
    warn_check "No database tables found with prefix '${TABLE_PREFIX}' (schema may not be applied yet)"
elif [[ "$DB_CHECK" == ERROR:* ]]; then
    warn_check "Database connection error: ${DB_CHECK#ERROR:}"
fi

# ──────────────────────────────────────────────
# Check 6: Health endpoint responds (if running)
# ──────────────────────────────────────────────
echo ""
echo "Check 6: Health endpoint (non-blocking)"

# Read port from registry
VERTICAL_PORT=$(python3 -c "
import yaml
with open('${REGISTRY}') as f:
    data = yaml.safe_load(f)
v = data.get('verticals', {}).get('${VERTICAL_NAME}', {})
print(v.get('port', 0))
" 2>/dev/null || echo "0")

if [[ "$VERTICAL_PORT" -gt 0 ]]; then
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://localhost:${VERTICAL_PORT}/health" 2>/dev/null || echo "000")
    if [[ "$HEALTH_RESPONSE" == "200" ]]; then
        pass_check "Health endpoint responds 200 on port $VERTICAL_PORT"
    elif [[ "$HEALTH_RESPONSE" == "000" ]]; then
        warn_check "Service not running on port $VERTICAL_PORT (health check skipped)"
    else
        warn_check "Health endpoint returned HTTP $HEALTH_RESPONSE on port $VERTICAL_PORT"
    fi
else
    warn_check "Could not determine port from registry"
fi

# ──────────────────────────────────────────────
# Check 7: Registered in verticals.yaml
# ──────────────────────────────────────────────
echo ""
echo "Check 7: Registry"

if [[ -f "$REGISTRY" ]]; then
    REGISTERED=$(python3 -c "
import yaml
with open('${REGISTRY}') as f:
    data = yaml.safe_load(f)
if '${VERTICAL_NAME}' in data.get('verticals', {}):
    print('YES')
else:
    print('NO')
" 2>/dev/null || echo "NO")
    if [[ "$REGISTERED" == "YES" ]]; then
        pass_check "Registered in verticals.yaml"
    else
        fail_check "NOT registered in verticals.yaml"
    fi
else
    fail_check "Registry file not found: $REGISTRY"
fi

# ──────────────────────────────────────────────
# Check 8: No hardcoded credentials
# ──────────────────────────────────────────────
echo ""
echo "Check 8: Credential safety"

CRED_PATTERNS=(
    'password\s*='
    'passwd\s*='
    'PGPASSWORD='
    'api_key\s*='
    'secret_key\s*='
    'token\s*=\s*["\x27][A-Za-z0-9]'
    'Bearer\s+[A-Za-z0-9._-]{20,}'
)

cred_found=0
for pattern in "${CRED_PATTERNS[@]}"; do
    # Search Python and YAML files, exclude __pycache__ and .git
    matches=$(grep -rEi "$pattern" "$VERTICAL_DIR" \
        --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.sh" \
        --exclude-dir=__pycache__ --exclude-dir=.git 2>/dev/null | \
        grep -vi 'os\.environ\|os\.getenv\|env\.\|\.env\|environ\.get\|# .*credential\|# .*password\|raise\|example\|placeholder\|your_.*_here\|CHANGE_ME\|""$\|"\s*"' || true)
    if [[ -n "$matches" ]]; then
        cred_found=1
        while IFS= read -r line; do
            fail_check "Possible hardcoded credential: $line"
        done <<< "$matches"
    fi
done

if [[ "$cred_found" -eq 0 ]]; then
    pass_check "No hardcoded credentials detected"
fi

# ──────────────────────────────────────────────
# Check 9: __init__.py files in all Python packages
# ──────────────────────────────────────────────
echo ""
echo "Check 9: Python package structure"

init_missing=0
while IFS= read -r pydir; do
    # Only check directories that contain .py files
    py_count=$(find "$pydir" -maxdepth 1 -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)
    if [[ "$py_count" -gt 0 ]]; then
        if [[ ! -f "$pydir/__init__.py" ]]; then
            rel_dir="${pydir#$VERTICAL_DIR/}"
            fail_check "Missing __init__.py in $rel_dir/"
            init_missing=1
        fi
    fi
done < <(find "$VERTICAL_DIR/backend" -type d 2>/dev/null)

if [[ "$init_missing" -eq 0 ]]; then
    pass_check "All Python packages have __init__.py"
fi

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
echo ""
echo "========================================"
echo "Validation Summary: $VERTICAL_NAME"
echo "========================================"
echo "  Checks run: $CHECKS"
echo "  Passed:     $((CHECKS - ERRORS - WARNINGS))"
echo "  Warnings:   $WARNINGS"
echo "  Failures:   $ERRORS"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}PASS${NC}: All checks passed for $VERTICAL_NAME"
    if [[ $WARNINGS -gt 0 ]]; then
        echo "  ($WARNINGS warning(s) — review recommended but not blocking)"
    fi
    echo ""
    echo "For Seven Generations — ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ"
    exit 0
else
    echo -e "${RED}FAIL${NC}: $ERRORS check(s) failed for $VERTICAL_NAME"
    echo ""
    echo "Fix the failures above and re-run validation."
    exit 1
fi
```

**Important:** After creating this file, run `chmod +x /ganuda/assist/scripts/validate_vertical.sh`.

---

## File 4: `/ganuda/assist/scripts/list_verticals.sh`

Quick status view of all registered verticals. Mark it executable after creation (`chmod +x`).

```bash
#!/bin/bash
# Assist Platform — List All Registered Verticals
# Cherokee AI Federation — For Seven Generations
#
# Usage: ./list_verticals.sh

set -euo pipefail

ASSIST_ROOT="/ganuda/assist"
REGISTRY="${ASSIST_ROOT}/verticals.yaml"

if [[ ! -f "$REGISTRY" ]]; then
    echo "ERROR: Registry not found at $REGISTRY"
    exit 1
fi

python3 << 'LISTEOF'
import yaml

with open("/ganuda/assist/verticals.yaml") as f:
    data = yaml.safe_load(f)

verticals = data.get("verticals", {})

if not verticals:
    print("No verticals registered.")
    exit(0)

header_fmt = "{:<15} {:<20} {:<12} {:<6} {}"
row_fmt = "{:<15} {:<20} {:<12} {:<6} {}"

print(header_fmt.format("Name", "Display", "Status", "Port", "Path"))
print("-" * 80)

for name, v in verticals.items():
    print(row_fmt.format(
        name,
        v.get("display_name", ""),
        v.get("status", "unknown"),
        str(v.get("port", "")),
        v.get("path", ""),
    ))

print("")
print(f"Total: {len(verticals)} vertical(s)")
LISTEOF
```

**Important:** After creating this file, run `chmod +x /ganuda/assist/scripts/list_verticals.sh`.

---

## Execution Steps

The Jr must execute these steps in order:

### Step 1 (directory): Create the scripts directory

```bash
mkdir -p /ganuda/assist/scripts
```

### Step 2 (file): Create `/ganuda/assist/verticals.yaml`

Write the complete YAML content from File 1 above.

### Step 3 (file): Create `/ganuda/assist/scripts/new_vertical.sh`

Write the complete bash script from File 2 above, then:

```bash
chmod +x /ganuda/assist/scripts/new_vertical.sh
```

### Step 4 (file): Create `/ganuda/assist/scripts/validate_vertical.sh`

Write the complete bash script from File 3 above, then:

```bash
chmod +x /ganuda/assist/scripts/validate_vertical.sh
```

### Step 5 (file): Create `/ganuda/assist/scripts/list_verticals.sh`

Write the complete bash script from File 4 above, then:

```bash
chmod +x /ganuda/assist/scripts/list_verticals.sh
```

---

## Verification Steps

After all files are created, run these verification checks:

### V1: List all registered verticals

```bash
/ganuda/assist/scripts/list_verticals.sh
```

**Expected output:** Table showing vetassist, ssidassist, and tribeassist with their ports and statuses.

### V2: Validate ssidassist (from Phase 2)

```bash
/ganuda/assist/scripts/validate_vertical.sh ssidassist
```

**Expected:** All structural checks pass. Database and health checks may warn (non-blocking) if schema is not applied or service is not running.

### V3: Validate tribeassist (from Phase 3)

```bash
/ganuda/assist/scripts/validate_vertical.sh tribeassist
```

**Expected:** All structural checks pass. Same notes as V2.

### V4: Generate a test vertical

```bash
/ganuda/assist/scripts/new_vertical.sh testassist "TestAssist" 8003
```

**Expected:** Creates `/ganuda/assist/testassist/` with all directories, files, configs, and SQL schema. Registers in verticals.yaml.

### V5: Validate the test vertical

```bash
/ganuda/assist/scripts/validate_vertical.sh testassist
```

**Expected:** All structural checks pass (PASS). Database and health warnings are acceptable.

### V6: Confirm test vertical appears in listing

```bash
/ganuda/assist/scripts/list_verticals.sh
```

**Expected:** Four verticals listed: vetassist, ssidassist, tribeassist, testassist.

### V7: Clean up test vertical

```bash
rm -rf /ganuda/assist/testassist
```

Then remove the testassist entry from `/ganuda/assist/verticals.yaml`:

```bash
python3 -c "
import yaml
with open('/ganuda/assist/verticals.yaml') as f:
    data = yaml.safe_load(f)
if 'testassist' in data.get('verticals', {}):
    del data['verticals']['testassist']
with open('/ganuda/assist/verticals.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
print('testassist removed from registry')
"
```

### V8: Confirm clean state

```bash
/ganuda/assist/scripts/list_verticals.sh
```

**Expected:** Three verticals: vetassist, ssidassist, tribeassist (back to original state).

---

## Safety and Constraints

1. **No hardcoded credentials** — all database credentials use environment variables (`ASSIST_DB_USER`, `ASSIST_DB_PASS`). The generator template enforces this.
2. **Crisis detection required** — every generated vertical includes `crisis_patterns.yaml` with real hotline numbers. This is non-negotiable.
3. **Audit trail table** — every generated schema includes an audit trail table. Council safety policy requires this.
4. **Port range enforcement** — verticals must use ports 8000-8099. The generator validates this.
5. **Name validation** — vertical names must be lowercase alphanumeric with underscores only.
6. **Idempotent SQL** — all schema files use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.

## Integration Notes

- **VetAssist** at `/ganuda/vetassist` is the original production vertical. It predates the Assist platform and is registered with an empty `table_prefix` because its tables have no prefix.
- **SSIDAssist** and **TribeAssist** were created in Phases 2 and 3. Their scaffolds should already exist at `/ganuda/assist/ssidassist` and `/ganuda/assist/tribeassist`. The validation script confirms their structure.
- The core framework at `/ganuda/assist/core/` (from Phase 1) is referenced in the generator's `config.py` and `main.py` templates via `sys.path.insert`.

## Files Modified

None — this phase only creates new files.

## Files Created

| File | Type | Size (approx) |
|------|------|---------------|
| `/ganuda/assist/verticals.yaml` | YAML registry | ~50 lines |
| `/ganuda/assist/scripts/new_vertical.sh` | Bash (executable) | ~350 lines |
| `/ganuda/assist/scripts/validate_vertical.sh` | Bash (executable) | ~270 lines |
| `/ganuda/assist/scripts/list_verticals.sh` | Bash (executable) | ~40 lines |

---

*For Seven Generations — ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ*
*Cherokee AI Federation*
