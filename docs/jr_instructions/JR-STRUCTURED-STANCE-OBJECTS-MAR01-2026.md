# JR Instruction: Structured Stance Objects for Council Specialists

**Task ID**: STANCE-001
**Priority**: 2 (High)
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**Sacred Fire Priority**: false

## Context

Council specialist concern detection currently uses simple substring matching (`spec["concern_flag"] in content` at line 922 of `specialist_council.py`). This is fragile — if a specialist mentions a concern flag string in passing, or formats it slightly differently, the detection breaks. Research (Sociocracy 3.0, Loomio, CONSENSAGENT ACL 2025) shows structured stance objects are more reliable.

We are replacing free-text concern extraction with a structured JSON stance that each specialist returns at the end of their response.

## What To Change

File: `lib/specialist_council.py`

### Step 1: Add StanceObject to imports and dataclasses (after line 832)

```python
<<<<<<< SEARCH
@dataclass
class CouncilVote:
    """Aggregated council vote result"""
=======
@dataclass
class SpecialistStance:
    """Structured stance from a specialist — no more regex parsing"""
    vote: str           # "consent" | "concern" | "dissent" | "sacred_dissent"
    reason: str         # why this stance
    condition: str      # what would resolve the concern (empty if consent)

    @classmethod
    def from_response(cls, content: str, concern_flag: str) -> 'SpecialistStance':
        """
        Parse structured stance from specialist response.
        Looks for a JSON block tagged STANCE at the end of the response.
        Falls back to legacy substring matching if no structured stance found.
        """
        import json as _json
        import re

        # Try to find structured stance JSON block
        stance_match = re.search(
            r'\[STANCE\]\s*(\{.*?\})\s*$', content, re.DOTALL
        )
        if stance_match:
            try:
                data = _json.loads(stance_match.group(1))
                return cls(
                    vote=data.get("vote", "consent"),
                    reason=data.get("reason", ""),
                    condition=data.get("condition", ""),
                )
            except _json.JSONDecodeError:
                pass

        # Legacy fallback: substring matching (preserves backward compatibility)
        if concern_flag and concern_flag in content:
            return cls(
                vote="dissent" if concern_flag == "DISSENT" else "concern",
                reason=f"Legacy detection: {concern_flag} found in response",
                condition="",
            )

        return cls(vote="consent", reason="", condition="")


@dataclass
class CouncilVote:
    """Aggregated council vote result"""
>>>>>>> REPLACE
```

### Step 2: Add stance field to SpecialistResponse (around line 823)

```python
<<<<<<< SEARCH
@dataclass
class SpecialistResponse:
    """Response from a single specialist"""
    specialist_id: str
    name: str
    role: str
    response: str
    has_concern: bool
    concern_type: Optional[str] = None
    response_time_ms: int = 0
=======
@dataclass
class SpecialistResponse:
    """Response from a single specialist"""
    specialist_id: str
    name: str
    role: str
    response: str
    has_concern: bool
    concern_type: Optional[str] = None
    response_time_ms: int = 0
    stance: Optional['SpecialistStance'] = None
>>>>>>> REPLACE
```

### Step 3: Update `_query_specialist` to parse stance (around line 921)

```python
<<<<<<< SEARCH
        # Check for concern flags
        has_concern = spec["concern_flag"] in content
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return SpecialistResponse(
            specialist_id=specialist_id,
            name=spec["name"],
            role=spec["role"],
            response=content,
            has_concern=has_concern,
            concern_type=spec["concern_flag"] if has_concern else None,
            response_time_ms=elapsed_ms
        )
=======
        # Parse structured stance (falls back to legacy substring matching)
        stance = SpecialistStance.from_response(content, spec.get("concern_flag", ""))
        has_concern = stance.vote in ("concern", "dissent", "sacred_dissent")
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return SpecialistResponse(
            specialist_id=specialist_id,
            name=spec["name"],
            role=spec["role"],
            response=content,
            has_concern=has_concern,
            concern_type=spec.get("concern_flag") if has_concern else None,
            response_time_ms=elapsed_ms,
            stance=stance
        )
>>>>>>> REPLACE
```

### Step 4: Update each specialist's system_prompt

Append this paragraph to the end of EACH specialist's `system_prompt` in the `SPECIALISTS` dict (crawdad, gecko, turtle, eagle_eye, spider, peace_chief, raven, coyote):

```
\n\nAt the end of your response, include a structured stance block:\n[STANCE] {"vote": "consent|concern|dissent", "reason": "brief reason", "condition": "what would resolve this, if any"}
```

**IMPORTANT**: Do NOT replace the existing system_prompt content. APPEND this paragraph at the end. Each specialist's existing prompt is sacred and must not be modified.

For each specialist entry in `SPECIALISTS`, the SEARCH block should be the last line of their `system_prompt` string (before the closing quote), and the REPLACE block should add the stance instruction after it.

## What NOT To Change

- Do NOT modify the `vote()` method's concern collection logic (line 1059). The `has_concern` and `concern_type` fields still work the same way. The stance is additive metadata.
- Do NOT modify `drift_detection.py`. It receives `has_concern` booleans, which still work.
- Do NOT modify specialist system prompt content beyond appending the stance instruction.

## Verification

1. Run a council vote: `python3 -c "from lib.specialist_council import SpecialistCouncil; sc = SpecialistCouncil(); r = sc.vote('Should we add a new monitoring endpoint?'); print(r.confidence, r.recommendation)"`
2. Check that `SpecialistResponse.stance` is populated for each response
3. Check that legacy concern detection still works (backward compatible)
4. Verify no import errors: `python3 -c "from lib.specialist_council import SpecialistStance; print('OK')"`

## References

- Sociocracy 3.0 consent-based decision-making
- Loomio stance model (GitHub: loomio/loomio)
- CONSENSAGENT (Virginia Tech, ACL 2025 Findings)
- Council Vote: pending (this is a structural improvement)
