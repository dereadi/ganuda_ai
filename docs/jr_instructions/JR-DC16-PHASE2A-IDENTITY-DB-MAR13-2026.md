# JR INSTRUCTION: DC-16 Phase 2a — Create Identity Database + Connection Helper

**Task**: Create cherokee_identity database, db_connections.py helper, migrate identity tables ONLY. Proof-of-concept for full separation.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: DC-16 Phase 1 (Jr #1288) — completed
**Council Vote**: cf4ac0aeddc7eb75 (DC-16 Longhouse, 0.858)
**Previous Assessment**: Jr #1289 found 168 orphan tables, 16 FK breaks, 40+ files. Original instruction too ambitious for single Jr. This is the safe first step.

## Why Phase 2a Instead of Full Phase 2

The original Phase 2 instruction tried to do everything at once — create 3 databases, migrate ~100 tables, update 40+ files. The Jr assessment correctly flagged this as unsafe. This revised approach:

1. **Phase 2a** (THIS TASK): Create cherokee_identity + connection helper + migrate core identity tables
2. **Phase 2b** (NEXT): Create cherokee_ops + migrate ops tables
3. **Phase 2c** (NEXT): Create cherokee_telemetry + migrate telemetry tables
4. **Phase 2d** (LAST): Rewire daemons one at a time

## Step 1: Audit Current FK Relationships

BEFORE creating anything, run this query on bluefin to get the ACTUAL FK map:

```sql
-- Find ALL foreign key relationships between tables we plan to separate
SELECT
    tc.table_name AS source_table,
    kcu.column_name AS source_column,
    ccu.table_name AS target_table,
    ccu.column_name AS target_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
```

Save this output to `/ganuda/logs/dc16_fk_audit_phase2a.txt`. This is the ground truth.

## Step 2: Create cherokee_identity Database

```sql
CREATE DATABASE cherokee_identity OWNER claude;
\c cherokee_identity
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## Step 3: Create db_connections.py

Create `/ganuda/lib/db_connections.py` with the following content. This is the ONLY new file in this phase.

```python
"""DC-16 database connection helpers — three metabolic databases.

During migration: new helpers point to cherokee_identity/ops/telemetry.
Legacy get_db() still points to zammad_production.
Both work simultaneously. No daemon breaks.
"""
import os
import re
import psycopg2


def _load_secrets():
    """Load secrets.env if env vars not already set."""
    if os.environ.get("CHEROKEE_DB_PASS"):
        return
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                m = re.match(r"^(\w+)=(.+)$", line.strip())
                if m:
                    os.environ.setdefault(m.group(1), m.group(2))
    except FileNotFoundError:
        pass


def _connect(db_name_env, db_name_default, host_env=None, host_default="192.168.132.222"):
    """Internal: create a connection to a specific database."""
    _load_secrets()
    host = os.environ.get(host_env, host_default) if host_env else host_default
    return psycopg2.connect(
        host=host,
        port=5432,
        dbname=os.environ.get(db_name_env, db_name_default),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
        connect_timeout=10,
    )


def get_identity_db():
    """Connect to cherokee_identity — thermals, council, sacred patterns."""
    return _connect("CHEROKEE_IDENTITY_DB", "cherokee_identity",
                     "CHEROKEE_IDENTITY_HOST")


def get_ops_db():
    """Connect to cherokee_ops — jr_work_queue, heartbeats, task pipeline."""
    return _connect("CHEROKEE_OPS_DB", "cherokee_ops",
                     "CHEROKEE_OPS_HOST")


def get_telemetry_db():
    """Connect to cherokee_telemetry — timeline, fedattn, health checks, IoT."""
    return _connect("CHEROKEE_TELEMETRY_DB", "cherokee_telemetry",
                     "CHEROKEE_TELEMETRY_HOST")


def get_db():
    """Legacy: connect to zammad_production. Use specific helpers for new code."""
    return _connect("CHEROKEE_DB_NAME", "zammad_production",
                     "CHEROKEE_DB_HOST")
```

## Step 4: Migrate Core Identity Tables

Migrate ONLY these core identity tables. NOT all identity tables — just the ones with no cross-database FK issues:

```bash
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
  --table=thermal_memory_archive \
  --table=cold_thermal_archive \
  --table=thermal_relationships \
  --table=thermal_heat_map \
  --table=thermal_entity_links \
  --table=thermal_clauses \
  --table=thermal_memory_alert_archive \
  --table=memory_links \
  --table=memory_co_retrieval \
  --table=memory_chunks \
  --table=memory_retrieval_log \
  --table=jewel_feedback \
  --table=council_votes \
  --table=council_emotion_state \
  --table=council_emotion_audit \
  --table=longhouse_sessions \
  --table=epigenetic_modifiers \
  --table=sacred_fire_priority \
  --table=coyote_wisdom_archive \
  --table=teaching_stories \
  --table=resonance_patterns \
  --table=procedural_memory \
  -Fc -f /tmp/cherokee_identity_core.dump

pg_restore -h 192.168.132.222 -U claude -d cherokee_identity \
  --no-owner --no-privileges \
  /tmp/cherokee_identity_core.dump
```

## Step 5: Verify Row Counts

```sql
-- Run on BOTH zammad_production AND cherokee_identity
-- Counts MUST match exactly
SELECT 'thermal_memory_archive' AS tbl, COUNT(*) FROM thermal_memory_archive
UNION ALL SELECT 'council_votes', COUNT(*) FROM council_votes
UNION ALL SELECT 'longhouse_sessions', COUNT(*) FROM longhouse_sessions
UNION ALL SELECT 'council_emotion_state', COUNT(*) FROM council_emotion_state
UNION ALL SELECT 'procedural_memory', COUNT(*) FROM procedural_memory
ORDER BY tbl;
```

Save comparison to `/ganuda/logs/dc16_phase2a_row_counts.txt`.

## Step 6: Update secrets.env

Add to `/ganuda/config/secrets.env`:

```
# DC-16 Phase 2a — cherokee_identity (logical separation)
CHEROKEE_IDENTITY_DB=cherokee_identity
CHEROKEE_IDENTITY_HOST=192.168.132.222
```

## Step 7: Smoke Test

Test that db_connections.py works:

```python
python3 -c "
import sys; sys.path.insert(0, '/ganuda/lib')
from db_connections import get_identity_db, get_db

# Test new identity connection
conn = get_identity_db()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM thermal_memory_archive')
print(f'Identity DB thermals: {cur.fetchone()[0]}')
cur.close(); conn.close()

# Test legacy connection still works
conn = get_db()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM thermal_memory_archive')
print(f'Legacy DB thermals: {cur.fetchone()[0]}')
cur.close(); conn.close()

print('Both connections work. Phase 2a smoke test PASSED.')
"
```

## Step 8: Thermalize

```sql
-- In zammad_production (legacy, still the active write target)
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'DC-16 Phase 2a complete. cherokee_identity database created on bluefin. Core identity tables migrated (thermals, council, longhouse, emotion, procedural). db_connections.py helper created. Row counts verified. Legacy get_db() still works. No daemons rewired yet — that is Phase 2d.',
  75, 'infrastructure', false,
  encode(sha256(('DC-16-Phase2a-' || NOW()::text)::bytea), 'hex')
);
```

## DO NOT

- Migrate tables that have cross-database FK dependencies (those are Phase 2b/2c after FK audit)
- Rewire ANY daemon connection strings (that is Phase 2d)
- Drop ANY table from zammad_production
- Modify table schemas — this is a copy, not a redesign
- Touch council_saga_transactions, council_reasoning_log, or other council tables with potential FK chains — those come after FK audit review

## Acceptance Criteria

- cherokee_identity database exists on bluefin with vector + pg_trgm extensions
- Core identity tables migrated with matching row counts
- `/ganuda/lib/db_connections.py` exists and passes smoke test
- `/ganuda/config/secrets.env` has CHEROKEE_IDENTITY_DB and CHEROKEE_IDENTITY_HOST
- FK audit saved to `/ganuda/logs/dc16_fk_audit_phase2a.txt`
- Row count comparison saved to `/ganuda/logs/dc16_phase2a_row_counts.txt`
- zammad_production untouched — all original tables still present and active
- Thermal result stored
