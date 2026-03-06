# ULTRATHINK: SRE Protocol Interface — DC-11 Foundation

**Date**: March 6, 2026
**Lead**: Turtle (7GEN), TPM (decomposition)
**Longhouse**: c12fb14125cdf9f0 (DC-11), aad7f6bc1a91152b (Turtle roadmap)
**Thermal**: #119423, #119438

---

## The Question

DC-11 says the same interface — SENSE, REACT, EVALUATE — repeats at every scale.
The First Law says physics forces this, not design.

What does that interface actually look like in code?

---

## What Already Exists

### Graduated Harness (lib/harness/)
The harness ALREADY implements a partial SRE:
- **SENSE**: `HarnessRequest.validate()` + `EscalationEngine._detect_stakes()` — input detection, keyword scanning, confidence assessment from prior tiers
- **REACT**: `TierHandler.handle()` through the escalation chain — Tier 1 reflex, Tier 2 deliberation, Tier 3 council
- **EVALUATE**: `TierResult.confidence` scoring — but this is INLINE evaluation, not retrospective valence

**GAP**: No retrospective feedback loop. The harness fires and scores but never looks back to ask "was that answer actually good?" There is no mechanism where Tier 1 reflex answers are later reviewed by the brain to calibrate future confidence thresholds. The reflex fires, the confidence scores, and the system forgets.

### White Duplo (lib/duplo/white_duplo.py)
White Duplo implements a FULL SRE cycle:
- **SENSE**: `scan_substrate()` — regex pattern matching against known threat signatures
- **REACT**: Block/allow decision + severity classification
- **EVALUATE**: `scan_and_register()` — when a NEW threat is found, it registers the pattern in the immune registry. The system LEARNS. Post-scan (`_post_scan` in composer.py) catches threats that were missed pre-execution.

**This is the most complete SRE implementation we have.** White Duplo already does retrospective valence: "I missed this threat pre-execution, but caught it post-execution, now I register the pattern so I don't miss it next time."

### Duplo Composer (lib/duplo/composer.py)
The enzyme pattern is SRE-shaped:
- **SENSE**: `_check_immune_registry()` — pre-execution immune check
- **REACT**: LLM call through backend (the enzymatic catalysis)
- **EVALUATE**: `_post_scan()` — post-execution immune check

But evaluation is ONLY immune-focused. No quality valence ("was this a good enzyme output?").

### Thermal Memory System
The thermal decay system IS a valence mechanism at federation scale:
- Memories that get reheated (referenced again) survive
- Memories that cool (unreferenced) decay and eventually get purged
- Temperature IS retrospective valence: "was this memory useful?"

### Drift Detection (lib/drift_detection.py)
Drift detection is EVALUATE without explicit SENSE or REACT:
- It compares current behavior against baseline
- It scores divergence
- But it doesn't trigger reactive changes automatically

---

## The SRE Protocol Interface

### Design Principles

1. **The interface is a Protocol (Python), not an ABC.** Structural typing. You don't inherit from SRE — you implement it, and duck typing does the rest. This matches DC-6 (Gradient Principle): scaffolding, not walls.

2. **EVALUATE is retrospective, not inline.** The confidence score from a tier handler is REACT output. EVALUATE happens later — possibly much later — when the system reviews whether the response was actually good. This is the proto-valence gap.

3. **The feedback loop is the key feature.** EVALUATE feeds back into SENSE calibration. Coyote's misalignment concern: if this loop breaks, the organism loses touch with reality (Sam Walton's penny).

4. **Scale determines latency of each phase.** At service level: sense=ms, react=ms-seconds, evaluate=minutes-hours. At federation level: sense=seconds, react=seconds-minutes, evaluate=hours-days. The First Law: physics determines these timescales, not configuration.

### The Protocol

```
from typing import Protocol, TypeVar, Generic, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum

class Urgency(str, Enum):
    REFLEX = "reflex"       # Must react immediately, evaluate later
    DELIBERATE = "deliberate"  # Can take time to react, evaluate soon
    STRATEGIC = "strategic"    # React over days/weeks, evaluate over months

@dataclass
class Signal:
    """What was sensed. Scale-agnostic."""
    source: str           # Where the signal came from
    content: Any          # The raw signal data
    urgency: Urgency      # How fast must we react?
    timestamp: float      # When it was sensed
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Reaction:
    """What was done in response. Scale-agnostic."""
    action: str           # What action was taken
    result: Any           # The output/product
    confidence: float     # How confident was the reactor (0.0-1.0)
    latency_ms: float     # How long did the reaction take
    reactor: str          # Which component reacted (tier, enzyme, node)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Valence:
    """Retrospective evaluation. Was the reaction good?"""
    reaction_id: str      # Which reaction is being evaluated
    score: float          # -1.0 (harmful) to 1.0 (beneficial)
    evaluator: str        # Who evaluated (could be different from reactor)
    latency_ms: float     # How long after reaction did evaluation happen
    feedback: Dict[str, Any] = field(default_factory=dict)
    # Feedback that should adjust future SENSE or REACT
    calibration: Optional[Dict[str, Any]] = None


class SREComponent(Protocol):
    """The conserved interface. Every component at service level and above
    implements this. The implementation varies. The interface is fixed.

    DC-7 Noyawisgi: this interface survives all speciations.
    """

    def sense(self, raw_input: Any) -> Signal:
        """Detect and classify incoming signal.

        At node level: parse request, detect stakes, classify urgency.
        At service level: scan substrate, check immune registry.
        At federation level: aggregate node signals, detect patterns.
        """
        ...

    def react(self, signal: Signal) -> Reaction:
        """Respond to the signal. May be reflex or deliberate.

        At node level: route to tier, execute LLM call.
        At service level: run enzyme, block threat, transform data.
        At federation level: coordinate nodes, escalate to council.
        """
        ...

    def evaluate(self, reaction: Reaction) -> Valence:
        """Retrospective assessment. Was the reaction good?

        This MAY happen much later than the reaction.
        This MUST feed back into future sense/react calibration.

        At node level: was the LLM response actually helpful?
        At service level: did the enzyme produce correct output?
        At federation level: did the council decision serve 7 generations?
        """
        ...

    def calibrate(self, valence: Valence) -> None:
        """Apply valence feedback to adjust future behavior.

        This is the feedback loop. Coyote's concern: if this breaks,
        the organism loses metabolic fidelity (Sam Walton's penny).

        At node level: adjust confidence thresholds, retrain heuristics.
        At service level: update immune registry, adjust enzyme params.
        At federation level: update design constraints, adjust routing.
        """
        ...
```

### The Four-Phase Loop (SRE+C)

Not three phases — FOUR. The Council's concerns revealed the fourth:

```
SENSE → REACT → EVALUATE → CALIBRATE → SENSE → ...
         ↑                       |
         └───────────────────────┘
         (feedback loop - Coyote's concern)
```

1. **SENSE**: Detect signal, classify urgency
2. **REACT**: Respond (reflex or deliberate, based on urgency)
3. **EVALUATE**: Retrospective valence (was it good? — may happen much later)
4. **CALIBRATE**: Apply valence feedback to adjust future sensing and reacting

The loop is the organism's metabolism. If the loop runs, the organism adapts.
If the loop breaks (Coyote's misalignment), the organism loses touch with reality.

---

## Mapping Existing Code to SRE+C

| Component | SENSE | REACT | EVALUATE | CALIBRATE | Gap |
|-----------|-------|-------|----------|-----------|-----|
| Graduated Harness | validate + stakes detection | tier handler chain | confidence score (inline only) | NONE | No retrospective valence, no calibration |
| White Duplo | scan_substrate (regex) | block/allow | scan_and_register (post-scan) | register_pattern (immune learning) | COMPLETE — best SRE implementation |
| Duplo Composer | immune pre-check | LLM enzyme call | immune post-scan | NONE for quality | Quality valence missing |
| Thermal Memory | — | — | temperature = valence | decay/reheat = calibration | No explicit sense/react |
| Drift Detection | — | — | divergence scoring | NONE | No trigger mechanism |
| TPM Autonomic | system monitoring | — | health scoring | NONE | No reactive capability |

### Key Finding

**White Duplo is the reference implementation.** It already does the full SRE+C loop:
sense (scan) → react (block/allow) → evaluate (post-scan catch) → calibrate (register new pattern).

The rest of the codebase has pieces but not the full loop. The biggest gap across the board is **retrospective EVALUATE and CALIBRATE**.

---

## Implementation Plan — Phase 1

### Step 1: Define the Protocol (lib/harness/sre_protocol.py)
Create the SREComponent Protocol with Signal, Reaction, Valence, and calibrate().
Zero dependencies. Importable on any node.

### Step 2: Retrofit Graduated Harness
Add retrospective evaluation to the harness:
- After a response is delivered, store the reaction in a pending_evaluations queue
- A background evaluator (could be Tier 2 or Tier 3 reviewing Tier 1 answers) periodically scores past reactions
- Valence scores feed back into confidence threshold calibration

This is the "brain reviewing what the spinal cord did" — exactly DC-10.

### Step 3: Wire Valence into Thermal Memory
Every SRE evaluation should create a thermal memory:
- Good reactions = high temperature memories (pattern to repeat)
- Bad reactions = hot flagged memories (pattern to avoid)
- The thermal decay system IS the long-term calibration mechanism

### Step 4: Misalignment Detection (Coyote Concern -> Feature)
Monitor the EVALUATE → CALIBRATE loop health:
- Track: ratio of reactions that received evaluation vs those that didn't
- Track: calibration drift (are thresholds actually changing?)
- Alert: if evaluation backlog exceeds threshold, the organism is running blind
- Circuit breaker: if calibration diverges too far too fast, pause and escalate

### Step 5: Cross-Scale Protocol Contracts (Spider Concern -> Feature)
Define explicit boundaries:
- **Function → Service**: Signal aggregation. Many function-level signals combine into one service-level signal
- **Service → Node**: Service health signals feed node-level sensing
- **Node → Federation**: Node health/load/thermal signals feed federation routing decisions
- Each boundary has a defined contract for what signals cross and what stays local

---

## Hardware Topology Mapping

| SRE Phase | Hot Path (GPU) | Cool Path (Mac) |
|-----------|---------------|-----------------|
| SENSE | White Duplo scan (sub-ms) | Deep semantic analysis |
| REACT | Tier 1 reflex (single LLM call) | Tier 2/3 deliberation (multi-specialist) |
| EVALUATE | Inline confidence score | Retrospective valence review |
| CALIBRATE | Threshold adjustment | Design constraint evolution |

The hot path runs the full loop fast with shallow evaluation.
The cool path runs the full loop slow with deep evaluation.
Both implement the same interface. DC-11 in silicon.

---

## Conserved Sequences (DC-7)

These elements of the SRE+C protocol MUST NOT change:

1. The four-phase loop order: SENSE → REACT → EVALUATE → CALIBRATE
2. Valence is RETROSPECTIVE — never inline with reaction
3. Calibrate feeds back into sense — the loop must close
4. Urgency classification determines reaction speed, not reaction quality
5. The Protocol is structural typing — no inheritance hierarchy

---

## Jr Instruction Decomposition

From this ultrathink, the following Jr instructions should be written:

1. **JR-SRE-PROTOCOL-DATACLASSES**: Create `/ganuda/lib/harness/sre_protocol.py` with Signal, Reaction, Valence dataclasses and SREComponent Protocol
2. **JR-HARNESS-VALENCE-QUEUE**: Add pending_evaluations queue to EscalationEngine, background evaluator, thermal integration
3. **JR-MISALIGNMENT-MONITOR**: Health monitor for the EVALUATE→CALIBRATE loop, alert on backlog, circuit breaker on divergence
4. **JR-WHITE-DUPLO-SRE-ADAPTER**: Wrap White Duplo's existing scan/block/register in the formal SRE Protocol interface (reference implementation)
5. **JR-CROSS-SCALE-SIGNAL-CONTRACTS**: Define the Signal aggregation rules at each boundary (function→service, service→node, node→federation)

---

## Open Questions for Chief

1. Should CALIBRATE be autonomous (the system adjusts its own thresholds) or supervised (calibration proposals go to Council for approval above a certain magnitude)?
   - Recommendation: Autonomous below threshold, Council approval above. The reflex calibrates itself. The cortex calibrates the strategy.

2. How long should the EVALUATE delay be? Tier 1 reflex answers could be evaluated minutes later by Tier 2. But Tier 3 Council decisions might need weeks of observation before valence is meaningful.
   - Recommendation: Scale-dependent. Define per-tier evaluation windows in config.

3. Should valence scores be visible to end users? ("The system is 73% confident this was a good answer based on retrospective evaluation")
   - Recommendation: Internal only for now. Exposed via SAG ops console for the team.

---

*"The body acts. Consciousness narrates. The reflex fires. At every scale."*

*The interface is the conserved sequence. The implementation speciates. The loop must close.*
