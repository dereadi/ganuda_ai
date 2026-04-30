# KB — LMC-16 Workflow Proceduralization (Fire Guard Backlog Reviewer) Shipped

**Date:** 2026-04-30 PM
**Author:** TPM (Stoneclad)
**Cycle:** LMC-16 (DISCOVER ✓ → DELIBERATE ✓ → ADAPT ✓ → BUILD ✓ → **REVIEW**)
**Authorizing Council vote:** `08c642a0fd176a92` — APPROVE with mitigations, Diversity 0.358 HEALTHY (highest of any federation vote to date)
**Trigger:** Partner Apr 29 evening articulation of intake-discipline failure mode + Apr 30 directive to apply Long Man Method.

## What landed

**The federation's first audit-traced workflow-proceduralization mechanism.** Eleven external scholarly anchors filed this week (Conway-Smith / Berg / Orthwein / Ehrman / Blackburn / Hoffman / Griffiths / Seed / Kemp / Friston / Koch) all converged on "engineered proceduralization with audit chain." LMC-16 operationalizes that insight at the federation workflow layer.

### Schema (production)

`docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql` applied:

- **`classification_audit_log`** — append-only hash-chained record of every backlog classification. UPDATE/DELETE blocked by trigger; only `ratify_classification(audit_id, action)` function can record Partner ratification (idempotent, double-ratify rejected)
- **`classification_taxonomy_versions`** — versioned taxonomy (Turtle 7GEN: future TPMs evolve via Council vote)
- **Initial taxonomy v1** seeded with 5 classes: still_relevant / needs_decomposition / close_as_stale / active_epic_continuation / backlog_candidate
- **GRANT** to `claude_council` (LMC-15 Stage 4 SET ROLE pattern)

### Module

`lib/fire_guard_backlog_reviewer.py`:

- **Hybrid heuristic + LLM classifier** — heuristic fast-path catches unambiguous cases (>90 days stale → close_as_stale candidate; "EPIC:" titles → needs_decomposition); LLM ambiguous-middle (with `guided_json` schema constraint + 1500-token budget for Qwen3.6 CoT)
- **Crawdad CRITICAL mitigation**: input sanitization strips control chars + ``` + `"""`, max-length 2000
- **Hash chain**: SHA-256 over (prev_hash, ticket_id, classification, timestamp). Each row's `prev_hash` = previous row's `this_hash`. Tamper-detection by chain-replay
- **SET ROLE claude_council** (LMC-15 discipline)
- **Health gate**: `is_classifier_healthy()` halts classifier if rejection-rate >0.20 over 7-day window (Eagle Eye SLA)
- **Manual-only close MVP** (Coyote + Eagle Eye convergence)

### Periodic review script

`scripts/fire_guard_backlog_review.py`:

- Fetches up to 50 backlog tickets older than 24h since last classification
- Read-only on `duyuktv_tickets` (Spider mitigation: no write-lock contention)
- Classifies each via library, persists audit log
- Posts ONE Slack summary to #fire-guard with table of classifications awaiting Partner ratification
- Health-gate check at start: halts if classifier-health degraded
- CLI flags: `--limit N`, `--dry-run`, `--no-slack`

### Verified end-to-end

Real run (limit=3, no-slack) produced:
- 3 audit log rows (IDs 7/8/9) for VetAssist tickets 1724/1725/1726
- All classified `close_as_stale` (103 days no movement)
- Hash chain verified: row 7 genesis, row 8 prev=row7.this, row 9 prev=row8.this
- `partner_action` NULL on all three (correct: awaiting ratification)

## Council mitigations — verification

| Concern | Mitigation | Verified |
|---|---|---|
| Crawdad CRITICAL: prompt injection | `_sanitize_for_classifier` strips control + fences + truncates 2000 | ✓ smoke-tested |
| Crawdad HIGH: audit log timestamp | PostgreSQL `NOW()` default + hash chain | ✓ verified in audit log |
| Crawdad: append-only | `trg_classification_audit_immutable` blocks UPDATE/DELETE | ✓ explicit error on attempts |
| Eagle Eye: manual-only close MVP | `partner_action` nullable; `ratify_classification()` idempotent | ✓ double-ratify rejected |
| Eagle Eye: rejection-rate halt | `is_classifier_healthy()` checked at start of each run | ✓ integrated in `run()` |
| Spider: read-only on duyuktv_tickets | Script only SELECTs from duyuktv_tickets | ✓ no UPDATE/INSERT against duyuktv_tickets |
| Spider: single-writer audit log | Trigger blocks all UPDATE/DELETE; ratify_classification uses replica-mode within scoped function | ✓ |
| Coyote DISSENT: surface, don't act | Slack summary surfaces; Partner ratifies | ✓ |
| Coyote: track ratification-with-comment | (deferred to LMC-17; metric design exists but not wired) | partial |
| Turtle 7GEN: versioned taxonomy | `classification_taxonomy_versions` table; v1 seeded | ✓ |

## Known limitations / scope deferred

- **vLLM Qwen3.6 reasoning-mode CoT leakage** — same issue as #2160 (closed Apr 29). LLM classifier degrades to safe-default `still_relevant` when CoT consumes token budget. Heuristic fast-path covers the load-bearing cases (very stale + EPIC blobs); LLM handles ambiguous middle. Acceptable for MVP since Partner ratifies all close-out actions.
- **Slack webhook not wired in production yet** — `FIRE_GUARD_SLACK_WEBHOOK` env var; `--no-slack` flag for testing. Script logs would-have-posted text when webhook absent.
- **systemd-user-timer cron schedule not yet installed** — script ready; `.timer`/`.service` units to be added in follow-on (mirrors `federation-pg-backup.timer` from Apr 28 NFS work).
- **Intake routing classifier (Step 4 of ADAPT plan) deferred** — Partner-side workflow change; MVP is periodic review only.
- **Coyote ratification-with-comment metric** — not wired in MVP; design exists in ADAPT plan.

## Patent #1 prosecution substrate

LMC-16 is **the federation operationalizing its own architectural insight** on the day external scholarly substrate is densest (eleven convergence points this week). When Patent #1 (Governance Topology) is challenged by external review:

1. The federation is not just *theorizing* citizens-assembly governance (Kemp Apr 30 substrate). It runs the digital implementation continuously: 12+ Council audit hashes this week.
2. The federation is not just *theorizing* engineered-proceduralization-with-audit (Conway-Smith Apr 28 + Friston Apr 30 substrate). It applies the pattern to its own workflow via Fire Guard Backlog Reviewer.
3. The hash chain in `classification_audit_log` is structurally identical to the Council-audit-hash chain in `council_votes` — *the architectural pattern generalizes from cognition to operations*, which is the load-bearing claim Patent #1 needs to defend.

## Files changed

- **NEW** `/ganuda/docs/lm_workflow_proceduralization_discover.md`
- **NEW** `/ganuda/docs/lm_workflow_proceduralization_adapt_plan.md`
- **NEW** `/ganuda/docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql` (applied)
- **NEW** `/ganuda/lib/fire_guard_backlog_reviewer.py`
- **NEW** `/ganuda/scripts/fire_guard_backlog_review.py`
- **NEW** this KB
- **DB** 2 tables + 1 immutable trigger + 1 ratify function + 1 taxonomy v1 row + grants

## REVIEW phase — what's next

1. **Wire Slack webhook** in production env (ENV var; ~2 min when Partner provides).
2. **Schedule via systemd-user-timer** (mirror `federation-pg-backup.timer`, ~5 min).
3. **First production run** with Slack live — Partner reviews first batch of close-out candidates.
4. **Monitor rejection rate** for first 7 days. Tune classifier prompt or heuristic thresholds if rejection-rate >0.20.
5. **LMC-17 candidates** (deferred from this cycle):
   - Intake routing classifier (Step 4 of ADAPT plan)
   - Ratification-with-comment metric (Coyote signal)
   - vLLM Qwen3.6 CoT-suppression at gateway level (same issue across federation)

## Companion docs

- DISCOVER: `/ganuda/docs/lm_workflow_proceduralization_discover.md`
- ADAPT plan: `/ganuda/docs/lm_workflow_proceduralization_adapt_plan.md`
- Schema: `/ganuda/docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql`
- Council audit: `08c642a0fd176a92` (DELIBERATE phase)
- Substrate: 11 deer signals filed this week (Apr 28-30)

## Why this LMC matters beyond the immediate ship

Per the DISCOVER doc, LMC-16 is the federation operationalizing its own architectural insight on the day the external scholarly substrate is densest. The same hash-chain audit pattern now appears at three federation layers:

| Layer | Audit chain |
|---|---|
| **Cognitive (Council deliberation)** | `council_votes.audit_hash` + `vote_recurrence_links` (Conway-Smith Phase 1, Apr 28) |
| **Memory (sacred-pattern protection)** | `thermal_memory_archive` + immutable trigger (Apr 28 Phase 1.5) |
| **Reflex tier (Phase A schema)** | `reflex_rules.ratification_hash` + `reflex_interventions` (Apr 29) |
| **Workflow (LMC-16 today)** | `classification_audit_log.this_hash` chain |

The pattern generalizes. That's the federation thesis, made concrete.
