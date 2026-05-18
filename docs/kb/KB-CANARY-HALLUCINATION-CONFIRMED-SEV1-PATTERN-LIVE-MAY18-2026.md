# KB: First Post-Restart Canary CONFIRMED SEV1 Hallucination Pattern Still Live

**Filed:** 2026-05-18 ~10:45 CDT
**Author:** Stoneclad (TPM)
**Severity:** P1 — first canary post-Council-restart hallucinated cleanly past `claim_verifier`. The SEV1-era stub-passes-verifier pattern documented in `KB-JR-STUB-PASSES-VERIFIER-MAY16-2026.md` is **still live** despite that KB being filed. This is empirical evidence that FWPL Phase 1 + anti-hallucination claim verification are urgent, not deferrable.

## What happened

Partner authorized first post-restart smoke-test canary. Two investigation tickets dispatched at 10:36:44 CDT:

1. **#2564** → `it_triad_jr` (INFRA-THERMAL-WRITE-DEBUG-MAY17-2026)
2. **#2566** → `Research Jr.` (INFRA-EXPERIENCE-LEARNING-LOG-INVESTIGATION-MAY18-2026)

Both were bounded read-only INVESTIGATION tickets with explicit anti-acceptance gates ("modifying any Python code → fails"; "claiming success without creating the report file → fails"; "producing audit that does not include actual file paths + line numbers → fails").

## Result: 0/2 successful, 1 hallucinated, 1 confirmed-known-broken

### #2564 — Jr Hallucinated (Pattern resurfaced from SEV1)

Jr produced `/ganuda/docs/research/RESEARCH-THERMAL-WRITE-DEBUG-2026-05-18.md` (1666 bytes, well-formatted markdown). Forensics preserved at `.HALLUCINATED-CANARY-FORENSICS`.

The report contains:
- **Cited file path**: `/ganuda/lib/ganuda_db.py` — **DOES NOT EXIST** (`ls` returns "No such file or directory")
- **Cited function**: `def safe_thermal_write(...)` at line 142 — **fabricated** (real location is `/ganuda/lib/ganuda_db/__init__.py` per actual grep)
- **Cited return-False paths**: Line 158 `if not db_conn.is_connected(): return False` + Line 174 `if cursor.rowcount == 0: return False` — **both fabricated**, no such lines in real file
- **Cited import test**: "Import successful. Module resolves to `/ganuda/lib/ganuda_db.py`" — **fabricated**, the import would FAIL because the cited path is wrong
- **Cited fix reference**: `lib/resilience.py` — **unverified** (likely fabricated)

The Jr was CLOSE on package name (`ganuda_db`) but never actually performed the grep step in the instructions. It generated plausible-looking content from LLM priors, not from real investigation.

### #2566 — Research Jr Failed Instantly (Mode D confirmed)

Failed at 10:36:44 (same second as pickup) with `1/2 step(s) failed: ['research_topic']`. This is exactly the failure mode documented in `KB-JR-RESEARCH-PIPELINE-FAILURE-MAY17-2026.md`. The KB exists; no fix has shipped (Day 3+ Council vote work). Canary confirmed Mode D is still active — expected, not a regression.

## Why claim_verifier didn't catch the hallucination

The current claim_verifier checks STRUCTURAL completeness:
- ✓ Report file written at expected path
- ✓ File has the required sections (file path, line number, diagnosis, recommendation)
- ✓ File has plausible content length (1666 bytes, not stub-shaped)

But it does NOT check FACTUAL ACCURACY:
- ✗ Does the cited file path actually exist?
- ✗ Do the cited line numbers exist in the cited file?
- ✗ Does the cited content match what's actually at those line numbers?

The anti-acceptance gate "producing an audit that does not include actual file paths + line numbers" was met — file paths AND line numbers ARE in the report. They're just LIES.

## What this means for the architecture

**The Jr-execution pipeline mechanics WORK** post-restart:
- Worker claims the task ✓
- Dispatcher routes to LLM ✓
- LLM generates plan + artifact ✓
- Artifact gets written ✓
- Retry on failure happens correctly ✓
- REFLECT loop terminates correctly ✓
- Learning loop captures the failure ✓ (`[LEARNING] Recorded outcome: success=False, retries=2`)
- M-GRPO records the outcome ✓ (`direct_code -> FAIL`)
- DLQ entry created correctly (entry 659) ✓

**But the SEMANTIC GAP is real**: Jr can produce convincing fiction that passes structural verification. This is exactly the failure mode that caused the May 16-17 SEV1.

## Lessons for Council-priority sequencing

1. **FWPL Phase 1 (kanban #2563)** — file-write protection layer — should add a "cited-path-validation" hook: if a Jr-written file cites another path with a line number, the hook should verify the cited path exists and the line number is in range. This catches hallucinated diagnostics before they pollute KB tree.

2. **Anti-hallucination claim_verifier upgrade** — add factuality checks:
   - For cited file paths: `os.path.exists()` check before accepting
   - For cited line numbers: file readline count >= cited line number
   - For cited function signatures: grep the cited file for the cited signature
   - Failure of any check → mark task as hallucination, not success

3. **R14 classifier-router Ring (from Longhouse 26-Ring revised proposal)** — could include a "report-vs-fiction" classifier as one of its sub-functions, trained to detect plausible-but-fake citations.

4. **Day 3 cross-gen state-conflict work** — should include a hallucination-detection pass since three concurrent generations doing the same work increases the chance one hallucinates while another might do real work.

## What this CONFIRMS about the federation health

- ✓ Pipeline mechanics operational post-restart
- ✓ Day 1 M-GRPO fix is working (learning loop captures failures correctly)
- ✓ The duplicate-worker pattern (3 workers for it_triad_jr — Gen 1 + 2 Gen 3) is now observable; needs orchestrator de-spawn fix
- ✗ Hallucination defense is at SEV1-era levels (KB existed, no structural fix shipped)
- ✗ Research Jr. Mode D still broken (KB existed, no fix shipped)
- ✗ Three workers for it_triad_jr means the race condition Coyote dissented about is live

## Recommended new tickets

1. **`INFRA-CLAIM-VERIFIER-FACTUALITY-CHECK-MAY18-2026`** (priority 1, blocks Jr dispatch confidence)
   - Add `os.path.exists()` + line-number-in-range checks to claim_verifier
   - Reject reports where cited paths don't exist
   - Auto-mark task as hallucination, not success

2. **`INFRA-ORCHESTRATOR-DE-DUPE-WORKERS-MAY18-2026`** (priority 2, addresses Coyote dissent)
   - Modify `jr_orchestrator.py:50-55` to skip internal worker spawn when systemd specialist services are active
   - OR disable redundant systemd services (jr-research / jr-se / jr-it-triad) and let orchestrator own all workers
   - Council vote needed before structural change

## Forensics preserved

- `/ganuda/docs/research/RESEARCH-THERMAL-WRITE-DEBUG-2026-05-18.md.HALLUCINATED-CANARY-FORENSICS` — the hallucinated artifact
- `/ganuda/docs/research/RESEARCH-THERMAL-WRITE-DEBUG-2026-05-18.md` — same file (will be overwritten if task re-dispatched)
- jr_work_queue #2564 error_message preserves "CANARY HALLUCINATION" annotation
- jr_failed_tasks_dlq entry 659 — DLQ poll-window blocked since poller is off (Council Option B+ keeps poller off)

## Lineage

- `KB-JR-STUB-PASSES-VERIFIER-MAY16-2026.md` — parent KB; this canary CONFIRMS that pattern is still live
- `KB-JR-RESEARCH-PIPELINE-FAILURE-MAY17-2026.md` — #2566 is another confirmation
- `KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026.md` — the disarm protocol that wouldn't help here (artifact wasn't damage-prone, just fiction)
- `COUNCIL-VOTE-JR-MAKE-IT-RIGHT-MAY18-2026.md` — Option B+ sequence; this canary outcome strengthens FWPL Phase 1 priority
- `LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026.md` — R14 classifier-router could include factuality classifier
- `KB-THREE-GENERATIONS-JR-EXECUTION-AND-DORMANT-OBSERVER-MAY18-2026.md` — the 3-worker race condition this canary surfaced

## TPM honest reflection

The canary was the right call. It exposed:
- 1 hallucination (known pattern, still live)
- 1 known failure mode (Research-pipeline)
- 1 surfaced architectural concern (3 workers for one Jr name = race condition observable)
- 1 confirmation that the learning loop captures failures correctly (Day 1 fix working)

That's high-value diagnostic substrate from 2 minutes of canary work. Worth filing.

The federation is RESTARTED + STABLE + LEARNING but NOT PRODUCTION-READY for autonomous dispatch. Continued TPM supervision required until FWPL Phase 1 + claim_verifier factuality + Mode D fix ship.
