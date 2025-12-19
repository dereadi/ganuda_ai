# KB-JR-001: Jr Agent Mission ID Regex Bug

**Date**: 2025-12-02
**Category**: Bug Fix
**Severity**: CRITICAL (blocks all non-hex mission IDs)
**Status**: Fix deployed via mission JR-REGEX-FIX-001

## Summary

The IT Jr Agent V3 mission ID parser uses a regex that only matches hex characters,
causing mission IDs with non-hex letters (G-Z) to be truncated.

## Root Cause

In `/ganuda/it_triad_jr_agent_v3.py`, the `parse_decision()` function:

```python
# BUGGY CODE (line ~117):
mission_match = re.search(r'MISSION ID:\s*([a-f0-9-]+)', content, re.IGNORECASE)
```

The character class `[a-f0-9-]` only matches:
- a-f (hex letters)
- 0-9 (digits)
- `-` (dashes)

## Example Failure

| Mission ID | Regex Captures | Result |
|------------|----------------|--------|
| `FARA-SAG-DB-001` | `FA` | ❌ Truncated at 'R' |
| `SAG-CSS-MONET-001` | `-` | ❌ Captures only dash |
| `abc123-def456` | `abc123-def456` | ✅ Works (all hex) |

## Fix

Change the regex to use `\w` (word characters) instead of `[a-f0-9]`:

```python
# FIXED CODE:
mission_match = re.search(r'MISSION ID:\s*([\w-]+)', content, re.IGNORECASE)
```

`[\w-]` matches:
- `\w` = letters (a-z, A-Z), digits (0-9), underscore (_)
- `-` = dashes

## Impact

Without this fix:
- Jr Agent acknowledges decisions but cannot fetch original mission content
- The UUID lookup fails because "FA" is not a valid UUID
- No actual work is performed (tables not created, files not written)
- All missions with non-hex IDs are effectively blocked

## Prevention

When writing regex patterns for IDs:
1. Use `[\w-]+` for alphanumeric IDs with dashes
2. Use `[a-f0-9-]{36}` for UUID format specifically
3. Test with non-hex mission IDs before deploying

## Related Missions

- JR-REGEX-FIX-001 (this bug fix)
- FARA-SAG-DB-001 (blocked)
- FARA-SAG-BACKEND-001 (blocked)
- FARA-SAG-FRONTEND-001 (blocked)
