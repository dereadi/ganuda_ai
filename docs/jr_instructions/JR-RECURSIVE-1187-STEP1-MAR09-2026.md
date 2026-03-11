# [RECURSIVE] Add Crane to longhouse.py TRIBE_MEMBERS - Step 1

**Parent Task**: #1187
**Auto-decomposed**: 2026-03-09T22:37:59.886550
**Original Step Title**: Add Crane to TRIBE_MEMBERS dict

---

### Step 1: Add Crane to TRIBE_MEMBERS dict

File: `/ganuda/lib/longhouse.py`

Find the TRIBE_MEMBERS dict, specifically after the Deer entry in the Outer Council section:

```
<<<<<<< SEARCH
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Otter":                {"role": "outer_council", "ghigau": False},  # unborn -- future seat
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn -- future seat
=======
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Crane":                {"role": "outer_council", "ghigau": False},  # Diplomat, ratified Mar 6 (1f8f9548, e16b9755, fa5a89fe)
    "Otter":                {"role": "outer_council", "ghigau": False},  # Legal/Regulatory, born Mar 6
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn -- future seat
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
