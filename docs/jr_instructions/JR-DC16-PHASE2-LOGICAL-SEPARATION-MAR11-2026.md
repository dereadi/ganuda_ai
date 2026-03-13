# JR INSTRUCTION: DC-16 Phase 2 — Logical Database Separation (Software-Only)

**Task**: Create cherokee_identity, cherokee_ops, cherokee_telemetry as separate databases on bluefin. Migrate tables. Update connection strings.
**Priority**: P1 — DC-16 core work, no hardware dependency
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 8
**Depends On**: DC-16 Phase 1 (Jr #1288) — indexes dropped, autovacuum tuned, retention applied
**Council Vote**: cf4ac0aeddc7eb75 (DC-16 Longhouse, 0.858)

## Problem Statement

271 tables in one database (zammad_production) share buffer cache, autovacuum workers, and WAL stream. thermal_memory_archive (identity) competes with jr_status (6.1M scans on 16 rows) for cache lines. Fire Guard heartbeats pollute the identity WAL. The logical separation must happen before the physical separation (hardware arriving by Sunday Mar 16).

## What You're Building

### Step 1: Create the Three Databases

Connect to bluefin (192.168.132.222) as the claude user (or a superuser if claude lacks CREATEDB).

```sql
-- Create the three metabolic databases
CREATE DATABASE cherokee_identity OWNER claude;
CREATE DATABASE cherokee_ops OWNER claude;
CREATE DATABASE cherokee_telemetry OWNER claude;

-- Enable pgvector in identity (for embedding indexes)
\c cherokee_identity
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm in identity (for text search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Step 2: Migrate Identity Tables

These tables ARE the organism's self. They move to cherokee_identity.

Use pg_dump/pg_restore for each table to preserve indexes, constraints, sequences, and data:

```bash
# Dump identity tables from zammad_production
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
  --table=thermal_memory_archive \
  --table=council_votes \
  --table=council_saga_transactions \
  --table=council_reasoning_log \
  --table=council_compensation_registry \
  --table=council_validations \
  --table=council_reflections \
  --table=council_agent_instances \
  --table=council_debate_rounds \
  --table=council_mcts_nodes \
  --table=council_refined_prompts \
  --table=council_validation_results \
  --table=council_objectives \
  --table=council_prediction_outcomes \
  --table=council_subtasks \
  --table=jr_council_awareness \
  --table=longhouse_sessions \
  --table=thermal_relationships \
  --table=thermal_memory_alert_archive \
  --table=thermal_clauses \
  --table=thermal_heat_map \
  --table=thermal_entity_links \
  --table=decision_reflections \
  --table=duyuktv_tickets \
  --table=sacred_fire_priority \
  --table=memory_links \
  --table=memory_co_retrieval \
  --table=project_specifications \
  --table=spec_task_links \
  --table=web_content \
  --table=linkedin_drafts \
  --table=legal_register \
  --table=ai_research_papers \
  --table=coyote_wisdom_archive \
  --table=teaching_stories \
  --table=epigenetic_modifiers \
  --table=resonance_patterns \
  -Fc -f /tmp/cherokee_identity_tables.dump

# Restore into cherokee_identity
pg_restore -h 192.168.132.222 -U claude -d cherokee_identity \
  --no-owner --no-privileges \
  /tmp/cherokee_identity_tables.dump
```

**CRITICAL**: Verify row counts match after restore:
```sql
-- On zammad_production
SELECT 'thermal_memory_archive' AS tbl, COUNT(*) FROM thermal_memory_archive
UNION ALL SELECT 'council_votes', COUNT(*) FROM council_votes
UNION ALL SELECT 'longhouse_sessions', COUNT(*) FROM longhouse_sessions;

-- On cherokee_identity (same queries)
-- Counts MUST match exactly
```

### Step 3: Migrate Operations Tables

These tables are the nervous system. They move to cherokee_ops.

```bash
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
  --table=jr_work_queue \
  --table=jr_status \
  --table=jr_agent_state \
  --table=jr_failed_tasks_dlq \
  --table=jr_task_completions \
  --table=jr_execution_learning \
  --table=jr_learning_events \
  --table=jr_learning_state \
  --table=jr_step_rewards \
  --table=jr_execution_sessions \
  --table=jr_task_announcements \
  --table=jr_macro_agent_state \
  --table=jr_collective_identity \
  --table=jr_agent_relationships \
  --table=jr_task_checkpoints \
  --table=jr_chief_flags \
  --table=jr_task_bids \
  --table=jr_rl_experience \
  --table=jr_agent_observable_state \
  --table=jr_bidding_fairness \
  --table=jr_trust_parameters \
  --table=jr_rl_models \
  --table=jr_agent_clusters \
  --table=jr_bid_intentions \
  --table=jr_network_shortcuts \
  --table=jr_exploration_log \
  --table=jr_coherence_measurements \
  --table=service_health \
  --table=elisi_state \
  --table=sag_events \
  --table=specialist_health \
  --table=specialist_memory_states \
  --table=immune_registry \
  --table=api_keys \
  --table=api_audit_log \
  --table=tpm_notifications \
  --table=moltbook_post_queue \
  --table=research_jobs \
  --table=emails \
  --table=email_classifications \
  --table=service_registry \
  --table=fse_key_strength \
  --table=fse_usage_events \
  --table=token_ledger \
  --table=users \
  --table=user_sessions \
  --table=long_man_cycles \
  --table=basin_signal_history \
  --table=execution_audit_log \
  --table=failure_detection_log \
  --table=kanban_ticket_log \
  -Fc -f /tmp/cherokee_ops_tables.dump

pg_restore -h 192.168.132.222 -U claude -d cherokee_ops \
  --no-owner --no-privileges \
  /tmp/cherokee_ops_tables.dump
```

### Step 4: Migrate Telemetry Tables

Time-series and sensory data. Moves to cherokee_telemetry.

```bash
pg_dump -h 192.168.132.222 -U claude -d zammad_production \
  --table=unified_timeline \
  --table=health_check_log \
  --table=fedattn_sessions \
  --table=fedattn_contributions \
  --table=tribe_power_metrics \
  --table=tribe_power_daily \
  --table=tribe_config_registry \
  --table=tribe_enrollments \
  --table=tribe_wizard_progress \
  --table=tribe_documents \
  --table=drift_metrics \
  --table=stereo_speed_detections \
  --table=iot_scan_history \
  --table=iot_devices \
  --table=iot_device_services \
  --table=iot_traffic_patterns \
  --table=agent_external_comms \
  --table=unified_brain_state \
  -Fc -f /tmp/cherokee_telemetry_tables.dump

pg_restore -h 192.168.132.222 -U claude -d cherokee_telemetry \
  --no-owner --no-privileges \
  /tmp/cherokee_telemetry_tables.dump
```

### Step 5: Update secrets.env

Add new connection parameters to `/ganuda/config/secrets.env`:

```bash
# DC-16 Separation of Memory — database-specific connections
# Phase 2: all on bluefin. Phase 3: ops→redfin, telemetry→SAN
CHEROKEE_IDENTITY_DB=cherokee_identity
CHEROKEE_OPS_DB=cherokee_ops
CHEROKEE_TELEMETRY_DB=cherokee_telemetry

# Host stays bluefin for now. Phase 3 changes these.
CHEROKEE_IDENTITY_HOST=192.168.132.222
CHEROKEE_OPS_HOST=192.168.132.222
CHEROKEE_TELEMETRY_HOST=192.168.132.222
```

### Step 6: Update Connection Strings in Daemons

Every daemon that connects to the DB must be updated to use the correct database. This is the biggest step.

**Pattern**: Replace `dbname=zammad_production` (or the env var that resolves to it) with the appropriate database.

Key files to update (search for `CHEROKEE_DB_NAME` or `zammad_production` or `get_db`):

**Identity consumers** (connect to cherokee_identity):
- `/ganuda/scripts/fire_guard.py` — thermal reads/writes
- `/ganuda/scripts/council_dawn_mist.py` — council + thermal
- `/ganuda/scripts/council_telegram_async.py` — council reads
- `/ganuda/scripts/generate_status_page.py` — thermal + council reads
- `/ganuda/scripts/generate_ops_console.py` — thermal + council reads
- `/ganuda/scripts/deer_jewel_digest.py` — thermal reads
- `/ganuda/lib/specialist_council.py` — council writes
- `/ganuda/lib/longhouse.py` — longhouse writes
- `/ganuda/lib/alert_manager.py` — thermal writes
- `/ganuda/daemons/governance_agent.py` — council reads/writes
- `/ganuda/services/breathing_api.py` — thermal + council reads (when built)

**Ops consumers** (connect to cherokee_ops):
- `/ganuda/daemons/tpm_autonomic_v2.py` — jr_work_queue polling
- `/ganuda/jr_executor/task_executor.py` — jr_work_queue updates
- `/ganuda/jr_executor/jr_queue_client.py` — jr_work_queue inserts
- `/ganuda/email_daemon/job_email_daemon_v2.py` — email processing
- `/ganuda/services/ulisi/heartbeat.py` — service_health writes
- `/ganuda/services/ulisi/observer.py` — service monitoring

**Telemetry consumers** (connect to cherokee_telemetry):
- `/ganuda/services/power_monitor/power_monitor.py` — iot writes
- `/ganuda/services/power_monitor/solix_monitor_daemon.py` — iot writes

**IMPORTANT**: Some daemons need MULTIPLE connections (e.g., fire_guard reads thermals from identity AND writes heartbeats that should go to telemetry). These need TWO connection helpers — `get_identity_db()` and `get_telemetry_db()`.

Create a shared connection helper in `/ganuda/lib/db_connections.py`:

```python
"""DC-16 database connection helpers — three metabolic databases."""
import os
import re
import psycopg2
import psycopg2.extras

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

def get_identity_db():
    """Connect to cherokee_identity — thermals, council, sacred patterns."""
    _load_secrets()
    return psycopg2.connect(
        host=os.environ.get("CHEROKEE_IDENTITY_HOST", "192.168.132.222"),
        port=5432,
        dbname=os.environ.get("CHEROKEE_IDENTITY_DB", "cherokee_identity"),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
    )

def get_ops_db():
    """Connect to cherokee_ops — jr_work_queue, heartbeats, task pipeline."""
    _load_secrets()
    return psycopg2.connect(
        host=os.environ.get("CHEROKEE_OPS_HOST", "192.168.132.222"),
        port=5432,
        dbname=os.environ.get("CHEROKEE_OPS_DB", "cherokee_ops"),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
    )

def get_telemetry_db():
    """Connect to cherokee_telemetry — timeline, fedattn, health checks, IoT."""
    _load_secrets()
    return psycopg2.connect(
        host=os.environ.get("CHEROKEE_TELEMETRY_HOST", "192.168.132.222"),
        port=5432,
        dbname=os.environ.get("CHEROKEE_TELEMETRY_DB", "cherokee_telemetry"),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
    )

# Backward compatibility — falls back to zammad_production during migration
def get_db():
    """Legacy: connect to zammad_production. Use specific helpers above for new code."""
    _load_secrets()
    return psycopg2.connect(
        host=os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222"),
        port=5432,
        dbname=os.environ.get("CHEROKEE_DB_NAME", "zammad_production"),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ.get("CHEROKEE_DB_PASS", ""),
    )
```

### Step 7: Dual-Write Transition Period

During migration, keep zammad_production as the source of truth. The new databases are shadows until verified.

1. Create the databases and restore tables (Steps 1-4)
2. Update ONE daemon at a time to use new connection strings
3. Verify it works (check logs, check data)
4. Move to next daemon
5. After ALL daemons migrated: verify zammad_production originals are no longer being written to
6. Only THEN: rename/archive the original tables in zammad_production

**DO NOT** drop tables from zammad_production until ALL consumers are verified on new databases.

### Step 8: Verify Separation

```sql
-- On cherokee_identity: should have thermals, council, longhouse
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- On cherokee_ops: should have jr_*, service_health, etc.
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- On cherokee_telemetry: should have unified_timeline, fedattn, health_check_log
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Row count verification: every migrated table must match source
```

### Step 9: Thermalize

```sql
-- In cherokee_identity (its new home!)
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
VALUES (
  'DC-16 Phase 2 complete. Logical separation achieved. Three databases created on bluefin: cherokee_identity, cherokee_ops, cherokee_telemetry. Tables migrated. Connection strings updated. Dual-write transition verified. Ready for Phase 3 physical separation when hardware arrives (by Mar 16).',
  78, 'infrastructure', false,
  encode(sha256(('DC-16-Phase2-' || NOW()::text)::bytea), 'hex')
);
```

## Constraints

- **DC-16**: This is the logical separation. Same server, different databases. Buffer cache, autovacuum, and connection pools are already separated at the database level in PostgreSQL.
- **DC-7**: Sacred and canonical memories must survive the migration with zero data loss. Verify row counts.
- **Turtle**: Dual-write transition. Do NOT drop originals until verified. One daemon at a time.
- **Crawdad**: The credential (CHEROKEE_DB_PASS) is the same for all three databases. One user, three databases. No new credentials to manage.
- Phase 1 (Jr #1288) must complete first — indexes dropped, autovacuum tuned, retention applied before migration.
- Some tables may have FK relationships that span categories (e.g., spec_task_links references both jr_work_queue and project_specifications). These FKs cannot cross databases. Document which FKs are broken and plan alternatives (application-level enforcement).

## Cross-Database FK Resolution

PostgreSQL does not support foreign keys across databases. The following known FKs will break:

1. `jr_work_queue.specification_id` → `project_specifications.id` (ops → identity)
   - **Resolution**: Drop FK. Enforce in application code. specification_id is nullable and rarely used.

2. `spec_task_links` references both `project_specifications` and `jr_work_queue`
   - **Resolution**: Keep spec_task_links in identity (it's metadata about specs). Application-level join when needed.

Document any additional cross-category FKs discovered during migration.

## Target Files

- bluefin PostgreSQL: CREATE DATABASE x3, pg_dump/pg_restore, verification queries
- `/ganuda/lib/db_connections.py` — new shared connection helper (CREATE)
- `/ganuda/config/secrets.env` — add new DB connection vars (MODIFY)
- ~15 daemon/script files — update get_db() calls to use specific helpers (MODIFY)

## Acceptance Criteria

- Three databases exist on bluefin: cherokee_identity, cherokee_ops, cherokee_telemetry
- Row counts match source for all migrated tables
- `lib/db_connections.py` provides get_identity_db(), get_ops_db(), get_telemetry_db()
- At least 3 critical daemons migrated to new connections (fire_guard, tpm_autonomic_v2, task_executor)
- No data loss — zammad_production originals preserved until full verification
- Thermal result stored in cherokee_identity

## DO NOT

- Drop any table from zammad_production during this phase
- Migrate all daemons at once — one at a time, verify each
- Create new credentials — same claude user for all three databases
- Skip row count verification after restore
- Break running services — if a daemon fails after migration, revert its connection string to zammad_production immediately
- Modify table schemas — this is a move, not a redesign
