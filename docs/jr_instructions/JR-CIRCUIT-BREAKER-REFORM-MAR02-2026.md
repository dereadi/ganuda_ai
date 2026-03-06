# JR Instruction: Circuit Breaker Reform — Mitigate, Don't Discount

**Task ID**: BREAKER-REFORM-001
**Priority**: 3 (of 10)
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: true
**Use RLM**: false
**TEG Plan**: false

## Context

Council vote ffbb923b05dc8f06 (0.85 confidence, PROCEED WITH CAUTION). Chief directive: "Their concerns are valid. Rather than weight their responses, maybe sometimes we write that risk mitigation into the project."

During the vote itself, Turtle raised 7GEN CONCERN about the reform to stop silencing 7GEN CONCERN, and the circuit breaker went OPEN and excluded it. The system silenced Turtle's voice on a vote about not silencing voices.

Current behavior in `lib/drift_detection.py`:
- OPEN specialists: concerns excluded entirely (0x weight)
- HALF_OPEN specialists: concerns weighted at 0.5x
- CLOSED specialists: normal weight (1.0x)

New behavior:
- ALL specialists: concerns count at full weight (1.0x) ALWAYS
- OPEN/HALF_OPEN states become SIGNALS, not silencers
- When a specialist is OPEN or HALF_OPEN, log a "RECURRING CONCERN — NEEDS STRUCTURAL MITIGATION" message
- The circuit breaker state machine stays — it still detects patterns. It just stops acting on them punitively.

## Acceptance Criteria

1. All concerns weighted at 1.0x regardless of circuit breaker state
2. OPEN/HALF_OPEN states logged as "needs mitigation" signals
3. Circuit breaker state detection (`check_circuit_breaker`) unchanged
4. Health recording (`record_specialist_health`) unchanged
5. Confidence formula uses raw concern count, not weighted

## Step 1: Reform the confidence function

File: `lib/drift_detection.py`

```python
<<<<<<< SEARCH
def apply_circuit_breaker_to_confidence(
    base_concerns: List[str],
    specialist_responses: List[Any],
    breaker_states: Dict[str, str]
) -> float:
    """
    Compute adjusted confidence score based on circuit breaker states.

    Logic:
      - OPEN specialists: their concerns are excluded from the count entirely
      - HALF_OPEN specialists: their concerns are weighted at 0.5x
      - CLOSED specialists: their concerns count normally (1.0x)

    Original formula: max(0.25, 1.0 - (len(concerns) * 0.15))
    Adjusted formula: max(0.25, 1.0 - (weighted_concern_count * 0.15))

    Args:
        base_concerns: List of concern_type strings from all specialists.
        specialist_responses: List of SpecialistResponse objects from vote().
        breaker_states: Dict from get_circuit_breaker_states().

    Returns:
        Adjusted confidence float, range [0.25, 1.0].
    """
    weighted_concern_count = 0.0

    for resp in specialist_responses:
        if not resp.has_concern:
            continue

        sid = resp.specialist_id
        state = breaker_states.get(sid, 'CLOSED')

        if state == 'OPEN':
            # Drifted specialist — exclude their concern
            logger.info(
                f"Circuit breaker OPEN for {sid}: "
                f"excluding concern '{resp.concern_type}'"
            )
            continue
        elif state == 'HALF_OPEN':
            # Partially drifted — half weight
            logger.info(
                f"Circuit breaker HALF_OPEN for {sid}: "
                f"concern '{resp.concern_type}' weighted at 0.5x"
            )
            weighted_concern_count += 0.5
        else:
            # CLOSED — normal weight
            weighted_concern_count += 1.0

    confidence = max(0.25, 1.0 - (weighted_concern_count * 0.15))

    logger.info(
        f"Confidence: {confidence:.2f} "
        f"(weighted concerns: {weighted_concern_count}, "
        f"raw concerns: {len(base_concerns)})"
    )
    return confidence
=======
def apply_circuit_breaker_to_confidence(
    base_concerns: List[str],
    specialist_responses: List[Any],
    breaker_states: Dict[str, str]
) -> float:
    """
    Compute confidence score — all voices at full weight.

    Reform (Council vote ffbb923b, Chief directive March 2 2026):
    Circuit breaker states are SIGNALS for structural mitigation, not silencers.
    Every specialist's concern counts at full weight (1.0x). OPEN/HALF_OPEN
    states trigger a "needs mitigation" log so the TPM can write risk mitigation
    into the next relevant specification.

    "Their concerns are valid. Rather than weight their responses, maybe
    sometimes we write that risk mitigation into the project." — Chief

    Args:
        base_concerns: List of concern_type strings from all specialists.
        specialist_responses: List of SpecialistResponse objects from vote().
        breaker_states: Dict from get_circuit_breaker_states().

    Returns:
        Confidence float, range [0.25, 1.0].
    """
    concern_count = 0

    for resp in specialist_responses:
        if not resp.has_concern:
            continue

        sid = resp.specialist_id
        state = breaker_states.get(sid, 'CLOSED')

        # Every concern counts at full weight — no voice is silenced
        concern_count += 1

        # OPEN/HALF_OPEN = signal that this concern recurs and needs
        # structural mitigation in specs, NOT discounting
        if state == 'OPEN':
            logger.warning(
                f"RECURRING CONCERN NEEDS MITIGATION — {sid}: "
                f"'{resp.concern_type}' (circuit breaker OPEN). "
                f"TPM: write mitigation into next relevant spec."
            )
        elif state == 'HALF_OPEN':
            logger.info(
                f"Recurring concern noted — {sid}: "
                f"'{resp.concern_type}' (circuit breaker HALF_OPEN). "
                f"Consider structural mitigation in specs."
            )

    confidence = max(0.25, 1.0 - (concern_count * 0.15))

    logger.info(
        f"Confidence: {confidence:.2f} "
        f"(concerns: {concern_count}, all at full weight)"
    )
    return confidence
>>>>>>> REPLACE
```

## What NOT To Change

- Do NOT modify `check_circuit_breaker()` — the state detection is still useful as a signal
- Do NOT modify `record_specialist_health()` — we still record health data
- Do NOT modify `measure_specialist_coherence()` — coherence measurement stays
- Do NOT add new DB tables or columns
- Do NOT change the confidence formula structure — just use raw count instead of weighted

## Verification

1. Import check: `python3 -c "from lib.drift_detection import apply_circuit_breaker_to_confidence; print('OK')"`
2. Grep for "excluding concern" — should return ZERO matches (old behavior removed)
3. Grep for "RECURRING CONCERN NEEDS MITIGATION" — should return matches (new behavior)
4. Run a council vote and confirm all concerns count at full weight in the logs

## Notes for Jr

- This is a sacred fire task — governance change, not just code change.
- The reform is simple: change what we DO with circuit breaker states, not how we detect them.
- The `logger.warning` for OPEN state (not `logger.info`) is intentional — recurring unmitigated concerns should be visible in monitoring.
- The variable name changes from `weighted_concern_count` to `concern_count` because there's no weighting anymore.
