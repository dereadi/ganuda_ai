# JR Instruction: Epigenetic Modifiers

**Task**: EPIGENETICS-001
**Title**: Create Epigenetic Modifier System
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.

## Context

In biology, epigenetics changes gene expression without changing the gene. In the federation, epigenetic modifiers adjust specialist/enzyme behavior without editing prompts or context profiles.

Example: During a "security_incident", Crawdad's sensitivity amplifies, Turtle's seven-generation thinking suppresses (urgency overrides long-term), and Coyote's dissent threshold lowers.

The `epigenetic_modifiers` table is created by `duplo_schema.sql`. The Duplo Composer already reads active modifiers via `_load_active_modifiers()`. This module provides:
1. Functions to activate/deactivate modifiers
2. Pre-seeded modifier definitions for common conditions
3. A query function to check current state

Depends on: DB migration `duplo_schema.sql`

## Files

Create `lib/duplo/epigenetics.py`

```python
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
                   activated_at, activated_by, expires_at, description
            FROM epigenetic_modifiers
            WHERE active = TRUE
        """
        params = []
        if target:
            query += " AND (target = %s OR target = '*')"
            params.append(target)
        query += " ORDER BY condition_name, target"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.commit()  # commit the auto-expire update
        return [dict(r) for r in rows]
    finally:
        conn.close()


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
```

## Verification

1. Import: `python3 -c "from lib.duplo.epigenetics import seed_defaults, list_conditions; print('OK')"`
2. Seed defaults (after DB migration):
   ```text
   python3 -c "
   from lib.duplo.epigenetics import seed_defaults, list_conditions
   seed_defaults()
   for c in list_conditions():
       print(f'{c[\"condition_name\"]}: {c[\"modifier_count\"]} modifiers')
   "
   ```
3. Activate/deactivate cycle:
   ```text
   python3 -c "
   from lib.duplo.epigenetics import activate_modifier, get_active_modifiers, deactivate_modifier
   activate_modifier('security_incident', 'test', expires_hours=1)
   print('Active:', len(get_active_modifiers()))
   deactivate_modifier('security_incident')
   print('After deactivate:', len(get_active_modifiers()))
   "
   ```
