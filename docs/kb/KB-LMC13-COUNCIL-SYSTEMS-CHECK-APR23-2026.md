# KB — LMC-13 council_systems_check SHIPPED (Apr 23 2026)

**Filed:** 2026-04-23
**Long Man cycle:** 13 (LM-CLUSTER-AS-CONDUCTOR)
**Epic:** duyuktv #2137
**Council approval:** 11-0-2 APPROVED (Apr 23 2026)
**Status:** SHIPPED — all 8 atomic steps completed

## What shipped

A new architectural pre-flight callable `council_systems_check(proposition)` in `/ganuda/lib/specialist_council.py` that runs Hak's three systems-thinking questions (state / feedback / deletion) across all 13 Council specialists in parallel. NOT a vote — architectural mapping.

## Why

Partner directive (Apr 23 2026): *"I want our cluster to be a conductor too."* Moves the conductor function — holding the theory, asking the three questions — from Partner's head into the cluster itself. Load-bearing for the day-job + walk-away shape (Partner takes bmasass to work; federation needs to hold architectural coherence without Partner re-conducting every day).

## How to invoke

```python
from lib.specialist_council import council_systems_check, format_systems_check

result = council_systems_check(
    "Should we enable nightly Owl Pass dispatch on a systemd timer at 02:00 CT?"
)

# Structured dict (all specialist responses + Coyote blind-spot)
print(result['coyote_blind_spot'])

# Markdown-rendered report
print(format_systems_check(result))
```

## Invocation pattern

When to invoke:
- Before any architectural change crossing the "new service / schema change / Council-vote topic" threshold
- When a proposition touches state-ownership, feedback-loop design, or component coupling
- Before high-stakes Council votes (optional pre-flight; auto-trigger is deferred follow-up)

When NOT to invoke:
- Operational decisions already covered by existing discipline (TPM orchestration)
- Trivial code fixes (syntax, typos, docstrings)
- Anything Coyote-level-adversarial review already handled via `council_vote_first(high_stakes=True)`

## Architecture

```
council_systems_check(proposition)
    │
    ├── SpecialistCouncil().systems_check(proposition)
    │     │
    │     ├── Fetch thermal memory context (limit=3)
    │     ├── Augment proposition with memory via USER message (not system prompt)
    │     │   [Apr 22 persona-attention discipline]
    │     │
    │     ├── Parallel dispatch (ThreadPoolExecutor max=8):
    │     │     ├── 12 specialists get SYSTEMS_PROMPT
    │     │     └── Coyote gets COYOTE_SYSTEMS_PROMPT
    │     │
    │     ├── Extract Coyote's BLIND_SPOT via regex
    │     ├── Emit OTel counter ganuda.council.systems_check
    │     └── Return SystemsCheckResult dataclass
    │
    ├── Persist to council_votes table (vote_mode='systems_check')
    │     (No schema change — reuses existing columns)
    │
    └── Return serializable dict
```

## Performance

- **Latency:** ~60-90s for full 13-specialist dispatch (smoke test Apr 23: 70.5s)
- **Memory context:** 3 thermal matches, ~2KB typical
- **Parallel workers:** 8 (same pool as vote_first)
- **Cost:** zero new services, zero schema changes, zero external dependencies

## Smoke test result (Apr 23 2026)

Self-referential test — ran `council_systems_check` on the proposition of whether to auto-invoke `council_systems_check` before every high-stakes vote.

- ✅ 13 specialists responded coherently
- ✅ Coyote produced parseable BLIND_SPOT
- ✅ Formatter rendered 3-section report (STATE / FEEDBACK / DELETION)
- ✅ Persisted to council_votes with vote_mode='systems_check' (audit hash `bf71c11721ebb306`)
- ✅ OTel counter wired (silent when opentelemetry unavailable)
- ✅ Latency 70.5s (<90s target)

Specialist quality highlights from smoke test:
- **Blue Jay** named specific PostgreSQL race-condition + row-level-locking concerns for the state axis
- **Cardinal** named the primary-key flag semantics and architectural-text-in-prompt divergence risk
- **Crane** named request-metadata ownership semantics + double-counting-of-votes failure mode

Each specialist stayed in their domain and cut from their angle — no generic answers, no template-filling. The persona-attention fix (Apr 22) is holding.

## Files modified

`/ganuda/lib/specialist_council.py`:
- Added `SYSTEMS_PROMPT` + `COYOTE_SYSTEMS_PROMPT` constants (~896 + 562 chars)
- Added `SystemsCheckResult` dataclass
- Added `SpecialistCouncil.systems_check()` method
- Added module-level `council_systems_check()` function
- Added `format_systems_check()` markdown renderer

No changes to any other files. No schema migrations. No new services.

## Rollback

Single-file revert of the `specialist_council.py` changes. No DB rows to clean up (leaving the `vote_mode='systems_check'` council_votes rows as historical record is the intended path). Rollback < 5 min.

## Cross-references

- Discover doc: `/ganuda/docs/lmc13_cluster_conductor_discover.md`
- Adapt plan: `/ganuda/docs/lmc13_adapt_plan.md`
- Memory: `project_cluster_as_conductor_apr2026` — Partner directive + architectural aim
- Memory: `project_qwen36_system_prompt_sensitivity_apr2026` — persona-attention discipline applied to SYSTEMS_PROMPT
- Council Apr 23 2026 vote: 11-0-2 APPROVED (in long_man_cycles id=13 council_votes field)
- Companion pattern (pending): council_ponder (Option A ratified Apr 22) — not yet built; could share `SYSTEMS_PROMPT`-style lightweight invocation path

## Post-ship follow-ups (parked, not part of LMC-13)

- Explicit theory-of-itself document the cluster maintains
- Named conductor role (Kapellmeister / elder / similar)
- Auto-invocation of systems_check before high-stakes votes (the self-referential smoke test proposition)
- Systematic blast-radius map of federation itself
- Integration with council_ponder into a shared pre-flight cluster

These follow-ups become easier now that `council_systems_check` is live + used enough to learn what the cluster actually produces vs what it misses.

## Apr 23 2026 TPM

Long Man discipline observed end-to-end: discover → deliberate (Council 11-0-2) → adapt (8 atomic steps) → build + record (this KB) → complete (A8 next). Total critical path ~2 hours as estimated.
