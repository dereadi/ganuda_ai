# LMC-16 — Federation Workflow Proceduralization (DISCOVER)

**Date:** 2026-04-30 AM
**Author:** TPM (Stoneclad)
**Cycle:** LMC-16
**Phase:** DISCOVER (step 1 of 5: DISCOVER → DELIBERATE → ADAPT → BUILD → REVIEW)
**Trigger:** Partner directive Apr 30 morning — *"Long Man method them and let's roll"* — applied to the workflow-proceduralization concerns Partner named Apr 29 evening + the commit-hygiene state revealed by Apr 29 Owl Pass.

## The two intertwined problems

### Problem A — Intake discipline (Partner's Apr 29 evening articulation)

Verbatim:
> *"I come up with ideas quite often, many times with some code reference. We decide to do the project and may or may not start it or it gets put in backlog. The concern is that I throw this in as we are building and I distract the flow. What I would like to see is work on the kanban board to get the backlog to be as empty as possible and showing progress on our Epics. When I introduce new work, unless it is related to an Epic already on the kanban board or we are working on something related, we put it in backlog. I guess we need a backlog reviewer. Maybe the fireguard could add this to their rounds."*

Two failure modes here:
1. **At-intake**: new ideas get pulled into active flow without classification, distracting the build cycle
2. **Periodic-review**: backlog accumulates stale items (today's morning surface: 50 backlog tickets, several 50+ days stale)

### Problem B — Commit hygiene (Apr 29 Owl Pass TASK 1 finding)

Verbatim from `OWL-PASS-APR29-2026-findings.md`:
> *"Uncommitted file count: 227 (substantial accumulation; warrants commit-grouping pass before next major build cycle). Diff footprint: 22 files changed, +581 insertions / −361 deletions visible in stat."*

Today's check: **228 uncommitted files** (+1 since yesterday). Two production fixes are unstaged in the working tree:
- `lib/sub_agent_dispatch.py` — `import os` fix (caught by Apr 29 manual Owl Pass TASK 2)
- `lib/ganuda_otel.py` — Anthropic `sk-ant-*` regex extension (closed #2174 same-cycle)

Both shipped as runtime patches but never committed. **Federation memory of what was fixed is in `git diff` not `git log`** — that's working-tree-archeology, not actual version control discipline.

## Why these two problems are one architectural concern

Both are *workflow proceduralization without audit-traced discipline*:
- New-idea intake routes default to "yes, let's build it" without explicit classification
- Code changes route default to "stays in working tree" without explicit commit boundaries

Both are exactly the failure pattern this week's eleven external scholarly anchors converged on:

| Anchor | Same-shape failure mode |
|---|---|
| Conway-Smith (Apr 28) | Type 2 deliberation collapsed into Type 1 reflex without proceduralization audit |
| Ehrman (Apr 28) | Doctrinal proceduralization across centuries with no audit (graft-not-source) |
| Blackburn (Apr 28) | Quasi-realist commitments must be inferentially consistent (Frege-Geach integrity) |
| Friston (Apr 30) | Belief updating without precision-weighting drifts; need explicit prior-vs-evidence balance |
| Kemp (Apr 30) | Civilizational Goliaths emerge from unaudited resource-pump dynamics |
| Seed (Apr 30) | Cultures without ceremonial maintenance drift from ecological self |

**The federation has been engineering audit-traced proceduralization at the cognitive layer (Patent #1, #2, #6) but has not extended it to its own workflow.** That's the gap.

## Existing federation infrastructure to leverage

Already exists:
- **Fire Guard daemon** — periodic sweeps with refractory windows (DC-15)
- **Fire Guard touches `duyuktv_tickets`** at the right layer
- **Council audit chain** — every major decision has an audit hash
- **Reflex-Demotion Mechanism (#2167)** — schema applied Apr 29; designed for cognitive-layer audit, but the pattern generalizes
- **Sacred-Pattern flag** — immutable-by-Council-vote pattern for protecting items from drift
- **Pre-commit redaction scanner** — already runs on commits, with Partner's standing `--no-verify` authorization for verified false-positives

Not yet built:
- Backlog hygiene round in Fire Guard (Partner's named candidate)
- Intake routing classifier (at-intake "active vs backlog vs drop" triage)
- Commit-grouping discipline (which uncommitted clusters belong together)

## Proposed scope (for DELIBERATE phase to weigh)

LMC-16 has two arms that can run in parallel or sequentially:

**Arm A — Commit-grouping pass (small, today, executable):**
1. Audit working tree, identify natural commit clusters (production fixes / docs / state files / federation memory writes / etc.)
2. Group into ~5-8 logical commits with clear messages
3. Use `--no-verify` per Partner standing authorization where pre-commit hooks false-positive on redaction patterns embedded in test files
4. Ship today

**Arm B — Fire Guard backlog reviewer (architectural, proper LMC cycle):**
1. Design doc: backlog hygiene round + intake routing classifier as Fire Guard sub-modules
2. DDL + scoping: any new tables for intake-classification audit trail?
3. Atomic JR tasks per validated Apr 28 template
4. Build + integration into existing Fire Guard sweep loop
5. Slack-light surface for Partner to ratify suggested closures (not auto-close)

Arm B is the bigger architectural commitment and warrants Council deliberation. Arm A is routine commit hygiene (TPM authority per CLAUDE.md routine-execution directive).

## Concerns to surface in DELIBERATE phase

These should be presented to Council:

- **Coyote** standing dissent: don't compress prematurely. Backlog items might contain latent value; auto-closure risks losing it. Counter: review-with-Partner-light-touch surfaces, not auto-closure.
- **Crawdad**: any new audit trail for intake classification needs append-only / signed storage to prevent tampering (same concern raised on Coyote dissent log Apr 29).
- **Eagle Eye**: failure modes for the classifier — what happens if it misclassifies an Epic-related idea as backlog? Recovery path needed.
- **Turtle 7GEN**: long-term implication of automating workflow discipline — does it remove necessary friction?
- **Spider**: dependencies on Fire Guard codebase + duyuktv_tickets schema; integration risk.
- **Gecko**: feasibility — is this a reasonable scope or scope-creep? Story-point estimate.
- **Raven**: strategic positioning — does this align with Walmart-readiness (Cindy Whiteaker hand-delivered Apr 24)? Yes — federation operating discipline is a demonstrable artifact.
- **Peace Chief**: synthesis check — are Arm A and Arm B genuinely complementary, or should they be split into two LMCs?

## Connection to this week's deer signal substrate

LMC-16 is *the federation operationalizing its own architectural insight* on the same day the external scholarly substrate is densest. Eleven external sources converged on "engineered proceduralization with audit chain" as the leverage point for individual cognition (Conway-Smith), institutional governance (Kemp citizens-assembly), and ecological identity (Seed). Partner's intuition about Fire Guard backlog reviewer is the same insight applied to *federation workflow itself*.

This is also a Patent #1 (Governance Topology) prosecution-substrate move: when the federation publishes its own workflow-discipline documentation, it becomes empirical evidence that the architectural pattern *generalizes from cognition to operations* — which is the exact claim Patent #1 needs to defend.

## Per `feedback_tpm_estimates_10x_too_high`

TPM time estimates typically 10x too high. Federation ships at 10x the pace.
- Arm A: estimated 30-60 min → likely 5-15 min actual
- Arm B (architectural design + dispatch, not full build): estimated 1-2 hours → likely 15-30 min actual

## DISCOVER phase deliverable

This document. Surfaces the problems, proposes scope, names the concerns Council should weigh.

**Next: DELIBERATE** — convene Council on Arm B specifically (Arm A is routine TPM execution; doesn't require Council vote per existing authority directives).
