# JR INSTRUCTION: Standing Dissent Test Coverage

**Task**: Implement the standing dissent test suite — currently all stubs
**Priority**: P2 (governance correctness — the fix is live but unverified by tests)
**Date**: 2026-03-29
**TPM**: Claude Opus
**Story Points**: 1
**Depends On**: longhouse.py standing_dissent fix (LIVE), test_standing_dissent.py (EXISTS, stubs only)

## Problem Statement

Standing dissent was fixed in `longhouse.py` — the code now correctly handles `standing_dissent=True` independent of `consent` value. But the test file at `/ganuda/tests/test_standing_dissent.py` contains only `pass` stubs. No tests actually verify the fix works, which means a regression could slip in silently.

## Context: What Standing Dissent Is

Standing dissent is Coyote's archetype function: consent to the decision but register a challenge that must be answered. It is NOT non-consent. It strengthens the decision it tests.

**Key behavior**: `consent=True, standing_dissent=True` must produce a resolution of `"consensus_with_standing_dissent"`, not plain `"consensus"`.

## Task: Implement Test Cases

**File**: `/ganuda/tests/test_standing_dissent.py`

### Test 1: `test_standing_dissent_with_consent`

The core case. Coyote consents but registers standing dissent.

```python
def test_standing_dissent_with_consent():
    """Standing dissent + consent=True → consensus_with_standing_dissent resolution."""
    responses = {}
    for member in TRIBE_MEMBERS:
        responses[member] = {"consent": True, "reason": "Approved"}

    # Coyote consents but files standing dissent
    responses["Coyote"] = {
        "consent": True,
        "standing_dissent": True,
        "reason": "I consent but challenge the certainty."
    }

    result = seek_consensus("Test proposal", responses)
    assert result["resolution"] == "consensus_with_standing_dissent"
    assert len(result.get("standing_dissent", [])) == 1
    assert result["standing_dissent"][0]["member"] == "Coyote"
```

### Test 2: `test_standing_dissent_with_non_consent`

Regression guard. Standing dissent + consent=False should still count as non-consent.

```python
def test_standing_dissent_with_non_consent():
    """Standing dissent + consent=False → non-consenting, not just standing dissent."""
    responses = {}
    for member in TRIBE_MEMBERS:
        responses[member] = {"consent": True, "reason": "Approved"}

    responses["Coyote"] = {
        "consent": False,
        "standing_dissent": True,
        "reason": "I object and challenge."
    }

    result = seek_consensus("Test proposal", responses)
    # Should be non-consent path, not consensus_with_standing_dissent
    assert result["resolution"] != "consensus"
    assert "Coyote" in [d["member"] for d in result.get("non_consenting", result.get("dissenting", []))]
```

### Test 3: `test_no_standing_dissent_plain_consensus`

Baseline. No standing dissent → plain consensus.

```python
def test_no_standing_dissent_plain_consensus():
    """All consent, no standing dissent → plain consensus."""
    responses = {}
    for member in TRIBE_MEMBERS:
        responses[member] = {"consent": True, "reason": "Approved"}

    result = seek_consensus("Test proposal", responses)
    assert result["resolution"] == "consensus"
    assert len(result.get("standing_dissent", [])) == 0
```

### Test 4: `test_multiple_standing_dissents`

Multiple members file standing dissent simultaneously.

```python
def test_multiple_standing_dissents():
    """Multiple standing dissents → consensus_with_standing_dissent, all recorded."""
    responses = {}
    for member in TRIBE_MEMBERS:
        responses[member] = {"consent": True, "reason": "Approved"}

    responses["Coyote"] = {
        "consent": True,
        "standing_dissent": True,
        "reason": "Challenge 1"
    }
    responses["Raven"] = {
        "consent": True,
        "standing_dissent": True,
        "reason": "Challenge 2"
    }

    result = seek_consensus("Test proposal", responses)
    assert result["resolution"] == "consensus_with_standing_dissent"
    assert len(result["standing_dissent"]) == 2
```

## Implementation Notes

- Import `seek_consensus` and `TRIBE_MEMBERS` from `lib.longhouse`
- Tests should be runnable with `pytest tests/test_standing_dissent.py`
- Check the actual return shape of `seek_consensus()` — the result dict keys may differ slightly from the test assumptions above. Read `_resolve()` in longhouse.py to confirm field names.
- If `seek_consensus()` requires external dependencies (DB, thermal memory), mock only the external I/O, not the logic.

## Verification

```bash
cd /ganuda && python -m pytest tests/test_standing_dissent.py -v
```

All 4 tests should pass. If any fail, the standing_dissent logic has a regression or the test assumptions about return shape are wrong — fix accordingly.

---

FOR SEVEN GENERATIONS
