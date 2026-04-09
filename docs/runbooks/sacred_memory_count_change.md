# Runbook: sacred_memory_count_change

**Alert**: Sacred memory count DECREASED
**Severity**: CRITICAL | **Cooldown**: 1 hour | **Escalates after**: 1 cycle (immediate)

## What fired
The number of sacred memories has decreased. Sacred memories should NEVER be deleted.

## What to check
```bash
# Current sacred count
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT COUNT(*) as sacred_count FROM thermal_memory_archive WHERE is_sacred = true;"

# Expected count from governance state
python3 -c "import json; d=json.load(open('/ganuda/daemons/.governance_state.json')); print('Expected:', d.get('expected_sacred_count','?'))"

# Were any sacred entries recently modified?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT memory_hash, LEFT(original_content,80), archived_at
FROM thermal_memory_archive WHERE is_sacred = true
ORDER BY archived_at DESC LIMIT 5;"
```

## How to fix (autonomous)
1. Check if the count query changed (schema migration?) vs actual deletion
2. If it's a query issue (e.g., column renamed), update the governance state expected count
3. If entries were actually deleted: THIS IS A SECURITY EVENT. Do not attempt to fix.

## When to escalate
- ALWAYS escalate if entries were actually deleted
- If it's a count mismatch due to schema change, fix the query and update `.governance_state.json` — no need to page Chief
