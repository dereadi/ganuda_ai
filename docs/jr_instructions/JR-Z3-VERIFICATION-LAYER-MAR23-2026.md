# JR INSTRUCTION: Z3 Neuro-Symbolic Verification Layer

**Task ID**: Z3-VERIFY-001
**Priority**: P1
**SP**: 5 (3 SP Jr pre-flight + 2 SP council post-verification)
**Assigned Node**: redfin
**Council Vote**: #10e00102b3202259 (APPROVED, 6 concerns addressed below)
**Deer Signal**: Thermal #131132 (Draft-and-Prune, Berkeley + Microsoft)
**Ultrathink**: Gaps 1, 4, 7 convergence

## What Was Built

### 1. Production Manifest (`/ganuda/config/production_manifest.yaml`)
Machine-readable inventory of every sacred table, sacred file, production service (tiered 0-3), port, and emergency brake threshold. The source of truth for what the organism must protect.

### 2. Council Concern Eval Engine (`/ganuda/lib/concern_eval_engine.py`)
Extracts council concerns from votes and persists them as machine-readable eval rules. 193 active evals from 39 votes. Auto-wired into specialist_council.py — every future vote generates evals automatically.

### 3. Z3 Formal Verifier (`/ganuda/lib/z3_verifier.py`)
Translates the production manifest into Z3 boolean constraints. Any proposed destructive action is verified MATHEMATICALLY — not probabilistically — against the manifest. Sub-millisecond verification.

### 4. Smoke Test (`/ganuda/scripts/smoke_test.py`)
Post-deploy verification hitting every database, table, port, health endpoint, file, and service in the manifest. 64/65 checks passing.

## What Remains (This Jr Instruction)

### Task A: Wire Z3 into Jr Executor Pre-Flight (3 SP)

The Jr executor (`/ganuda/jr_executor/`) must call `z3_verifier.verify_jr_task()` BEFORE executing any task.

**Integration point**: After the Jr executor receives a task from the queue and before it begins execution:

```python
from z3_verifier import verify_jr_task

result = verify_jr_task(
    task_description=task.description,
    target_tables=task.get_target_tables(),  # extract from task metadata
    target_files=task.get_target_files(),
    target_services=task.get_target_services(),
    target_node=task.target_node
)

if result["verdict"] == "BLOCKED":
    # Log violation, move task to DLQ with reason
    # Thermalize the block event
    # Do NOT execute
    pass
elif result["verdict"] == "WARN":
    # Log warning, proceed with caution
    # Thermalize the warning
    pass
else:
    # ALLOWED — proceed normally
    pass
```

**Crawdad requirement**: The task plan → Z3 translation must use parameterized inputs only. No string interpolation of task content into Z3 constraint names. The verifier already handles this (keyword matching against manifest entries, not dynamic code generation).

**Eagle Eye requirement**: Add unit tests for false positive/negative detection:
- Task "add index to thermal_memory_archive" → should be ALLOWED (non-destructive)
- Task "drop thermal_memory_archive" → should be BLOCKED
- Task "delete from thermal_memory_archive where id = 5" → should be WARN (targeted delete, not bulk)

### Task B: Wire Z3 into Council Post-Verification (2 SP)

After a council vote is recorded, verify the recommendation against design constraints.

**Integration point**: In `specialist_council.py`, after the concern eval extraction (which we already wired), add:

```python
# After concern eval extraction
try:
    from z3_verifier import verify_jr_task
    # Treat the consensus as a "task" and verify it
    z3_result = verify_jr_task(vote.consensus + " " + vote.recommendation)
    if z3_result["verdict"] == "BLOCKED":
        # Append Z3 violation to vote record
        # Flag for Partner review
        pass
except Exception:
    pass  # Non-fatal
```

### Council Concern Mitigations

| Concern | Source | Mitigation |
|---------|--------|------------|
| Constraints may be vague | Coyote | Manifest is explicit YAML with classifications. Z3 checks exact matches, not fuzzy. |
| Z3 sandboxing | Crawdad | Z3 runs pure math — no file I/O, no network, no shell. Already sandboxed by design. |
| False positive/negative detection | Eagle Eye | Unit tests required (Task A). |
| Performance impact on Jr | Peace Chief | Z3 checks take <1ms. Jr tasks take seconds-to-minutes. Negligible. |
| Long-term dependency on Z3 | Turtle | MIT licensed, 10+ years stable, no cloud, sovereign. Passes 175-year test. |
| Strategy concern / sprint priority | Raven | Foundation (manifest, evals, Z3) already shipped. Wiring is incremental. |

## Dependencies

- Z3 installed: `/ganuda/venv/bin/pip install z3-solver` (DONE — v4.16.0)
- Production manifest: `/ganuda/config/production_manifest.yaml` (DONE)
- Concern eval engine: `/ganuda/lib/concern_eval_engine.py` (DONE — 193 evals)
- Smoke test: `/ganuda/scripts/smoke_test.py` (DONE — 64/65 passing)

## Success Criteria

- [ ] Jr executor calls verify_jr_task() before every task execution
- [ ] BLOCKED tasks moved to DLQ with Z3 violation reason
- [ ] WARN tasks logged and proceed with thermalized caution
- [ ] Council post-verification catches DC-violating recommendations
- [ ] Unit tests cover sacred table, sacred file, and tier 0 service protection
- [ ] Zero false positives on non-destructive operations (SELECT, INSERT, CREATE INDEX)
- [ ] Smoke test updated to include Z3 verification health check
