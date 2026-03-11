# JR INSTRUCTION: Fix standing_dissent Unreachable When consent=True

**Task**: Fix governance integrity bug where standing_dissent resolution is unreachable when consent=True
**Priority**: P1 — governance integrity
**Date**: 2026-03-10
**TPM**: Claude Opus
**Kanban**: #2054
**Story Points**: 1

## Problem Statement

In the Longhouse/council voting code, when overall `consent=True` on a vote, the `standing_dissent` resolution type becomes unreachable. This is a governance integrity bug. Coyote's standing dissent is an architectural feature (DC-7, Noyawisgi) — it must always be expressible regardless of the consent state of the overall vote. A unanimous "yes" with Coyote's standing dissent recorded is a valid and important governance outcome. Without it, Coyote's dissent is silently swallowed.

The bug was identified during the Slack federation wiring votes (Mar 9 2026). Coyote's standing dissent was noted in conversation but could not be recorded in the vote structure because the code path short-circuits when consent is True.

## Where to Look

The bug is likely in one or more of these files:

1. **`/ganuda/lib/longhouse.py`** — the Longhouse voting engine. Look for where `consent` is evaluated and where `resolution_type` is set. The bug is probably a conditional that skips dissent recording when consent=True.

2. **`/ganuda/lib/specialist_council.py`** — the specialist council that feeds votes to Longhouse. Check if standing_dissent is filtered out before reaching Longhouse.

3. **`/ganuda/daemons/governance_agent.py`** — the governance daemon that orchestrates votes. Check if it drops dissent data when composing the final vote record.

## What the Fix Should Do

1. **Identify the exact code path** where `standing_dissent` becomes unreachable. Document it clearly in a code comment.

2. **Ensure `standing_dissent` is always a valid resolution type**, regardless of `consent` state. The fix should allow a vote result like:
   ```python
   {
       "consent": True,
       "confidence": 0.857,
       "resolution_type": "approved",
       "standing_dissents": [
           {
               "specialist": "coyote",
               "reason": "Non-consent IS consent to governance",
               "dissent_type": "standing"
           }
       ]
   }
   ```

3. **Do not change the meaning of `consent`**. A vote with consent=True and a standing_dissent is still an approved vote. The dissent is recorded metadata, not a veto.

4. **Preserve backward compatibility**. Existing votes in the `council_votes` table must not be invalidated. The fix should be additive — adding a `standing_dissents` field to vote records that have them, not changing the structure of existing records.

## The Fix Pattern

The fix should be minimal. Likely one of:

- Remove an `if consent: return` early exit that skips dissent recording
- Add a separate code path that records standing_dissents independently of the consent evaluation
- Ensure the `resolution_type` enum/check includes `standing_dissent` as valid when consent=True (not just when consent=False)

## Testing

Write a test case that proves the fix works. Create `/ganuda/tests/test_standing_dissent.py`:

```python
"""
Test that standing_dissent is recordable when consent=True.
This is a governance integrity test — Coyote's dissent must never be silenced.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

def test_standing_dissent_with_consent_true():
    """A vote with consent=True should still allow standing_dissent."""
    # Import the relevant voting function
    # Run a mock vote where all specialists consent but Coyote registers standing dissent
    # Assert that the vote result contains:
    #   - consent = True
    #   - standing_dissents is not empty
    #   - Coyote's dissent reason is preserved
    pass

def test_standing_dissent_with_consent_false():
    """A vote with consent=False should also allow standing_dissent (regression check)."""
    pass

def test_vote_without_dissent_unchanged():
    """A normal vote without standing_dissent should work exactly as before."""
    pass

if __name__ == "__main__":
    test_standing_dissent_with_consent_true()
    test_standing_dissent_with_consent_false()
    test_vote_without_dissent_unchanged()
    print("All standing_dissent tests passed")
```

Fill in the test bodies with actual imports and assertions based on what you find in the code.

## Target Files

- `/ganuda/lib/longhouse.py` — likely fix location (MODIFY)
- `/ganuda/lib/specialist_council.py` — possible fix location (MODIFY if needed)
- `/ganuda/daemons/governance_agent.py` — possible fix location (MODIFY if needed)
- `/ganuda/tests/test_standing_dissent.py` — test case (CREATE)

## Constraints

- Do NOT change the meaning of `consent` — True still means approved
- Do NOT modify existing vote records in the database
- Do NOT add new database columns or tables
- Do NOT break backward compatibility with existing vote consumers (dawn mist, status page, etc.)
- Minimal change — this is a 1 SP fix, not a refactor

## Files to Read Before Starting

- `/ganuda/lib/longhouse.py` — full file, understand the vote flow
- `/ganuda/lib/specialist_council.py` — understand how specialists submit their positions
- `/ganuda/daemons/governance_agent.py` — understand the orchestration layer
- `/ganuda/docs/design/DC-BACKLOG-RECKONING-MAR10-2026.md` — recent vote structure reference

## Acceptance Criteria

- A council vote with consent=True can include a standing_dissent from Coyote
- The standing_dissent reason and specialist name are preserved in the vote record
- Test case passes: `python3 /ganuda/tests/test_standing_dissent.py`
- Existing votes are not affected
- `python3 -c "import py_compile; py_compile.compile('lib/longhouse.py', doraise=True)"` passes
- `python3 -c "import py_compile; py_compile.compile('lib/specialist_council.py', doraise=True)"` passes

## DO NOT

- Change the consent semantics
- Add new DB tables or columns
- Break existing vote consumers
- Refactor the entire voting system — surgical fix only
