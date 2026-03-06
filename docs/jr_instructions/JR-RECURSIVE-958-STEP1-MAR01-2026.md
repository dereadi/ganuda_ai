# [RECURSIVE] Diamond 2: Ghigau Veto Class — Sacred Dissent for Medicine Woman - Step 1

**Parent Task**: #958
**Auto-decomposed**: 2026-03-01T08:01:58.597494
**Original Step Title**: Update the confidence calculation in `vote()` method

---

### Step 1: Update the confidence calculation in `vote()` method

This modifies BOTH the production path (drift_detection) and fallback path. The sacred dissent check happens BEFORE the normal confidence calculation.

```python
<<<<<<< SEARCH
        # Calculate confidence with circuit breaker awareness
        try:
            from lib.drift_detection import get_circuit_breaker_states, apply_circuit_breaker_to_confidence, record_specialist_health
            breaker_states = get_circuit_breaker_states()
            confidence = apply_circuit_breaker_to_confidence(concerns, responses, breaker_states)
=======
        # Check for Sacred Dissent (Ghigau authority) BEFORE normal confidence
        sacred_dissent_active = False
        sacred_dissent_by = None
        sacred_dissent_condition = ""
        for resp in responses:
            if resp.stance and resp.stance.vote == "sacred_dissent":
                sacred_dissent_active = True
                sacred_dissent_by = resp.name
                sacred_dissent_condition = resp.stance.condition
                print(f"[COUNCIL] GHIGAU INVOKED: {resp.name} — Sacred Dissent. "
                      f"Condition: {resp.stance.condition}")
                break  # One sacred dissent is sufficient

        if sacred_dissent_active:
            confidence = 0.0
        else:
            # Calculate confidence with circuit breaker awareness
            try:
                from lib.drift_detection import get_circuit_breaker_states, apply_circuit_breaker_to_confidence, record_specialist_health
                breaker_states = get_circuit_breaker_states()
                confidence = apply_circuit_breaker_to_confidence(concerns, responses, breaker_states)
>>>>>>> REPLACE
```

Then update the closing of the try/except block and recommendation logic:

```python
<<<<<<< SEARCH
        except ImportError:
            # Coyote's [DISSENT] carries 2x weight (error neuron amplification)
            weighted_concern_count = sum(2 if '[DISSENT]' in c else 1 for c in concerns)
            confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))

        # Generate recommendation
        if len(concerns) == 0:
            recommendation = "PROCEED: No concerns raised"
        elif len(concerns) <= 2:
            recommendation = f"PROCEED WITH CAUTION: {len(concerns)} concern(s)"
        else:
            recommendation = f"REVIEW REQUIRED: {len(concerns)} concerns raised"
=======
            except ImportError:
                # Coyote's [DISSENT] carries 2x weight (error neuron amplification)
                weighted_concern_count = sum(2 if '[DISSENT]' in c else 1 for c in concerns)
                confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))

        # Generate recommendation
        if sacred_dissent_active:
            recommendation = (
                f"BLOCKED: {sacred_dissent_by} invokes Sacred Dissent (Ghigau). "
                f"Condition for resolution: {sacred_dissent_condition}"
            )
        elif len(concerns) == 0:
            recommendation = "PROCEED: No concerns raised"
        elif len(concerns) <= 2:
            recommendation = f"PROCEED WITH CAUTION: {len(concerns)} concern(s)"
        else:
            recommendation = f"REVIEW REQUIRED: {len(concerns)} concerns raised"
>>>>>>> REPLACE
```
