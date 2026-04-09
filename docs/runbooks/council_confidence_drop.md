# Runbook: council_confidence_drop

**Alert**: Council avg confidence below 0.6 in last 24h
**Severity**: WARNING | **Cooldown**: 6 hours | **Escalates after**: 6 cycles (3 hours)

## What fired
The average confidence across all council votes in the last 24 hours dropped below 0.6. This means the council is uncertain — too many split decisions, low-agreement votes, or ambiguous queries.

## What to check
```bash
# Recent vote confidence scores
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT audit_hash, LEFT(question,60), confidence, concern_count, voted_at
FROM council_votes ORDER BY voted_at DESC LIMIT 10;"

# Are specific specialists dragging confidence down?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT specialist_id, COUNT(*) as concern_count
FROM specialist_health WHERE had_concern = true
AND measured_at > NOW() - INTERVAL '24 hours'
GROUP BY specialist_id ORDER BY concern_count DESC;"
```

## How to fix (autonomous)
1. Check if low confidence is caused by ambiguous queries (not a system problem — normal)
2. Check if a specialist's system prompt was corrupted or truncated
3. Check if vLLM is returning degraded responses (GPU memory pressure, model swap)
4. If one specialist is dragging confidence, check their circuit breaker state
5. If vLLM is unhealthy: `sudo systemctl restart vllm-qwen` and re-evaluate next cycle

## When to escalate
- Confidence stays below 0.4 for 12+ hours (systemic problem, not transient)
- Confidence drop correlates with a model change or deployment (rollback candidate)
- NEVER escalate if confidence is 0.5-0.6 — that's normal for complex queries
