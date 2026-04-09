# Runbook: memory_growth_anomaly

**Alert**: Unusual memory growth: >500 new memories in 24h
**Severity**: WARNING | **Cooldown**: 12 hours | **Escalates after**: 6 cycles

## What fired
More than 500 thermal memories were written in the last 24 hours. Normal is ~50-200/day.

## What to check
```bash
# What's writing all these memories?
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT metadata->>'source' as source, COUNT(*)
FROM thermal_memory_archive
WHERE archived_at > NOW() - INTERVAL '24 hours'
GROUP BY metadata->>'source' ORDER BY count DESC LIMIT 10;"

# Check thermal write rate per hour
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 10.100.0.2 -U claude -d zammad_production -c "
SELECT date_trunc('hour', archived_at) as hour, COUNT(*)
FROM thermal_memory_archive
WHERE archived_at > NOW() - INTERVAL '24 hours'
GROUP BY hour ORDER BY hour DESC;"
```

## How to fix (autonomous)
1. If one source is dominating, check if a Jr task is looping
2. If spread across sources, may be a legitimately busy day — note in dawn mist but don't intervene
3. If write rate exceeds 100/min, Fire Guard's emergency brake should engage automatically
4. Check disk usage on bluefin — high memory growth = high DB growth

## When to escalate
- Write rate sustained at >50/min for 1+ hours (something is looping)
- Disk usage on bluefin exceeding 85% due to memory growth
- NEVER escalate for 500-800 memories in 24h during active development
