# Add Standing Dissent Resolution Type to Longhouse

## Context
Coyote's non-consent to the Deer Regency Charter was identified as archetype function, not
obstruction. The Longhouse needs a resolution type that acknowledges standing dissent without
blocking consensus. Currently, ANY non-consent defers the matter.

Standing dissent = a member whose archetype function IS perpetual challenge. Their non-consent
is acknowledged and recorded but does not prevent consensus.

Kanban: #1943 | Epic: #1941 | Long Man phase: ADAPT | Cycle: #1

## Changes

File: `/ganuda/lib/longhouse.py`

### Change 1: Add standing_dissent tracking variable and response handling

```
<<<<<<< SEARCH
        non_consenting = []
        ghigau_invoked = False

        for member, response in responses.items():
            if member not in TRIBE_MEMBERS:
                raise ValueError(f"'{member}' is not a recognized tribe member.")
            if not response.get("consent", True):
                entry = {
                    "member": member,
                    "role": TRIBE_MEMBERS[member]["role"],
                    "reason": response.get("reason", ""),
                }
                non_consenting.append(entry)
                if TRIBE_MEMBERS[member].get("ghigau"):
                    ghigau_invoked = True

        if non_consenting:
            resolution_type = "deferred"
            if ghigau_invoked:
=======
        non_consenting = []
        standing_dissent = []
        ghigau_invoked = False

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

        if non_consenting:
            resolution_type = "deferred"
            if ghigau_invoked:
>>>>>>> REPLACE
```

### Change 2: Add standing_dissent resolution path

```
<<<<<<< SEARCH
        else:
            resolution_type = "consensus"
            resolution = "The tribe speaks with one voice. Consensus reached."
=======
        elif standing_dissent:
            resolution_type = "consensus_with_standing_dissent"
            names = ", ".join(sd["member"] for sd in standing_dissent)
            resolution = (
                f"Consensus reached with standing dissent from: {names}. "
                "Their challenge is honored as archetype function — "
                "the voice that asks 'but what if we are wrong?' "
                "strengthens the decision it tests."
            )
        else:
            resolution_type = "consensus"
            resolution = "The tribe speaks with one voice. Consensus reached."
>>>>>>> REPLACE
```

### Change 3: Pass combined lists to _resolve

```
<<<<<<< SEARCH
        return self._resolve(
            session_hash, resolution, resolution_type, non_consenting
        )
=======
        return self._resolve(
            session_hash, resolution, resolution_type,
            non_consenting + standing_dissent
        )
>>>>>>> REPLACE
```

## Verification
1. Normal non-consent still defers
2. Ghigau non-consent still defers with grandmother message
3. Standing dissent (`standing_dissent: True` in response) → `consensus_with_standing_dissent`
4. Mix of standing_dissent + real non-consent still defers (real non-consent takes priority)
