# JR INSTRUCTION: ARC-AGI-3 Internal Dogfood Run — 25 Public Games

**JR ID:** JR-ARC-AGI-3-DOGFOOD-APR11-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (or whichever Jr the dispatch lane routes to)
**PRIORITY:** P2 (not blocking Gate 1, not blocking Hulsey Monday, but Partner has greenlit and Eagle flagged the "architectural validation without credit" risk — don't let this sit for more than a week)
**DATE:** April 11, 2026
**SIZE ESTIMATE:** ~8 SP (spike, not epic)
**CDR REFERENCE:** /ganuda/docs/council/COUNCIL-READING-ARC-AGI-3-APR11-2026.md (RATIFIED)

## Context

ARC Prize released **ARC-AGI-3** on April 11, 2026, along with ARC Prize 2026 — a $2M Kaggle competition. ARC-AGI-3 tests four capabilities that current frontier AI scores under 1% on:

1. Explore an unknown environment
2. Acquire its own goals (games ship with no instructions)
3. Build a world model on the fly
4. Learn continuously across levels and sessions

Council (Eagle + Owl) deliberated and converged on the following position:
- **Enter the 25 public games as internal dogfood** against Ganuda's SkillRL + Experience Bank + Jr executor architecture
- **Do NOT enter the Kaggle main track in 2026** — Partner is in spend-down phase, probability-weighted cycles lose
- **Use this as validation of existing federation work** — if the architecture actually produces the four capabilities, the internal scores will beat 1% by a real margin

Partner greenlit: *"I am game!"*

## What to do

### Task 1 — Integration path discovery

**Before writing any code**, determine the integration path for running the 25 public ARC-AGI-3 games against an agent. Options to investigate, in order:

1. **Check arcprize.org** for a public API, Python SDK, or standalone game engine that lets an agent play the games programmatically (not just humans via a web UI)
2. **Check the Kaggle ARC Prize 2026 competition starter kit** — Kaggle upgraded their platform to support the ARC-AGI-3 engine; there will almost certainly be a Python harness in the starter repo even if we're not entering the main track
3. **Check GitHub** — `github.com/fchollet`, `github.com/arc-prize`, or similar — for the ARC-AGI-3 engine source
4. If no public programmatic access exists, check whether ARC Prize offers a research access tier

**Deliverable for Task 1**: a short markdown note at `/ganuda/docs/jr_instructions/JR-ARC-AGI-3-DOGFOOD-APR11-2026-INTEGRATION-NOTES.md` describing the available integration path(s), any API keys or licensing required, and the recommended approach. **If integration requires terms of service acceptance or account creation, STOP and thermalize the blocker for Partner review — do not accept TOS on Partner's behalf.**

### Task 2 — Harness integration

Once the integration path is clear:

1. Clone or install the ARC-AGI-3 game engine in a fresh venv at `/ganuda/services/arc_agi_3_dogfood/`
2. Wire the Jr executor as the agent interface — the Jr executor already has Experience Bank retrieval against thermal memory, so we get cross-session continuity for free
3. Set up per-game logging: action count, success/failure, total wall-clock time, and which Experience Bank entries were retrieved during play (for post-hoc analysis)
4. Confirm that the 25 public games are correctly loaded and that a null/random-action agent can play them through (smoke test)

**Deliverable for Task 2**: the harness running on redfin with all 25 games playable via a Python call like `play_game(game_id, agent=jr_executor)` and returning a structured result dict.

### Task 3 — Baseline run

Run the Jr executor with Experience Bank retrieval enabled against all 25 public games. For each game:

- Attempt the game 3 times (variance control)
- Record action count per attempt
- Record success/failure per attempt
- Record which Experience Bank entries were retrieved (if any) and whether retrieval helped

**Deliverable for Task 3**: a results table in `/ganuda/docs/blog/DRAFT-ARC-AGI-3-DOGFOOD-RESULTS-APR11-2026.md` with:
- Per-game score (actions taken / human baseline)
- Success rate across 3 attempts
- Aggregate efficiency score (for comparison against Chollet's <1% frontier baseline)
- Honest notes on failure modes observed (matching or differing from Chollet's two failure modes: forward simulation and hypothesis anchoring)

### Task 4 — Thermalization

Post a structured SITREP to thermal memory at 90°C, source_triad `it_triad_jr`, tags `arc_agi_3, dogfood, skillrl_validation, experience_bank, apr2026`. Include:
- Pass/fail for Tasks 1–3
- Aggregate efficiency score
- Any blockers or surprises
- Partner-facing one-paragraph summary that TPM can lift directly into a Partner SITREP

## Acceptance Criteria

- Integration path identified and documented
- 25 games running against Jr executor in the harness
- Baseline results table written to `DRAFT-ARC-AGI-3-DOGFOOD-RESULTS-APR11-2026.md`
- Thermal SITREP posted at 90°C
- No perturbation of fiber Gate 1 observation window (this task is pure software, outside the fabric, safe to run during Gate 1)
- No TPM code-writing involved — this is a Jr task end to end

## Guardrails

1. **Do NOT submit anything to the Kaggle competition.** This is an internal dogfood run only. Kaggle main track is Council-ratified NO for 2026.
2. **Do NOT publish the results externally without Partner's editorial review.** The draft results file goes to `DRAFT-ARC-AGI-3-DOGFOOD-RESULTS-APR11-2026.md` for Partner to review and then decide when/how to publish. Eagle's strategic framing is "time to first ARC-AGI-3 leaderboard update" but Partner owns the timing.
3. **Do NOT accept Terms of Service, Kaggle account creation, or any other legal-binding action on Partner's behalf.** If integration requires these, STOP and thermalize a blocker.
4. **Do NOT consume cycles that should go to fiber Gate 1, the Hulsey Monday prep, or the Carlini sandbox audit (B1 per CDR-FIBER-BRINGUP-APR11-2026).** Those have higher immediate priority. ARC-AGI-3 dogfood is validation work, not urgent defense work.
5. **Honor the Stoneclad language discipline memory** (`feedback_stoneclad_language_discipline.md`) in any draft text produced — never write "synthetic being," "emergent consciousness," or "digital life."

## What this task is NOT

- Not a production deployment
- Not a Kaggle entry
- Not a public blog post (draft only, Partner publishes)
- Not a patent filing trigger
- Not a replacement for SkillRL Phase 0 KG Formalization work (which continues on its own track)

## Related Council work

- `COUNCIL-READING-ARC-AGI-3-APR11-2026.md` — Eagle + Owl takes + TPM synthesis
- `COUNCIL-READING-CARLINI-APR11-2026.md` — security posture context
- `COUNCIL-READING-BRIDLE-APR11-2026.md` — language discipline context
- `HULSEY-CONSULT-PREP-APR13-2026.md` — patent claim relevance (Patent #3 + #4 broadening)
- `project_skillrl_epic.md` — the architecture this task validates
