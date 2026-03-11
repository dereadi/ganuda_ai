# [RECURSIVE] FIX: Longhouse standing_dissent unreachable when consent=True - Step 1

**Parent Task**: #1186
**Auto-decomposed**: 2026-03-10T02:26:21.489277
**Original Step Title**: Restructure the consent evaluation loop

---

### Step 1: Restructure the consent evaluation loop

In `/ganuda/lib/longhouse.py`, replace the loop in `seek_consensus()`:

```
<<<<<<< SEARCH
        for member, response in responses.items():
            if member not in TRIBE_MEMBERS:
                raise ValueError(f"'{member}' is not a recognized tribe member.")
            if not response.get("consent", True):
                entry = {
                    "member": member,
                    "role": TRIBE_MEMBERS[member]["role"],
                    "reason": response.get("reason", ""),
                }
                if response.get("standing_dissent", False):
                    standing_dissent.append(entry)
                else:
                    non_consenting.append(entry)
                if TRIBE_MEMBERS[member].get("ghigau"):
                    ghigau_invoked = True
=======
        for member, response in responses.items():
            if member not in TRIBE_MEMBERS:
                raise ValueError(f"'{member}' is not a recognized tribe member.")
            entry = {
                "member": member,
                "role": TRIBE_MEMBERS[member]["role"],
                "reason": response.get("reason", ""),
            }
            # Standing dissent is independent of consent -- Coyote's archetype
            # consents to the decision but registers a challenge that must be answered.
            # This is NOT non-consent. It strengthens the decision it tests.
            if response.get("standing_dissent", False):
                standing_dissent.append(entry)
            elif not response.get("consent", True):
                non_consenting.append(entry)
                if TRIBE_MEMBERS[member].get("ghigau"):
                    ghigau_invoked = True
>>>>>>> REPLACE
```

## Acceptance Criteria
- Coyote can submit `{"consent": True, "standing_dissent": True}` and it resolves as `consensus_with_standing_dissent`
- Non-consent (consent=False without standing_dissent) still resolves as `deferred`
- Ghigau veto still works (consent=False from Elisi)
- Standing dissent names appear in resolution text
- Standing dissent entries appear in non_consenting list passed to _resolve (for thermal record)
- Write a test: call seek_consensus with Coyote consent=True, standing_dissent=True, verify resolution_type

## Dependencies
- None. This is a standalone bug fix.
- Kanban #2054, Jr task #1186.
