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