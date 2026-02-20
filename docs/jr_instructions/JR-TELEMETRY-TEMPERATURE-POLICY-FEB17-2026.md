# Jr Instruction: Telemetry Temperature Policy

**Kanban**: #1816
**Priority**: 8
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

On Feb 17 2026, the federation discovered that 52,000+ routine telemetry records (vision detections, coherence heartbeats) were stored at temperatures 80-100, drowning actual knowledge in RAG semantic search. Combined with the Grafana false-memory contamination (16,820 records), 82,311 records were manually recalibrated.

This instruction fixes the temperature assignment AT THE SOURCE so new telemetry follows the correct policy:

| Event Type | Temperature | Rationale |
|-----------|-------------|-----------|
| Routine vision detection (0 objects, normal counts) | 30 | Telemetry, not knowledge |
| Vision detection with security alerts | 85 | Actionable, needs attention |
| Council vote (real deliberation question) | 85 | Decision record — keep as-is |
| Council coherence heartbeat check | 35 | Routine heartbeat, not a real question |
| Vote-first result | 75 | Faster path, lower ceremony |
| Sacred/manual entries | 95-100 | Protected, TPM or council decision |

IMPORTANT: This is purely SEARCH/REPLACE on temperature values. No new features, no new logic. Just changing numbers.

## Step 1: Fix vision detection temperature in tribal_vision.py

File: `/ganuda/services/vision/tribal_vision.py`

<<<<<<< SEARCH
                    'WHITE_HOT' if detections['alerts'] else 'FRESH',
                    100 if detections['alerts'] else 50,
=======
                    'WHITE_HOT' if detections['alerts'] else 'COOL',
                    85 if detections['alerts'] else 30,
>>>>>>> REPLACE

## Step 2: Fix vote-first storage temperature in specialist_council.py

The vote-first results are stored at temp 85. These are quick votes, not full deliberations. Drop to 75.

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (result.audit_hash, content, 85.0, json.dumps(metadata)))
=======
            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (result.audit_hash, content, 75.0, json.dumps(metadata)))
>>>>>>> REPLACE

## Verification

After deployment, create a test vision detection and verify it stores at temp 30:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT id, temperature_score, LEFT(original_content, 80) FROM thermal_memory_archive WHERE original_content LIKE 'VISION DETECTION%' ORDER BY id DESC LIMIT 3;"
```

New routine detections should show temperature_score = 30.

## Notes

- The full council vote path (/council/vote) stores at temp 85 — this is correct for real deliberation questions, leave it
- The vote-first path stores at 75 — lower ceremony, lower temp
- Sacred memories (temp 95-100) are ONLY set by TPM or explicit sacred_pattern=true
- The coherence heartbeat checks from cruise_monitor.py are historical (stopped generating Feb 6) — no code fix needed, the daemon is not currently running
- The bulk historical records were already recalibrated on Feb 17 2026 (memory #101771)
