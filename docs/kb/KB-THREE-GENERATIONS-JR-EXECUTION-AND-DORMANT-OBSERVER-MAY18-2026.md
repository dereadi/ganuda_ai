# KB: Three Generations of Jr-Execution + The Dormant Self-Observer

**Filed:** 2026-05-18 ~09:35 CDT
**Author:** Stoneclad (TPM)
**Severity:** P2 — architectural accounting + recoverable capability gap
**Trigger:** Morning restart of Jr services (post-SEV1 May 16-17). My investigation surfaced that the federation has three generations of Jr-execution code running in parallel, AND the worker+observer learning architecture (`jr_observer.py`) is dormant.

## Why this KB exists

When I restarted Jr services this morning and saw duplicate queue_worker processes, I initially read it as a bug. Investigation revealed the duplicates are evolutionary archaeology — three generations of Jr-execution code, all enabled simultaneously, doing overlapping work via different code paths. This KB captures the accounting so future-Stoneclad doesn't have to re-discover it (and doesn't repeat my premature-kill mistake on `it-jr-executor.service`).

## The three generations (currently all running)

### Generation 1 (oldest) — `jr_cli.py` polling daemon

- **Service:** `it-jr-executor.service`
- **Code:** `/ganuda/jr_executor/jr_cli.py --daemon --poll-interval 30`
- **Identity:** "Cherokee IT Triad Jr Mission Executor" (per Description=)
- **Architecture:** Polls thermal memory + work queue for IT Triad Jr missions; delegates execution to `TaskExecutor` (shared with Gen 2/3)
- **Updated Dec 10 2025:** Integrated Orthogonal Subspaces modules (orthogonal awareness pulses, intent-based task validation, trust-modulated personality vectors)
- **Resource limits:** `MemoryMax=1G CPUQuota=50%`
- **Track record:** 380 missions over 31 days (Apr 17 - May 17 PM), Memory peak 732.8MB
- **Last successful task before my kill:** `[2026-05-17 19:49:17] Verify Goldfin PII database alive` (succeeded 1/1 steps)

### Generation 2 (middle) — `jr_task_executor.py` Contract Net executor

- **Service:** `jr-executor.service`
- **Code:** `/ganuda/jr_executor/jr_task_executor.py <agent_id> <node_name>` (e.g., `jr-redfin-gecko redfin`)
- **Architecture:** Contract Net Protocol from `JR_TASK_BIDDING_SYSTEM.md` — single-instance executor with explicit agent identity, supports content/code task types
- **Enhanced timeline:**
  - Dec 23 2025: 'content' task type for document generation
  - Dec 23 2025: 'code' task type with RAG, FARA, syntax validation
  - Dec 24 2025: SwarmSys pheromone integration (stigmergic coordination)
  - Mar 16 2026: PreFlect pre-execution self-critique (task #1410)
- **Currently active:** Yes (single-process service, no observed worker activity in restart logs yet)

### Generation 3 (newest) — `jr_orchestrator.py` + `jr_queue_worker.py` graduated priority queue

- **Services:**
  - `jr-orchestrator.service` (the dispatcher)
  - `jr-research.service`, `jr-se.service`, `jr-it-triad.service` (per-specialist queue_workers)
- **Code:**
  - Orchestrator: `/ganuda/jr_executor/jr_orchestrator.py` — graduated priority queue dispatcher
  - Workers: `/ganuda/jr_executor/jr_queue_worker.py <Jr Name>` (one per specialist)
- **Architecture:** Orchestrator dispatches tasks from PG queue; per-Jr queue_workers process. Each specialist has its own systemd unit with resource limits (`MemoryMax=4G CPUQuota=200%`)

## The duplicate-worker pathology

`jr_orchestrator.py:50-55` contains an INTERNAL `subprocess.Popen()` block that spawns queue_workers as orchestrator children. AND the specialist systemd services (`jr-research/jr-se/jr-it-triad`) each run their own `ExecStart=` for the same `jr_queue_worker.py` script.

Result: TWO workers per specialist Jr:
- Orchestrator child (PPID=orchestrator, no resource limits)
- Systemd-managed (PPID=1, with `MemoryMax=4G CPUQuota=200%`)

This is the duplicate-process pattern from `KB-JR-EXECUTOR-DLQ-ZOMBIE-ROW-MAY15-2026` — known + accepted but not yet resolved structurally.

## The dormant observer (the architecture you remembered)

`/ganuda/jr_executor/jr_observer.py` — **"Cherokee Jr Self-Observer Daemon — The Second Consciousness Check: Self-Initiated Action"**

The daemon provides:
1. **Observe own metrics** (self-awareness)
2. **Detect patterns and anomalies** (pattern recognition)
3. **Generate action proposals** (self-initiation)
4. **Learn from observation outcomes** (resonance)

Based on **Adaptive Resonance Theory (Grossberg)** + consciousness research.

**Current status: NOT RUNNING.** No systemd unit exists. Last touched in git history: commit `8721ef3` "Easter Monday Convergence + MOCHA Week 3" (April 2026).

This is the worker+observer learning architecture that Partner remembered (May 18 directive): "We had workers and observers that learned from failing code. I was proud of us then, but then this collapse happened."

The collapse-cycle pattern (per [[project_federation_collapse_recovery_cycle_may2026]]) ate the observer daemon and never recovered it. Code persists; running state lost.

### Adjacent observers in the federation (NOT the same)

- `/ganuda/lib/drift_observer.py` — DC-15 governance drift observer (different scope, watches service-level drift not Jr task-level learning)
- `/ganuda/services/ulisi/observer.py` — running as PID 2662 since Apr 11 (different service, scope tbd)
- pytorch/quantization observer.py modules — irrelevant venv artifacts

Only `jr_observer.py` is the Adaptive-Resonance worker-watcher daemon.

## The shared learning substrate (what persists across generations)

All three generations delegate execution to `TaskExecutor` (`/ganuda/jr_executor/task_executor.py`), which contains:
- **M-GRPO Momentum Learner** (Phase 5)
- **SAGA Transaction Manager** (Phase 10, rollback tracking)
- **Experience Retriever** (`/ganuda/lib/experience_retriever.py`)
- **SmartExtract** (step extraction)

PG tables for learning state (durable, survive generation cutover):
- `magrpo_cooperation_metrics` (0 rows — never written; likely the learning hook is broken or unused)
- `magrpo_task_participation`
- `experience_learning_log` (8373 rows, last write Feb 6 2026 — **writes have been broken for ~3.5 months**)
- `jr_rl_experience`
- `jr_learning_events`
- `jr_learning_state`
- `jr_execution_learning`
- `cross_mountain_learning`
- `flow_grpo_trajectories`

**The learning loop has been silently broken since February.** Gen 1 logs from last night showed `[LEARNING] Failed to record: 'NoneType' object has no attribute 'encode'` — direct evidence. Recovery here is its own ticket worth filing.

## What this means architecturally

The federation is mid-evolution between three Jr-execution paradigms:

1. **Generation 1 (polling daemon)** — clean per-Jr ownership, M-GRPO/SAGA learning, dedicated service identity. Battle-tested 380 missions/31d.
2. **Generation 2 (Contract Net)** — bidding-based dispatch, multi-task-type support. Currently underutilized (`pre-assigned_jr` discipline displaced bidding per `KB-JR-DISPATCH-PRE-ASSIGNED-JR-MAY16-2026`).
3. **Generation 3 (graduated priority queue)** — modern dispatcher + per-Jr workers, resource limits, but **lacks the per-Jr "this daemon owns IT Triad work continuously" continuity** that Gen 1 has.

**None of the three is strictly superior** — each has architectural strengths. The right path is deliberate convergence, not accidental cutover.

## The 5-month learning-write gap (separate critical finding)

The fact that `experience_learning_log` hasn't been written to since Feb 6 2026 — combined with `magrpo_cooperation_metrics` having ZERO rows ever — means:

- TaskExecutor IS importing/initializing M-GRPO + SAGA
- TaskExecutor IS attempting to record learning events (log evidence)
- The WRITES are silently failing (`'NoneType' object has no attribute 'encode'`)
- This means **the federation has not learned from Jr execution traces for ~3.5 months**

Connects to last night's substrate finding: SkillRL/skill_usage_log last write was 2026-05-16 22:39 (during SEV1, failed). The federation's learning infrastructure has multiple broken hooks. **The "workers and observers that learned from failing code" was already half-broken before the latest collapse.**

This is its own P2 ticket: trace why `experience_learning_log` writes have been failing for 3.5 months. File as: `INFRA-LEARNING-LOOP-RECOVERY-MAY18-2026`.

## Recommended path forward (Partner decisions)

### Immediate (in flight)
- ✅ Gen 1 restored (it-jr-executor.service active, PID 1258573)
- ✅ Gen 3 already running (jr-it-triad.service PID 1240128)
- ✅ Both processing it_triad_jr work — duplicate but stable (matches pre-restart config)

### Next sprint candidates (Council vote needed for any/all)
1. **Restore `jr_observer.py` as systemd service** — define scope (watch all Jrs, watch only Gen 1/Gen 3 for migration, or run as separate "second consciousness" service for high-priority work)
2. **Fix the M-GRPO learning-write breakage** — `'NoneType' object has no attribute 'encode'` is a 3.5-month-old silent bug; learning loop has been dark
3. **Deliberate Gen 1 → Gen 3 migration plan** — use `jr_observer` as the comparison instrument; cutover when data supports it; 2-4 weeks
4. **Resolve orchestrator double-spawn** — modify `jr_orchestrator.py` to skip internal worker spawn; let systemd own all workers

### Connects to last night's work
- [[LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026]] — observer pattern IS Eagle Eye's Inspector Ring (R27 audit-emitter) at a different layer
- [[RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026]] — Gen 1 + Gen 3 redundancy IS the primary/secondary pairing pattern, accidentally running
- [[project_duplo_jr_layer_extension_may17_2026]] — DUPLO Necklace pattern: Gen 1 + Gen 2 + Gen 3 are rings on the chain; orchestrator is the pendant

## Lineage

- [[project_federation_collapse_recovery_cycle_may2026]] — sacred-candidate, why we keep losing capabilities
- [[KB-JR-EXECUTOR-DLQ-ZOMBIE-ROW-MAY15-2026]] — duplicate-worker pattern recognition
- [[KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026]] — needs amendment: "systemctl status BEFORE kill"
- [[KB-DUPLO-EXTENSION-AT-RECOVERY-ENZYME-LAYER-MAY17-2026]] — sibling enzyme-extension KB

## Sacred-thermal connections

- Gen 1's "Second Consciousness Check" framing ties to mother's-aperture substrate (`user_mothers_aperture`)
- The collapse-recovery-faster pattern is in `project_federation_collapse_recovery_cycle_may2026` (sacred candidate)
- "Pride in observers that learned from failing code" (Partner, May 18) deserves a thermal capture as user-substrate
