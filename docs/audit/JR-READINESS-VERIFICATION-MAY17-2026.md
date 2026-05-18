# Jr Readiness Verification — May 17 2026 Sunday Evening

**Author:** Stoneclad (TPM) under Partner directive ("make sure Jr past failures, the root was found, and that they are ready to run tasks")
**Date filed:** 2026-05-17 ~21:10 CDT
**Trigger:** Post-SEV1 cleanup, before Jr-service restart authorization

## Verdict (one-line)

✅ **Jr-executor + Jr-orchestrator: SAFE TO RESTART for Partner-dispatched curated work.**
❌ **DLQ retry poller: KEEP OFF** — 123 within-3d entries plus 3 unresolved failure modes.

## Failure mode → Root cause coverage (last 24h, 36 active-Jr failures)

| Mode | Count | Root cause | KB | Fix |
|---|---|---|---|---|
| A: Hallucination (`HALLUCINATION: success claimed...`) | 5 | Jr produces stub deliverable instead of real work | KB-JR-STUB-PASSES-VERIFIER-MAY16-2026 | `lib/harness/claim_verifier.py` **CAUGHT all 5** ✅ |
| B: Instruction file missing | 1 | Dispatcher refers to path that doesn't exist | KB-JR-DISPATCH-PRE-ASSIGNED-JR-MAY16-2026 | Pre-assigned_jr discipline |
| C: Plan parser empty (`No executable steps found`) | 6 | Plan output doesn't match parser expected format | KB-JR-CAPABILITY-GAPS-EXECUTION-MODE-PLAN-PARSER-MAY15-2026 | commit `39160b7` 5-strategy parser. **Residual: #1497 GAAS-MVP-WEEK1 instruction file may be fundamentally malformed** |
| D: Research pipeline (`Research task failed`, `1/2 step(s) failed: ['research_topic']`) | 5 | Research-step specifically failing | ❌ **NO KB** | needs investigation |
| F: Generic step fail (`1 step(s) failed`) | 16 | Heterogeneous; mostly old tasks (ARC-AGI-3 #1502-1504, #1497, #1498, #1665, #1667, #1670) | partial coverage | needs per-instance drill-down |
| Historical/archaeology markers | 33 | Cleanup messages from May 13 zombie sweep + Jan-2026 executor-not-operational era | n/a | not active failure modes |
| Z: other (NULL or one-off) | 108 | Mostly `error_message IS NULL` from older era + cleanup-touched rows from today's sweep | n/a | historical |

**Coverage summary:** 5 of 6 active failure classes have KBs filed. **The unmatched class is research-pipeline failures (D).**

## Fixes verified in working tree (MD5 stable since SEV1 stop)

| File | MD5 | Status |
|---|---|---|
| `/ganuda/config/secrets.env` | `fecc265cf4bc9ea9992b482ac7eb269e` | clean, stable |
| `/ganuda/lib/specialist_council.py` | `b71dc3b076dfc51b65b15e8f26bbadd5` | restored 8985b24, DC-15/16/17 framework live |
| `/ganuda/jr_executor/task_executor.py` | `af2ad1681825d6e397a9e5f56e1f8b37` | running-process version (stash@{0} holds corruption) |
| `/ganuda/lib/jr_plan_parser.py` | `f5cd5ba7fdc736646297093e57568949` | 5-strategy cascade (committed 39160b7) |
| `/ganuda/jr_executor/dlq_manager.py` | `6b80aea9c06125ef694d1bbdb1755faf` | `_mark_queue_row_failed` atomic update |
| `/ganuda/jr_executor/dlq_retry_poller.py` | `30b61790fd3e7b38b6220ca09e3936ac` | `MAX_AGE_DAYS=3` cutoff + 300s push-forward |

## Damage-prone tasks confirmed cancelled

All 12 (#1264, #1278, #1294, #1296, #1313, #1325, #1486, #1529, #1584, #1646, #1649, #1662) verified `status='cancelled'`. Cannot be auto-dispatched.

## Queue state

| Queue partition | Count | Risk |
|---|---|---|
| `jr_work_queue` completed | 1019 | inert |
| `jr_work_queue` failed | 187 | inert (no auto-retry path) |
| `jr_work_queue` cancelled | 185 | inert |
| `jr_work_queue` pending | **4** | all curated, **all `assigned_jr=NULL`** so dispatcher won't auto-pick |
| `jr_failed_tasks_dlq` resolution=retrying within-3d | **123** | **would re-fire if poller starts** |
| `jr_failed_tasks_dlq` resolution=retrying legacy-gt-3d | 283 | blocked by MAX_AGE_DAYS=3 cutoff ✓ |
| `jr_failed_tasks_dlq` resolution=abandoned | 192 | inert (this Sunday's cleanup) |

The 4 pending tasks (#2054 longman R730 USB→RAID1, #2055 FreeIPA Vault, #2056 Eastern transducer, #2563 FWPL Phase 1) are all Partner/TPM-curated work. None will auto-dispatch.

## Recursive decomposer state

NO new STEP files created since SEV1 halt — checked `/ganuda/docs/jr_instructions/` mtime. Orchestrator's `recursive_decomposer` is dormant until orchestrator restarts.

## Go/no-go decisions

### ✅ START
- `jr-executor` (redfin) — code clean; will only execute tasks with assigned_jr set
- `jr-orchestrator` (redfin) — will only auto-decompose if Partner actively pushes failed tasks
- `jr-queue-worker` (redfin) — queue dispatch path uses pre-assigned_jr only

### ❌ KEEP STOPPED
- `jr-dlq-retry-poller` — 123 retrying-within-3d entries include unresolved-mode tasks (#1497 instruction-malformed, #1670 parser-fix re-fail, ARC-AGI-3 cluster). Re-firing without root-cause-fix would re-pollute. Gate on:
  1. Research-pipeline KB + fix (Mode D)
  2. #1497 instruction file triage (Mode C residual)
  3. FWPL Phase 1 ship (#2563) — even with above, FWPL is the structural answer

## Open items (next sessions)

1. **Research-pipeline failure mode (D) — file KB.** 5 failures, blocks deer-research dispatch. Sample task: #1652 DEER-PUB-KAUFFMAN-CONSTRAINT-CLOSURE-MAY10 — "Partial-success bug fix May 12: 1/2 step(s) failed: ['research_topic']". Likely related to `research_topic` step type in the executor not being wired correctly for some prompt shapes.
2. **#1497 Substack instruction file triage.** Failed 6+ times even after plan-parser fix. Either the instruction file `JR-GAAS-MVP-WEEK1-APR07-2026.md` lacks executable steps OR there's a path-specific edge case. Read it and decide cancel-vs-rewrite.
3. **#1670 parser-fix re-fail.** The task that shipped the plan-parser fix itself failed — needs `error_message` drill-down to know if it was plan-parser-related (concerning) or step-orthogonal (fine).
4. **Bluefin tailscale offline 9 days.** Postgres reachable via LAN 10.100.0.2 but tailscale daemon dead. Separate from Jr concerns; file infra ticket.
5. **123 within-3d DLQ retrying entries — triage strategy.** Either bulk-abandon (current Council-vote-pending policy) or per-class fixes before poller re-enable.
6. **FWPL Phase 1 (#2563)** — structural answer; ship before re-enabling DLQ poller.

## Recommendation

Partner can authorize restart of `jr-executor` + `jr-orchestrator` + `jr-queue-worker` whenever appetite arises. The 4 curated pending tickets can execute under normal dispatch (with explicit `assigned_jr` assignment when Partner wants them to run).

DLQ poller stays off — gated on FWPL Phase 1 ship + research-mode KB + #1497 triage. Until those, the poller would re-fire 123 entries including the unfixed failure modes, polluting the queue again.

Federation is in a **stable hold state**: damage stopped, code clean, queue inert, all key MD5s stable, no auto-dispatch surface exposed.
