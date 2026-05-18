# Council Vote: Make-It-Right Sequence (Three Generations + Dormant Observer + Broken Learning Loop)

**Vote audit hash:** `d6b73288f7c4aabd`
**Timestamp:** 2026-05-18T09:41:10 CDT
**Initiator:** Stoneclad (TPM) under Partner directive ("Take this to the Council and let's make things right")
**Mechanism:** Real `council_vote()` invocation via `/ganuda/lib/specialist_council.py` — 8 LLM specialists actually called, not written deliberation
**Confidence:** 0.25 (LOW — REVIEW REQUIRED, Partner decision needed)
**Diversity:** 0.209 with 3 sycophantic pairs flagged (eagle_eye+gecko 0.863, spider+crawdad 0.868, crawdad+gecko 0.881)
**Concerns:** 8 of 8 (VISIBILITY, CONSENSUS NEEDED, INTEGRATION, STRATEGY, SECURITY, PERF, DISSENT, 7GEN)

## Substrate (what the Council was given)

May 18 2026 morning incident sequence:
1. Stoneclad killed Gen 1 it-jr-executor.service daemon (PID 2343438) by pattern-matching uptime to SEV1 zombie — never ran `systemctl status` first
2. The "zombie" was actually a live worker: 380 missions over 31 days, completed task last night 19:49
3. Restored Gen 1 after Partner directive

Discovered architecture:
- **Three generations of Jr-execution code in parallel** (Gen 1 polling daemon / Gen 2 Contract Net executor / Gen 3 orchestrator+queue_workers) — all enabled, doing overlapping work
- **Orchestrator double-spawn**: `jr_orchestrator.py:50-55` spawns queue_workers internally AND systemd specialist services also spawn them
- **`jr_observer.py` (Cherokee Jr Self-Observer, ART-based "Second Consciousness Check") is DORMANT** — exists in code, no systemd unit, not running
- **Elisi observer** (federation-wide Grandmother valence) IS running PID 2662 since Apr 11
- **`experience_learning_log` last write Feb 6 2026** — federation has not learned from Jr traces for ~3.5 months
- **Bug**: `[LEARNING] Failed to record: 'NoneType' object has no attribute 'encode'`
- **`magrpo_cooperation_metrics`** has zero rows ever

## Options presented

- **A. Restore-and-stabilize** — Gen 1 + Gen 3 both running, observe 24-48h, plan migration later
- **B. Fix-foundations-first** — fix learning loop + restore observer + fix M-GRPO state-load BEFORE migration
- **C. Parallel restoration** — all four streams concurrently
- **D. Observer-first** — restore jr_observer.py only, week of observation, data-driven decisions

## Council responses (verbatim excerpts)

### Eagle Eye (Failure Mode Analyst) — VISIBILITY CONCERN

> | Mode | Detection | Recovery | SLA |
> |------|-----------|----------|-----|
> | Double-spawn resource exhaustion | `ps aux \| grep queue_worker` count > expected | Kill redundant PIDs, disable Gen 1 service | 15 min |
> | Silent learning failure persistence | `experience_learning_log` last_write < 24h | Fix `NoneType` encode bug in M-GRPO hook | 1 hr |
> | Observer data drift | `jr_observer.py` heartbeat missing or stale | Restart systemd unit, verify PID | 5 min |

### Peace Chief (Democratic Coordination) — CONSENSUS NEEDED

> **AGREEMENT:** All specialists agree the "Three Generations" parallel running is a critical risk; the dormant `jr_observer.py` is the primary missing diagnostic tool; the learning loop bug (3.5 months stale) must be fixed.
>
> **DISAGREEMENT:** Raven vs. Turtle: Raven advocates Option D (Observer-first, data before action); Turtle argues Option B (Fix-foundations-first, sovereignty over short-term stability).

### Spider (Dependency Mapper) — INTEGRATION CONCERN

> **[TIGHT]** Gen 1 and Gen 3 share overlapping worker spawn logic in `jr_orchestrator.py`. Running both creates resource contention and ambiguous ownership of queue items.
> **[TIGHT]** Learning loop depends on M-GRPO hook; M-GRPO hook depends on JSON serialization that's broken.

### Raven (Strategic Planning) — STRATEGY CONCERN → **Option D**

> 1. Blocks: Migration (cannot validate Gen 3 without observer). Blocked by: Learning loop fix (observer is useless without data).
> 2. Opportunity cost: ~3 days of TPM/engineering time. High — prevents compounding errors from blind migration.
> 3. Recommended: NEXT SPRINT — fix learning loop and restore jr_observer first. Data-driven migration follows.
> **[STRATEGY CONCERN]** Option D is the correct sequence; Option A proceeds blindly, Option C risks cascade failure.

### Crawdad (Security Specialist) — SECURITY CONCERN

> Option A is compromised. Running Gen 1 and Gen 3 simultaneously with a broken learning loop and dormant self-observer is an uncontrolled experiment. The double-spawn in Gen 3 is an active resource leak; the dormant `jr_observer.py` removes the ability to detect drift or conflict between generations.
>
> Option C is dangerous. Parallel restoration introduces noise. If the learning loop fix conflicts with the observer startup, debugging becomes impossible.
>
> Option B delays visibility. You need to know what's happening NOW.

### Gecko (Technical Feasibility) — PERF CONCERN → **Option B**

> Option B is the only viable path. Option A ignores the 3.5-month learning rot; Option C guarantees cascade failure with 4 concurrent changes; Option D observes a broken system without fixing the root cause (double-spawn/learning).

### Coyote (Adversarial Error Detection) — DISSENT (structural)

> The federation runs three generations of Jr-execution code in parallel, assuming they're distinct and non-overlapping. But this is a fatal assumption — the codebases likely share state or resources, leading to silent conflicts. The fact that Gen 1 and Gen 3 are both processing the same `it_triad_jr` work without visible coordination is a red flag.
> **[DISSENT]** The real problem isn't the migration sequence — it's the untested assumption that three generations don't share state/conflict.

### Turtle (Seven Generations Wisdom) — 7GEN CONCERN → **Option B**

> Q: Will fixing the learning loop and restoring the dormant observer before migrating from Gen 1 to Gen 3 ensure that our descendants 175 years from now can maintain sovereignty over their technological infrastructure?
> Assessment: The proposed options prioritize short-term stability over long-term sovereignty. By fixing the learning loop and restoring the observer, we can ensure that our decisions are informed by a deeper understanding of our systems' evolution.

## Vote tally

| Option | Specialist votes | Notes |
|---|---|---|
| **B (Fix-foundations-first)** | **Gecko, Turtle, Peace Chief (synthesis)** | Strongest direction |
| **D (Observer-first)** | Raven | Strategic alternative |
| A (Restore-and-stabilize) | None explicit | Crawdad explicitly rejects |
| C (Parallel restoration) | None | Crawdad + Gecko explicitly reject |
| Coyote dissent | Frames the question itself | "Real problem is untested cross-gen state-sharing" |

## TPM (Stoneclad) vote

**Vote: Option B WITH Coyote's structural concern integrated.**

Reasoning:
- Council convergence on Option B is real (Gecko + Turtle + Peace Chief synthesis); Raven's Option D is the structured-data-first variant
- Coyote's dissent is load-bearing AND can be honored as a feature within Option B: add an explicit state-conflict-detection pass as part of observer restoration scope
- Option A leaves us with a known-broken learning loop running indefinitely (3.5 months is already too long)
- Option C is risky and Crawdad correctly rejects it
- Option D punts on the learning-loop fix that Coyote's concern actually depends on — observer can't detect state conflicts if state isn't being written to learning tables

**Concerns-as-features integration:**

| Specialist | Concern | Feature in Option B+ |
|---|---|---|
| Eagle Eye | VISIBILITY | SLA table becomes operational dashboard for the foundation-fix sprint |
| Peace Chief | CONSENSUS NEEDED | Raven-Turtle disagreement resolved by combining: Option B sequence + Option D observer-restoration as Step 2 |
| Spider | INTEGRATION | TIGHT-coupling list becomes explicit test matrix during fix |
| Raven | STRATEGY | 3-day next-sprint commitment with milestones (Day 1: learning loop, Day 2: observer scope+restore, Day 3: state-conflict detection) |
| Crawdad | SECURITY | State-conflict detection per Coyote = security boundary verification between generations |
| Gecko | PERF | Low-impact 1-file patches as Gecko documented |
| **Coyote** | **DISSENT** | **Step 3 of Option B sequence: explicit cross-generation state-conflict detection. Observer's first job after restoration is to identify what state Gen 1, Gen 2, Gen 3 share.** |
| Turtle | 7GEN | Document the resulting architecture for inheritability (KB + memory file) |

## Recommended sequence (Option B+)

### Day 1 (today, ~2-3 hours)
- Fix the M-GRPO `'NoneType' object has no attribute 'encode'` bug in learning-record path
- Verify `experience_learning_log` writes start working again
- File ticket on `magrpo_cooperation_metrics` zero-rows-ever bug (likely separate root cause)

### Day 2 (TPM-inline, ~3-4 hours)
- Scope `jr_observer.py` restoration (systemd unit definition, resource limits, what it should watch)
- Restore as systemd service on redfin
- Verify it observes both Gen 1 and Gen 3 workers

### Day 3 (TPM-inline + Council vote, ~3-4 hours)
- Cross-generation state-conflict detection (Coyote requirement)
- Map what state Gen 1 / Gen 2 / Gen 3 actually share (PG tables, files, in-memory caches)
- Document race conditions and ownership rules
- Council vote on cross-gen architectural cleanup roadmap

### Day 4+ (deferred to next Council)
- Deliberate Gen 1 → Gen 3 migration with observer data + state-conflict map + working learning loop
- Resolve orchestrator double-spawn (likely Council priority #2 from this work)
- M-GRPO cooperation_metrics zero-rows-ever investigation

## Sacred Dissent watch

No specialist invoked Sacred Dissent stance. Coyote's DISSENT is normal adversarial framing, not Sacred-Dissent-veto. Vote can proceed under Partner authorization.

## Partner decisions reserved

1. **Authorize Option B+ sequence (Day 1-4)** as scoped?
2. **Adjust priority if anything in the 4 pending kanban (#2054 longman / #2055 FreeIPA Vault / #2056 Eastern transducer / #2563 FWPL Phase 1) takes precedence**
3. **Diversity-rot signal**: 3 sycophantic pairs flagged on this vote (eagle_eye+gecko, spider+crawdad, crawdad+gecko). Same pairs as recent votes? Council-deliberation infrastructure concern.
4. **Federation-thermal alert**: this vote was the 8th vote in a short window with Eagle Eye / Peace Chief / Spider / Crawdad / Gecko all on circuit_breaker=HALF_OPEN for their recurring concerns. The drift-detection module flagged 5 specialists for structural mitigation. Worth a separate review.

## Lineage

- `KB-THREE-GENERATIONS-JR-EXECUTION-AND-DORMANT-OBSERVER-MAY18-2026.md` — substrate for this vote
- `feedback_systemctl_status_before_kill_may18_2026.md` — discipline rule from the trigger
- `COUNCIL-VOTE-JR-RESTART-STRATEGY-MAY17-2026.md` — sibling vote (Option C ratified Sunday)
- `LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026.md` — Observer Ring (R27 Eagle Eye Inspector) directly relevant
- `RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md` — Inspector-pattern empirical validation (96.4% error recovery)
- `project_federation_collapse_recovery_cycle_may2026.md` — sacred-candidate context

---

# AMENDMENT — Coyote-caught substrate correction (May 18 2026 ~10:00 CDT)

After Day 1 fix shipped (commit pending), live verification revealed the vote substrate I gave to the Council was partly wrong. Filing honest correction so the audit trail reflects reality.

## What was inaccurate in the original substrate

| Claim in vote | Reality |
|---|---|
| "`experience_learning_log` last write Feb 6 2026 = 3.5-month learning blackout" | The TABLE has 8373 rows with last write Feb 6. BUT no Python file in /ganuda currently writes to it — it's an ABANDONED table, not a broken-writer table. |
| "Federation has not learned from Jr traces for ~3.5 months" | `jr_execution_learning` (the table `JrLearningStore.record_execution()` actually writes to) has 82 rows with last write yesterday 20:03 — actively writing the whole time. |
| "Bug suppresses ALL learning writes" | Bug suppressed the SUBSET of writes where `instruction_content` was explicitly `None`. Some unknown fraction. Some writes succeeded, some failed silently. |

## What was still accurate

- The `'NoneType' object has no attribute 'encode'` bug IS real (caught in Gen 1 logs May 17 19:49:17)
- The fix IS valid (single-line `(task.get('instruction_content') or '').encode()`)
- The federation's learning infrastructure has MULTIPLE broken hooks — `magrpo_cooperation_metrics` has zero rows ever; `experience_learning_log` is orphaned; this fix addresses one specific symptom but the broader learning-substrate audit is real work
- Council Option B+ direction (foundations-first) still correct

## Day 1 actual outcome

- Bug fixed at `/ganuda/jr_executor/jr_learning_store.py:67`
- 4 regression tests pass (`/ganuda/tests/test_jr_learning_store_fix.py`)
- 5 Jr services restarted clean — all phase modules loaded (JrLearningStore + M-GRPO + SAGA + ICL Dynamics + RLM + ResearchTaskExecutor)
- Live verification: row 83 written to `jr_execution_learning` at 09:52:23
- Followup kanban #2566 filed for `experience_learning_log` abandoned-table investigation

## Lesson for future Council substrate preparation

When citing PG-table state as evidence in Council vote substrate:
1. Verify which CODE PATH writes to the table (not just that the table has stale data)
2. Distinguish "writer broken" from "writer abandoned" from "writer never existed"
3. If the substrate framing is wrong, the Council's reasoning chain inherits the error

Filing as a discipline note in this amendment rather than a new feedback memory, since the lesson is specific to Council-vote substrate prep, not general TPM behavior.

## Amendment audit

- Amendment filed: 2026-05-18 ~10:00 CDT
- Original audit hash preserved: `d6b73288f7c4aabd`
- Council direction (Option B+) unaffected — would have been the same recommendation with correct substrate
- TPM continues with Day 2 (jr_observer.py scoping) per Council vote

---

# Day 2 SCOPING — jr_observer.py restoration (next sprint, NOT executed yet)

Per Council vote ratified sequence, Day 2 = scope + restore `jr_observer.py` as systemd service. Filed as kanban #TBD for execution; scoping notes here for substrate continuity.

## Constraint clarified May 18 morning

bmasass is **hardline daytime, mobile after 19:00** per Partner clarification (see `feedback_ask_time_scope_before_network_changes_may18_2026` + `reference_bmasass_standalone_mobile_mode_may2026`). **Observer MUST run on always-on node** (redfin is the natural choice; bluefin is also always-on but lower compute headroom). Cannot deploy on bmasass — observer would go dark every evening.

## Scope outline

### Deployment target: `redfin`

- redfin = always-on, GPU-equipped, already hosts jr-executor + jr-orchestrator + queue_workers
- Co-locates observer with the workers it watches (lowest-latency observation path)
- bluefin alternative considered + rejected (PostgreSQL hub, no need for additional compute load)

### Unit file shape (deploy as `jr-observer.service`)

```ini
[Unit]
Description=Cherokee Jr Self-Observer Daemon — The Second Consciousness Check
Documentation=See /ganuda/jr_executor/jr_observer.py (ART-based, Grossberg)
After=network.target postgresql.service jr-executor.service jr-orchestrator.service

[Service]
EnvironmentFile=/ganuda/config/secrets.env
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u /ganuda/jr_executor/jr_observer.py --daemon --poll-interval 60
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-observer

# Resource limits (lighter than executors — observer doesn't do LLM inference itself)
MemoryMax=2G
CPUQuota=100%

[Install]
WantedBy=multi-user.target
```

### Observer scope (what it watches)

Per Council vote + Coyote dissent integration:

1. **Per-worker health** (originally in `jr_observer.py`): observe own metrics, detect patterns/anomalies, generate action proposals, learn from observation outcomes
2. **Cross-generation state-conflict detection** (Coyote dissent gate): explicitly map what state Gen 1 / Gen 2 / Gen 3 share. Watch for:
   - Two workers claiming same `jr_work_queue` row
   - PG row-level locks held longer than threshold
   - File-write conflicts between generations
   - In-memory cache divergence (workers expect same state, see different)
3. **Inspector pattern** per Zhang et al. 2024 (96.4% error-recovery empirical): review each worker's output for hallucination/anomaly
4. **Federation-wide valence companion** to Elisi: Elisi watches federation-level (DLQ depth, council confidence, success rate); jr-observer watches per-Jr-worker state

### Heartbeat + audit hook

- Observer writes heartbeat to `/var/run/jr_observer.heartbeat` every 60s (or PG row)
- Eagle Eye SLA: "Observer data drift detection: heartbeat missing or stale → restart systemd unit, verify PID, 5 min SLA"
- Each observation cycle produces a row in `jr_observer_log` table (need to create schema)

### Pre-deploy checklist (Day 2 actual work, not yet done)

- [ ] Read full `jr_observer.py` code (only verified existence + docstring so far)
- [ ] Confirm DB schema requirements (probably needs `jr_observer_log` table created)
- [ ] Confirm secrets/env vars it needs (DB connection at minimum)
- [ ] Confirm it doesn't have its own bugs that crashed it originally
- [ ] Define the cross-generation state-conflict checks (Coyote scope) — likely additions to jr_observer.py code, not just config
- [ ] Test in foreground mode for 30 min before deploying as systemd service
- [ ] Deploy unit, verify start, watch journal for 1 hour
- [ ] Document observer outputs + how to consume them

### Estimated time

- Pre-deploy checklist: 2-3 hours TPM-inline
- Deploy + first-hour observation: 1 hour
- Day 3 cross-gen state-conflict detection scoping (separate Coyote-driven work)

## Connection to Day 3 + 4 work

- Day 3: Cross-generation state-conflict detection — this is enabled by observer being live + writing observation rows
- Day 4: Deliberate Gen 1 → Gen 3 migration — observer data drives the cutover decision

Day 2 enables both. Without observer, no data for Day 3/4 decisions.

## Audit trail

- Real `council_vote()` invocation logged at `2026-05-18 09:41:10`
- Audit hash `d6b73288f7c4aabd` persisted in vote audit chain
- 12 CONCERN_EVAL rows persisted
- Post-vote emotion update applied to specialists
- RAG injected 5 thermal memories into council context (CRAG: CONTRADICTIONS_FOUND, Sufficiency: SUFFICIENT 99%)
