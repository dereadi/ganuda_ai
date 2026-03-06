# Add Outer Council Members to Longhouse TRIBE_MEMBERS

## Context
Deer (ᎠᏫ) was born March 2 2026 (Longhouse 8cbfe8f8b804695a, unanimous). She is the first seat
of the Outer Council — Market & Business specialist. Otter (Legal/Regulatory) and Blue Jay
(HR/Talent) are future seats, unborn but acknowledged.

The Longhouse code at /ganuda/lib/longhouse.py does not yet include Outer Council members in
TRIBE_MEMBERS. Deer cannot currently speak or vote in Longhouse sessions.

Kanban: #1942 | Epic: #1941 | Long Man phase: ADAPT | Cycle: #1

## Changes

File: `/ganuda/lib/longhouse.py`

```
<<<<<<< SEARCH
    "Owl":                  {"role": "reviewer",   "ghigau": False},
}
=======
    "Owl":                  {"role": "reviewer",   "ghigau": False},
    # Outer Council (Longhouse 916bc7343be8f3c7, March 2 2026)
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Otter":                {"role": "outer_council", "ghigau": False},  # unborn — future seat
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn — future seat
}
>>>>>>> REPLACE
```

## Verification
After edit, confirm that `len(TRIBE_MEMBERS)` is 17 (was 14, adding 3).
