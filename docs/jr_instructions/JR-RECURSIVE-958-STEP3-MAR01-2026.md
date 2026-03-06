# [RECURSIVE] Diamond 2: Ghigau Veto Class — Sacred Dissent for Medicine Woman - Step 3

**Parent Task**: #958
**Auto-decomposed**: 2026-03-01T08:01:58.604111
**Original Step Title**: Update the thermal memory log for sacred dissent votes

---

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
