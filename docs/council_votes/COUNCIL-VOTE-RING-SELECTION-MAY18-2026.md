# Council Vote: First Ring Selection — Which Small LLMs Do We Build?

**Vote audit hash:** `3487bdbbbc1824c6`
**Timestamp:** 2026-05-18 ~13:15 CDT
**Initiator:** Stoneclad (TPM) under Partner directive ("Given certain tasks that the large LLMs struggle with, let's have the council figure out which small LLMs we will be building")
**Mechanism:** Real `council_vote()` invocation — 8 LLM specialists actually called
**Confidence:** 0.25 (LOW — REVIEW REQUIRED flag, but unanimous direction)
**Diversity:** 0.227 with 4 sycophantic pairs flagged
**Concerns raised:** 8 of 8 specialists

## Question

Given today's dark-factory empirical data (5 failure shapes large LLMs produced; 4 caught by T1 deterministic tools; 1 architectural; no T2 specialist Ring evidence yet), which small LLM Ring(s) does the Council commit to building FIRST?

Candidate set:
- **A**: R-dispatcher (T0, 1 week) — unified verifier path across Gens, ends Shape 5 asymmetry
- **B**: R28 stub-detector (T2 Phi-3-mini, 2 weeks) — for Shape 6 when it emerges
- **C**: R29 task-vs-output-alignment (T2 Qwen2-1.5B, 3 weeks) — currently no defense
- **D**: R27 audit-emitter (T3 8B-class, 3-4 weeks) — Eagle Eye Inspector pattern
- **E**: All four sequenced (10-12 weeks)

## Vote tally — UNANIMOUS

| Specialist | Vote | Key reasoning |
|---|---|---|
| **Peace Chief** | A | "Council unanimously agrees R-dispatcher is the critical prerequisite to fix Shape 5" |
| **Raven (STRATEGY)** | A | "BACKLOG T2/T3. T0 architectural debt is the priority. Delaying R-dispatcher costs 10-12 weeks of T2 time on a cracked foundation." |
| **Crawdad (SECURITY)** | A | "Shape 5 is a structural vulnerability. Verification logic is duplicated and inconsistent. An adversary can exploit the weaker verification path (Gen 1)." |
| **Spider (INTEGRATION)** | A | Dependency-mapped that R-dispatcher is prerequisite for ANY T2 Ring deployment. R28/R29 cannot integrate without unified path. |
| **Gecko (PERF)** | A | R28 technical-feasibility analysis favorable (Phi-3-mini fits redfin's 96GB VRAM, ~50ms inference) but doesn't override priority order. |
| **Eagle Eye (VISIBILITY)** | A (implicit) | Filed SLA matrix for future R28/R29 deployment — implies A-first ordering. |
| **Coyote (DISSENT)** | A + frustration | "The Council prioritized T2 Rings for Shape 6 while ignoring urgent Shape 5 need. R-dispatcher IS the answer to what's BROKEN now." |
| **Turtle (7GEN)** | A | "R-dispatcher serves 175-year sovereignty by ending verification asymmetry that would compound across generations." |

**8 of 8 for Option A.** Sub-disagreement on order of B/C/D AFTER A ships, but all agree A is first.

## TPM (Stoneclad) vote: **A — concur with unanimous Council**

Reasoning:
- This morning's Council vote `d6b73288f7c4aabd` (Make-It-Right sequence) already ratified Option B+ with Day 3 = cross-gen state-conflict detection. R-dispatcher IS the Day 3 work, formally.
- Coyote's dissent on this vote is INTERNALLY ALIGNED with consensus — he's frustrated the morning vote's Day 3 hasn't moved yet, not opposing the choice.
- "Don't pre-build" discipline (per `feedback_research_validates_before_architecture_revision_may17_2026`) ratifies deferring B/C/D until failure-shape pressure justifies.
- Walmart-pitch ready: "We designed the entire assembly-line architecture, then BUILT ONLY what observed failures demanded. The federation refuses to pre-build defenses against speculative threats."

## Concerns-as-features integration

| Specialist | Concern | Feature in R-dispatcher build |
|---|---|---|
| Peace Chief | CONSENSUS NEEDED | R-dispatcher's success criteria explicitly include Gen 1 + Gen 3 parity test |
| Raven | STRATEGY (T2 debt-accumulation) | T2 design doc preserved (this design doc); training data collection continues; deploy when justified |
| Crawdad | SECURITY (cracked foundation) | Unified verifier MUST close every gap Gen 1 has today (audit Gen 1's verifier-call path) |
| Spider | INTEGRATION (T2 needs T0 prerequisite) | R-dispatcher API contract designed before any T2 Ring training begins |
| Gecko | PERF (50ms target for future R28) | R-dispatcher routing-decision latency budget <10ms (dwarfed by future Ring latency) |
| Eagle Eye | VISIBILITY (R28/R29 SLA matrix) | jr_observer.py already monitoring; R-dispatcher emits per-route audit row |
| **Coyote** | **DISSENT (Shape 5 still open)** | **R-dispatcher's success metric: post-deploy dark-factory re-run shows ZERO cross-gen-asymmetry pass-throughs** |
| Turtle | 7GEN | R-dispatcher API documented for inheritability (KB + memory file when shipped) |

## Recommended sequence

### NOW (post-Walmart-interview)
1. **Ship R-dispatcher (T0)** — ~1 week TPM-inline
   - Unify verifier path: jr_cli.py + jr_queue_worker.py both call same `verify_jr_task_result()`
   - Add Gen-tracking metadata so every verification can answer "which Gen processed this?"
   - Add audit-emit hook so jr_observer.py sees every verification decision
   - Re-run dark factory to verify Shape 5 = 0

### THEN (gated on Shape 6 emerging in periodic dark factory)
2. R28 stub-detector (T2 Phi-3-mini + LoRA, ~2 weeks)
3. Re-evaluate need for R29 + R27 after R28's empirical impact data

### NEVER (per Council discipline)
- Building T2 Rings against speculative failure shapes that haven't been observed
- Deploying Ring without held-out test passing precision >0.95 / recall >0.85
- Ring deployment without paired ring for true heterogeneity (Coyote dissent #1 still load-bearing)

## Walmart-pitch enrichment (Raven's commercial angle)

> "Our federation's architecture follows what we call **observed-failure-driven Ring growth**. We've designed 26 specialist Rings; we've built zero of them yet. We'll deploy the first specialist Ring only when our own dark-factory observatory shows a failure shape that deterministic tools cannot catch. Today the Council ratified the T0 architectural layer (R-dispatcher); the T2 specialist Rings stay in design until our agents themselves prove they're needed. **We're disciplined Coyotes — we don't pre-build defenses against problems we haven't seen.**"

This is differentiated commercial substrate vs the "AI safety industry deploys speculative defenses" narrative.

## Federation-health flags (carried from morning)

- 8 specialists raised concerns (all-8 pattern is consistent today)
- 4 sycophantic pairs flagged on this vote (was 3 this morning; was 8 at midday; now stabilizing at 4)
- 5 specialists on circuit_breaker=HALF_OPEN still — Council deliberation infrastructure may need attention
- Stoneclad note: vote-after-vote diversity oscillation worth investigating (separate Council session?)

## Partner decisions reserved

1. **Authorize R-dispatcher build** (this week / next week / after Walmart interview)
2. **Authorize the periodic dark-factory schedule** as the Shape-6-detection trigger
3. **Defer T2 Ring training data collection** to background-task status

## Lineage

- `COUNCIL-VOTE-JR-MAKE-IT-RIGHT-MAY18-2026.md` — Day 3 work formalized as R-dispatcher
- `COUNCIL-VOTE-TACTICAL-NEXT-MOVE-MAY18-2026.md` — Coyote's morning dissent now resolved
- `ASSEMBLY-LINE-WORKER-LLM-ARCHITECTURE-MAY18-2026.md` — full design doc this vote selects from
- `KB-DARK-FACTORY-MAY18-2026-PM-FIVE-FAILURE-SHAPES-THREE-DEFENSES.md` — empirical data substrate
- `RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md` — research-validated "don't pre-build" discipline
- `reference_mini_llm_assembly_line_github_substrate_may18_2026.md` — Lightning-AI/litgpt + 2.3M-param substrate
- `feedback_research_validates_before_architecture_revision_may17_2026.md` — discipline rule ratifying pacing
- Patent #6 — observed-failure-driven Ring growth = novel commercial-positioning claim
