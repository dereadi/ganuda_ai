# Jr Instruction: Add Crane to longhouse.py TRIBE_MEMBERS

## Context
Crane (External Governance/Diplomacy) was ratified in 3 Longhouse votes (1f8f9548, e16b9755, fa5a89fe) on March 6, 2026. Crane is already in specialist_council.py OUTER_COUNCIL and SPECIALIST_BACKENDS, but was never added to longhouse.py TRIBE_MEMBERS. This means Crane cannot convene or speak in Longhouse sessions.

## Task

### Step 1: Add Crane to TRIBE_MEMBERS dict

File: `/ganuda/lib/longhouse.py`

Find the TRIBE_MEMBERS dict, specifically after the Deer entry in the Outer Council section:

```
<<<<<<< SEARCH
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Otter":                {"role": "outer_council", "ghigau": False},  # unborn — future seat
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn — future seat
=======
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Crane":                {"role": "outer_council", "ghigau": False},  # Diplomat, ratified Mar 6 (1f8f9548, e16b9755, fa5a89fe)
    "Otter":                {"role": "outer_council", "ghigau": False},  # Legal/Regulatory, born Mar 6
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn — future seat
>>>>>>> REPLACE
```

## Acceptance Criteria
- `Crane` exists in TRIBE_MEMBERS with role=outer_council, ghigau=False
- Crane can convene a Longhouse session without ValueError
- Crane can speak in a Longhouse session without ValueError
- Existing members unaffected

## Dependencies
- None. Standalone fix.
- Kanban #2055, Jr task #1187.
