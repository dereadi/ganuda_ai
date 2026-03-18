# JR INSTRUCTION: DB Health Completion — Rollback Rate to SLA

**Task**: Complete the DB health remediation. Patch remaining psycopg2 commit patterns, deploy PgBouncer, wire weekly reports, add memory leak monitoring.
**Priority**: P1
**Date**: 2026-03-18
**TPM**: Claude Opus
**Story Points**: 9
**Project Spec**: #3
**Depends On**: DB query monitor (LIVE), fire-guard (LIVE), ganuda_db (MODIFIED)
**Thermal Context**: DB rollback investigation, Partner Remedy heritage

## Context

Rollback rate dropped from 37.7% to 29.4% after fixing psycopg2 autocommit=False in `ganuda_db/__init__.py`, `jr_task_executor.py`, and `jr_bidding_daemon.py`. Still above 5% SLA target. Root cause: psycopg2's default autocommit=False causes every SELECT without commit to count as ROLLBACK when connection closes.

## Task 1: Patch Remaining psycopg2 Commit Patterns (3 SP, P-3)

Find ALL Python files that use psycopg2 connections and close them without committing after read-only queries.

**Search pattern**: Look for `conn.close()` without preceding `conn.commit()` in the same function/block.

**Known locations to check**:
- `/ganuda/services/` — all service files
- `/ganuda/scripts/` — fire_guard, safety_canary, governance_agent, db_query_monitor
- `/ganuda/lib/` — any module that imports psycopg2 or ganuda_db

**Fix pattern**:
```python
# BEFORE (causes rollback on read-only):
cur.execute("SELECT ...")
result = cur.fetchall()
conn.close()

# AFTER:
cur.execute("SELECT ...")
result = cur.fetchall()
conn.commit()  # Explicit commit, even for reads
conn.close()
```

**Do NOT change**: Any path that intentionally uses transactions with rollback on error. Only fix the "forgot to commit before close" pattern.

## Task 2: PgBouncer Connection Pooling (3 SP, P-2)

Deploy PgBouncer on bluefin as a connection pooler in front of PostgreSQL.

**Requires**: Council vote before deploy.

**Configuration**:
- Pool mode: transaction (not session — we want connection reuse)
- Max client connections: 200
- Default pool size: 20
- Reserve pool size: 5
- Listen on: localhost:6432
- Forward to: localhost:5432

**Migration path**: Update ganuda_db connection string to point to :6432 instead of :5432. Test with one service first (db_query_monitor), then roll to all.

## Task 3: Weekly Query Offender Report Timer (1 SP, P-1)

The db-query-monitor has a `--report` mode. Wire it to a systemd timer.

```ini
[Unit]
Description=Weekly DB Query Offender Report

[Timer]
OnCalendar=Wed 04:45
Persistent=true

[Install]
WantedBy=timers.target
```

Report should post to Slack #fire-guard and be compatible with owl-debt-reckoning consumption.

## Task 4: Fire-Guard RSS Tracking (2 SP, P-1)

Add to fire-guard's health check loop:
1. For each service in the necklace, read `/proc/<pid>/status` for VmRSS
2. Store RSS readings in a rolling 24-hour window (CSV or DB)
3. Alert if RSS grows >20% from baseline over 24 hours without restart
4. Weekly memory report alongside query offender report

**Services to monitor**: consultation-ring, gateway, jr-executor, jr-bidding-daemon, db-query-monitor, fire-guard itself.

## Task 5: Verify SLA (0 SP, P-Day)

Run: `SELECT round(100.0 * xact_rollback / (xact_commit + xact_rollback), 1) FROM pg_stat_database WHERE datname = current_database()`

Must show < 5%. If not, identify remaining offenders from the weekly report.
