# Jr Instruction: SRE+C Protocol Dataclasses — DC-11 Foundation

**Task**: Create the conserved SRE+C protocol interface for DC-11 Macro Polymorphism
**Priority**: 1 (Foundation — everything else depends on this)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false

## Context

DC-11 (Macro Polymorphism) says the same interface repeats at every scale: SENSE, REACT,
EVALUATE, CALIBRATE. This file defines the shared data types and Protocol interface that
every component at service level and above will implement.

DC-7 (Noyawisgi): This interface is a CONSERVED SEQUENCE. It survives all speciations.
The implementations change. The interface does not.

Design notes:
- dataclasses, not Pydantic (zero external deps, importable on any node)
- Protocol (structural typing), not ABC (no inheritance hierarchy)
- DC-6 (Gradient Principle): scaffolding, not walls

Codebase audit found that harness, White Duplo, TPM autonomic, and drift detection ALL
independently implemented SRE patterns without coordination. This Protocol unifies them.

## Steps

### Step 1: Create the protocol file

Create `/ganuda/lib/harness/sre_protocol.py`

```python
"""
SRE+C Protocol — The Conserved Interface (DC-11 Macro Polymorphism)

SENSE -> REACT -> EVALUATE -> CALIBRATE -> SENSE -> ...

This interface repeats at every scale of the organism:
  - Function level (White Duplo scan -> block -> learn -> adjust)
  - Service level (enzyme sense -> catalyze -> post-scan -> register)
  - Node level (health monitor -> alert -> score -> threshold adjust)
  - Federation level (tier routing -> LLM call -> valence -> calibrate)

DC-7 Noyawisgi: This interface is a conserved sequence.
The implementation speciates. The interface survives.

Longhouse c12fb14125cdf9f0 (DC-11, 0.857 confidence)
First Law: The same governance pattern repeats at every scale
because physics demands it -- not because we designed it.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Protocol
import time
import uuid


class Urgency(str, Enum):
    """How fast must we react? Physics determines this, not preference."""
    REFLEX = "reflex"           # <100ms. Spinal cord. Fire now, evaluate later.
    PAUSE = "pause"             # 100ms-1s. Coyote's gift. Check before escalating.
    DELIBERATE = "deliberate"   # 1s-120s. Basal ganglia / Tier 2. Pattern matching.
    STRATEGIC = "strategic"     # Minutes to days. Prefrontal cortex / Council.


@dataclass
class Signal:
    """What was sensed. Scale-agnostic input to the SRE loop.

    At node level: a request arrives, stakes are detected.
    At service level: a substrate is scanned, threat level assessed.
    At federation level: node health signals aggregate into system state.
    """
    source: str
    content: Any
    urgency: Urgency
    signal_id: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.signal_id:
            self.signal_id = uuid.uuid4().hex[:16]
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class Reaction:
    """What was done in response. The output of REACT.

    At node level: a tier handler produced an answer.
    At service level: an enzyme catalyzed a substrate.
    At federation level: the council voted on a question.
    """
    signal_id: str              # Which signal triggered this reaction
    action: str                 # What was done (human-readable)
    result: Any                 # The output / product
    confidence: float           # How confident is the reactor (0.0-1.0)
    latency_ms: float           # How long did the reaction take
    reactor: str                # Which component reacted
    reaction_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.reaction_id:
            self.reaction_id = uuid.uuid4().hex[:16]


@dataclass
class Valence:
    """Retrospective evaluation. Was the reaction good?

    This is NOT inline confidence scoring. This happens LATER --
    possibly much later -- when the system has enough information
    to assess whether the reaction was actually beneficial.

    At node level: was the LLM response helpful? (user feedback, requery rate)
    At service level: did the enzyme produce correct output? (downstream errors)
    At federation level: did the council decision serve 7 generations?
    """
    reaction_id: str            # Which reaction is being evaluated
    score: float                # -1.0 (harmful) to 1.0 (beneficial)
    evaluator: str              # Who evaluated (may differ from reactor)
    delay_ms: float             # How long after reaction did evaluation happen
    valence_id: str = ""
    feedback: Dict[str, Any] = field(default_factory=dict)
    calibration: Optional[Dict[str, Any]] = None  # Adjustments for future behavior

    def __post_init__(self):
        if not self.valence_id:
            self.valence_id = uuid.uuid4().hex[:16]


class SREComponent(Protocol):
    """The conserved interface. DC-11 Macro Polymorphism.

    Every component at service level and above implements this.
    The implementation varies by scale. The interface is fixed.

    Usage:
        class WhiteDuploSRE:
            def sense(self, raw_input): ...
            def react(self, signal): ...
            def evaluate(self, reaction): ...
            def calibrate(self, valence): ...

        # Structural typing -- no inheritance needed
        component: SREComponent = WhiteDuploSRE()
    """

    def sense(self, raw_input: Any) -> Signal:
        """Detect and classify incoming signal."""
        ...

    def react(self, signal: Signal) -> Reaction:
        """Respond to the signal. Speed determined by signal.urgency."""
        ...

    def evaluate(self, reaction: Reaction) -> Valence:
        """Retrospective: was the reaction good? May happen much later."""
        ...

    def calibrate(self, valence: Valence) -> None:
        """Apply valence feedback to adjust future sense/react behavior.

        This closes the loop. If this breaks, the organism loses
        metabolic fidelity (Sam Walton's penny).
        """
        ...
```

## Verification

```text
cd /ganuda && python3 -c "
from lib.harness.sre_protocol import Signal, Reaction, Valence, Urgency, SREComponent
# Test dataclass creation
s = Signal(source='test', content='hello', urgency=Urgency.REFLEX)
r = Reaction(signal_id=s.signal_id, action='respond', result='world', confidence=0.9, latency_ms=50, reactor='tier1')
v = Valence(reaction_id=r.reaction_id, score=0.8, evaluator='retrospective', delay_ms=60000)
print(f'Signal: {s.signal_id}, Urgency: {s.urgency}')
print(f'Reaction: {r.reaction_id}, Confidence: {r.confidence}')
print(f'Valence: {v.valence_id}, Score: {v.score}, Delay: {v.delay_ms}ms')
print('SREComponent Protocol importable: OK')
print('All dataclasses instantiate: OK')
"
```

Expected output: All three dataclasses instantiate cleanly. Protocol importable.

## Notes

- This file has ZERO external dependencies. Only stdlib.
- The Protocol uses structural typing (duck typing). Components don't inherit from SREComponent.
  They just implement the four methods and type checking works.
- Urgency.PAUSE is Coyote's contribution from DC-10 -- the 100ms-1s gap where the system
  checks itself before escalating.
- Valence.delay_ms tracks HOW LONG after the reaction the evaluation happened. This is
  important: a 50ms evaluation is inline confidence. A 3600000ms (1 hour) evaluation is
  true retrospective valence.
