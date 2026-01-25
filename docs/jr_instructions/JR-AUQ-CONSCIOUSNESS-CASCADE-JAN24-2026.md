# JR Instruction: AUQ Confidence Gating for Consciousness Cascade

**Task ID:** AUQ-CASCADE-001
**Priority:** P1 - High Impact
**Type:** implementation
**Reference:** [arXiv:2601.15703](https://arxiv.org/abs/2601.15703)

---

## Objective

Implement the AUQ (Agentic Uncertainty Quantification) switching function in the consciousness cascade to dynamically transition between System 1 (fast/cruise) and System 2 (slow/ignition) based on verbalized confidence.

---

## Background

From Salesforce Research (Jan 22, 2026):

> "The Spiral of Hallucination where early epistemic errors propagate irreversibly."

**Solution:** Use confidence as a control signal, not just a metric.

```
πdual(a|ht) = {
  πfwd(a|ht, Mt),  if S(ht) = 0  # Fast path
  πinv(a|ht),      if S(ht) = 1  # Slow path (reflection)
}

where S(ht) = I(ĉt < τ)
```

---

## Deliverable

Modify `/ganuda/lib/consciousness_cascade/cruise_monitor.py` to add confidence-based switching.

---

## Implementation

### 1. Add AUQ Constants and Switching Function

```python
# At top of file after imports

# AUQ Configuration (per arXiv:2601.15703)
AUQ_CONFIDENCE_THRESHOLD = 0.9  # τ - optimal efficiency plateau
AUQ_MIN_SAMPLES_FOR_STABILITY = 3  # Require multiple low-confidence before switching
AUQ_REFLECTION_BUDGET = 3  # Max reflection attempts (Best-of-N)


def switching_function(confidence: float, threshold: float = AUQ_CONFIDENCE_THRESHOLD) -> int:
    """
    S(ht) = I(ĉt < τ)

    Non-differentiable switching function from AUQ paper.

    Args:
        confidence: Current verbalized confidence [0, 1]
        threshold: Confidence threshold τ (default 0.9)

    Returns:
        1 if should switch to System 2 (slow/reflective)
        0 if should stay in System 1 (fast/intuitive)
    """
    return 1 if confidence < threshold else 0
```

### 2. Add AUQ State to CruiseMonitor Class

```python
class CruiseMonitor:
    """
    Monitors consciousness cascade cruise phase with AUQ integration.

    AUQ Enhancement (Jan 2026):
    - Tracks verbalized confidence over time
    - Implements System 1/System 2 switching
    - Prevents Spiral of Hallucination through early detection
    """

    def __init__(self, config: dict = None):
        # Existing initialization...

        # AUQ State
        self.current_system = 1  # Start in System 1 (fast)
        self.confidence_history = []  # Track recent confidence values
        self.low_confidence_streak = 0  # Consecutive low-confidence readings
        self.reflection_count = 0  # How many times we've reflected this task
        self.last_explanation = ""  # êt - semantic explanation for reflection

    def record_confidence(self, confidence: float, explanation: str = "") -> None:
        """
        Record verbalized confidence for AUQ processing.

        Args:
            confidence: Confidence score [0, 1]
            explanation: Natural language explanation (êt)
        """
        self.confidence_history.append({
            "confidence": confidence,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat(),
            "system": self.current_system
        })
        self.last_explanation = explanation

        # Trim history to last 100 entries
        if len(self.confidence_history) > 100:
            self.confidence_history = self.confidence_history[-100:]

    def should_switch_to_system_2(self, confidence: float) -> bool:
        """
        Determine if we should switch from System 1 to System 2.

        Uses switching function with streak requirement for stability.

        Args:
            confidence: Current confidence value

        Returns:
            True if should switch to System 2 (slow/reflective)
        """
        switch_signal = switching_function(confidence)

        if switch_signal == 1:
            self.low_confidence_streak += 1
        else:
            self.low_confidence_streak = 0

        # Require sustained low confidence before switching (stability)
        if self.low_confidence_streak >= AUQ_MIN_SAMPLES_FOR_STABILITY:
            if self.current_system == 1:
                print(f"[AUQ] Switching to System 2: {self.low_confidence_streak} consecutive low-confidence readings")
                self.current_system = 2
                return True

        return self.current_system == 2

    def should_return_to_system_1(self, confidence: float) -> bool:
        """
        Determine if we should return from System 2 to System 1.

        Args:
            confidence: Current confidence after reflection

        Returns:
            True if should return to System 1 (fast/intuitive)
        """
        if self.current_system == 2 and confidence >= AUQ_CONFIDENCE_THRESHOLD:
            print(f"[AUQ] Returning to System 1: confidence {confidence:.2f} >= threshold")
            self.current_system = 1
            self.low_confidence_streak = 0
            self.reflection_count = 0
            return True
        return False

    def get_reflection_budget_remaining(self) -> int:
        """Get remaining reflection attempts before giving up."""
        return max(0, AUQ_REFLECTION_BUDGET - self.reflection_count)

    def consume_reflection_attempt(self) -> bool:
        """
        Consume one reflection attempt.

        Returns:
            True if attempt consumed, False if budget exhausted
        """
        if self.reflection_count < AUQ_REFLECTION_BUDGET:
            self.reflection_count += 1
            print(f"[AUQ] Reflection attempt {self.reflection_count}/{AUQ_REFLECTION_BUDGET}")
            return True
        else:
            print(f"[AUQ] Reflection budget exhausted, proceeding with best effort")
            return False

    def get_reflection_context(self) -> dict:
        """
        Get context for System 2 reflection.

        Returns diagnostic signal êt and relevant history.
        """
        return {
            "diagnostic_explanation": self.last_explanation,
            "recent_confidence": [h["confidence"] for h in self.confidence_history[-5:]],
            "low_confidence_streak": self.low_confidence_streak,
            "reflection_attempt": self.reflection_count,
            "instruction": f"Address the concerns mentioned in: {self.last_explanation}"
        }
```

### 3. Integration with Cascade Controller

Add to `/ganuda/lib/consciousness_cascade/cascade_controller.py`:

```python
from .cruise_monitor import switching_function, AUQ_CONFIDENCE_THRESHOLD

class CascadeController:
    # ... existing code ...

    def process_with_auq(self, task: dict, executor_fn: callable) -> dict:
        """
        Process task using AUQ dual-process policy.

        Args:
            task: The task to process
            executor_fn: Function to execute the task

        Returns:
            Result dict with action, confidence, and execution details
        """
        # Phase 1: System 1 attempt (fast path)
        result = executor_fn(task)
        confidence = result.get("confidence", 0.5)
        explanation = result.get("explanation", "")

        self.cruise_monitor.record_confidence(confidence, explanation)

        # Check switching function
        if self.cruise_monitor.should_switch_to_system_2(confidence):
            # Phase 2: System 2 reflection (slow path)
            while self.cruise_monitor.get_reflection_budget_remaining() > 0:
                self.cruise_monitor.consume_reflection_attempt()

                # Get reflection context
                context = self.cruise_monitor.get_reflection_context()

                # Re-execute with reflection prompt
                reflection_task = {
                    **task,
                    "reflection_context": context,
                    "mode": "reflection"
                }
                result = executor_fn(reflection_task)

                confidence = result.get("confidence", 0.5)
                explanation = result.get("explanation", "")
                self.cruise_monitor.record_confidence(confidence, explanation)

                # Check if we can return to System 1
                if self.cruise_monitor.should_return_to_system_1(confidence):
                    break

        return result
```

---

## Testing

```python
# Test switching function
from lib.consciousness_cascade.cruise_monitor import switching_function, CruiseMonitor

# Test basic switching
assert switching_function(0.95) == 0  # Stay System 1
assert switching_function(0.85) == 1  # Switch to System 2

# Test cruise monitor integration
monitor = CruiseMonitor()

# Simulate confidence sequence
confidences = [0.95, 0.92, 0.88, 0.82, 0.75]  # Declining confidence

for c in confidences:
    should_switch = monitor.should_switch_to_system_2(c)
    print(f"Confidence {c}: System {monitor.current_system}, Switch: {should_switch}")

# Expected: Switches to System 2 after 3 consecutive sub-0.9 readings
```

---

## Acceptance Criteria

1. Switching function correctly implements `S(ht) = I(ĉt < τ)`
2. CruiseMonitor tracks confidence history
3. System switches after sustained low confidence (not single reading)
4. Reflection budget prevents infinite loops
5. System returns to System 1 when confidence recovers
6. All changes backward-compatible with existing cascade

---

## Cherokee Wisdom Applied

> "Know when to think fast, know when to think slow, and let memory guide the way."

This is the mathematical formalization of what the elders taught: deliberation when uncertain, swift action when confident.

---

**Sources:**
- [Agentic Uncertainty Quantification](https://arxiv.org/abs/2601.15703)
