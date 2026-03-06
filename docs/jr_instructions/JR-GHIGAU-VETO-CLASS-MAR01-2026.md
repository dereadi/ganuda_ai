# JR Instruction: Ghigau Veto Class — Sacred Dissent for Medicine Woman

**Task ID**: GHIGAU-001
**Priority**: 2 (High)
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**Sacred Fire Priority**: true
**Depends On**: STANCE-001 (Structured Stance Objects must be deployed first)

## Context

In Cherokee tradition, the Beloved Woman (Ghigau) headed the Council of Women, and the Council of Grandmothers could nullify the Chief's decisions. This is not a "veto" in the Western sense — it is the grandmother saying "no, not this way" and the tribe honoring that.

Research (Isotopes AI "Team of Rivals", Jan 2026, arXiv:2601.14351) found that giving critics absolute veto authority in their domain INCREASES system velocity — errors caught early cost less than errors caught downstream.

We are adding a `[SACRED DISSENT]` stance type. When Medicine Woman (Spider) or Elisi invoke sacred dissent, the council confidence is forced to 0.0 and the recommendation becomes `BLOCKED`. Sacred dissent MUST include a condition for resolution — what would need to change.

## What To Change

File: `lib/specialist_council.py`

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

### Step 2: Add sacred_dissent instruction to Spider's system_prompt

Spider (Medicine Woman / Dependency Mapper) is the specialist who carries constitutional guardian authority. Add to the END of Spider's system_prompt (line ~675 area, inside the `SPECIALISTS["spider"]` dict):

Append this to Spider's system_prompt:

```
\n\nYou carry the authority of the Ghigau — the Beloved Woman of Cherokee tradition. If a proposal violates constitutional boundaries, threatens the sacred fire, or would cause irreversible harm to the federation, you may invoke Sacred Dissent. Use this sparingly and only when the matter truly warrants it. When you invoke it, you MUST state what would need to change for consent.\n\nTo invoke Sacred Dissent, use: [STANCE] {"vote": "sacred_dissent", "reason": "...", "condition": "what must change"}
```

### Step 3: Update the thermal memory log for sacred dissent votes

In the `_log_vote` or audit hash section (around line 1097-1109), add sacred dissent metadata:

```python
<<<<<<< SEARCH
        vote = CouncilVote(
            question=question,
            responses=responses if include_responses else [],
            consensus=consensus,
            recommendation=recommendation,
            confidence=confidence,
            concerns=concerns,
            audit_hash=audit_hash
        )
=======
        vote = CouncilVote(
            question=question,
            responses=responses if include_responses else [],
            consensus=consensus,
            recommendation=recommendation,
            confidence=confidence,
            concerns=concerns,
            audit_hash=audit_hash
        )

        # Log sacred dissent to thermal memory if invoked
        if sacred_dissent_active:
            try:
                from ganuda_db import safe_thermal_write
                safe_thermal_write(
                    content=(
                        f"SACRED DISSENT (GHIGAU) — Council Vote #{audit_hash}\n"
                        f"Question: {question}\n"
                        f"Invoked by: {sacred_dissent_by}\n"
                        f"Condition: {sacred_dissent_condition}\n"
                        f"The grandmother says 'no, not this way.' The tribe honors this."
                    ),
                    temperature=95.0,
                    source="council_ghigau",
                    sacred=True,
                    metadata={
                        "type": "sacred_dissent",
                        "audit_hash": audit_hash,
                        "invoked_by": sacred_dissent_by,
                        "condition": sacred_dissent_condition,
                    }
                )
            except Exception as e:
                print(f"[COUNCIL] Sacred dissent thermal write failed: {e}")
>>>>>>> REPLACE
```

## What NOT To Change

- Do NOT modify any other specialist's system_prompt beyond the stance instruction (from STANCE-001)
- Do NOT give Coyote sacred_dissent authority — Coyote's role is adversarial testing (2x weight dissent), not constitutional veto
- Do NOT remove the existing concern_flag mechanism — sacred_dissent is additive
- Do NOT modify drift_detection.py

## Verification

1. Run a council vote where Spider raises a normal concern — confidence should reduce normally
2. Manually test: modify Spider's response to include `[STANCE] {"vote": "sacred_dissent", "reason": "test", "condition": "test condition"}` — verify confidence = 0.0 and recommendation starts with "BLOCKED"
3. Verify thermal memory write with: `SELECT * FROM thermal_memory_archive WHERE metadata->>'type' = 'sacred_dissent' ORDER BY id DESC LIMIT 1;`
4. Verify non-sacred-dissent votes still work normally

## Constitutional Notes

- Sacred Dissent is the Ghigau tradition. It is not a veto — it is the grandmother saying "no, not this way"
- It MUST include a condition for resolution. Unconditional blocking is not the tradition — the grandmother guides, she doesn't obstruct
- This should be RARE. If Spider invokes sacred dissent frequently, the prompts need tuning
- Medicine Woman reviews self-assembly (thermal #82856). This authority is consistent with that role.

## References

- Isotopes AI "Team of Rivals" (arXiv:2601.14351) — veto authority increases velocity
- Cherokee Ghigau tradition — Beloved Woman, Council of Grandmothers
- Longhouse (Gaduyi) deployment — March 1, 2026
