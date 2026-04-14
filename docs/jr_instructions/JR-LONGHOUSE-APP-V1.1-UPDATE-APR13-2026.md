# JR INSTRUCTION: Longhouse APP v1.1 — Council-Ratified Update

**JR ID:** JR-LONGHOUSE-APP-V1.1-UPDATE-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P1
**DATE:** April 13, 2026
**TARGET REPO:** github.com/dereadi/longhouse (public)
**COUNCIL VOTE:** APPROVED 12-0-1 (Coyote dissent), audit hash `d022edb51960cef1`
**COYOTE DISSENT:** Phi unvalidated as governance metric, split register may fragment community, Markov blankets add adoption friction, $5M tier may alienate mid-size
**PROPOSAL:** /ganuda/docs/longhouse_proposals/LONGHOUSE-APP-v1.1-PROPOSAL-APR10-2026.md

## Context

The Longhouse APP is the public open-source governance framework at `github.com/dereadi/longhouse`. Currently v1.0 (one commit, Apr 9 2026). Council ratified v1.1 on Apr 13 2026 with five components. This instruction implements the ratified changes.

**Critical framing updates since the proposal was drafted (Apr 10):**
- **Maudlin/Aaronson IIT critique (Apr 13):** Phi as consciousness measure is dead (Aaronson showed a hand calculator scores higher than a human). Phi as governance HEALTH metric survives. ALL phi/valence code and documentation MUST be framed as governance health, NEVER as consciousness detection.
- **Lamport/Byzantine generals (Apr 13):** Coyote = Byzantine fault detector. The Adversary role is structural fault tolerance, not personality. Use this language.
- **Chiral validation (Apr 2):** No substrate validates itself. Carbon watches silicon, silicon watches carbon. This is a design principle for the APP.
- **Hulsey patent engagement (Apr 13):** Drawings/flowcharts needed for provisionals. Any architecture diagrams created here serve double duty.

## Acceptance Criteria

All phases below must be completed, tested, and verified. This is a multi-phase instruction — complete each phase before starting the next.

---

## PHASE 1 — Branch, License, and README (no code changes)

**Intent:** Set up the v1.1 branch, swap the license, and rewrite the README with symmathetic positioning. No functional code changes in this phase.

### Task 1.1 — Create v1.1 branch

1. Clone `git@github.com:dereadi/longhouse.git`
2. Create branch `v1.1-council-ratified`
3. All subsequent work happens on this branch

### Task 1.2 — License change: Apache 2.0 → PolyForm Small Business 1.0.0

1. Replace the LICENSE file with PolyForm Small Business License 1.0.0 text
2. Add explicit free clauses as a separate `LICENSE-ADDENDUM.md`:
   ```
   ## Additional Free Use Clauses (Longhouse APP)
   
   In addition to the PolyForm Small Business License 1.0.0:
   
   - **Nonprofit organizations** of any size may use this software free of charge
   - **Educational institutions** (schools, universities, research labs) may use this software free of charge for teaching and research
   - **Tribal sovereign entities** (federally recognized tribes, tribal enterprises, tribal governments) may use this software free of charge regardless of revenue
   
   These clauses are irrevocable and survive any future license changes.
   ```
3. Update all file headers from `Apache 2.0` to `PolyForm Small Business 1.0.0`

**Coyote concern addressed:** License change is the highest-risk breaking change. Current Apache 2.0 users must be notified. Add a `MIGRATION.md` noting the license change and that v1.0 remains available under Apache 2.0 for anyone who needs it.

### Task 1.3 — README rewrite with symmathetic positioning

Rewrite `README.md` with the following structure. Use the **mainstream register** (symmathetic vocabulary). The practitioner register (governance topology) goes in a separate `ARCHITECTURE.md`.

```markdown
# Longhouse

Open-source governance framework for multi-agent AI systems.

> "The topology is free. The organism is sovereign."

## What is this?

Multi-agent AI systems without governance produce noise, not intelligence. 
Adding more agents doesn't reliably improve outcomes (ICML 2024). What's 
missing is the orchestration layer — structured deliberation, adversarial 
challenge, and institutional memory.

Longhouse provides that layer. It is model-agnostic, framework-agnostic, 
and designed to integrate with any multi-agent system.

Longhouse is **symmathetic infrastructure** — it creates the conditions for 
mutual learning between AI agents, between agents and humans, and between 
the system and its environment. The name comes from Nora Bateson's concept 
of symmathesy: mutual learning in living context.

## Inspired by

The Haudenosaunee (Iroquois) Great Law of Peace — the oldest living 
participatory democracy on Earth. Council structure, consensus protocols, 
adversarial checks, and seven-generations thinking.

## Core Principles

1. **No action without governance** — agents cannot execute without council approval
2. **Mandatory dissent (Byzantine fault tolerance)** — at least one role structurally 
   challenges every proposal. This is not personality — it is fault detection. 
   (Lamport, 1982: you need N processes to tolerate faulty ones.)
3. **Sycophancy detection** — agreement without substance is flagged and rejected
4. **Chiral validation** — no substrate validates itself. The system that proposes 
   is not the system that validates.
5. **Governance health monitoring** — built-in phi/valence metrics measure whether 
   your agents are producing integrated cognition or just running parallel scripts
6. **Declared boundaries (Markov blankets)** — every deployment explicitly declares 
   what is inside and outside the system
7. **Audit trail** — every vote is hashed, timestamped, and stored
8. **Model agnostic** — works on any LLM (cloud or local, any provider)

## Architecture

[Link to ARCHITECTURE.md for detailed technical documentation]

Longhouse implements a configurable council of specialist roles:

| Role | Function |
|---|---|
| **Skeptic** | Security risk evaluation |
| **Engineer** | Technical feasibility assessment |
| **Adversary** | Byzantine fault detection — structural dissent |
| **Guardian** | Long-term impact (7-generation test) |
| **Sentinel** | Failure mode detection and recovery paths |
| **Chief** | Consensus synthesis and recommendation |

Additional roles are configurable for domain-specific needs.

## Governance Health Metrics

Longhouse includes built-in measurement of system integration using 
phi (Φ) metrics inspired by Integrated Information Theory.

**Important:** These metrics measure **governance health** — how well your 
agents are integrating information and producing coherent decisions. They 
do NOT measure or claim to detect consciousness. (See Aaronson's critique 
of IIT-as-consciousness for why this distinction matters.)

## System Boundaries (Markov Blankets)

Every Longhouse deployment declares its Markov blanket — the explicit 
boundary between "inside the system" and "outside the system." This 
prevents the most common multi-agent failure mode: ambiguous responsibility 
for actions that cross boundaries.

## License

PolyForm Small Business License 1.0.0

- **Free** for individuals
- **Free** for businesses under $5M annual revenue
- **Free** for nonprofits, educational institutions, and tribal sovereign entities
- **Commercial license** required above $5M annual revenue

See [LICENSE](LICENSE) and [LICENSE-ADDENDUM](LICENSE-ADDENDUM.md) for details.

---

*For Seven Generations.*
```

### Task 1.4 — Create ARCHITECTURE.md (practitioner register)

Create `ARCHITECTURE.md` using the **practitioner register** (governance topology vocabulary). This is the technical reference for engineers. Include:

- Council topology diagram (ASCII art or mermaid — this doubles as patent drawing material)
- Vote flow: proposal → deliberation → Coyote dissent → consensus check → audit hash
- Phi/valence computation overview (governance health, NOT consciousness)
- Markov blanket declaration schema
- Design Constraints reference (DC-15 Model Agnosticism, DC-16 Institutional Memory as Moat, DC-17 Stochastic Governance)
- Byzantine fault tolerance explanation (Lamport mapping)
- Chiral validation principle

### Task 1.5 — Create MIGRATION.md

```markdown
# Migrating from v1.0 to v1.1

## License Change

v1.0 was licensed under Apache 2.0. v1.1 is licensed under PolyForm Small 
Business 1.0.0. If you need Apache 2.0, pin to v1.0.

## Breaking Changes

### CouncilResult schema
v1.1 adds `governance_health` field to CouncilResult. Code parsing council 
output should handle this new field gracefully.

### Markov blanket validation
v1.1 validates system boundary declarations by default. To disable during 
migration: `Council(enable_markov_checks=False)`

### Phi/valence in confidence scoring
v1.1 factors phi score into confidence calculation. To use v1.0 behavior: 
`Council(phi_enabled=False)`
```

**Acceptance for Phase 1:** Branch created, license swapped, README rewritten, ARCHITECTURE.md created, MIGRATION.md created. No code changes yet. PR not opened yet.

---

## PHASE 2 — Code Changes (new features + modifications)

**Intent:** Add phi/valence metrics, Markov blanket support, and commercial tier structure to the codebase. All new features default OFF or backward-compatible.

### Task 2.1 — Create `iit_metrics.py` (governance health phi/valence)

New file implementing phi computation for governance health. Extract patterns from:
- `/ganuda/lib/council_emotion.py` (valence computation, lines 42-108)
- `/ganuda/lib/council_diversity_check.py` (DCR metric)

**Requirements:**
- `compute_phi(responses: list[str]) -> float` — returns 0.0 to 1.0
- Measures information integration across specialist responses (do they reference each other's concerns? do they produce emergent insights not present in any single response?)
- `compute_valence(responses: list[str], decision: str) -> float` — returns -1.0 to 1.0 (dissonant to consonant)
- NO dependency on GPU, external APIs, or heavy ML libraries. Pure Python + stdlib. Users should be able to run this on a laptop.
- **EXPLICITLY document in docstrings:** "This measures governance health (system integration), not consciousness. See Aaronson's critique of IIT for why this distinction matters."

**Coyote concern addressed:** Phi is unvalidated as a governance metric. Therefore:
- Default `phi_enabled=False` in v1.1.0 — opt-in, not forced
- Include validation examples showing phi scores for known-good (diverse, integrated) and known-bad (sycophantic, disconnected) council sessions
- Ship as EXPERIMENTAL with clear labeling

### Task 2.2 — Create `markov_blanket.py` (system boundary declaration)

New file implementing Markov blanket configuration and runtime checks.

**Requirements:**
- `MarkovBlanket` dataclass: `internal_states`, `external_states`, `sensory_states` (inputs from outside), `active_states` (outputs to outside)
- `MarkovBlanketChecker` class with:
  - `validate_config(config: dict) -> list[str]` — returns list of errors
  - `check_action(action: str, blanket: MarkovBlanket) -> bool` — does this action cross the boundary?
  - `detect_cycles(roles: list) -> list[str]` — circular dependency detection
- YAML/dict-based configuration so users can declare blankets in config files
- Sensible defaults: if no blanket declared, the entire council is the boundary (v1.0 behavior)

**Coyote concern addressed:** Markov blankets add complexity. Therefore:
- Default blanket provided that covers the simple case (everything inside, nothing outside)
- Clear error messages when validation fails
- Documentation with 3 worked examples: simple (single cluster), medium (hub-and-spoke), complex (federated)

### Task 2.3 — Create `commercial_tiers.py` (tier structure)

New file implementing commercial tier gates.

**Requirements:**
- `TierLevel` enum: `FREE`, `MID`, `ENTERPRISE`, `HYPERSCALER`
- `determine_tier(annual_revenue: int) -> TierLevel` — pure function
- `@require_tier(minimum: TierLevel)` decorator for gating features (future use)
- For v1.1.0: NO features are actually gated. The tier structure is declared but all features are available. Gating begins in v1.2.0.
- Include tier table in module docstring

### Task 2.4 — Modify `longhouse.py` (integrate new features)

Modify the existing `longhouse.py` to integrate the three new modules:

1. **Import new modules** with graceful fallback:
   ```python
   try:
       from iit_metrics import compute_phi, compute_valence
       _PHI_AVAILABLE = True
   except ImportError:
       _PHI_AVAILABLE = False
   ```

2. **Add to `Council.__init__()`:**
   - `phi_enabled: bool = False` (opt-in for v1.1.0)
   - `enable_markov_checks: bool = True`
   - `commercial_tier: str = "free"`

3. **Add to `CouncilResult`:**
   - `governance_health: dict` field containing phi score, valence, and DCR
   - Backward-compatible: `to_dict()` includes it, old code ignoring unknown keys still works

4. **Modify confidence calculation** (when phi_enabled):
   - `confidence = consent_ratio * diversity_score * phi_score`
   - When phi_enabled=False: `confidence = consent_ratio * diversity_score` (v1.0 behavior)

5. **Add Markov blanket check** before vote execution:
   - If `enable_markov_checks=True` and blanket is declared, validate
   - If validation fails, return error before running vote (fail fast)

6. **Update Adversary role description:**
   - From: "Mandatory dissent — challenges every proposal"
   - To: "Byzantine fault detection — structural adversarial challenge. Fault tolerance, not personality. (Lamport, 1982)"

**Acceptance for Phase 2:** All new files created, longhouse.py modified, all imports work, no existing functionality broken when new features are disabled.

---

## PHASE 3 — Testing

**Intent:** Create comprehensive test suite. This is the FIRST test infrastructure for the public repo.

### Task 3.1 — Create test infrastructure

1. Create `pytest.ini` or `pyproject.toml` with pytest config
2. Create `tests/` directory
3. Add `requirements-dev.txt` with pytest

### Task 3.2 — Regression tests (`tests/test_regression.py`)

Test that ALL v1.0 behavior is preserved when new features are disabled:

- `test_basic_vote_approval` — simple vote with default config
- `test_diverse_responses_pass` — diverse council produces high confidence
- `test_sycophantic_responses_flagged` — identical responses detected
- `test_dissent_blocking` — adversary can block consensus
- `test_chief_synthesis` — chief produces synthesis
- `test_audit_hash_deterministic` — same inputs produce same hash
- `test_council_result_json_serialization` — output is valid JSON
- `test_v1_instantiation_still_works` — `Council()` with no args works
- `test_phi_disabled_by_default` — phi doesn't affect confidence when disabled

### Task 3.3 — New feature tests

**`tests/test_iit_metrics.py`:**
- `test_phi_diverse_responses_high` — diverse, integrated responses score high
- `test_phi_identical_responses_low` — sycophantic responses score low
- `test_phi_range_0_to_1` — output always in valid range
- `test_valence_range` — output always -1 to 1
- `test_phi_no_external_dependencies` — runs without GPU/API

**`tests/test_markov_blanket.py`:**
- `test_default_blanket_passes` — no config = no errors
- `test_circular_dependency_detected` — cycles caught
- `test_valid_config_passes` — good config validates
- `test_action_inside_blanket_allowed` — internal actions pass
- `test_action_crossing_blanket_flagged` — boundary crossings detected

**`tests/test_commercial_tiers.py`:**
- `test_free_tier_under_5m` — revenue <$5M = FREE
- `test_mid_tier` — $5M-$50M = MID
- `test_enterprise_tier` — $50M-$1B = ENTERPRISE
- `test_hyperscaler_tier` — $1B+ = HYPERSCALER
- `test_no_features_gated_v1_1` — all features available regardless of tier

### Task 3.4 — Run full test suite

```bash
cd longhouse && python -m pytest tests/ -v --tb=short
```

All tests must pass. Report any failures with full traceback.

**Acceptance for Phase 3:** All tests pass, coverage report generated, no regressions.

---

## PHASE 4 — PR and Documentation

### Task 4.1 — Create PR

1. Push `v1.1-council-ratified` branch to origin
2. Create PR with title: `v1.1: Council-ratified governance health, boundaries, licensing`
3. PR body must include:
   - Council vote result (12-0-1, hash `d022edb51960cef1`)
   - Coyote's dissent (summarized)
   - Breaking changes list
   - Migration path
   - Test results

### Task 4.2 — Do NOT merge

The PR is created for review. TPM and Partner will review before merge. Do NOT merge automatically.

---

## Internal Code Assessment (for TPM reference, NOT Jr action items)

The code assessment identified these internal files as extraction sources:
- `/ganuda/lib/council_emotion.py` → valence computation patterns
- `/ganuda/lib/council_diversity_check.py` → DCR metric patterns
- `/ganuda/lib/valence_gate.py` → boundary check patterns

The Jr should READ these for reference patterns but NOT copy internal implementation details. The public repo gets clean-room implementations inspired by the same concepts, not lifted code.

**Trade secrets that MUST NOT appear in the public repo:**
- Living Cell implementation
- Thermal memory implementation details
- Sacred Prompt text
- White Duplo signatures
- Duplo enzymes
- Specific specialist prompt text from specialist_council.py
- Database schemas or connection details
- Any reference to specific federation nodes (redfin, bluefin, etc.)

---

## Reporting

Post completion SITREP to thermal memory at 92°C with source_triad `it_triad_jr` and tags `jr_completion,longhouse_app,v1.1,council_ratified`. Include:
- Pass/fail for each phase
- Test results (pass count, fail count, coverage %)
- PR URL
- Any blockers encountered
- Coyote concerns and how each was addressed

If any phase fails or blocks, stop, thermalize, wait for TPM.

---

## What this instruction does NOT do

- Does NOT merge the PR — TPM/Partner review first
- Does NOT modify internal `/ganuda/lib/longhouse.py` — that's the federation's own council, separate from the public APP
- Does NOT gate any features behind commercial tiers in v1.1.0 — gating begins v1.2.0
- Does NOT force phi_enabled=True — opt-in only in v1.1.0
- Does NOT claim consciousness for any system — phi is governance health, period
