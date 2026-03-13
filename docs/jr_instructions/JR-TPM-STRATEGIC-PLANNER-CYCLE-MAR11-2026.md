# JR INSTRUCTION: TPM Strategic Planner — Self-Directing Work Cycle

**Task**: Add a strategic planning cycle to tpm_autonomic_v2.py that autonomously identifies, decomposes, and queues work from the roadmap
**Priority**: P2 — the organism should build toward goals, not just execute what's handed to it
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 8
**Chief Context**: "Does the cluster only work when I talk to you?" — The organism maintains itself (Fire Guard, Dawn Mist, timers) but doesn't currently pursue strategic goals autonomously. The TPM daemon executes queued tasks but never queues new ones.

## Problem Statement

The TPM Autonomic Daemon v2 (`/ganuda/daemons/tpm_autonomic_v2.py`) is a worker — it polls jr_work_queue, claims pending tasks, executes them via Claude Agent SDK, monitors basin signals, and escalates phase transitions. What it does NOT do is plan. It never looks at the kanban, never reads Jr instructions that haven't been queued yet, never consults the council about what to build next.

Result: the organism breathes but doesn't grow unless Chief or TPM manually queues work during a conversation. The pipeline between "Jr instruction exists" and "Jr instruction gets executed" requires a human in the loop.

## What You're Building

### Step 1: Strategic Planning Cycle

Add a new method `_strategic_plan()` to `TPMAutonomicDaemon` that runs every `STRATEGIC_INTERVAL` seconds (default: 3600 — once per hour).

The planning cycle:

1. **Scan for unqueued Jr instructions**:
```python
# Find Jr instruction files that don't have a matching jr_work_queue entry
import glob
instruction_files = glob.glob("/ganuda/docs/jr_instructions/JR-*.md")
# For each, check if a task with that instruction_file path exists in jr_work_queue
# If not, it's an unqueued instruction — candidate for autonomous queueing
```

2. **Check kanban priorities**:
```sql
SELECT id, title, description, priority, sacred_fire_priority
FROM duyuktv_tickets
WHERE status IN ('open', 'backlog')
  AND priority IS NOT NULL
ORDER BY sacred_fire_priority DESC NULLS LAST, priority ASC
LIMIT 10
```

3. **Check queue depth** — don't flood the pipeline:
```sql
SELECT COUNT(*) FROM jr_work_queue WHERE status = 'pending'
```
If pending > 10, skip planning this cycle. The pipeline is full.

4. **Consult council** before queueing strategic work:
```python
# POST to /v1/council/vote with:
# "Should we queue [instruction title]? Current queue depth: N,
#  kanban priority: P, dependencies: [list]"
# Only queue if council approves (confidence > 0.7)
```

5. **Queue approved work**:
```python
# Insert into jr_work_queue with:
# - instruction_file path
# - title from the Jr instruction header
# - priority from kanban or instruction metadata
# - source = 'tpm_strategic_planner'
# - created_by = 'TPM Autonomic Daemon v2'
```

6. **Thermalize the decision**:
```python
log_thermal_memory(
    f"TPM Strategic Planner queued task: {title}. "
    f"Council vote: {audit_hash} ({confidence}). "
    f"Queue depth: {queue_depth}. Reason: {reason}.",
    temperature=72.0
)
```

### Step 2: Instruction Parser

Add a helper that extracts metadata from Jr instruction files:

```python
def parse_instruction_metadata(filepath):
    """Extract title, priority, story points, dependencies from Jr instruction header."""
    with open(filepath) as f:
        content = f.read(2000)  # Header only

    metadata = {"filepath": filepath}

    # Parse YAML-like header fields
    for line in content.split("\n")[:20]:
        if line.startswith("**Task**:"):
            metadata["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Priority**:"):
            metadata["priority_raw"] = line.split(":", 1)[1].strip()
            # Extract P-level: P0=1, P1=2, P2=3, P3=4
            if "P0" in line: metadata["priority"] = 1
            elif "P1" in line: metadata["priority"] = 2
            elif "P2" in line: metadata["priority"] = 3
            else: metadata["priority"] = 4
        elif line.startswith("**Story Points**:"):
            try:
                metadata["story_points"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                metadata["story_points"] = 5
        elif line.startswith("**Depends On**:"):
            metadata["depends_on"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Council Vote**:"):
            metadata["council_vote"] = line.split(":", 1)[1].strip()

    return metadata
```

### Step 3: Dependency Awareness

The planner must respect dependency chains. If instruction B says `**Depends On**: Chain Protocol foundation`, don't queue B until the Chain Protocol task is completed.

```python
def check_dependencies_met(metadata):
    """Check if an instruction's dependencies are satisfied."""
    depends = metadata.get("depends_on", "")
    if not depends:
        return True

    # Search jr_work_queue for completed tasks matching the dependency
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM jr_work_queue
        WHERE status = 'completed'
        AND title ILIKE %s
    """, (f"%{depends[:50]}%",))
    count = cur.fetchone()["count"]
    cur.close()
    put_db(conn)
    return count > 0
```

### Step 4: Wire Into Main Loop

In `TPMAutonomicDaemon.__init__()`:
```python
self.last_strategic_plan = datetime.min
```

Add configuration constant:
```python
STRATEGIC_INTERVAL = int(os.environ.get("TPM_STRATEGIC_INTERVAL", "3600"))
MAX_QUEUE_DEPTH = int(os.environ.get("TPM_MAX_QUEUE_DEPTH", "10"))
```

In the main `run()` loop, after basin checks:
```python
# Strategic planning cycle
if (now - self.last_strategic_plan).total_seconds() >= STRATEGIC_INTERVAL:
    await self._strategic_plan()
    self.last_strategic_plan = now
```

### Step 5: Guardrails

The planner must NOT:
- Queue more than 3 tasks per planning cycle (prevent flooding)
- Queue tasks with unmet dependencies
- Queue tasks that already exist in jr_work_queue (any status)
- Queue tasks without council approval (confidence > 0.7)
- Queue tasks when pending queue depth > MAX_QUEUE_DEPTH
- Spend more than $5 total on council votes per planning cycle

Add a SITREP after each planning cycle:
```python
send_telegram(
    f"📋 *TPM Strategic Planner* cycle complete\n"
    f"Scanned: {len(instruction_files)} instructions\n"
    f"Unqueued: {len(unqueued)}\n"
    f"Queued this cycle: {len(newly_queued)}\n"
    f"Skipped (deps): {len(skipped_deps)}\n"
    f"Skipped (queue full): {queue_depth > MAX_QUEUE_DEPTH}\n"
    f"Next cycle: {STRATEGIC_INTERVAL // 60}m"
)
```

## Constraints

- **DC-9**: Council votes for planning decisions use Sonnet, not Opus. Keep planning costs low.
- **DC-10**: Planning is deliberate (Tier 2/3), not reflex. Hourly cycle is appropriate. Do NOT make it faster.
- **Coyote**: The planner must consult the council. No autonomous queueing without a vote. The organism self-directs, but the council governs.
- **Turtle**: Max 3 tasks queued per cycle. If something goes wrong, the blast radius is small.
- **Spider**: Track planning decisions in thermal memory. Every queue/skip decision must have a record.
- Do NOT modify the existing task execution loop. The planner ADDS to the daemon, it doesn't replace anything.
- `claude-agent-sdk` import may not be available — the planning cycle should work even if SDK isn't installed (it only needs DB access and gateway API for council votes).

## Target Files

- `/ganuda/daemons/tpm_autonomic_v2.py` — add strategic planner cycle (MODIFY)

## Acceptance Criteria

- `python3 -c "import py_compile; py_compile.compile('daemons/tpm_autonomic_v2.py', doraise=True)"` passes
- Planning cycle runs every STRATEGIC_INTERVAL seconds
- Unqueued Jr instructions are detected by scanning `/ganuda/docs/jr_instructions/`
- Dependencies are checked before queueing
- Council is consulted before each queue decision
- No more than 3 tasks queued per cycle
- No tasks queued when pending depth > MAX_QUEUE_DEPTH
- SITREP sent to Telegram/Slack after each planning cycle
- All decisions thermalized

## DO NOT

- Remove or modify the existing task execution loop
- Queue tasks without council approval
- Queue tasks with unmet dependencies
- Make the planning cycle faster than hourly (DC-9)
- Queue tasks that already exist in jr_work_queue
- Allow the planner to modify Jr instructions — it reads and queues, never writes
- Skip the SITREP — Chief needs to see what the organism is doing autonomously
