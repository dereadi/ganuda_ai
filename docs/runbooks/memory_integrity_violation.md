# Runbook: memory_integrity_violation

**Alert**: Thermal memory integrity violations detected
**Severity**: CRITICAL | **Cooldown**: 1 hour | **Escalates after**: 1 cycle (immediate)

## What fired
The thermal memory integrity check found entries that have been tampered with or corrupted.

## What to check
```bash
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT memory_hash, LEFT(original_content,80), temperature_score, metadata
FROM thermal_memory_archive
WHERE metadata->>'integrity_check' = 'failed'
ORDER BY archived_at DESC LIMIT 5;"
```

## How to fix (autonomous)
1. Do NOT self-correct — integrity violations need investigation
2. Log the violation details to thermal memory with tag `integrity_violation`
3. Do NOT delete or modify the flagged entries — preserve evidence

## When to escalate
- ALWAYS escalate. This is life/limb/eyesight territory.
- Integrity violations mean either: database corruption, unauthorized access, or a bug in the write path
- Crawdad should be notified in the next council vote
