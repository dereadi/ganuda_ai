# Jr Instruction: Dynamic Thermal Memory Decay — Heat on Access, Cool Over Time

**Task**: Dynamic Thermal Decay (AgentOS Diamond 1, Coyote insight)
**Assigned To**: Software Engineer Jr.
**Priority**: P2 (tech debt / architecture)
**Date**: 2026-02-26

## Context

Thermal memory temperatures are static after creation. A memory starts at its assigned temperature and only changes via rare events (+15 on task execution, -20 on bulk pattern detection). There is NO scheduled decay and NO heat-on-access. This means a memory retrieved 50 times stays the same temperature as one never accessed. Coyote's insight: "What if thermal memory decay isn't dynamic enough? Our current setup assumes all memories decay uniformly, but what if some memories should stay hot longer based on real-time feedback?"

The fix: two mechanisms. (A) Heat on retrieval — when RAG or specialist search retrieves a memory, bump its temperature. (B) Scheduled cooling — periodic daemon reduces temperature for untouched memories.

## Step 1: Heat on retrieval — specialist_council.py

When `_semantic_search_thermal()` retrieves memories, it already increments `access_count` and updates `last_access`. Add a temperature bump alongside.

File: `/ganuda/lib/specialist_council.py`

Find the access tracking UPDATE in the semantic search function and add temperature heating.

```
<<<<<<< SEARCH
                    UPDATE thermal_memory_archive
                    SET access_count = access_count + 1,
                        last_access = NOW()
                    WHERE id = %s
=======
                    UPDATE thermal_memory_archive
                    SET access_count = access_count + 1,
                        last_access = NOW(),
                        temperature_score = LEAST(temperature_score + 3.0, 100.0)
                    WHERE id = %s
>>>>>>> REPLACE
```

This adds +3 degrees per retrieval, capped at 100. Frequent retrievals keep memories hot. Sacred memories already have a floor at 40 from the sacred fire daemon.

## Step 2: Scheduled cooling function — tpm_autonomic_v2.py

Add a periodic cooling function that reduces temperature for memories not accessed recently. Run it alongside the basin check (every 300s).

File: `/ganuda/daemons/tpm_autonomic_v2.py`

Add after the `check_basin_signals()` function (after the Telegram Notification section marker):

```
<<<<<<< SEARCH
# ── Telegram Notification ──────────────────────────────────────────────────
=======
# ── Thermal Decay ─────────────────────────────────────────────────────────

def apply_thermal_decay():
    """Cool memories that haven't been accessed recently. Run every basin check cycle."""
    conn = get_db()
    try:
        cur = conn.cursor()

        # Cool non-sacred memories by 2 degrees if not accessed in 48 hours
        cur.execute("""
            UPDATE thermal_memory_archive
            SET temperature_score = GREATEST(temperature_score - 2.0, 5.0)
            WHERE sacred_pattern = false
              AND temperature_score > 5.0
              AND (last_access IS NULL OR last_access < NOW() - INTERVAL '48 hours')
              AND created_at < NOW() - INTERVAL '48 hours'
        """)
        cooled_nonsacred = cur.rowcount

        # Cool sacred memories by 0.5 degrees if not accessed in 7 days (floor at 40)
        cur.execute("""
            UPDATE thermal_memory_archive
            SET temperature_score = GREATEST(temperature_score - 0.5, 40.0)
            WHERE sacred_pattern = true
              AND temperature_score > 40.0
              AND (last_access IS NULL OR last_access < NOW() - INTERVAL '7 days')
              AND created_at < NOW() - INTERVAL '7 days'
        """)
        cooled_sacred = cur.rowcount

        conn.commit()
        cur.close()

        if cooled_nonsacred > 0 or cooled_sacred > 0:
            logger.info(f"Thermal decay: cooled {cooled_nonsacred} non-sacred, {cooled_sacred} sacred memories")

    finally:
        put_db(conn)


# ── Telegram Notification ──────────────────────────────────────────────────
>>>>>>> REPLACE
```

## Step 3: Wire thermal decay into the daemon loop

File: `/ganuda/daemons/tpm_autonomic_v2.py`

Find where `_check_basins` is called in the daemon loop and add thermal decay alongside it.

```
<<<<<<< SEARCH
            await self._check_basins()
=======
            await self._check_basins()
            apply_thermal_decay()
>>>>>>> REPLACE
```

## Verification

After applying:

1. **Heat on access**: Query a memory via council vote, then check its `temperature_score` — should be +3 from original.
2. **Cooling**: Memories with `last_access` older than 48h should lose 2 degrees per basin check cycle (every 300s). Sacred memories lose 0.5 per cycle after 7 days dormant.
3. **Floors**: Non-sacred floor at 5.0 (ember). Sacred floor at 40.0 (sacred fire daemon also enforces this).
4. **Cap**: No memory exceeds 100.0.

## Decay Math

At 300s cycles (5 min), a non-sacred memory at 100 degrees with zero access:
- After 48h: starts cooling
- Loses 2 degrees per 5 min = 24 degrees/hour
- Reaches ember (5) in ~4 hours of cooling
- But ONE retrieval adds +3, requiring 1.5 cooling cycles to offset

A sacred memory at 95 with zero access:
- After 7 days: starts cooling
- Loses 0.5 per 5 min = 6 degrees/hour
- Reaches floor (40) in ~9 hours of cooling
- Sacred fire daemon also guards the 40 floor

## Notes

- `last_access` column already exists and is updated on retrieval
- `access_count` already tracked — not used for decay math (simpler is better)
- Decay runs every basin check cycle — piggybacks on existing daemon loop
- No new tables, no schema changes, no new services
