# Runbook: circuit_breaker_open

**Alert**: Specialist circuit breaker(s) OPEN
**Severity**: WARNING | **Cooldown**: 8 hours | **Escalates after**: 12 cycles (6 hours)

## What fired
One or more specialists have had concerns on 7+ of their last 10 votes, or their coherence score dropped below 0.5. The circuit breaker is a SIGNAL, not a silencer.

## What to check
```bash
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT specialist_id, had_concern, coherence_score, concern_type, measured_at
FROM specialist_health
ORDER BY measured_at DESC LIMIT 20;"
```

## How to fix (autonomous)
1. Circuit breakers self-correct as new clean votes push old concerned votes out of the 10-record window
2. Check if the specialist is legitimately concerned or if the concern threshold is miscalibrated
3. If OPEN for 24+ hours and votes are coming in clean, verify the health window is updating
4. Do NOT manually reset circuit breakers — let them age out naturally

## When to escalate
- Specialist OPEN for 48+ hours with no sign of recovery
- All specialists go OPEN simultaneously (systemic issue — likely vLLM degradation)
- NEVER escalate for 1-2 specialists being OPEN for a few hours
