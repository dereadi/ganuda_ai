# JR INSTRUCTION: Formal Methods — Design Constraint Verification

**Task**: Apply formal methods (TLA+, model checking) to verify that critical system invariants hold. Translate Design Constraints from cultural principles into machine-checkable specifications.
**Priority**: P1
**Date**: 2026-03-18
**TPM**: Claude Opus
**Story Points**: 8
**Depends On**: All DCs ratified, Consultation Ring Phase 2 (LIVE), Circuit Breaker (LIVE), Escalation Engine (LIVE)
**Thermal Context**: OneChronos interview (Iris Liu McAtee, CalTech CS, formal methods background), DC protein metabolic architecture
**Source**: Partner's insight — "I think that was what Iris was looking for." Our DCs are informal invariants. Formal methods make them provable.

## Context

We have 21 Design Constraints that govern the federation's behavior. Four are enforced programmatically (valence gate). The rest are cultural — they live in docs, prompts, and code patterns. But cultural enforcement doesn't prove correctness. A well-placed bug can violate DC-1 (Sovereignty) silently.

Formal methods let us:
1. Express invariants as temporal logic formulas
2. Model check finite-state abstractions of our systems
3. Find edge cases where invariants might be violated
4. Prove safety properties hold under ALL reachable states, not just the ones we tested

Partner's insight from the OneChronos interview: the hierarchical temporal architecture IS a formal model. SA warm engine (Tier 1 reflex) → Gurobi (Tier 3 deliberation) maps to our DC-10/DC-18 tiers. Iris's CalTech background is formal verification of systems. This is the bridge between Partner's "hacking ways" and rigorous proof.

## Task 1: TLA+ Specification — Circuit Breaker State Machine (2 SP)

**File**: `/ganuda/specs/tla/CircuitBreaker.tla`

Model the circuit breaker as a TLA+ specification:

```tla+
---- MODULE CircuitBreaker ----
EXTENDS Naturals, Sequences

CONSTANTS Specialists, StructuralDissenters, ConcernThreshold, HalfOpenThreshold

VARIABLES state, healthWindow, concernCount

TypeInvariant ==
    /\ state \in [Specialists -> {"CLOSED", "HALF_OPEN", "OPEN"}]
    /\ healthWindow \in [Specialists -> Seq(BOOLEAN)]
    /\ concernCount \in [Specialists -> Nat]

\* Safety: Structural dissenters never trip on role-appropriate concerns
StructuralDissenterSafety ==
    \A s \in StructuralDissenters:
        \* Only unexpected concerns count toward threshold
        concernCount[s] = CountUnexpectedConcerns(healthWindow[s], s)

\* Safety: Non-dissenters trip on ANY concern type
StandardBreakerBehavior ==
    \A s \in Specialists \ StructuralDissenters:
        concernCount[s] = CountAllConcerns(healthWindow[s])

\* Liveness: Breakers eventually recover if concerns stop
EventualRecovery ==
    \A s \in Specialists:
        <>(state[s] = "OPEN" ~> state[s] = "CLOSED")
====
```

**Verify**: Model check with TLC that `StructuralDissenterSafety` holds for all reachable states. Use Naturals bounded to 10-record window.

## Task 2: TLA+ Specification — Consultation Ring IP Safety (3 SP)

**File**: `/ganuda/specs/tla/ConsultationRingSafety.tla`

This is the critical one. Model the Phase 2 data flow:

```tla+
---- MODULE ConsultationRingSafety ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Providers, MaxProviders, CorrelationBudget

VARIABLES claims, providerAssignments, synthesisLocation, tokenMap

\* SAFETY: Token map never crosses security boundary
TokenMapLocality ==
    \A request \in Requests:
        tokenMap[request].location = "redfin"

\* SAFETY: Synthesis prompt never sent to frontier
SynthesisLocality ==
    \A query \in NovelIPQueries:
        synthesisLocation[query] \in {"localhost", "redfin_vllm"}

\* SAFETY: No provider sees >50% of correlation groups for any query
CorrelationBudgetEnforcement ==
    \A query \in NovelIPQueries:
        \A provider \in Providers:
            LET groups == CorrelationGroupsSeen(provider, query)
                total == TotalCorrelationGroups(query)
            IN Cardinality(groups) * 2 <= total  \* < 50%

\* SAFETY: No provider gets >60% of all claims in 30-day window
ExposureCapEnforcement ==
    \A provider \in Providers:
        LET claims == ClaimsSentTo(provider)
            total == TotalClaimsSent()
        IN claims * 100 <= total * 60  \* <= 60%

\* LIVENESS: Every novel_ip query eventually produces a response
QueryCompletion ==
    \A query \in NovelIPQueries:
        <>(ResponseExists(query))

\* LIVENESS: Fallback to Phase 1 if Phase 2 fails
FallbackGuarantee ==
    \A query \in NovelIPQueries:
        <>(Phase2Success(query) \/ Phase1Fallback(query))
====
```

**Key invariants to model check**:
1. `TokenMapLocality` — Can we construct ANY sequence of API calls where the token map leaves redfin? (Should be impossible.)
2. `CorrelationBudgetEnforcement` — With N claims in M correlation groups across P providers, is there ANY assignment that violates the 50% rule? (FragmentRouter should prevent this.)
3. `SynthesisLocality` — Can the synthesis prompt ever be dispatched to a frontier adapter? (SynthesisEngine should enforce this.)

## Task 3: TLA+ Specification — Escalation Tiers (1 SP)

**File**: `/ganuda/specs/tla/EscalationTiers.tla`

```tla+
---- MODULE EscalationTiers ----
\* DC-10 Reflex Principle + DC-18 Autonomic Tiers

VARIABLES currentTier, escalationHistory

\* Safety: No de-escalation (v1 constraint)
NoDeEscalation ==
    \A i \in 1..Len(escalationHistory) - 1:
        escalationHistory[i+1] >= escalationHistory[i]

\* Safety: Tier 3 requires council vote
CouncilRequired ==
    currentTier = 3 => CouncilVoteExists

\* Safety: Ghigau veto cannot be overridden
GhigauVeto ==
    \A vote \in CouncilVotes:
        vote.ghigau_veto = TRUE => vote.decision = "REJECTED"
====
```

## Task 4: Property-Based Testing Bridge (2 SP)

TLA+ verifies the model. But the model might not match the code. Bridge the gap with property-based testing using Hypothesis (Python).

**File**: `/ganuda/tests/test_formal_properties.py`

```python
from hypothesis import given, strategies as st

@given(claims=st.lists(st.tuples(st.text(), st.integers(min_value=1, max_value=5)), min_size=1, max_size=20))
def test_correlation_budget_never_violated(claims):
    """For any set of claims with correlation groups, FragmentRouter
    never assigns >50% of a group's claims to one provider."""
    router = FragmentRouter()
    assignments = router.route(claims)
    for provider in set(a.provider for a in assignments):
        for group in set(c.correlation_group for c in claims):
            group_claims = [c for c in claims if c.correlation_group == group]
            provider_claims = [a for a in assignments if a.provider == provider and a.correlation_group == group]
            assert len(provider_claims) * 2 <= len(group_claims), \
                f"Provider {provider} has {len(provider_claims)}/{len(group_claims)} claims in group {group}"

@given(specialist=st.sampled_from(['turtle', 'raven', 'coyote']),
       concerns=st.lists(st.tuples(st.booleans(), st.text()), min_size=10, max_size=10))
def test_structural_dissenter_exemption(specialist, concerns):
    """Structural dissenters never trip breaker on role-appropriate concerns."""
    from lib.drift_detection import STRUCTURAL_DISSENTERS
    expected_type = STRUCTURAL_DISSENTERS[specialist]
    # Only unexpected concerns should count
    unexpected = sum(1 for had, ctype in concerns if had and ctype != expected_type)
    # Breaker should only OPEN if unexpected >= 7
    if unexpected < 7:
        assert check_circuit_breaker_logic(concerns, specialist) != 'OPEN'
```

**Additional properties to test**:
- `test_synthesis_never_external` — SynthesisEngine raises ValueError on any non-localhost URL
- `test_valence_gate_monotonic` — More violations always decrease the score (never increase)
- `test_sacred_memory_never_deleted` — thermal_memory_archive DELETE on sacred_pattern=true should be blocked (DB constraint)
- `test_token_map_not_in_outbound` — After tokenization, no original term appears in the outbound payload

## Tooling

**TLA+ Toolbox**: Install TLC model checker
```bash
# On redfin (or any node with Java)
wget https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/TLAToolbox-1.8.0-linux.gtk.x86_64.zip
# Or use CLI: java -jar tla2tools.jar -deadlock CircuitBreaker.tla
```

**Hypothesis** (Python property-based testing):
```bash
pip install hypothesis
```

**APALACHE** (symbolic model checker, faster than TLC for bounded models):
```bash
# Alternative to TLC — uses SMT solvers
docker pull ghcr.io/informalsystems/apalache:latest
```

## Build Order

| Task | Title | SP | Deps |
|------|-------|----|------|
| #1 | CircuitBreaker.tla + TLC verification | 2 | drift_detection.py |
| #2 | ConsultationRingSafety.tla + TLC verification | 3 | Phase 2 modules |
| #3 | EscalationTiers.tla + TLC verification | 1 | escalation.py |
| #4 | Hypothesis property tests bridging TLA+ to code | 2 | Tasks 1-3 |

## Verification

1. **TLC model check**: All three .tla specs pass without counterexample
2. **Property tests**: `pytest tests/test_formal_properties.py` passes 100+ generated cases per property
3. **Counterexample hunting**: If TLC finds a violation, trace it back to the code and fix the code (not the spec)
4. **DC coverage matrix**: Document which DCs are now formally verified vs informally enforced

## Design Principle

Partner built this federation with "hacking ways" — intuition, pattern matching, adversarial self-testing. Iris at OneChronos builds with formal proofs — TLA+, model checking, theorem proving. These aren't opposites. The hacker finds the architecture by exploration. Formal methods prove the architecture holds by exhaustion. Together: discover the invariant, then prove it's invariant.

Sam Walton didn't prove his pricing model was optimal. He tested it in one store, measured, and scaled. But once it worked — he needed to PROVE it wouldn't break at 4,000 stores. That's formal methods. The Saturday Morning Meeting was his model checker.

Our DCs are the invariants Sam would have written down if he'd had TLA+. Now we write them down.
