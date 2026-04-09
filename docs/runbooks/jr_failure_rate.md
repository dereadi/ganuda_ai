# Runbook: jr_failure_rate

**Alert**: Jr task failure rate >30% in 24h
**Severity**: ALERT | **Cooldown**: 4 hours | **Escalates after**: 3 cycles

## What fired
More than 30% of Jr tasks failed in the last 24 hours. This is an execution quality problem.

## What to check
```bash
# What's failing and why?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT task_id, task_type, status, LEFT(result,100) as error
FROM jr_task_announcements
WHERE status IN ('failed', 'permanently_failed')
AND announced_at > NOW() - INTERVAL '24 hours'
ORDER BY announced_at DESC LIMIT 10;"

# Is vLLM healthy?
curl -s http://localhost:8000/health

# Is the gateway healthy?
curl -s http://localhost:8080/health | python3 -m json.tool
```

## How to fix (autonomous)
1. If vLLM is down: `sudo systemctl restart vllm-qwen`
2. If gateway is down: `sudo systemctl restart llm-gateway`
3. If failures are all the same task type: check if that task type has a broken prompt template
4. If failures say "context length exceeded": tasks are too large, need decomposition
5. Reset zombie tasks: Fire Guard already handles this (tasks stuck >6 hours auto-reset)

## When to escalate
- Failure rate >60% for 2+ hours (something is fundamentally broken)
- All failures are the same error and autonomous fixes didn't help
- Failures correlate with a recent code deployment (rollback candidate)
