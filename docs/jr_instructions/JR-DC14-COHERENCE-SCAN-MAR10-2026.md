# JR INSTRUCTION: DC-14 Coherence Scan — Session Boot Delta Detection
**Task**: DC14-COHERENCE-001
**Priority**: P2
**Estimated SP**: 3
**Assigned**: Software Engineer Jr.
**Created**: 2026-03-10
**Design Ref**: /ganuda/docs/design/DC-14-WATERSHED-ZERO-TRUST-TRANSIT-MAR10-2026.md

## Objective
Build the coherence scan — the federation's session boot sequence. When a new Claude session starts, it needs to know what changed since the last session before doing anything else. Like waking up: check the room before checking the calendar. This is sub-check #1 of the DC-14 Watershed Layer amendment: delta detection across thermal memory, fire guard state, Jr queue, council votes, and thread bookmarks.

## Structured Replacement Blocks

### CREATE `/ganuda/scripts/coherence_scan.py`

The script has been pre-written at `/ganuda/scripts/coherence_scan.py`. Verify it matches the following structure and behavior:

**Connection pattern**: Use `ganuda_db.get_db_config()` from `/ganuda/lib/ganuda_db/__init__.py` as primary. Fall back to manual config (host=192.168.132.222, dbname=zammad_production, user=claude, password from CHEROKEE_DB_PASS env var) if ganuda_db import fails.

**sys.path setup**:
```python
sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda')
```

**Five scan functions**:

1. `scan_thermal_delta(cur)` — Query `thermal_memory_archive` for entries where `created_at > NOW() - INTERVAL '24 hours'`. Return count + top 5 ordered by `temperature DESC`.

2. `scan_fire_guard_alerts(cur)` — Query `specialist_health` for most recent entry per `specialist_id` where `circuit_breaker_state != 'CLOSED'`. Use `DISTINCT ON (specialist_id)` with `ORDER BY specialist_id, last_check_at DESC`.

3. `scan_jr_tasks(cur)` — Query `jr_work_queue` where `status IN ('pending', 'in_progress', 'assigned')`. Count + list with title, status, priority. Order by priority (P1 first) then created_at DESC.

4. `scan_recent_votes(cur)` — Query `council_votes` ordered by `voted_at DESC LIMIT 3`. Return question snippet (first 100 chars), vote_confidence, audit_hash.

5. `scan_thread_bookmarks()` — Read `/ganuda/config/thread_bookmarks.json` if it exists. Handle FileNotFoundError and JSONDecodeError gracefully. Return `{'available': False, 'note': ...}` if missing.

**Output modes**:
- Default / `--dry-run`: Structured text to stdout, suitable for loading into Claude session context.
- `--json`: Full scan results as JSON with `indent=2`. Use a custom serializer for datetime objects (`obj.isoformat()`).

**Text format**:
```
COHERENCE SCAN — Monday March 10, 2026 06:15 CT
============================================================

THERMAL DELTA: 47 memories in last 24h
  Top 5 by temperature:
    #120600 (temp 95) [SACRED]: ...content preview...
    ...

FIRE GUARD: All circuits CLOSED. No active alerts.

JR TASKS IN FLIGHT: 12
    [pending] P2 #1045: Wire Crane into specialist_council...
    ...

RECENT COUNCIL VOTES (last 3):
    [dae9f2a065b4f3a0] conf=0.839 — Slack federation channel mapping...
    ...

THREAD BOOKMARKS: thread_bookmarks.json not found

============================================================
End coherence scan. Room checked. Ready to proceed.
```

**Error handling**: Wrap main in try/finally, always close DB connection. Log errors via `logging`. Exit code 1 on failure.

**Cursor**: Use `psycopg2.extras.RealDictCursor` for all queries (consistent with dawn_mist pattern).

## Acceptance Criteria
- Script runs successfully: `python3 /ganuda/scripts/coherence_scan.py`
- `--json` flag produces valid JSON to stdout
- `--dry-run` flag produces structured text to stdout (same as no flags)
- All 5 scan sections appear in output even when results are empty (show zero counts, "no alerts", etc.)
- Missing `thread_bookmarks.json` does not cause an error — handled gracefully with a note
- DB connection uses `ganuda_db.get_db_config()` as primary path
- DB connection falls back to manual config if ganuda_db is unavailable
- Script exits cleanly (connection closed) on both success and failure
- No hardcoded passwords in the script — password comes from secrets_loader chain or CHEROKEE_DB_PASS env var
- Output is suitable for direct injection into a Claude session's context window

## Gotchas
- `specialist_health` table may not have rows yet if Fire Guard hasn't run — handle empty result set, don't crash.
- `thermal_memory_archive` column is `temperature` not `temperature_score` in the DB schema, but the column name may vary — check with `\d thermal_memory_archive` if queries fail. The script uses `temperature` aliased as `temperature_score` in the SELECT.
- `council_votes` uses `voted_at` for the timestamp, not `created_at`. Dawn mist already uses this convention — be consistent.
- `thread_bookmarks.json` does not exist yet. This is expected. The file will be created by a future Jr task (Watershed Layer sub-check #2: thread continuity). For now, the scan just reports it as missing.
- The `DISTINCT ON` syntax is PostgreSQL-specific. This is fine — bluefin is our only DB and it runs PostgreSQL.
- `jr_work_queue.priority` may contain values beyond P1-P4 or be NULL. The CASE statement in ORDER BY handles this with an ELSE clause.
- Text output says "CT" for timezone. The DB stores UTC. The script uses `datetime.now()` which gives local time. Ensure the redfin node's timezone is set to America/Chicago, or this label will be misleading.
