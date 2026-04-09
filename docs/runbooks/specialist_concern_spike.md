# Runbook: specialist_concern_spike

**Alert**: Specialist raised >5 concerns in 24h
**Severity**: WARNING | **Cooldown**: 6 hours | **Escalates after**: 6 cycles

## What fired
A single specialist flagged concerns on more than 5 votes in 24 hours. This could mean: (a) the queries genuinely have problems the specialist is right to flag, or (b) the specialist's prompt is over-sensitive.

## What to check
```bash
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT specialist_id, concern_type, COUNT(*)
FROM specialist_health WHERE had_concern = true
AND measured_at > NOW() - INTERVAL '24 hours'
GROUP BY specialist_id, concern_type ORDER BY count DESC;"
```

## How to fix (autonomous)
1. Review the concern types — if all the same type, the specialist prompt may need tuning
2. Check if a new feature or Jr instruction introduced queries that legitimately trigger concerns
3. Cross-reference with council vote questions — are we asking questions that SHOULD trigger concerns?
4. If false positives: note in dawn mist for TPM prompt review. Do NOT modify specialist prompts autonomously.

## When to escalate
- Same specialist flags >15 concerns in 24h (prompt is broken, not cautious)
- Multiple specialists spike simultaneously (systemic issue)
- NEVER escalate if concern count is 6-8 — that can be a busy day with legitimate flags
