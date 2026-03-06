# KB: TEG Planner Deployment

**Date:** Feb 25 2026
**Updated:** Mar 2 2026 (post-reboot note)
**Status:** DEPLOYED, VERIFIED
**Thermal:** #116986
**Kanban:** #1897 (completed)

---

## Problem Statement

Complex multi-file Jr instructions crash autonomous agents through context collapse. When an instruction contains many file operations — Creates, SEARCH/REPLACE blocks across multiple files — the executor loses track of attribution, partial writes occur, and the instruction either partially executes or fails silently. The search space for correct multi-file edits grows combinatorially with the number of files touched.

---

## Inspiration

- **OpenSage** (arXiv:2602.16891, UCSB/Berkeley/DeepMind) — attention firewall concept prevents context collapse by isolating execution units
- **AlphaEvolve** (arXiv:2602.16928, DeepMind) — evolutionary search over task patterns; LLM as evolutionary optimizer over discrete non-differentiable structures
- **Council Vote #ec088d89** — PROCEED WITH CAUTION (0.843 consensus). Raven strategy. Turtle 7-generation review applied. Constitutional constraint: Council fixed-star topology is sacred; TEG applies to Jr executor layer only.

---

## Solution: Topological Execution Graph (TEG)

TEG decomposes multi-block instructions into atomic DAG nodes before execution begins. Dependency ordering ensures correct execution sequence. Each child task gets exactly one atomic operation — one file Create or one SEARCH/REPLACE block. Context collapse becomes structurally impossible.

**Key Insight:** The search space for correct multi-file edits grows combinatorially with the number of files. TEG eliminates this by ensuring each execution step touches exactly one file with exactly one operation.

---

## Files

| File | Change |
|------|--------|
| `/ganuda/jr_executor/teg_planner.py` | Created — core TEG decomposition logic |
| `jr_queue_worker.py` | Modified — TEG intercept added at task pickup |
| `jr_queue_client.py` | Modified — child task insertion hooks added |

---

## How It Works

1. Set `parameters = '{"teg_plan": true}'` on `jr_work_queue` INSERT
2. `jr_queue_worker.py` picks up the task and sees the `teg_plan` flag
3. TEG planner (`teg_planner.py`) reads the instruction file
4. Decomposes multi-block instructions into individual child tasks
5. Each child task receives exactly one atomic operation (single file Create or single SEARCH/REPLACE block)
6. Children are inserted into `jr_work_queue` with `parent_task_id` pointing to the parent
7. Dependency ordering (DAG topology) ensures correct execution sequence
8. Parent task waits for all children to complete

---

## Pipeline Architecture

Two parallel pipelines exist independently — both must be updated separately if gateway changes are made:

| Pipeline | Service | Script | TEG Enabled |
|----------|---------|--------|-------------|
| A | `jr-se.service` | `jr_queue_worker.py "Software Engineer Jr."` | YES |
| B | `jr-executor.service` | `jr_task_executor.py` | NO |

Pipeline A handles `jr_work_queue` tasks with SEARCH/REPLACE execution.
Pipeline B handles `jr_task_announcements` (bidding/plan generation only, no execution).

---

## Council Votes

- **#ec088d89** — TEG planner APPROVED WITH CAUTION (0.843). Raven strategy. Turtle 7-gen constraint applied.
- **#aae3bd86** — Option A (start `jr-se.service`) unanimous. Pipeline A is the canonical TEG execution path.

---

## Bugs Fixed During Deployment

1. **Jr truncated 415-line Create file at line 134** — Executor hit an internal limit and silently stopped writing. TPM wrote the file directly to resolve. TEG prevents recurrence by keeping each Create atomic and small.
2. **RealDictRow dict-access vs tuple-unpacking in hooks** — `jr_queue_client.py` child hooks were unpacking rows as tuples; RealDictRow requires key access. Fixed.
3. **Filepath attribution changed to last-match** — Previously, filepath was attributed to the first code block header found. Changed to last-match (closest preceding header to the SR block). Correct attribution is critical for TEG child decomposition.
4. **Killed orphan worker processes from Feb 22** — Stale `jr_queue_worker.py` processes from prior deploy attempts were consuming queue slots. Killed before clean service start.

---

## Post-Reboot Note (Mar 2 2026)

`jr-se.service` was DEAD after redfin rebooted. Had to be restarted manually with `sudo systemctl start jr-se.service`.

**Action item:** Verify `systemctl is-enabled jr-se.service` on redfin. If not enabled, run `sudo systemctl enable jr-se.service`. This is a scoped FreeIPA sudo command — `dereadi` can execute via `ganuda-service-ctl` wrapper.

Do not assume TEG is running after a reboot without checking service status.

---

## Usage

To queue a task with TEG decomposition enabled:

```sql
INSERT INTO jr_work_queue (
    task_id, title, instruction_file, assigned_jr,
    priority, source, created_by, parameters
) VALUES (
    md5(random()::text), 'Your Task Title', '/ganuda/docs/jr_instructions/YOUR-JR.md',
    'Software Engineer Jr.', 5, 'tpm', 'tpm',
    '{"teg_plan": true}'
);
```

TEG is only triggered when `teg_plan` is `true` in parameters. Tasks without this flag execute via standard Pipeline A without decomposition.

---

## Verification

Thermal #116986 captures deploy confirmation and smoke test result. Kanban #1897 closed as completed Feb 25 2026.

---

## Related

- KB-LONG-MAN-SPRINT-DAY2-FEB24-2026.md — context for TEG motivation (Debt Reckoning sprint)
- KB-OPENSAGE-ALPHAEVOLVE-DISCRETE-TOPOLOGY-FEB25-2026.md — research synthesis that inspired TEG
- KB-JR-DUAL-PIPELINE-ARCHITECTURE-FEB11-2026.md — Pipeline A vs B background
- KB-EXECUTOR-MIXED-STEP-TYPES-SKIP-BUG-FEB12-2026.md — original bug TEG addresses
- Thermals #116983 (OpenSage), #116984 (AlphaEvolve), #116985 (Synthesis), #116986 (TEG deploy)
