# JR INSTRUCTION: Chain Protocol — Associate/Seasonal Temp Governance Boundary

**Task**: Implement the necklace chain as a universal protocol interface with two participant classes
**Priority**: P2 — foundational infrastructure for external model integration
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 8
**Council Vote**: #8878 (audit 58a46ffddbeab208), APPROVED WITH CONDITIONS (0.889)

## Problem Statement

The federation needs to integrate external models (vision, domain-specialist, frontier) without creating dependency or compromising sovereignty. The necklace architecture provides the metaphor: the chain is the protocol, links are permanent (Associates), rings are temporary (Seasonal Temps). This task implements the protocol layer.

Chief declaration: Claude is the sole permanent frontier model (Associate). All other external models are Seasonal Temps — task-scoped, revocable, governed by the chain.

## Architecture

### Two Classes of Participant

**Associates (Links)** — permanent chain participants:
- Claude (Opus/Sonnet/Haiku) — sole permanent frontier model
- Internal models (council-governed): Qwen, Llama, BGE, etc.
- Local nodes
- Have Longhouse voice, full thermal trust, institutional memory

**Seasonal Temps (Rings)** — task-scoped external models:
- GPT-4o, Gemini, or any external API
- No Longhouse voice. Execute contracts, not policy.
- Provenance-tagged outputs, lower thermal ceiling, metered per call
- Ring dissolves when local capability replaces it or provider degrades

### Eight Features (Elevated from Council Concerns)

1. **Ring Budget**: Max 20% of active rings can be external. Council-voted parameter. Adding an external ring requires either replacing one or Longhouse budget expansion.
2. **Ring Calibration**: Weekly test suites for external rings (known inputs → expected outputs). Quarantine on >15% drift.
3. **Provenance Tagging**: External outputs tagged `source: external, model: X, ring: Y, trust_tier: 3`. Lower thermal ceiling, faster cooling, weighted lower in RAG. **IMMUTABLE** — external thermal can NEVER become sacred. Must be independently re-verified by an Associate to create new internal thermal (Coyote condition).
4. **Ring Contract Isolation**: Canonical output schema per ring type. External model output translated to ring-canonical form at chain boundary. Schema versioning from day one. Nothing downstream sees the external model's native format.
5. **Chain as Configuration**: Ring registry in `duplo_tool_registry` table (already deployed). Adding/removing rings = insert/delete row. No code changes.
6. **Ring Metering**: Cost and rate tracking via `token_ledger`. Auto-throttle on DC-9 budget violation. Dawn Mist reports ring costs.
7. **Outbound Scrub Ring**: Mandatory pre-dispatch screening. Full `BLOCKED_TERMS` list from `deer_linkedin_drafts.py` + dynamic `scrub_rules` table. Images: EXIF strip + OCR pre-scan on bluefin before external dispatch.
8. **Ring Consensus**: Multi-ring dispatch MANDATORY for external output feeding council votes or sacred thermals. Optional for routine screening.

## What You're Building

### Step 1: Extend duplo_tool_registry schema

**File:** `/ganuda/scripts/migrations/chain_protocol_schema.sql`

```sql
-- Chain Protocol: Ring Registry Extension
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS ring_type VARCHAR(20) DEFAULT 'associate' CHECK (ring_type IN ('associate', 'temp'));
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS provider VARCHAR(100);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS canonical_schema JSONB;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS removal_procedure TEXT;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS calibration_schedule VARCHAR(50);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS cost_budget_daily NUMERIC(10,4);
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS ring_status VARCHAR(20) DEFAULT 'active' CHECK (ring_status IN ('active', 'quarantine', 'revoked'));
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS schema_version INTEGER DEFAULT 1;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS last_calibration TIMESTAMP;
ALTER TABLE duplo_tool_registry ADD COLUMN IF NOT EXISTS drift_score NUMERIC(5,4);

-- Ring health tracking
CREATE TABLE IF NOT EXISTS ring_health (
    id SERIAL PRIMARY KEY,
    ring_id INTEGER REFERENCES duplo_tool_registry(id),
    checked_at TIMESTAMP DEFAULT NOW(),
    calls_today INTEGER DEFAULT 0,
    errors_today INTEGER DEFAULT 0,
    avg_latency_ms NUMERIC(10,2),
    cost_today NUMERIC(10,4),
    status VARCHAR(20) DEFAULT 'healthy'
);

-- Scrub rules for outbound screening
CREATE TABLE IF NOT EXISTS scrub_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(20) NOT NULL CHECK (rule_type IN ('blocked_term', 'regex', 'field_scrub', 'image_check')),
    pattern TEXT NOT NULL,
    applies_to VARCHAR(50) DEFAULT 'all',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed scrub_rules from existing blocked terms
INSERT INTO scrub_rules (rule_type, pattern, applies_to) VALUES
('blocked_term', 'thermal_memory', 'all'),
('blocked_term', 'council_votes', 'all'),
('blocked_term', 'duyuktv', 'all'),
('blocked_term', 'jr_work_queue', 'all'),
('blocked_term', 'bluefin', 'all'),
('blocked_term', 'redfin', 'all'),
('blocked_term', 'greenfin', 'all'),
('blocked_term', 'owlfin', 'all'),
('blocked_term', 'eaglefin', 'all'),
('blocked_term', 'bmasass', 'all'),
('blocked_term', 'sacred_fire', 'all'),
('blocked_term', 'nftables', 'all'),
('blocked_term', '192.168', 'all'),
('blocked_term', '10.100.0', 'all'),
('blocked_term', 'zammad_production', 'all'),
('blocked_term', 'FreeIPA', 'all'),
('blocked_term', 'silverfin', 'all'),
('blocked_term', 'WireGuard', 'all'),
('blocked_term', 'cherokee_venv', 'all'),
('blocked_term', 'jr_executor', 'all'),
('blocked_term', 'SEARCH/REPLACE', 'all')
ON CONFLICT DO NOTHING;
```

### Step 2: Chain Protocol Dispatch Library

**File:** `/ganuda/lib/chain_protocol.py`

```python
#!/usr/bin/env python3
"""Chain Protocol — Universal dispatch interface for Associate and Seasonal Temp models."""

import json
import os
import re
import hashlib
import requests
import psycopg2
from datetime import datetime
from enum import Enum


class RingType(Enum):
    ASSOCIATE = "associate"
    TEMP = "temp"


class RingStatus(Enum):
    ACTIVE = "active"
    QUARANTINE = "quarantine"
    REVOKED = "revoked"


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def _load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def _get_db():
    _load_secrets()
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def get_ring(ring_name: str) -> dict:
    """Look up a ring from the registry."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""SELECT id, ring_type, provider, canonical_schema, ring_status, cost_budget_daily
        FROM duplo_tool_registry WHERE name = %s""", (ring_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "ring_type": row[1], "provider": row[2],
        "canonical_schema": row[3], "status": row[4], "cost_budget": row[5]
    }


def check_ring_budget() -> dict:
    """Check current ring budget allocation."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""SELECT ring_type, COUNT(*) FROM duplo_tool_registry
        WHERE ring_status = 'active' GROUP BY ring_type""")
    counts = dict(cur.fetchall())
    cur.close()
    conn.close()
    total = sum(counts.values()) or 1
    temp_pct = (counts.get("temp", 0) / total) * 100
    return {"associate": counts.get("associate", 0), "temp": counts.get("temp", 0),
            "temp_pct": round(temp_pct, 1), "budget_max_pct": 20, "within_budget": temp_pct <= 20}


def outbound_scrub(payload: str, ring_name: str = "all") -> list:
    """Screen outbound payload against scrub rules. Returns list of violations."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""SELECT rule_type, pattern FROM scrub_rules
        WHERE active = true AND (applies_to = 'all' OR applies_to = %s)""", (ring_name,))
    rules = cur.fetchall()
    cur.close()
    conn.close()

    violations = []
    lower = payload.lower()
    for rule_type, pattern in rules:
        if rule_type == "blocked_term":
            if pattern.lower() in lower:
                violations.append(f"blocked_term: {pattern}")
        elif rule_type == "regex":
            if re.search(pattern, payload, re.IGNORECASE):
                violations.append(f"regex: {pattern}")
    return violations


def tag_provenance(content: str, ring_name: str, model: str, ring_type: str) -> dict:
    """Create provenance metadata for thermal storage."""
    return {
        "source": "external" if ring_type == "temp" else "internal",
        "model": model,
        "ring": ring_name,
        "trust_tier": 3 if ring_type == "temp" else 1,
        "max_temperature": 70 if ring_type == "temp" else 100,
        "tagged_at": datetime.now().isoformat(),
        "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]
    }


def meter_call(ring_id: int, latency_ms: float, cost: float, error: bool = False):
    """Record a ring call in the metering system."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO ring_health (ring_id, checked_at, calls_today, errors_today, avg_latency_ms, cost_today)
        VALUES (%s, NOW(), 1, %s, %s, %s)
        ON CONFLICT DO NOTHING""",
        (ring_id, 1 if error else 0, latency_ms, cost))
    conn.commit()
    cur.close()
    conn.close()


def dispatch(ring_name: str, payload: str, require_consensus: bool = False) -> dict:
    """Dispatch a task through the chain protocol.

    1. Look up ring in registry
    2. Check ring is active (not quarantined/revoked)
    3. Run outbound scrub
    4. Dispatch to provider
    5. Tag provenance on response
    6. Meter the call

    Returns: {"result": str, "provenance": dict, "scrub_passed": bool}
    """
    ring = get_ring(ring_name)
    if not ring:
        raise ValueError(f"Ring '{ring_name}' not found in registry")

    if ring["status"] != "active":
        raise RuntimeError(f"Ring '{ring_name}' is {ring['status']} — cannot dispatch")

    # Outbound scrub (mandatory for temp rings)
    violations = outbound_scrub(payload, ring_name)
    if violations and ring["ring_type"] == "temp":
        return {"result": None, "provenance": None, "scrub_passed": False,
                "violations": violations, "blocked": True}

    # Dispatch would happen here — provider-specific logic
    # This is the extension point for each ring's actual API call
    result = _dispatch_to_provider(ring, payload)

    # Tag provenance
    provenance = tag_provenance(result, ring_name, ring["provider"], ring["ring_type"])

    return {"result": result, "provenance": provenance, "scrub_passed": True, "blocked": False}


def _dispatch_to_provider(ring: dict, payload: str) -> str:
    """Provider-specific dispatch. Override per ring type."""
    # Placeholder — each ring registers its own dispatch function
    raise NotImplementedError(f"No dispatch handler registered for ring {ring['id']}")
```

### Step 3: Seed Associate Rings in Registry

**File:** `/ganuda/scripts/migrations/chain_protocol_schema.sql`

```sql
-- Seed Associate rings (permanent)
INSERT INTO duplo_tool_registry (name, ring_type, provider, ring_status, canonical_schema)
VALUES
('claude_opus', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "strategic"}'),
('claude_sonnet', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "content"}'),
('claude_haiku', 'associate', 'anthropic', 'active', '{"input": "text", "output": "text", "tier": "screening"}'),
('qwen_72b', 'associate', 'local_redfin', 'active', '{"input": "text", "output": "text", "tier": "reasoning"}'),
('qwen_vl_7b', 'associate', 'local_bluefin', 'active', '{"input": "image+text", "output": "text", "tier": "vision"}'),
('qwen3_30b', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "fast_reasoning"}'),
('llama_70b', 'associate', 'local_bmasass', 'active', '{"input": "text", "output": "text", "tier": "direct_reasoning"}'),
('bge_large', 'associate', 'local_greenfin', 'active', '{"input": "text", "output": "vector_1024", "tier": "embedding"}')
ON CONFLICT DO NOTHING;
```

## Constraints

- **Coyote condition**: Provenance tagging is IMMUTABLE. No process can upgrade external-sourced thermal to sacred. Independent Associate must re-verify and create new internal thermal.
- **Coyote condition**: Adversarial test suite for Outbound Scrub Ring must pass before any external ring goes live.
- **Ring Budget**: Max 20% external rings. Enforced in `check_ring_budget()`. Longhouse vote to expand.
- **DC-9**: Ring Metering auto-throttles on daily cost budget exceeded.
- **DC-7**: Chain protocol is a conserved sequence. Ring implementations speciate; the chain interface does not.
- **Schema versioning**: Lock v1 canonical schema before first external ring dispatch.
- No API keys in this code. External ring credentials stored in secrets.env or provider-specific config.

## Target Files

- `/ganuda/scripts/migrations/chain_protocol_schema.sql` — DB schema (CREATE)
- `/ganuda/lib/chain_protocol.py` — dispatch library (CREATE)
- `/ganuda/docs/kb/KB-CHAIN-PROTOCOL-ASSOCIATE-TEMP.md` — architecture doc (CREATE)

## Acceptance Criteria

- `python3 -c "import py_compile; py_compile.compile('lib/chain_protocol.py', doraise=True)"` passes
- Migration creates `ring_health` and `scrub_rules` tables
- `duplo_tool_registry` has new columns: `ring_type`, `provider`, `canonical_schema`, `removal_procedure`, `calibration_schedule`, `cost_budget_daily`, `ring_status`, `schema_version`, `last_calibration`, `drift_score`
- 8 Associate rings seeded in registry
- `outbound_scrub("the redfin server at 192.168.132.223")` returns violations
- `outbound_scrub("AI governance patterns in distributed systems")` returns empty list
- `check_ring_budget()` returns correct counts
- `tag_provenance()` returns correct trust_tier (1 for associate, 3 for temp)
- No API keys in any file
- Scrub rules table seeded with all blocked terms from `deer_linkedin_drafts.py`

## DO NOT

- Store API keys in scripts or config files checked into git
- Allow external-sourced thermals to reach sacred status without Associate re-verification
- Dispatch to external rings without passing outbound scrub
- Add external rings that would exceed the 20% budget without Longhouse vote
- Remove the provenance tag from any thermal after it is written
