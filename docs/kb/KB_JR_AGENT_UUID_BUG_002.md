# KB-JR-002: Jr Agent UUID Lookup Bug

**Date**: 2025-12-03
**Category**: Bug Fix
**Severity**: CRITICAL (blocks all human-readable mission IDs)
**Status**: Fix deployed to `/ganuda/it_triad_jr_agent_v3.py`

## Summary

The IT Jr Agent V3 `fetch_original_mission()` function tried to use mission IDs
as UUIDs directly, causing PostgreSQL errors when mission IDs were human-readable
strings like "FARA-SAG-DB-001".

## Root Cause

In `/ganuda/it_triad_jr_agent_v3.py`, the `fetch_original_mission()` function
(line 152) passed the mission_id directly to a UUID lookup query without
checking if it was actually a valid UUID format.

```python
# BUGGY CODE (line ~165):
cur.execute("""
    SELECT content FROM triad_shared_memories
    WHERE id = %s;  -- Fails when mission_id is not a UUID!
""", (mission_id,))
```

## Error Message

```
Error processing decision: invalid input syntax for type uuid: "FARA-SAG-DB-001"
LINE 3:         WHERE id = 'FARA-SAG-DB-001';
```

## Fix (V3.2)

Added UUID format validation before attempting direct lookup:

```python
def fetch_original_mission(mission_id):
    """Fetch original Command Post mission content.

    V3.2 FIX: Check if mission_id is a valid UUID before trying direct lookup.
    Human-readable IDs like "FARA-SAG-DB-001" are not UUIDs.
    """
    # ... initialization ...

    # Check if mission_id looks like a UUID
    is_uuid = bool(re.match(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        mission_id,
        re.IGNORECASE
    ))

    if is_uuid:
        # Try direct UUID lookup (fastest)
        try:
            cur.execute("""...""", (mission_id,))
            row = cur.fetchone()
        except Exception as e:
            row = None

    if not row:
        # Fall back: search Command Post missions by content
        cur.execute("""
            SELECT content FROM triad_shared_memories
            WHERE content LIKE 'COMMAND POST -%'
              AND source_triad = 'command_post'
            ...
        """)
        # Filter in Python for mission_id match
```

## Impact

Without this fix:
- Jr Agent would error on every mission with a human-readable ID
- Work would never be executed (files not created, tables not built)
- All FARA-SAG missions were blocked

## Verification

After applying the fix, the Jr daemon log shows successful processing:
```
Processing Decision: 83aa0a45-6786-4914-b25e-c779b5ca5fd7
Mission ID: cff6d725-3d71-4473-82bc-32660e5ecbbd
...
Created CSS and JS files:
  - /ganuda/sag/static/css/light-theme.css
  - /ganuda/sag/static/css/dark-theme.css
  - /ganuda/sag/static/js/theme-switcher.js
```

## Prevention

When working with mission IDs that could be either UUIDs or human-readable:
1. Always validate UUID format before using in `WHERE id = %s` queries
2. Have a fallback mechanism (content search) for non-UUID IDs
3. Use try/except around UUID-specific database operations

## Related

- KB-JR-001: Regex bug (also affected mission ID parsing)
- Mission JR-UUID-FIX-001: Bug fix mission
- FARA-SAG-DB-001, FARA-SAG-BACKEND-001, FARA-SAG-FRONTEND-001 (blocked by this bug)
