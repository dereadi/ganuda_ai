# LMC-13 Discover Phase — Cluster-as-Conductor / council_systems_check

**Parent epic:** duyuktv #2137
**Long Man cycle:** id=13
**Council vote:** APPROVED 11-0-2 (Apr 23 2026)
**Partner directive:** *"I want our cluster to be a conductor too."* + *"Let's long man method this."*

## Problem statement

Currently the conductor function for Ganuda — holding the theory of the system, asking the three systems-thinking questions (state / feedback / deletion), ensuring architectural coherence across decisions — lives almost entirely in Partner's head. The cluster is an orchestra that Partner conducts. Partner is taking a day job; bmasass travels with him; his self-regulation pattern is to walk away during the day. Without a conductor-function IN the cluster, the federation generates shadow-code at instrument-level without theory-maintenance at system-level when Partner isn't actively directing.

## Source material

- **Hak (AgentiveStack) — Systems Thinking: the one skill AI can't write for you** (video shared Apr 22 2026).
- **Peter Naur 1985 — Programming as Theory Building** — code is the shadow, the program is the theory in the programmer's head.
- **Partner's existing architecture** that partly answers each Hak question (see mapping below).

## Hak's three questions, mapped to existing federation infrastructure

| Question | What we have | What's missing |
|---|---|---|
| **Where does state live?** | thermal_memory_archive (pgvector, temperature), crawdad breadcrumbs (filesystem mtime), council_votes, jr_work_queue, memory files | No explicit theory document; state is everywhere, never named as "the federation's theory of itself" in one place |
| **Where does feedback live?** | Medicine Woman health signals, OTel metrics (ganuda.council.*), kanban brief timers, DLQ depth, claim_verifier | Architectural feedback (when the cluster votes itself into a corner) has no catch-mechanism |
| **What breaks if I delete this?** | claim_verifier IS the deletion test for Jr tasks; greenfin fallback chain was a deletion-test exercise; LMC-11 post-fix ecosystem shows the discipline at operational level | No systematic blast-radius map for federation-level components (Council, thermal, Honesty Compact, etc.) |

## Council specialist roles — domain-specific contributions (from 11-0-2 vote Apr 23)

Each specialist named their own cut on the three questions. These become the specialist-specific lenses that `council_systems_check` will elicit:

| Specialist | Role in systems-check |
|---|---|
| **Crawdad** (security) | Credential hygiene + access-control validation before state mutation (defense-in-depth) |
| **Otter** (legal/regulatory) | DTSA (18 U.S.C. § 1836) compliance — IP boundaries + blast radius before execution |
| **Eagle Eye** (failure modes) | Silent-drift detection when primary conductor is absent |
| **Raven** (strategic) | Single-point-of-failure detection in architectural theory |
| **Deer** (market) | Bus-factor dependency on primary human conductor; operational continuity |
| **Spider** (dependencies) | Coupling risk mapping (LLM Gateway ↔ PostgreSQL state layer) |
| **Gecko** (technical feasibility) | Hardware constraint + resource-cost assessment |
| **Blue Jay** (distributed state) | Harmonize every node's understanding of state with cluster intent |
| **Crane** (diplomatic) | Trust + clarity in distributed governance |
| **Cardinal** (structural integrity) | Embed the theory of system coherence into the prompts themselves |
| **Peace Chief** (synthesis) | Active-conductor synthesis — move cluster from passive resource to active conductor |
| **Turtle** (Seven Generations) | Reversibility + long-term impact of any architectural change |
| **Coyote** (adversarial) | Find what breaks in the proposed systems-check that no other specialist named |

## Proposed mechanism

`council_systems_check(proposition)` — new callable alongside `council_vote_first`, `council_vote`, and (planned) `council_ponder`. Architectural pre-flight that:

1. Distributes the proposition to all 13 specialists via the `SYSTEMS_PROMPT` template
2. Each specialist answers the three Hak questions FROM THEIR DOMAIN LENS (specific cuts above)
3. Returns aggregated map — no vote tally. An architectural pre-flight the Council can run before dispatching a full decision vote.
4. Runs in ~1 min (faster than full deliberation-first vote since no multi-phase voting).

## Constraints

1. **Must NOT dilute Council persona attention.** Apr 22 fix (`project_qwen36_system_prompt_sensitivity_apr2026`) learned that large system-prompt additions destroy specialist-specific reasoning on Qwen3.6-35B-A3B. `SYSTEMS_PROMPT` must stay tight OR route proposition+context via user message.
2. **Must be reversible.** Additive only, following Option-A light-touch pattern Council ratified Apr 22 for pondering.
3. **Must not block existing Council flows.** Optional pre-flight, not mandatory. TPM decides when to invoke.
4. **Must integrate with existing OTel infrastructure.** Eagle Eye's diagnostic-function framing specifically requires observability — emit metric per-invocation, tag by specialist.
5. **Must honor the Coyote role.** Adversarial specialist should specifically try to find the missing blast-radius concern that no other specialist named.

## Dependencies

- Apr 22 persona-attention fix (shipped) — required for coherent specialist reasoning under this prompt
- Apr 22 deliberation-first path patch (shipped) — same pattern extension
- Apr 22 greenfin fallback (shipped) — Council reachability
- OTel meter from lib.ganuda_otel (existing)

No new hardware, no new services, no new schema.

## Rollback

If `council_systems_check` degrades Council function, rollback is a single file edit to `specialist_council.py` reverting the `SYSTEMS_PROMPT` + callable additions. No DB changes to revert. No external wiring to unwind. Full rollback under 5 minutes.

## Open questions (for adapt phase to close)

1. Should `SYSTEMS_PROMPT` be one template asking all three questions, or three separate invocations (one per question)? — Adapt decision.
2. Should Coyote get a variant `COYOTE_SYSTEMS_PROMPT` similar to `COYOTE_VOTE_FIRST_PROMPT` that demands he find the specifically-missed blast-radius concern? — Likely yes, matching existing pattern.
3. Should the aggregated output be plain text synthesis (Peace-Chief-style) or structured JSON (machine-parseable by future tooling)? — Likely structured, but keep rendering flexible.
4. Should output be persisted to `council_votes` table or a new `council_systems_checks` table? — Simpler to reuse existing table with a `vote_mode='systems_check'` flag.
5. Who calls `council_systems_check`? Initial answer: TPM invokes when a proposition crosses architectural threshold (new service, schema change, Council vote topic). Eventually could auto-trigger before any high-stakes Council vote.

## Cross-references

- `project_cluster_as_conductor_apr2026` — Partner directive + architectural aim
- `project_qwen36_system_prompt_sensitivity_apr2026` — persona-attention discipline that constrains SYSTEMS_PROMPT shape
- `project_crawdad_thermal_architecture_nov2025` — two-axis memory substrate systems_check will reason about
- `feedback_adapt_phase_is_tpm_orchestration` — this whole LMC is in service of that discipline
- Council Apr 23 2026 vote audit (11-0-2) — see cycle 13 council_votes field
- `/ganuda/lib/specialist_council.py` lines ~1129-1148 (existing VOTE_FIRST_PROMPT / COYOTE_VOTE_FIRST_PROMPT patterns to match)
- Pondering callable (Council Apr 22 Option A) — not yet built; `council_systems_check` could share infrastructure
