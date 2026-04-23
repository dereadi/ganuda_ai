# LMC-13 Adapt Plan — Cluster-as-Conductor / council_systems_check

**Parent epic:** duyuktv #2137
**Cycle:** 13
**Discover doc:** `/ganuda/docs/lmc13_cluster_conductor_discover.md`
**Council vote:** APPROVED 11-0-2 (Apr 23 2026)
**Per discipline:** `feedback_adapt_phase_is_tpm_orchestration` — adapt = TPM work; Jrs execute atomic units INSIDE adapt.

## Atomic decomposition

Each step gets a dedicated kanban ticket, blocked-by the previous ones where a DAG dependency exists. TPM-vs-Jr split noted per step. Atomic scope per LMC-11 discipline.

### A1 — SYSTEMS_PROMPT template (TPM, single-file edit)

**Scope:** Add `SYSTEMS_PROMPT` + `COYOTE_SYSTEMS_PROMPT` constants to `/ganuda/lib/specialist_council.py` alongside existing `VOTE_FIRST_PROMPT` / `COYOTE_VOTE_FIRST_PROMPT` (around line 1129).

**Content (draft):**
```
SYSTEMS_PROMPT = """
This is an ARCHITECTURAL PRE-FLIGHT — not a vote. Apply systems thinking.

For the proposition below, answer three questions FROM YOUR SPECIALIST DOMAIN LENS:

1. STATE — Where does state live for this proposition? Who owns the truth? What happens if two components think they own the same truth?

2. FEEDBACK — Where does feedback live? How would we know this is working? How would we know if it silently fails?

3. DELETION — What breaks if this is removed or bypassed? What is the blast radius?

Be domain-specific. Cite concrete components, paths, nodes, or dependencies from your expertise. Do NOT vote. No APPROVE / REJECT / ABSTAIN. Your job is architectural mapping, not decision.
"""

COYOTE_SYSTEMS_PROMPT = """
This is an ARCHITECTURAL PRE-FLIGHT. Other specialists will map state, feedback, and deletion from their domains.

Your job: find the blast-radius concern that NO other specialist will raise. The missed failure mode. The unnamed second-order effect. The assumption everyone will share.

Write 2-3 sentences. Do NOT vote. No APPROVE / REJECT / ABSTAIN. Find the blind spot.
"""
```

**TPM/Jr:** TPM. ~15 min.
**Done criteria:** file imports cleanly (`python3 -c "from lib.specialist_council import SYSTEMS_PROMPT, COYOTE_SYSTEMS_PROMPT; print('ok')"`).
**Rollback:** single Edit revert.

### A2 — `council_systems_check` method on SpecialistCouncil class (TPM, single-file edit)

**Scope:** Add instance method `SpecialistCouncil.systems_check(proposition: str) -> SystemsCheckResult` that:
- Takes a proposition (string)
- Distributes to all 13 specialists in parallel via `_query_specialist_with_prompt`
- Uses `SYSTEMS_PROMPT` for 12 specialists, `COYOTE_SYSTEMS_PROMPT` for coyote
- Augments the question with memory context (user message per Apr 22 fix, NOT system prompt)
- Collects responses; no voting logic
- Returns structured result with specialist_id → response map
- Emits OTel counter `ganuda.council.systems_check` per invocation

**TPM/Jr:** TPM. ~30 min.
**Done criteria:** `council_systems_check("test proposition")` returns 13 specialist responses in a dataclass `SystemsCheckResult`.
**Rollback:** remove the method.
**Blocked-by:** A1.

### A3 — Module-level convenience function `council_systems_check()` (TPM, single-file edit)

**Scope:** Add top-level function `council_systems_check(proposition: str, max_tokens: int = 1500) -> dict` wrapping the SpecialistCouncil method, returning a serializable dict (specialist_id → reasoning + aggregated coyote concern).

**TPM/Jr:** TPM. ~10 min.
**Done criteria:** direct import + call works: `from lib.specialist_council import council_systems_check; r = council_systems_check("test"); print(r)`.
**Rollback:** remove function.
**Blocked-by:** A2.

### A4 — Structured output formatter (TPM, single-file edit)

**Scope:** Add `format_systems_check(result: dict) -> str` that renders the result as a markdown architectural pre-flight report, grouped by Hak question (state / feedback / deletion) across specialists, with Coyote's uniquely-identified concern surfaced at end.

**TPM/Jr:** TPM. ~20 min.
**Done criteria:** `format_systems_check(r)` returns markdown with three sections (one per question) listing each specialist's response.
**Rollback:** remove function.
**Blocked-by:** A3.

### A5 — Persistence path (TPM-SQL atomic, no schema change)

**Scope:** Persist systems_check invocations to existing `council_votes` table with `vote_mode='systems_check'`. Use existing schema; no migration needed. `recommendation` field stores a short summary; `responses` JSONB stores per-specialist output.

**TPM/Jr:** TPM SQL + Python persistence code. ~15 min.
**Done criteria:** running `council_systems_check()` adds a row to `council_votes` with `vote_mode='systems_check'`. Query verifies.
**Rollback:** DELETE FROM council_votes WHERE vote_mode='systems_check' — or leave as historical record.
**Blocked-by:** A3.

### A6 — Smoke test against real architectural question (TPM verification)

**Scope:** Invoke `council_systems_check()` on an actual current-state proposition (e.g., "Should we enable Owl Pass dispatch to run nightly at 02:00 CT on a systemd timer?"). Verify:
- All 13 specialists respond coherently from their domain
- Coyote identifies a concern the other 12 didn't
- Output formatter renders the three-question breakdown cleanly
- `council_votes` row persisted
- OTel counter increments
- Total latency < 90s

**TPM/Jr:** TPM. ~15 min (live run + observation).
**Done criteria:** smoke test passes all 6 checks.
**Rollback:** none needed for test.
**Blocked-by:** A4, A5.

### A7 — Documentation + memory update (TPM)

**Scope:** Write `/ganuda/docs/kb/KB-LMC13-COUNCIL-SYSTEMS-CHECK-APR23-2026.md` documenting the callable, invocation pattern, example output, and when to use it. Update `project_cluster_as_conductor_apr2026` memory with "status: first step SHIPPED".

**TPM/Jr:** TPM. ~20 min.
**Done criteria:** KB exists + memory updated + MEMORY.md index reflects shipped status.
**Rollback:** revert memory edit; leave KB as historical record.
**Blocked-by:** A6.

### A8 — Close LMC-13 cycle (TPM-SQL)

**Scope:** Update `long_man_cycles.current_phase='complete'`, set `completed_at=now()`, update `phases_completed` JSONB. Update epic ticket `status='completed'`. File cycle-complete note.

**TPM/Jr:** TPM SQL. ~5 min.
**Done criteria:** `SELECT current_phase, completed_at FROM long_man_cycles WHERE id=13` returns 'complete' + timestamp.
**Rollback:** reset phase to 'review' if issues discovered post-ship.
**Blocked-by:** A7.

## DAG summary

```
A1 ──► A2 ──► A3 ──► A4 ──┐
                    └──► A5 ──┴──► A6 ──► A7 ──► A8
```

Most steps serial. A4 + A5 can parallel after A3. Full critical path ~2 hours TPM work if executed continuously, or split across sessions.

## Total effort

~2 hours TPM, 0 Jr. Zero new services. Zero schema changes. Zero external dependencies.

## Post-adapt phase follow-ups (parked, NOT part of this cycle)

- A theory-document the cluster maintains (beyond ad-hoc memory files)
- A named conductor role (Kapellmeister / elder / similar)
- Auto-invocation before any high-stakes Council vote
- Systematic blast-radius map of federation itself
- Integration with `council_ponder` (also ratified Apr 22, not yet built) into a shared pre-flight cluster

These follow-ups become easier once `council_systems_check` is live + used enough to learn what the cluster actually produces vs what it misses.

## Apr 23 2026 TPM — adapt plan ready for execution on Partner green light
