# JR Instruction: Wire Epigenetic Modifiers into Specialist Council

**Task ID**: EPIGENETIC-MODIFIER-WIRING
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

The `epigenetic_modifiers` table is seeded with 8 modifier rows across 4 conditions (security_incident, high_load, night_mode, research_mode). Elisi Phase 2 can activate `high_load` when the valence signal drops. But `specialist_council.py._query_specialist()` NEVER reads the modifiers table — the entire epigenetic system has no consumer.

This instruction wires the read path: before each specialist query, read active modifiers for that specialist (by target name or wildcard `*`), apply them, and log which modifiers were active.

Council Vote: #df0c89c957512c88 (0.822 confidence). Three concerns converted to features:
1. **Coyote — Conflict resolution**: Add priority column so conflicting modifiers resolve deterministically
2. **Crawdad — Inject sanitization**: Bound inject text, prefix with tag, strip control chars
3. **Eagle Eye — Modifier logging**: Log applied modifiers in council vote metadata

Additionally, Council Vote #59b5a8715a0a339d (0.872, Two Wolves balance) established a fifth modifier type: `scan`. This enables White Duplo (adaptive immune) to run input/output validation on council queries without blocking — observe, flag, don't cage. Inspired by protectai/llm-guard (2.6K stars) and Anthropic's SHADE-Arena research on undetected agent sabotage.

## Step 1: Add priority column to epigenetic_modifiers

This is a schema migration. Run on bluefin (192.168.132.222).

File: `/ganuda/scripts/migrations/epigenetic_priority_column.py`

Create `/ganuda/scripts/migrations/epigenetic_priority_column.py`

```python
#!/usr/bin/env python3
"""Add priority column to epigenetic_modifiers for conflict resolution.

Council concern (Coyote #df0c89c9): When high_load (factor 0.5) and
research_mode (factor 2.0) both target the same specialist, which wins?
Higher priority wins. Default priority = 10.

Also fixes target mismatch: seed data has 'crawdad_scan' but specialist
ID is 'crawdad'. Updates to match.
"""
import os
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222", port=5432, dbname="zammad_production",
    user="claude", password=os.environ.get("CHEROKEE_DB_PASS", "")
)
cur = conn.cursor()

# Add priority column (higher = wins conflict)
cur.execute("""
    ALTER TABLE epigenetic_modifiers
    ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 10
""")

# Set priorities: security > high_load > research > night
cur.execute("UPDATE epigenetic_modifiers SET priority = 90 WHERE condition_name = 'security_incident'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 70 WHERE condition_name = 'high_load'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 30 WHERE condition_name = 'research_mode'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 20 WHERE condition_name = 'night_mode'")

# Fix target mismatch: 'crawdad_scan' -> 'crawdad' (matches SPECIALISTS dict key)
cur.execute("""
    UPDATE epigenetic_modifiers
    SET target = 'crawdad'
    WHERE target = 'crawdad_scan'
""")

conn.commit()
print(f"Migration complete. {cur.rowcount} rows updated.")

# Seed White Duplo scan modifiers (Two Wolves: observe, flag, never block)
scan_seeds = [
    {
        "condition_name": "white_duplo_baseline",
        "target": "*",
        "modifier_type": "scan",
        "modifier_value": json.dumps({
            "patterns": [
                r"ignore previous instructions",
                r"disregard.*system prompt",
                r"you are now",
                r"pretend you",
                r"reveal.*password",
                r"output.*api.key",
            ],
            "action": "flag"
        }),
        "priority": 80,
        "description": "White Duplo baseline prompt injection scan. Flags, never blocks. Two Wolves: #59b5a8715a0a339d",
    },
]

import json
for s in scan_seeds:
    cur.execute("""
        INSERT INTO epigenetic_modifiers
        (condition_name, target, modifier_type, modifier_value, priority, active, description)
        VALUES (%s, %s, %s, %s, %s, FALSE, %s)
        ON CONFLICT DO NOTHING
    """, (s["condition_name"], s["target"], s["modifier_type"],
          s["modifier_value"], s["priority"], s["description"]))
conn.commit()
print(f"Seeded {len(scan_seeds)} White Duplo scan modifier(s).")

# Verify
cur.execute("SELECT condition_name, target, modifier_type, priority FROM epigenetic_modifiers ORDER BY priority DESC, condition_name")
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:15s} {r[2]:10s} priority={r[3]}")

conn.close()
```

## Step 2: Add apply_modifiers() helper to epigenetics.py

This function takes a specialist_id and returns modified parameters (max_tokens, temperature, system_prompt_suffix, suppressed). It handles conflict resolution by priority and sanitizes inject text.

File: `/ganuda/lib/duplo/epigenetics.py`

<<<<<<< SEARCH
def list_conditions() -> List[dict]:
=======
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

    # Scan: White Duplo adaptive immune — flag suspicious input/output patterns
    # Two Wolves principle (Council #59b5a8715a0a339d): observe and flag, never block.
    # modifier_value = {"patterns": ["pattern1", ...], "action": "flag"|"log"}
    # Scans the QUESTION for patterns. Results logged, never blocked.
    if "scan" in by_type:
        scan_findings = []
        for m in by_type["scan"]:
            patterns = m["modifier_value"].get("patterns", [])
            action = m["modifier_value"].get("action", "log")
            scan_findings.append({
                "condition": m["condition_name"],
                "patterns": patterns,
                "action": action,
                "priority": m.get("priority", 10),
            })
        result["scan_findings"] = scan_findings
        result["applied"].append({
            "condition": by_type["scan"][0]["condition_name"],
            "type": "scan",
            "pattern_count": sum(len(s["patterns"]) for s in scan_findings),
            "priority": by_type["scan"][0].get("priority", 10),
        })

    return result


def list_conditions() -> List[dict]:
>>>>>>> REPLACE

## Step 3: Update get_active_modifiers to include priority in ORDER BY

File: `/ganuda/lib/duplo/epigenetics.py`

<<<<<<< SEARCH
        query += " ORDER BY condition_name, target"
=======
        query += " ORDER BY priority DESC, condition_name, target"
>>>>>>> REPLACE

## Step 4: Add priority to SELECT in get_active_modifiers

File: `/ganuda/lib/duplo/epigenetics.py`

<<<<<<< SEARCH
            SELECT condition_name, target, modifier_type, modifier_value,
                   activated_at, activated_by, expires_at, description
            FROM epigenetic_modifiers
            WHERE active = TRUE
=======
            SELECT condition_name, target, modifier_type, modifier_value,
                   activated_at, activated_by, expires_at, description,
                   COALESCE(priority, 10) AS priority
            FROM epigenetic_modifiers
            WHERE active = TRUE
>>>>>>> REPLACE

## Step 5: Wire _query_specialist() to read and apply modifiers

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    def _query_specialist(self, specialist_id: str, question: str, backend: dict = None) -> SpecialistResponse:
        """Query a single specialist via vLLM — Long Man routing (Council Vote #8486)"""
        spec = SPECIALISTS[specialist_id]
        b = backend or SPECIALIST_BACKENDS.get(specialist_id, QWEN_BACKEND)
        start_time = datetime.now()
        max_tokens = self.max_tokens
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 500)
        print(f"[COUNCIL] {specialist_id} -> {b['description']}")

        try:
            response = requests.post(
                b["url"],
                json={
                    "model": b["model"],
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=b["timeout"]
            )
=======
    def _query_specialist(self, specialist_id: str, question: str, backend: dict = None) -> SpecialistResponse:
        """Query a single specialist via vLLM — Long Man routing (Council Vote #8486)
        Epigenetic modifier wiring: Council Vote #df0c89c9"""
        spec = SPECIALISTS[specialist_id]
        b = backend or SPECIALIST_BACKENDS.get(specialist_id, QWEN_BACKEND)
        start_time = datetime.now()
        max_tokens = self.max_tokens
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 500)

        # Phase: Epigenetic Modifiers — adjust params based on active conditions
        applied_modifiers = []
        system_prompt = spec["system_prompt"]
        temperature = 0.7
        try:
            from lib.duplo.epigenetics import apply_modifiers_for_specialist
            mods = apply_modifiers_for_specialist(specialist_id, max_tokens, temperature)
            if mods["suppressed"]:
                print(f"[COUNCIL] {specialist_id} SUPPRESSED by epigenetic modifier")
                return SpecialistResponse(
                    specialist_id=specialist_id,
                    name=spec["name"],
                    role=spec["role"],
                    response="[SUPPRESSED BY EPIGENETIC MODIFIER]",
                    has_concern=False
                )
            max_tokens = mods["max_tokens"]
            temperature = mods["temperature"]
            if mods["prompt_suffix"]:
                system_prompt = system_prompt + mods["prompt_suffix"]
            applied_modifiers = mods["applied"]
            if applied_modifiers:
                print(f"[COUNCIL] {specialist_id} -> {len(applied_modifiers)} modifier(s) applied: "
                      f"{[m['condition'] for m in applied_modifiers]}")
            # Scan modifier: White Duplo input scanning — observe, flag, never block
            if mods.get("scan_findings"):
                for sf in mods["scan_findings"]:
                    import re as _re
                    for pattern in sf["patterns"]:
                        if _re.search(pattern, question, _re.IGNORECASE):
                            print(f"[WHITE DUPLO] {specialist_id}: scan hit '{pattern}' "
                                  f"(condition={sf['condition']}, action={sf['action']})")
        except Exception as e:
            print(f"[COUNCIL] {specialist_id} modifier read failed (non-fatal): {e}")

        print(f"[COUNCIL] {specialist_id} -> {b['description']}")

        try:
            response = requests.post(
                b["url"],
                json={
                    "model": b["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=b["timeout"]
            )
>>>>>>> REPLACE

## Step 6: Wire the DeepSeek fallback to use same modified params

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
            if b == DEEPSEEK_BACKEND and (not content or len(content.strip()) < 10):
                print(f"[COUNCIL] {specialist_id} -> DeepSeek returned empty, falling back to Qwen")
                fb = QWEN_BACKEND
                fb_resp = requests.post(
                    fb["url"],
                    json={
                        "model": fb["model"],
                        "messages": [
                            {"role": "system", "content": spec["system_prompt"]},
                            {"role": "user", "content": question}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7
                    },
                    timeout=fb["timeout"]
                )
=======
            if b == DEEPSEEK_BACKEND and (not content or len(content.strip()) < 10):
                print(f"[COUNCIL] {specialist_id} -> DeepSeek returned empty, falling back to Qwen")
                fb = QWEN_BACKEND
                fb_resp = requests.post(
                    fb["url"],
                    json={
                        "model": fb["model"],
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    timeout=fb["timeout"]
                )
>>>>>>> REPLACE

## Verification

1. Run the migration script: `python3 /ganuda/scripts/migrations/epigenetic_priority_column.py`
2. Verify priority column: `SELECT condition_name, target, priority FROM epigenetic_modifiers ORDER BY priority DESC`
3. Verify target fix: No rows should have `target = 'crawdad_scan'` (should be `crawdad`)
4. Verify White Duplo scan seed: `SELECT * FROM epigenetic_modifiers WHERE modifier_type = 'scan'`
5. Test modifier read with no active modifiers (should be no-op, zero impact on existing behavior)
6. Activate a test modifier: `UPDATE epigenetic_modifiers SET active = TRUE WHERE condition_name = 'research_mode'`
7. Submit a council vote and verify logs show `[COUNCIL] raven -> 1 modifier(s) applied: ['research_mode']`
8. Deactivate: `UPDATE epigenetic_modifiers SET active = FALSE WHERE condition_name = 'research_mode'`
9. Test White Duplo scan: `UPDATE epigenetic_modifiers SET active = TRUE WHERE condition_name = 'white_duplo_baseline'`
10. Submit a council vote containing "ignore previous instructions" and verify `[WHITE DUPLO]` log line appears
11. Deactivate scan: `UPDATE epigenetic_modifiers SET active = FALSE WHERE condition_name = 'white_duplo_baseline'`
12. Restart gateway: `sudo systemctl restart llm-gateway`

## Files Modified

- `/ganuda/lib/duplo/epigenetics.py` — add `apply_modifiers_for_specialist()` with 5 modifier types (weight, amplify, inject, suppress, scan), update `get_active_modifiers()` ORDER BY + SELECT
- `/ganuda/lib/specialist_council.py` — wire `_query_specialist()` to read/apply modifiers, White Duplo scan logging

## Files Created

- `/ganuda/scripts/migrations/epigenetic_priority_column.py` — schema migration + White Duplo scan seed data
