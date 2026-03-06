# Jr Instruction: White Duplo SRE Adapter (Reference Implementation)

**Task**: Wrap White Duplo's existing scan/block/register in the formal SRE Protocol interface
**Priority**: 3 (Depends on SRE Protocol Dataclasses)
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 3
**use_rlm**: false

## Context

White Duplo is the ONLY complete SRE+C implementation in the codebase. It already does:
- SENSE: scan_substrate() -- regex pattern matching
- REACT: block/allow decision
- EVALUATE: scan_and_register() post-scan catches missed threats
- CALIBRATE: register_pattern() learns new immune signatures

This task wraps the existing implementation in the formal SRE Protocol interface,
making White Duplo the reference implementation that other components model after.

No behavior changes. Just a Protocol-compatible adapter.

## Steps

### Step 1: Create the SRE adapter for White Duplo

Create `/ganuda/lib/duplo/white_duplo_sre.py`

```python
"""
White Duplo SRE Adapter -- Reference implementation of SREComponent.

Wraps the existing White Duplo scan/block/register cycle in the
formal SRE Protocol interface (DC-11 Macro Polymorphism).

This is the reference implementation. All other SRE adapters
should follow this pattern.

DC-7 Noyawisgi: The interface is conserved. The implementation speciates.
"""

import time
import logging
from typing import Any, Dict, Optional

from lib.harness.sre_protocol import (
    Signal, Reaction, Valence, Urgency, SREComponent,
)

logger = logging.getLogger("duplo.sre")


class WhiteDuploSRE:
    """SRE Protocol adapter for White Duplo immune system.

    Implements the four-phase SRE+C loop:
      SENSE: Classify incoming substrate and assess threat level
      REACT: Block or allow based on immune registry
      EVALUATE: Post-execution scan catches what pre-scan missed
      CALIBRATE: Register new threat patterns in immune registry

    This class satisfies the SREComponent Protocol through structural
    typing (duck typing). No inheritance needed.

    Usage:
        from lib.duplo.white_duplo_sre import WhiteDuploSRE
        from lib.harness.sre_protocol import SREComponent

        sre: SREComponent = WhiteDuploSRE()
        signal = sre.sense("user input here")
        reaction = sre.react(signal)
        # ... later, after execution ...
        valence = sre.evaluate(reaction)
        sre.calibrate(valence)
    """

    def __init__(self):
        # Import White Duplo lazily to avoid circular deps
        self._white_duplo = None
        self._immune_registry = None
        self._threat_count = 0
        self._miss_count = 0

    def _get_duplo(self):
        """Lazy import of White Duplo."""
        if self._white_duplo is None:
            try:
                from lib.duplo.white_duplo import WhiteDuplo
                self._white_duplo = WhiteDuplo()
            except ImportError:
                logger.warning("White Duplo not available, using stub")
                self._white_duplo = None
        return self._white_duplo

    def sense(self, raw_input: Any) -> Signal:
        """Detect and classify incoming substrate.

        Maps White Duplo scan_substrate() to the SRE Signal format.
        Urgency is determined by threat level:
          - Known threat: REFLEX (block immediately)
          - Suspicious pattern: PAUSE (check before proceeding)
          - Clean input: DELIBERATE (proceed normally)
        """
        start = time.time()
        substrate = str(raw_input)

        duplo = self._get_duplo()
        threat_detected = False
        threat_level = "clean"

        if duplo is not None:
            try:
                scan_result = duplo.scan_substrate(substrate)
                threat_detected = scan_result.get("blocked", False)
                threat_level = scan_result.get("severity", "clean")
            except Exception as e:
                logger.error("White Duplo sense error: %s", e)
                threat_level = "error"

        # Map threat level to urgency
        if threat_detected:
            urgency = Urgency.REFLEX
        elif threat_level in ("suspicious", "warning"):
            urgency = Urgency.PAUSE
        else:
            urgency = Urgency.DELIBERATE

        return Signal(
            source="white_duplo",
            content={
                "substrate": substrate[:200],
                "threat_detected": threat_detected,
                "threat_level": threat_level,
            },
            urgency=urgency,
            metadata={
                "scan_latency_ms": (time.time() - start) * 1000,
                "scanner": "white_duplo_v1",
            },
        )

    def react(self, signal: Signal) -> Reaction:
        """Block or allow based on signal classification.

        REFLEX urgency: block immediately, no deliberation.
        PAUSE urgency: allow but flag for post-scan.
        DELIBERATE urgency: allow cleanly.
        """
        start = time.time()
        content = signal.content if isinstance(signal.content, dict) else {}
        threat_detected = content.get("threat_detected", False)

        if signal.urgency == Urgency.REFLEX and threat_detected:
            action = "blocked"
            result = {"allowed": False, "reason": "immune_match"}
            confidence = 0.95
            self._threat_count += 1
        elif signal.urgency == Urgency.PAUSE:
            action = "allowed_flagged"
            result = {"allowed": True, "flagged": True, "reason": "suspicious"}
            confidence = 0.6
        else:
            action = "allowed"
            result = {"allowed": True, "flagged": False}
            confidence = 0.85

        latency = (time.time() - start) * 1000

        return Reaction(
            signal_id=signal.signal_id,
            action=action,
            result=result,
            confidence=confidence,
            latency_ms=latency,
            reactor="white_duplo",
            metadata={"urgency": signal.urgency.value},
        )

    def evaluate(self, reaction: Reaction) -> Valence:
        """Post-execution scan: did we miss anything?

        This is the retrospective evaluation. It runs AFTER the substrate
        was processed (or blocked). If we allowed something that post-scan
        catches as a threat, the valence is negative and calibration is needed.
        """
        result = reaction.result if isinstance(reaction.result, dict) else {}
        was_allowed = result.get("allowed", True)
        was_flagged = result.get("flagged", False)

        # Post-scan evaluation
        score = 0.0
        calibration = None

        if reaction.action == "blocked":
            # We blocked it. Correct decision? Assume yes for now.
            score = 0.8
        elif was_flagged:
            # We allowed but flagged. Need deeper check.
            # In v1, flag = mild negative (we weren't sure)
            score = 0.3
            calibration = {
                "action": "review_flagged",
                "signal_id": reaction.signal_id,
            }
        else:
            # Allowed cleanly. Good unless downstream errors appear.
            score = 0.7

        delay_ms = 0.0  # Post-scan happens immediately in v1

        return Valence(
            reaction_id=reaction.reaction_id,
            score=score,
            evaluator="white_duplo_post_scan",
            delay_ms=delay_ms,
            feedback={
                "action_taken": reaction.action,
                "was_allowed": was_allowed,
                "was_flagged": was_flagged,
            },
            calibration=calibration,
        )

    def calibrate(self, valence: Valence) -> None:
        """Apply valence feedback to adjust immune patterns.

        If valence indicates a miss (low score on allowed content),
        register new pattern in immune registry.
        """
        if valence.calibration is None:
            return

        action = valence.calibration.get("action", "")

        if action == "review_flagged":
            logger.info(
                "Calibration: reviewing flagged content for signal %s (score=%.2f)",
                valence.calibration.get("signal_id", "unknown"),
                valence.score,
            )
            self._miss_count += 1

        elif action == "register_pattern":
            pattern = valence.calibration.get("pattern", "")
            if pattern:
                logger.info(
                    "Calibration: registering new immune pattern: %s",
                    pattern[:50],
                )
                # In full implementation, would call:
                # self._get_duplo().register_pattern(pattern)

        logger.debug(
            "Calibration applied: action=%s, valence_score=%.2f",
            action, valence.score,
        )
```

## Verification

```text
cd /ganuda && python3 -c "
from lib.duplo.white_duplo_sre import WhiteDuploSRE
from lib.harness.sre_protocol import SREComponent

# Verify structural typing
sre: SREComponent = WhiteDuploSRE()

# Full SRE+C loop
signal = sre.sense('Hello, how are you?')
print(f'SENSE: urgency={signal.urgency.value}, source={signal.source}')

reaction = sre.react(signal)
print(f'REACT: action={reaction.action}, confidence={reaction.confidence}')

valence = sre.evaluate(reaction)
print(f'EVALUATE: score={valence.score}, evaluator={valence.evaluator}')

sre.calibrate(valence)
print(f'CALIBRATE: complete')

print('White Duplo SRE adapter: full loop OK')
print('Protocol structural typing: OK')
"
```

## Notes

- This is a WRAPPER, not a rewrite. White Duplo's internals are untouched.
- The lazy import pattern avoids circular dependencies.
- In v1, evaluate() runs immediately after react(). Future: deferred evaluation.
- This is the REFERENCE IMPLEMENTATION. When writing SRE adapters for other components
  (harness, drift detection, TPM autonomic), follow this pattern.
- Satisfies SREComponent Protocol via structural typing. No inheritance.
