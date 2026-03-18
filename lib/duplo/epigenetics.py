"""
Epigenetic Modifiers — Environmental Gene Expression
Cherokee AI Federation — The Living Cell Architecture

Modifiers adjust enzyme/specialist behavior based on environmental
conditions WITHOUT changing the underlying prompts or profiles.

Modifier types:
  - weight: Scale max_tokens by a factor (1.5 = more verbose, 0.5 = terser)
  - amplify: Lower temperature by a factor (more focused/aggressive)
  - suppress: Disable an enzyme entirely
  - inject: Append context text to the system prompt

Usage:
    from lib.duplo.epigenetics import activate_modifier, deactivate_modifier
    from lib.duplo.epigenetics import get_active_modifiers, seed_defaults

    # Activate security incident mode
    activate_modifier("security_incident", activated_by="crawdad_alert")

    # Check what's active
    active = get_active_modifiers()

    # Deactivate when resolved
    deactivate_modifier("security_incident")
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("duplo.epigenetics")


def seed_defaults() -> int:
    """
    Seed the epigenetic_modifiers table with default modifier definitions.
    These are created inactive. Activate them when conditions arise.
    Returns count of modifiers seeded.
    """
    from lib.ganuda_db import get_connection

    defaults = [
        # Security incident — amplify Crawdad, inject urgency, suppress Turtle long-term
        {
            "condition_name": "security_incident",
            "target": "crawdad_scan",
            "modifier_type": "amplify",
            "modifier_value": {"factor": 0.5},
            "description": "Lower temperature for more focused security scanning during incidents",
        },
        {
            "condition_name": "security_incident",
            "target": "crawdad_scan",
            "modifier_type": "inject",
            "modifier_value": {"text": "ALERT: Security incident active. Prioritize threat detection. Flag all anomalies."},
            "description": "Inject urgency context into Crawdad during security incidents",
        },
        {
            "condition_name": "security_incident",
            "target": "turtle",
            "modifier_type": "weight",
            "modifier_value": {"factor": 0.5},
            "description": "Reduce Turtle verbosity during urgent incidents (speed over depth)",
        },
        {
            "condition_name": "security_incident",
            "target": "coyote",
            "modifier_type": "inject",
            "modifier_value": {"text": "HEIGHTENED ALERT: Lower your dissent threshold. Be more suspicious than usual."},
            "description": "Make Coyote more suspicious during security incidents",
        },

        # High load — reduce token budgets across the board
        {
            "condition_name": "high_load",
            "target": "*",
            "modifier_type": "weight",
            "modifier_value": {"factor": 0.5},
            "description": "Halve token budgets when federation is under heavy load",
        },

        # Night mode — reduce activity, longer intervals
        {
            "condition_name": "night_mode",
            "target": "*",
            "modifier_type": "weight",
            "modifier_value": {"factor": 0.7},
            "description": "Reduce token usage during off-hours (circadian rhythm)",
        },

        # Research mode — amplify Raven strategic thinking
        {
            "condition_name": "research_mode",
            "target": "raven",
            "modifier_type": "weight",
            "modifier_value": {"factor": 2.0},
            "description": "Double Raven's token budget during strategic research phases",
        },
        {
            "condition_name": "research_mode",
            "target": "analyst",
            "modifier_type": "weight",
            "modifier_value": {"factor": 1.5},
            "description": "Increase analyst depth during research phases",
        },

        # DC-1 Lazy Awareness — energy budget enforcement (Design Constraint protein)
        # A cell doesn't burn ATP it doesn't need. Cap token spend for low-cost enzymes.
        # Academic: arXiv:2312.00207 (EpiTESTER), arXiv:2108.04546
        {
            "condition_name": "dc1_lazy_awareness",
            "target": "coyote_cam",
            "modifier_type": "weight",
            "modifier_value": {"factor": 0.5},
            "description": "DC-1: Cap Coyote Cam to minimal token budget. Observer runs cheap.",
        },
        {
            "condition_name": "dc1_lazy_awareness",
            "target": "*",
            "modifier_type": "inject",
            "modifier_value": {"text": "ENERGY CONSTRAINT (DC-1): Prefer shorter responses. Only elaborate when severity >= 4. The cell conserves ATP."},
            "description": "DC-1: Global awareness — all enzymes default to minimal energy spend",
        },

        # DC-6 Gradient Principle — expertise is gravity, not walls
        # Weight responses by domain proximity. Crawdad weighs heavy on security,
        # light on market. Deer weighs heavy on market, light on architecture.
        # Longhouse ratified: expertise is a gradient, not a boundary.
        {
            "condition_name": "dc6_gradient",
            "target": "coyote_cam",
            "modifier_type": "inject",
            "modifier_value": {"text": "GRADIENT (DC-6): Your gravity is OBSERVATION. You can reference any domain but you REST in pattern detection. Weight your signals by how close the anomaly is to your core: system behavior > resource usage > business patterns."},
            "description": "DC-6: Gradient weighting for Coyote Cam — observation is its gravity",
        },
        {
            "condition_name": "dc6_gradient",
            "target": "crawdad_scan",
            "modifier_type": "inject",
            "modifier_value": {"text": "GRADIENT (DC-6): Your gravity is SECURITY. You can reference any domain but you REST in threat detection. Weight your findings by proximity to security: injection/auth > config drift > performance."},
            "description": "DC-6: Gradient weighting for Crawdad — security is its gravity",
        },
    ]

    conn = get_connection()
    try:
        cur = conn.cursor()
        count = 0
        for d in defaults:
            cur.execute("""
                INSERT INTO epigenetic_modifiers
                (condition_name, target, modifier_type, modifier_value,
                 active, description)
                VALUES (%s, %s, %s, %s, FALSE, %s)
                ON CONFLICT DO NOTHING
            """, (
                d["condition_name"], d["target"], d["modifier_type"],
                json.dumps(d["modifier_value"]), d["description"],
            ))
            count += 1
        conn.commit()
        logger.info(f"Seeded {count} default modifiers")
        return count
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def activate_modifier(
    condition_name: str,
    activated_by: str = "unknown",
    expires_hours: Optional[int] = None,
) -> int:
    """
    Activate all modifiers for a given condition.
    Optionally set an expiration (auto-deactivate after N hours).
    Returns count of modifiers activated.
    """
    from lib.ganuda_db import get_connection

    expires_at = None
    if expires_hours:
        expires_at = datetime.now() + timedelta(hours=expires_hours)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE epigenetic_modifiers
            SET active = TRUE,
                activated_at = NOW(),
                activated_by = %s,
                expires_at = %s
            WHERE condition_name = %s
            RETURNING modifier_id
        """, (activated_by, expires_at, condition_name))
        count = cur.rowcount
        conn.commit()
        logger.info(f"Activated {count} modifiers for condition '{condition_name}' by {activated_by}")
        return count
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def deactivate_modifier(condition_name: str) -> int:
    """
    Deactivate all modifiers for a given condition.
    Returns count of modifiers deactivated.
    """
    from lib.ganuda_db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE epigenetic_modifiers
            SET active = FALSE, activated_at = NULL, activated_by = NULL, expires_at = NULL
            WHERE condition_name = %s AND active = TRUE
            RETURNING modifier_id
        """, (condition_name,))
        count = cur.rowcount
        conn.commit()
        logger.info(f"Deactivated {count} modifiers for condition '{condition_name}'")
        return count
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def get_active_modifiers(target: Optional[str] = None) -> List[dict]:
    """
    Get all currently active modifiers, optionally filtered by target.
    Auto-deactivates expired modifiers before returning.
    """
    from lib.ganuda_db import get_connection
    import psycopg2.extras

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Auto-expire
        cur.execute("""
            UPDATE epigenetic_modifiers
            SET active = FALSE
            WHERE active = TRUE AND expires_at IS NOT NULL AND expires_at < NOW()
        """)

        query = """
            SELECT condition_name, target, modifier_type, modifier_value,
                   activated_at, activated_by, expires_at, description,
                   COALESCE(priority, 10) AS priority
            FROM epigenetic_modifiers
            WHERE active = TRUE
        """
        params = []
        if target:
            query += " AND (target = %s OR target = '*')"
            params.append(target)
        query += " ORDER BY priority DESC, condition_name, target"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.commit()  # commit the auto-expire update
        return [dict(r) for r in rows]
    finally:
        conn.close()


# Constants for inject sanitization (Crawdad concern #df0c89c9)
INJECT_MAX_LENGTH = 500
INJECT_TAG = "[EPIGENETIC SIGNAL]"


def apply_modifiers_for_specialist(
    specialist_id: str,
    base_max_tokens: int = 150,
    base_temperature: float = 0.7,
) -> dict:
    """
    Read active modifiers for a specialist and compute adjusted parameters.

    Returns dict with:
        max_tokens: int (adjusted)
        temperature: float (adjusted)
        prompt_suffix: str (inject text to append, or empty)
        suppressed: bool (skip this specialist entirely)
        applied: list[dict] (which modifiers were applied, for logging)

    Conflict resolution (Coyote concern #df0c89c9):
        For weight/amplify: highest-priority modifier of each type wins.
        For inject: all inject texts are concatenated (additive, not conflicting).
        For suppress: any active suppress = suppressed (OR logic).
    """
    active = get_active_modifiers(target=specialist_id)

    result = {
        "max_tokens": base_max_tokens,
        "temperature": base_temperature,
        "prompt_suffix": "",
        "suppressed": False,
        "applied": [],
    }

    if not active:
        return result

    # Group by type, sort by priority DESC within each type
    by_type = {}
    for m in active:
        t = m["modifier_type"]
        by_type.setdefault(t, []).append(m)

    # Weight: highest priority wins
    if "weight" in by_type:
        winner = max(by_type["weight"], key=lambda m: m.get("priority", 10))
        factor = winner["modifier_value"].get("factor", 1.0)
        result["max_tokens"] = max(int(base_max_tokens * factor), 50)  # floor 50
        result["applied"].append({
            "condition": winner["condition_name"],
            "type": "weight",
            "factor": factor,
            "priority": winner.get("priority", 10),
        })

    # Amplify: highest priority wins
    if "amplify" in by_type:
        winner = max(by_type["amplify"], key=lambda m: m.get("priority", 10))
        factor = winner["modifier_value"].get("factor", 1.0)
        result["temperature"] = round(max(base_temperature * factor, 0.1), 2)  # floor 0.1
        result["applied"].append({
            "condition": winner["condition_name"],
            "type": "amplify",
            "factor": factor,
            "priority": winner.get("priority", 10),
        })

    # Inject: concatenate all, sanitized (Crawdad concern #df0c89c9)
    if "inject" in by_type:
        parts = []
        for m in sorted(by_type["inject"], key=lambda m: m.get("priority", 10), reverse=True):
            raw = m["modifier_value"].get("text", "")
            # Sanitize: strip control chars, bound length
            clean = "".join(c for c in raw if c.isprintable() or c in ("\n", " "))
            clean = clean[:INJECT_MAX_LENGTH]
            if clean:
                parts.append(clean)
                result["applied"].append({
                    "condition": m["condition_name"],
                    "type": "inject",
                    "text_len": len(clean),
                    "priority": m.get("priority", 10),
                })
        if parts:
            result["prompt_suffix"] = f"\n\n{INJECT_TAG}\n" + "\n".join(parts)

    # Suppress: any active suppress = suppressed
    if "suppress" in by_type:
        result["suppressed"] = True
        result["applied"].append({
            "condition": by_type["suppress"][0]["condition_name"],
            "type": "suppress",
            "priority": by_type["suppress"][0].get("priority", 10),
        })

    return result


def list_conditions() -> List[dict]:
    """List all defined conditions with their modifier counts and active status."""
    from lib.ganuda_db import execute_query

    return execute_query("""
        SELECT
            condition_name,
            COUNT(*) AS modifier_count,
            COUNT(*) FILTER (WHERE active = TRUE) AS active_count,
            array_agg(DISTINCT target) AS targets
        FROM epigenetic_modifiers
        GROUP BY condition_name
        ORDER BY condition_name
    """)