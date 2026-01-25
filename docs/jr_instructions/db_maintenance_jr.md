# Jr Task: PostgreSQL Database Maintenance

**Date**: January 5, 2026
**Priority**: HIGH
**Target Node**: bluefin (192.168.132.222)
**Database**: zammad_production

## Background
Regular maintenance is critical for PostgreSQL performance. This task ensures:
- Dead rows are cleaned up (prevent bloat)
- Idle transactions don't hold locks indefinitely
- Statistics are current for query planner

## Task 1: Set Idle Transaction Timeout

The database currently has `idle_in_transaction_session_timeout = 0` (no timeout), which allowed transactions to sit idle for 16+ hours holding locks.

**Execute as postgres user on bluefin:**

```bash
sudo -u postgres psql -c "ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';"
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

**Verify:**
```bash
sudo -u postgres psql -c "SHOW idle_in_transaction_session_timeout;"
# Should show: 5min
```

## Task 2: Schedule Weekly VACUUM FULL

thermal_memory_archive has persistent bloat requiring VACUUM FULL.

**Create maintenance script `/ganuda/scripts/weekly_vacuum.sh`:**

```bash
#!/bin/bash
# Cherokee AI Federation - Weekly PostgreSQL Maintenance
# Run Sunday 3 AM when system is quiet

LOG_FILE="/var/log/ganuda/weekly_vacuum.log"
echo "=== VACUUM FULL Started $(date) ===" >> $LOG_FILE

PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production <<EOF >> $LOG_FILE 2>&1
-- VACUUM FULL reclaims disk space (blocking operation)
VACUUM FULL thermal_memory_archive;
VACUUM FULL fedattn_sessions;
VACUUM FULL fedattn_contributions;

-- ANALYZE all tables for query planner
ANALYZE;

-- Report
SELECT relname, n_live_tup, n_dead_tup, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
WHERE n_live_tup > 100
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
EOF

echo "=== VACUUM FULL Completed $(date) ===" >> $LOG_FILE
```

**Add to crontab:**
```bash
chmod +x /ganuda/scripts/weekly_vacuum.sh
crontab -e
# Add: 0 3 * * 0 /ganuda/scripts/weekly_vacuum.sh
```

## Task 3: Create Monitoring Query

Add to Grafana or periodic check:

```sql
-- Connection health
SELECT state, count(*), max(NOW() - query_start) as oldest
FROM pg_stat_activity
WHERE datname = 'zammad_production'
GROUP BY state;

-- Bloat detection (alert if dead_pct > 20)
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup, 0), 1) as dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 100
ORDER BY dead_pct DESC;

-- Long queries (alert if > 1 hour)
SELECT pid, NOW() - query_start as duration, LEFT(query, 60)
FROM pg_stat_activity
WHERE state = 'active' AND NOW() - query_start > interval '1 hour';
```

## Acceptance Criteria
- [ ] idle_in_transaction_session_timeout set to 5min
- [ ] weekly_vacuum.sh created and scheduled
- [ ] Monitoring query added to Grafana or periodic check
- [ ] KB article KB-DB-001 created documenting this maintenance

## For Seven Generations
