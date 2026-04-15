# RUNBOOK: PostgreSQL Connection Exhausted

## Symptoms
- "too many connections for role" errors
- New database queries failing
- Services timing out on DB operations

## Severity
**P1** - Affects all database-dependent services

## Diagnosis
```bash
# Check connection count
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT count(*) FROM pg_stat_activity;\""

# Check by client
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT client_addr, count(*) FROM pg_stat_activity GROUP BY client_addr ORDER BY count DESC;\""

# Check idle connections
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state = 'idle' ORDER BY query_start;\""
```

## Resolution Steps

### Step 1: Terminate Idle Connections
```bash
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c \"
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < NOW() - INTERVAL '10 minutes'
  AND usename = 'claude';
\""
```

### Step 2: Increase Connection Limit (temporary)
```bash
# On bluefin as postgres user
sudo -u postgres psql -c "ALTER ROLE claude CONNECTION LIMIT 200;"
```

### Step 3: Identify Leaking Service
- Check which client_addr has most connections
- Review that service's connection pooling
- Restart the offending service

## Prevention
- Use connection pooling (PgBouncer)
- Set idle timeout in service configs
- Monitor pg_stat_activity in Grafana
- Alert when connections > 80% of limit

## Post-Incident
- Identify service that leaked connections
- Add connection pooling if missing
- Update thermal memory with incident

---
Cherokee AI Federation | FOR SEVEN GENERATIONS
