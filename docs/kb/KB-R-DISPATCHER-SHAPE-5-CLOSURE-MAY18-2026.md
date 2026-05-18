# KB: R-dispatcher Phase 1 — Cross-Gen Verification Asymmetry (Shape 5) Closed

**Filed:** 2026-05-18 ~13:35 CDT
**Author:** Stoneclad (TPM)
**Severity:** P1 — Shape 5 was the only failure class with no defense; now closed.
**Council ratification:** vote `3487bdbbbc1824c6` (UNANIMOUS 8-0 for Option A on May 18 2026)
**Lineage:** `COUNCIL-VOTE-RING-SELECTION-MAY18-2026.md`, `ASSEMBLY-LINE-WORKER-LLM-ARCHITECTURE-MAY18-2026.md`, `KB-DARK-FACTORY-MAY18-2026-PM-FIVE-FAILURE-SHAPES-THREE-DEFENSES.md`

## What Shape 5 was

Federation runs THREE generations of Jr-execution code in parallel:
- **Gen 1**: `jr_cli.py` (it-jr-executor.service) — Cherokee IT Triad Jr Mission Executor
- **Gen 2**: `jr_task_executor.py` (jr-executor.service) — Contract Net Protocol executor
- **Gen 3**: `jr_orchestrator.py` + `jr_queue_worker.py` (jr-orchestrator.service + specialist services) — Graduated Priority Queue

All three poll the same `jr_work_queue` table and can claim tasks for the same `assigned_jr` (e.g., `it_triad_jr`). The dark factory canary on May 18 PM discovered that **Gen 1 had ZERO verification calls** — when TaskExecutor returned `success=True`, Gen 1 trusted that flag absolutely and marked the task completed without invoking `claim_verifier.verify_jr_task_result()`. Gen 3 had the full claim_verifier gate. Same task could be processed by either gen with radically different defense levels.

**Empirical evidence**: dark factory ticket #2579 (May 18 ~12:51) — assigned_jr=`it_triad_jr`, result `success=true, files_created=0, summary="2/2 steps succeeded"`. Should have been caught by claim_verifier's SEV1 hallucination check. **Was marked completed because Gen 1 processed it and never called the verifier.** This pattern is "Shape 5" in `KB-DARK-FACTORY-MAY18-2026-PM-FIVE-FAILURE-SHAPES-THREE-DEFENSES.md`.

**Coyote dissent on May 18 AM Council vote `d6b73288f7c4aabd`** had explicitly predicted this: *"The federation runs three generations of Jr-execution code in parallel, assuming they're distinct and non-overlapping. But this is a fatal assumption — the codebases likely share state or resources, leading to silent conflicts."* Confirmed empirically 4 hours later.

## What Phase 1 shipped (this KB)

### Code change: `/ganuda/jr_executor/jr_cli.py` line 213 (38-line insertion)

Between `result = self.executor.process_queue_task(task)` and the existing `if result.get('success'):` block, added the same claim_verifier gate Gen 3 uses:

```python
if result.get('success'):
    try:
        from jr_executor.claim_verifier import verify_jr_task_result
        verification = verify_jr_task_result(task, result)
        if not verification.verified:
            if verification.hallucination_flag:
                reason = (
                    f"HALLUCINATION: success claimed with "
                    f"{len(result.get('steps_executed', []) or [])} steps but "
                    f"zero artifacts/files and zero verifiable claims"
                )
            else:
                reason = (
                    f"{verification.failed}/{verification.total_claims} claims failed: "
                    f"{verification.mismatches[:3]}"
                )
            self._log(f"CLAIM-VERIFIER FAILED [gen1]: {reason}")
            result['success'] = False
            result['error'] = f"Claim verifier: {reason}"
            result['claim_verification'] = verification.as_dict()
            result['gen_tracking'] = {'gen': 1, 'worker': 'jr_cli.py', 'jr_name': self.jr_name}
        else:
            self._log(f"Claim verifier PASSED [gen1] ({verification.passed}/{verification.total_claims} claims)")
            result.setdefault('claim_verification', verification.as_dict())
            result.setdefault('gen_tracking', {'gen': 1, 'worker': 'jr_cli.py', 'jr_name': self.jr_name})
    except ImportError:
        self._log("Claim verifier not available (non-fatal)")
    except Exception as _cv_err:
        self._log(f"Claim verifier error (non-fatal): {_cv_err}")
```

### Observability additions
- **`[gen1]` log tag** — distinguishes Gen 1 verification calls from Gen 3's (which logs the same line without the tag). Operators can grep journalctl for "CLAIM-VERIFIER" + tag to filter by generation.
- **`gen_tracking` metadata** — every Gen 1 result now includes `{'gen': 1, 'worker': 'jr_cli.py', 'jr_name': ...}` in the result dict. Downstream (Medicine Woman, jr_observer.py, audit consumers) can see which generation processed each task.

### Verification (live proof)

Canary ticket `#2585` dispatched at 13:14:30 May 18. Gen 1 picked it up, ran the new code path, caught its own hallucination:

```
May 18 13:14:30 redfin python3[1576920]: [2026-05-18 13:14:30] [it_triad_jr] 
  CLAIM-VERIFIER FAILED [gen1]: HALLUCINATION: success claimed with 1 steps 
  but zero artifacts/files and zero verifiable claims
May 18 13:14:30 redfin python3[1576920]: [2026-05-18 13:14:30] [it_triad_jr] 
  Queue task 2585 failed: Claim verifier: HALLUCINATION...
```

**The `[gen1]` tag is the smoking-gun proof** — that log line cannot exist except via the new code path. First time in federation history Gen 1 has caught a hallucination.

## What Phase 1 did NOT include

Per Council vote scope, Phase 1 was the minimum-viable Shape 5 closure. Phase 2 (still pending) includes:
1. **Audit-emit hook** — structured event emission to `jr_observation_log` (or via journalctl tag) so `jr_observer.py` can react to verification events programmatically rather than just log-watching
2. **Unit tests for Gen 1 verifier path** — pytest cases mocking executor + asserting claim_verifier is invoked
3. **Dark-factory regression suite** — automated run that confirms Shape 5 stays at 0 over time
4. **Gen 2 (`jr_task_executor.py`) audit** — does Gen 2 also bypass verification? If yes, same hardening pattern.

## Why Shape 5 closure was unanimous Council priority

Per `COUNCIL-VOTE-RING-SELECTION-MAY18-2026.md`, all 8 specialists voted Option A:

- **Crawdad**: "Shape 5 is not a model failure; it is a structural vulnerability. Verification logic is duplicated and inconsistent. An adversary can exploit the weaker verification path (Gen 1) to bypass security gates."
- **Spider**: "R-dispatcher is the only upstream guard. Without it, jr_observer processes garbage."
- **Coyote** (frustration-dissent): "Council prioritized T2 Rings for Shape 6 while ignoring urgent Shape 5 need. R-dispatcher IS the answer to what's BROKEN now."
- **Turtle**: "R-dispatcher serves 175-year sovereignty by ending verification asymmetry that would compound across generations."
- **Raven**: "T0 architectural debt is the priority. T2 specialization is optional optimization, not prerequisite."

## Federation-architectural significance

Shape 5 was the federation's first **structural** failure class (vs the four behavioral classes 1-4). All other shapes were Jr-output patterns that defenses could catch; Shape 5 was a CODE PATH ASYMMETRY where defenses simply weren't called. The fix is not a new defense — it's making the existing defenses reachable from all paths.

This pattern generalizes: any time the federation grows a new code path that handles tasks (Gen 4 in the future?), that path must call the same `verify_jr_task_result()` gate. Otherwise it inherits Shape 5.

**Phase 2 audit-emit hook will make this checkable**: every task completion emits a structured event with `gen` field. Medicine Woman can alert if any task completes with no audit event, or if completion-vs-audit-emit ratio drifts.

## Walmart-pitch substrate

> "We don't just build defenses — we map and unify the paths those defenses must cover. The federation discovered an entire code-path generation that bypassed every defense we'd built. We closed it within the same hour the dark-factory canary surfaced it. The Council had predicted this gap four hours earlier in their morning vote; the canary just confirmed it. Disciplined observability + Coyote-driven adversarial-error detection means we catch architectural debt before it becomes incident debt."

## Lineage
- `KB-DARK-FACTORY-MAY18-2026-PM-FIVE-FAILURE-SHAPES-THREE-DEFENSES.md` — the canary that surfaced Shape 5
- `COUNCIL-VOTE-RING-SELECTION-MAY18-2026.md` — unanimous Council mandate to ship Phase 1
- `COUNCIL-VOTE-JR-MAKE-IT-RIGHT-MAY18-2026.md` — Coyote's morning prediction
- `KB-THREE-GENERATIONS-JR-EXECUTION-AND-DORMANT-OBSERVER-MAY18-2026.md` — the three-generations architecture
- `ASSEMBLY-LINE-WORKER-LLM-ARCHITECTURE-MAY18-2026.md` — Phase 2 substrate
- `feedback_systemctl_status_before_kill_may18_2026.md` — discipline rule from the earlier mistake that exposed Gen 1

## Open follow-ups (kanban candidates)

1. **`INFRA-R-DISPATCHER-PHASE-2-MAY18-2026`** — audit-emit hook + unit tests + dark-factory regression
2. **`INFRA-GEN-2-VERIFIER-AUDIT-MAY18-2026`** — does Gen 2 also bypass verification?
3. **`INFRA-PERIODIC-DARK-FACTORY-SCHEDULER-MAY18-2026`** — nightly canary to detect Shape 6+ emergence
