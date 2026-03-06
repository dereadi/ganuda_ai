# ULTRATHINK: Specification Engineering Layer

**Date**: February 27, 2026
**Author**: TPM (Peace Chief)
**Council Vote**: #1d2ba22feb928108 (0.743 confidence, APPROVED WITH CONDITIONS)
**Long Man Phase**: DISCOVER ✓ → DELIBERATE ✓ → ADAPT (this document) → BUILD → RECORD → REVIEW

---

## Origin

Three threads converged on February 27, 2026:

1. **Gap Analysis**: 22 gaps identified from the Feb 26 night session. Gaps 13+14 (CRITICAL): DC-1 through DC-5 declared BINDING but never ratified by council. Now ratified.
2. **Nate B. Jones Framework**: Four disciplines of prompting — Prompt Craft, Context Engineering, Intent Engineering, Specification Engineering. The federation already implements all four, but the spec layer is implicit (one-shot Jr instructions) rather than explicit (persistent specifications).
3. **System 3 Neuro-Symbolic Papers**: LogicGraph + ImpRIF demonstrate LLMs build semantic bridges (sounds right) not logical bridges (is right). DLQ failures are semantic bridges that collapsed. Specifications are the discrete reasoning graph that constrains Jr execution to verified logic.

**Chief's directive**: "Below stories we should have specifications. We can have the Jrs follow those specs for days."

---

## Problem Statement

**Current flow**: Kanban ticket → Jr instruction (one-shot markdown) → Jr work queue → execute

Jr instructions are disposable. Each describes a single task. There is no persistent specification layer that:
- Records the actual state of target files at write-time
- Defines machine-checkable acceptance criteria
- Provides framework/architecture context to prevent mismatches
- Supports multi-day Jr execution against a stable reference
- Links strategy (kanban) to execution (Jr tasks) with traceability

**DLQ root cause analysis** (KB-DLQ-TRIAGE-PATTERNS-FEB22-2026):
- 60% of failures: stale SEARCH strings (TPM's mental model diverged from actual code)
- 15% of failures: mixed step types in one instruction (structural error)
- 10% of failures: architecture assumption mismatches (psycopg2 vs SQLAlchemy)

**Estimated prevention**: Specification layer could prevent ~65% of DLQ failures.

---

## Architecture Design

### New Tables

#### `project_specifications`

The persistent, agent-readable spec that lives between kanban tickets and Jr instructions.

```sql
CREATE TABLE project_specifications (
    id                  SERIAL PRIMARY KEY,
    spec_id             VARCHAR(64) UNIQUE NOT NULL,

    -- Links
    kanban_ticket_id    INTEGER REFERENCES duyuktv_tickets(id),

    -- Identity
    title               VARCHAR(255) NOT NULL,
    goal                TEXT NOT NULL,

    -- Nate Jones Five Primitives
    problem_statement   TEXT NOT NULL,           -- Primitive 1: Self-contained
    acceptance_criteria JSONB DEFAULT '[]',      -- Primitive 2: What done looks like
    constraints         JSONB DEFAULT '{}',      -- Primitive 3: Musts, must-nots, preferences, escalation
    decomposition       JSONB DEFAULT '[]',      -- Primitive 4: Typed DAG phases
    evaluation_criteria JSONB DEFAULT '[]',      -- Primitive 5: How to prove output is good

    -- Code context (DLQ prevention)
    target_files        TEXT[] NOT NULL DEFAULT '{}',
    target_file_hashes  JSONB DEFAULT '{}',      -- {filepath: sha256_at_spec_write}
    framework_notes     TEXT,                    -- "Uses FastAPI+SQLAlchemy, NOT raw psycopg2"

    -- Lifecycle
    status              VARCHAR(50) DEFAULT 'draft',
    river_cycle         VARCHAR(50),
    council_vote_id     VARCHAR(64),
    created_by          VARCHAR(100) NOT NULL DEFAULT 'tpm',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `spec_task_links`

Many-to-many: one spec → many Jr tasks. One Jr task → one spec (usually).

```sql
CREATE TABLE spec_task_links (
    spec_id     INTEGER REFERENCES project_specifications(id),
    task_queue_id INTEGER REFERENCES jr_work_queue(id),
    phase_id    VARCHAR(50),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (spec_id, task_queue_id)
);
```

### Schema Design Decisions

**Why `acceptance_criteria` is JSONB array, not text**:
Each criterion maps to a post-execution check. Types:
- `{"type": "grep", "file": "/ganuda/path", "pattern": "def my_func"}` — file contains pattern
- `{"type": "not_grep", "file": "/ganuda/path", "pattern": "DEPRECATED"}` — file does not contain
- `{"type": "syntax", "file": "/ganuda/path"}` — py_compile passes
- `{"type": "service_running", "service": "web-materializer"}` — systemd active
- `{"type": "db_query", "sql": "SELECT count(*) FROM table", "expected": ">0"}` — DB state

**Why `decomposition` is JSONB array of phases, not freeform**:
```json
[
  {"phase_id": "p1", "name": "Schema migration", "files": ["/ganuda/scripts/migrations/..."], "depends_on": null},
  {"phase_id": "p2", "name": "Seeder script", "files": ["/ganuda/scripts/..."], "depends_on": "p1"},
  {"phase_id": "p3", "name": "Daemon implementation", "files": ["/ganuda/services/..."], "depends_on": "p1"},
  {"phase_id": "p4", "name": "Service deployment", "files": [], "depends_on": ["p2", "p3"]}
]
```
This feeds the TEG planner's `_build_file_dag()` directly. Phases with `depends_on: null` run in parallel. Phases with dependencies are sequenced.

**Why `constraints` is JSONB object with typed categories**:
```json
{
  "must": ["Use psycopg2 connection pooling", "All files under /ganuda/"],
  "must_not": ["No bash blocks in instructions", "Never modify sacred patterns"],
  "prefer": ["Surgical SEARCH blocks over whole-file replacement", "One operation per instruction"],
  "escalate": ["Any change to specialist_council.py requires council approval", "Service file changes need Chief sudo"]
}
```
Maps directly to Nate's constraint architecture primitive and our existing CLAUDE.md patterns.

**Why `target_file_hashes` prevents DLQ failures**:
The task_executor already runs `_preflight_hash_check()` before execution. If the spec records the file hash at write-time:
- Spec-write hash ≠ execution-time hash → file changed since spec was written → WARN, possible stale SEARCH
- This catches the #1 DLQ cause before execution, not after failure

---

## Integration Points

### TEG Planner (`teg_planner.py`)

1. `expand_task()` — fetch spec by `spec_id` from task parameters
2. `_build_file_dag()` — use spec phases for cross-file semantic ordering (not just filepath grouping)
3. `_build_node_instruction()` — inject spec context header into each child instruction:
   ```
   ## Spec Context
   - Goal: {spec.goal}
   - Phase: {phase_id} — {phase_name}
   - Framework: {spec.framework_notes}
   - File state at spec-write: sha256:{hash[:16]}
   ```

### Task Executor (`task_executor.py`)

1. **Preflight**: Compare spec-write hash vs execution-time hash. Warn if diverged.
2. **Post-flight**: Run acceptance criteria checks after all steps succeed.
3. **DLQ requeue**: Include spec context in retry augmentation for better recovery.

### Jr Work Queue

Add `specification_id INTEGER REFERENCES project_specifications(id)` column.

### Kanban

No schema change needed — `project_specifications.kanban_ticket_id` provides the FK.

---

## Pilot Specifications (Coyote's Condition)

Council condition: start with 3 pilot specs before scaling. Measure DLQ rate before/after.

### Pilot 1: Gateway Health Check Fix
- **Current problem**: 20+ false-positive gateway DOWN alerts (async health endpoint + debounce needed)
- **Target files**: services/health_monitor.py, gateway.py
- **Why it's a good pilot**: Small scope, clear acceptance criteria (zero false alerts in 24h)

### Pilot 2: Self-Replication Containment Audit
- **Current problem**: Gap 4 — Qwen2.5-72B self-replicates in 90% of trials, our containment untested
- **Target files**: nftables configs, FreeIPA sudo rules, systemd service files
- **Why it's a good pilot**: Research + verification spec, not code generation. Tests spec layer for non-coding tasks.

### Pilot 3: Three Rivers KB Article
- **Current problem**: Gap 10 — Three Rivers research synthesis has no KB article
- **Target files**: docs/kb/KB-THREE-RIVERS-PROCLUS-MERKAVAH-FEB27-2026.md (new)
- **Why it's a good pilot**: Documentation spec, tests whether specs work for non-code deliverables.

### Baseline Measurement

Before pilots, record:
- Current DLQ rate (last 50 Jr tasks)
- Average Jr task completion time
- Retry rate per task

After pilots, compare same metrics for spec-linked tasks vs non-spec tasks.

---

## Coyote's Concerns (Addressed)

**"Does the spec layer actually reduce DLQ failures, or does it just add a step?"**
- Answer: The pilot program will measure this. If specs don't reduce DLQ rate by >20%, we revisit.
- The `target_file_hashes` column alone should catch 60% of DLQ root cause #1 (stale SEARCH strings).

**"Don't over-formalize too early" (Raven)**
- Answer: Specs are optional. `specification_id` on jr_work_queue is nullable. Existing workflow unchanged for simple tasks. Specs are for multi-file, multi-day projects only.

**"Ensure specs don't become bureaucratic overhead" (Turtle)**
- Answer: 2-week review after pilots. If spec writing takes longer than the work it prevents, we simplify or kill.

---

## Implementation Plan (BUILD Phase)

1. Deploy `project_specifications` and `spec_task_links` tables on bluefin
2. Add `specification_id` column to `jr_work_queue`
3. Write 3 pilot specifications
4. Write Jr instructions for Pilot 1 (Gateway Health Fix) linked to spec
5. Measure baseline DLQ metrics
6. RECORD: thermal + KB article
7. REVIEW: Owl audit after pilots complete

---

## References

- Council Vote #1d2ba22feb928108 (DC-1 through DC-5 ratification + spec layer approval)
- Thermal #118321 (Breaker Design Constraints)
- Thermal #118324 (DC-4 Hoffman Interface refinement)
- Thermal #118326 (Graduated Basin Model founding synthesis)
- System 3 thermal (LogicGraph + ImpRIF neuro-symbolic reasoning)
- Nate Jones thermal (Four Disciplines framework)
- KB-DLQ-TRIAGE-PATTERNS-FEB22-2026.md (failure root causes)
- KB-OPENSAGE-ALPHAEVOLVE-DISCRETE-TOPOLOGY-FEB25-2026.md (TEG origin)
