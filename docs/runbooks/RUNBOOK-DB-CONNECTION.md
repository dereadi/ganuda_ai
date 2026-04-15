# RUNBOOK: PostgreSQL Connection Issues

## Symptoms
- Jrs failing with "could not connect to server"
- Thermal memory operations timing out
- "too many connections" errors

## Diagnosis

1. Test connectivity:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
   ```

2. Check connection count:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT count(*) FROM pg_stat_activity WHERE datname = 'zammad_production';"
   ```

3. Check for blocked queries:
   ```bash
   psql -h 192.168.132.222 -U claude -d zammad_production -c \
     "SELECT pid, state, query, wait_event_type
      FROM pg_stat_activity
      WHERE datname = 'zammad_production' AND state != 'idle';"
   ```

4. Check network:
   ```bash
   nc -zv 192.168.132.222 5432
   ping -c 3 192.168.132.222
   ```

## Resolution

### Level 1: Clear Idle Connections
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -c \
  "SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'zammad_production'
   AND state = 'idle'
   AND state_change < NOW() - INTERVAL '30 minutes';"
```

### Level 2: Check pg_hba.conf
On bluefin:
```bash
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -E "192.168|redfin"
# Ensure: host zammad_production claude 192.168.132.0/24 md5
```

### Level 3: Restart PostgreSQL (Maintenance Window)
On bluefin:
```bash
sudo systemctl restart postgresql
```

## Prevention
- Set connection pool limits in Jr code
- Configure idle connection timeout in pg
- Monitor connection count: alert at 80% of max
- Use connection pooler (PgBouncer) for high load

## Escalation
1. Check disk space on bluefin
2. Review PostgreSQL logs: /var/log/postgresql/
3. Contact DBA if persistent issues
