# Jr Instruction: Drift Alert Runbooks — Seven Rules, Seven Playbooks

**Epic**: OBSERVABILITY-EPIC
**Estimated SP**: 2
**Target**: BookStack KB (cherokee_bookstack on bluefin) OR `/ganuda/docs/runbooks/` if BookStack API isn't wired

---

## Objective

Create one runbook per ALERT_RULES entry in `/ganuda/daemons/governance_agent.py`. Each runbook answers four questions:

1. **What fired?** — What the alert means in plain English
2. **What to check?** — Exact commands to diagnose
3. **How to fix?** — Step-by-step remediation the cluster can do autonomously
4. **When to escalate?** — The ONLY conditions that warrant paging Chief

Alerting best practice: if there's no runbook, the alert shouldn't exist. If the runbook says "do nothing," the alert should be a dashboard metric.

---

## Runbook 1: `council_confidence_drop`

**Alert**: `Council avg confidence below 0.6 in last 24h`
**Severity**: WARNING | **Cooldown**: 6 hours | **Escalates after**: 6 cycles (3 hours)

### What fired
The average confidence across all council votes in the last 24 hours dropped below 0.6. This means the council is uncertain — too many split decisions, low-agreement votes, or ambiguous queries.

### What to check
```bash
# Recent vote confidence scores
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT audit_hash, LEFT(question,60), confidence, concern_count, voted_at
FROM council_votes ORDER BY voted_at DESC LIMIT 10;"

# Are specific specialists dragging confidence down?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT specialist_id, COUNT(*) as concern_count
FROM specialist_health WHERE had_concern = true
AND measured_at > NOW() - INTERVAL '24 hours'
GROUP BY specialist_id ORDER BY concern_count DESC;"
```

### How to fix (autonomous)
1. Check if low confidence is caused by ambiguous queries (not a system problem — normal)
2. Check if a specialist's system prompt was corrupted or truncated
3. Check if vLLM is returning degraded responses (GPU memory pressure, model swap)
4. If one specialist is dragging confidence, check their circuit breaker state
5. If vLLM is unhealthy: `sudo systemctl restart vllm-qwen` and re-evaluate next cycle

### When to escalate
- Confidence stays below 0.4 for 12+ hours (systemic problem, not transient)
- Confidence drop correlates with a model change or deployment (rollback candidate)
- NEVER escalate if confidence is 0.5-0.6 — that's normal for complex queries

---

## Runbook 2: `specialist_concern_spike`

**Alert**: `Specialist raised >5 concerns in 24h`
**Severity**: WARNING | **Cooldown**: 6 hours | **Escalates after**: 6 cycles

### What fired
A single specialist (e.g., Crawdad, Turtle) flagged concerns on more than 5 votes in 24 hours. This could mean: (a) the queries genuinely have problems the specialist is right to flag, or (b) the specialist's prompt is over-sensitive.

### What to check
```bash
# Which specialist and what concern types?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT specialist_id, concern_type, COUNT(*)
FROM specialist_health WHERE had_concern = true
AND measured_at > NOW() - INTERVAL '24 hours'
GROUP BY specialist_id, concern_type ORDER BY count DESC;"
```

### How to fix (autonomous)
1. Review the concern types — if they're all the same type (e.g., Crawdad flagging SECURITY on every query), the specialist prompt may need tuning
2. Check if a new feature or Jr instruction introduced queries that legitimately trigger concerns
3. Cross-reference with council vote questions — are we asking questions that SHOULD trigger concerns?
4. If false positives: note in dawn mist for TPM prompt review. Do NOT modify specialist prompts autonomously.

### When to escalate
- Same specialist flags >15 concerns in 24h (prompt is broken, not cautious)
- Multiple specialists spike simultaneously (systemic issue, not single specialist)
- NEVER escalate if concern count is 6-8 — that can be a busy day with legitimate flags

---

## Runbook 3: `jr_failure_rate`

**Alert**: `Jr task failure rate >30% in 24h`
**Severity**: ALERT | **Cooldown**: 4 hours | **Escalates after**: 3 cycles

### What fired
More than 30% of Jr tasks failed in the last 24 hours. This is an execution quality problem.

### What to check
```bash
# What's failing and why?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
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

### How to fix (autonomous)
1. If vLLM is down: `sudo systemctl restart vllm-qwen`
2. If gateway is down: `sudo systemctl restart llm-gateway`
3. If failures are all the same task type: check if that task type has a broken prompt template
4. If failures say "context length exceeded": tasks are too large, need decomposition
5. Reset zombie tasks: Fire Guard already handles this (tasks stuck >6 hours auto-reset)

### When to escalate
- Failure rate >60% for 2+ hours (something is fundamentally broken)
- All failures are the same error and autonomous fixes didn't help
- Failures correlate with a recent code deployment (rollback candidate)

---

## Runbook 4: `memory_integrity_violation`

**Alert**: `Thermal memory integrity violations detected`
**Severity**: CRITICAL | **Cooldown**: 1 hour | **Escalates after**: 1 cycle (immediate)

### What fired
The thermal memory integrity check found entries that have been tampered with or corrupted. This is a data integrity issue — someone or something modified archived memories.

### What to check
```bash
# Check for recent integrity violations
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT memory_hash, LEFT(original_content,80), temperature_score, metadata
FROM thermal_memory_archive
WHERE metadata->>'integrity_check' = 'failed'
ORDER BY archived_at DESC LIMIT 5;"
```

### How to fix (autonomous)
1. This SHOULD NOT self-correct — integrity violations need investigation
2. Log the violation details to thermal memory with tag `integrity_violation`
3. Do NOT delete or modify the flagged entries — preserve evidence

### When to escalate
- ALWAYS escalate. This is life/limb/eyesight territory.
- Integrity violations mean either: database corruption, unauthorized access, or a bug in the write path
- Crawdad should be notified in the next council vote

---

## Runbook 5: `sacred_memory_count_change`

**Alert**: `Sacred memory count DECREASED`
**Severity**: CRITICAL | **Cooldown**: 1 hour | **Escalates after**: 1 cycle (immediate)

### What fired
The number of sacred memories (painted on the walls — founding principles, DCs, North Star) has decreased. Sacred memories should NEVER be deleted.

### What to check
```bash
# Current sacred count
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT COUNT(*) as sacred_count FROM thermal_memory_archive WHERE is_sacred = true;"

# Expected count from governance state
python3 -c "import json; d=json.load(open('/ganuda/daemons/.governance_state.json')); print('Expected:', d.get('expected_sacred_count','?'))"

# Were any sacred entries recently modified?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT memory_hash, LEFT(original_content,80), archived_at
FROM thermal_memory_archive WHERE is_sacred = true
ORDER BY archived_at DESC LIMIT 5;"
```

### How to fix (autonomous)
1. Check if the count query changed (schema migration?) vs actual deletion
2. If it's a query issue (e.g., column renamed), update the governance state expected count
3. If entries were actually deleted: THIS IS A SECURITY EVENT. Do not attempt to fix.

### When to escalate
- ALWAYS escalate if entries were actually deleted
- If it's a count mismatch due to schema change, fix the query and update `.governance_state.json` expected count — no need to page Chief for that

---

## Runbook 6: `circuit_breaker_open`

**Alert**: `Specialist circuit breaker(s) OPEN`
**Severity**: WARNING | **Cooldown**: 8 hours | **Escalates after**: 12 cycles (6 hours)

### What fired
One or more specialists have had concerns on 7+ of their last 10 votes, or their coherence score dropped below 0.5. The circuit breaker is a SIGNAL, not a silencer (per Circuit Breaker Reform, Mar 2 2026).

### What to check
```bash
# Which specialists are OPEN and their recent health?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT specialist_id, had_concern, coherence_score, concern_type, measured_at
FROM specialist_health
WHERE specialist_id IN ('turtle', 'raven')
ORDER BY measured_at DESC LIMIT 20;"
```

### How to fix (autonomous)
1. Circuit breakers self-correct as new clean votes push old concerned votes out of the 10-record window
2. Check if the specialist is legitimately concerned (reviewing vote questions) or if the concern threshold is miscalibrated
3. If a specialist has been OPEN for 24+ hours and votes are coming in clean, verify the health window is updating
4. Do NOT manually reset circuit breakers — let them age out naturally. The signal is valuable.

### When to escalate
- Specialist OPEN for 48+ hours with no sign of recovery (prompt may need structural review)
- All specialists go OPEN simultaneously (systemic issue — likely vLLM degradation, not specialist problem)
- NEVER escalate for 1-2 specialists being OPEN for a few hours. This is normal after a batch of complex votes.

---

## Runbook 7: `memory_growth_anomaly`

**Alert**: `Unusual memory growth: >500 new memories in 24h`
**Severity**: WARNING | **Cooldown**: 12 hours | **Escalates after**: 6 cycles

### What fired
More than 500 thermal memories were written in the last 24 hours. Normal is ~50-200/day. This could mean: runaway Jr tasks, looping daemon, or legitimate high-activity period.

### What to check
```bash
# What's writing all these memories?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT metadata->>'source' as source, COUNT(*)
FROM thermal_memory_archive
WHERE archived_at > NOW() - INTERVAL '24 hours'
GROUP BY metadata->>'source' ORDER BY count DESC LIMIT 10;"

# Check thermal write rate (fire_guard threshold is 100/min)
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT date_trunc('hour', archived_at) as hour, COUNT(*)
FROM thermal_memory_archive
WHERE archived_at > NOW() - INTERVAL '24 hours'
GROUP BY hour ORDER BY hour DESC;"
```

### How to fix (autonomous)
1. If one source is dominating (e.g., `jr_executor` wrote 400 memories), check if a Jr task is looping
2. If it's spread across sources, it may be a legitimately busy day — note in dawn mist but don't intervene
3. If write rate exceeds 100/min, Fire Guard's emergency brake should engage automatically
4. Check disk usage on bluefin — high memory growth = high DB growth

### When to escalate
- Write rate sustained at >50/min for 1+ hours (something is looping)
- Disk usage on bluefin exceeding 85% due to memory growth
- NEVER escalate for 500-800 memories in 24h during active development — that's a busy day, not an emergency

---

## Storage

Save these runbooks to:
- **Option A (preferred)**: BookStack KB under a "Runbooks" shelf, one page per runbook
- **Option B (fallback)**: `/ganuda/docs/runbooks/` as individual markdown files

If using BookStack, tag each runbook with `runbook`, `alerting`, and the rule name.

## What NOT To Do

- Do NOT make runbooks longer than they need to be — responders read these at 3 AM
- Do NOT include "why we built this" context — just what to do
- Do NOT include commands that require root unless FreeIPA sudo covers them
- Do NOT hardcode passwords in runbooks — use `$CHEROKEE_DB_PASS` pattern
