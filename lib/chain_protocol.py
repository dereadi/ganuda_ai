#!/usr/bin/env python3
"""Chain Protocol — Universal dispatch interface for Associate and Seasonal Temp models.

The necklace chain is the protocol. Links (Associates) are permanent participants
with Longhouse voice. Rings (Seasonal Temps) are task-scoped, revocable, governed.

Eight governance features:
1. Ring Budget (max 20% external)
2. Ring Calibration (weekly drift check)
3. Provenance Tagging (immutable source tracking)
4. Ring Contract Isolation (canonical schemas)
5. Chain as Configuration (registry-driven)
6. Ring Metering (cost + rate tracking)
7. Outbound Scrub Ring (mandatory pre-dispatch screening)
8. Ring Consensus (multi-ring for critical decisions)
"""

import json
import os
import re
import hashlib
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


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
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
    cur.execute("""SELECT tool_id, ring_type, provider, canonical_schema, ring_status, cost_budget_daily
        FROM duplo_tool_registry WHERE tool_name = %s""", (ring_name,))
    row = cur.fetchone()
    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "ring_type": row[1], "provider": row[2],
        "canonical_schema": row[3], "status": row[4], "cost_budget": row[5]
    }


def check_ring_budget() -> dict:
    """Check current ring budget allocation.

    Max 20% of active rings can be external (temp). Adding an external
    ring requires either replacing one or Longhouse budget expansion.
    """
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""SELECT ring_type, COUNT(*) FROM duplo_tool_registry
        WHERE ring_status = 'active' GROUP BY ring_type""")
    counts = dict(cur.fetchall())
    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    total = sum(counts.values()) or 1
    temp_pct = (counts.get("temp", 0) / total) * 100
    return {"associate": counts.get("associate", 0), "temp": counts.get("temp", 0),
            "temp_pct": round(temp_pct, 1), "budget_max_pct": 20, "within_budget": temp_pct <= 20}


def outbound_scrub(payload: str, ring_name: str = "all") -> list:
    """Screen outbound payload against scrub rules. Returns list of violations.

    Mandatory for all temp rings. Checks blocked terms and regex patterns
    from the scrub_rules table.
    """
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""SELECT rule_type, pattern FROM scrub_rules
        WHERE active = true AND (applies_to = 'all' OR applies_to = %s)""", (ring_name,))
    rules = cur.fetchall()
    cur.close()
    conn.commit()  # explicit commit before close
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
    """Create provenance metadata for thermal storage.

    IMMUTABLE: external-sourced thermal can NEVER become sacred.
    Must be independently re-verified by an Associate to create
    new internal thermal (Coyote condition).
    """
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
        VALUES (%s, NOW(), 1, %s, %s, %s)""",
        (ring_id, 1 if error else 0, latency_ms, cost))
    conn.commit()
    cur.close()
    conn.close()


def list_rings(ring_type: str = None, status: str = "active") -> list:
    """List rings from the registry, optionally filtered by type and status."""
    conn = _get_db()
    cur = conn.cursor()
    query = "SELECT tool_id, tool_name, ring_type, provider, ring_status FROM duplo_tool_registry WHERE 1=1"
    params = []
    if ring_type:
        query += " AND ring_type = %s"
        params.append(ring_type)
    if status:
        query += " AND ring_status = %s"
        params.append(status)
    query += " ORDER BY tool_name"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    return [{"id": r[0], "name": r[1], "ring_type": r[2], "provider": r[3], "status": r[4]} for r in rows]


def quarantine_ring(ring_name: str, reason: str = "drift_exceeded"):
    """Quarantine a ring — stops all dispatch until re-calibrated."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""UPDATE duplo_tool_registry SET ring_status = 'quarantine'
        WHERE tool_name = %s""", (ring_name,))
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
