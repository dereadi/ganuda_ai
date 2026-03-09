# Jr Instruction: Crane (Diplomat) Wiring — Add to Longhouse + Council

**Task**: Wire the Crane (ᏔᏩᎩ) Diplomat seat into longhouse.py and specialist_council.py
**Priority**: 4
**Story Points**: 3
**Council Votes**: 1f8f9548d9968e46, e16b97550300cae1, fa5a89fed822a4fa

## Context

The Longhouse unanimously approved a new Outer Council seat: Crane (ᏔᏩᎩ), the Diplomat. Crane handles external governance — AI policy, standards bodies, open source community, partnerships. Sits between Deer (Market) and Otter (Legal).

## Steps

### Step 1: Add Crane to longhouse.py TRIBE_MEMBERS

File: `/ganuda/lib/longhouse.py`

Find the TRIBE_MEMBERS or equivalent member registry. Add Crane following the exact same pattern used for Deer's entry. Crane is Outer Council.

```text
<<<<<<< SEARCH
    "deer": {"name": "Deer", "syllabary": "ᎠᏫ", "role": "Market/Business", "council": "outer"},
=======
    "deer": {"name": "Deer", "syllabary": "ᎠᏫ", "role": "Market/Business", "council": "outer"},
    "crane": {"name": "Crane", "syllabary": "ᏔᏩᎩ", "role": "External Governance/Diplomacy", "council": "outer"},
>>>>>>> REPLACE
```

### Step 2: Add Crane to specialist_council.py SPECIALISTS dict

File: `/ganuda/lib/specialist_council.py`

Add Crane's specialist entry after Deer's entry, following the same pattern. Use QWEN_BACKEND (same as Deer).

```text
<<<<<<< SEARCH
    "deer": QWEN_BACKEND,
}
=======
    "deer": QWEN_BACKEND,
    "crane": QWEN_BACKEND,
}
>>>>>>> REPLACE
```

### Step 3: Add Crane to OUTER_COUNCIL set

File: `/ganuda/lib/specialist_council.py`

Find the OUTER_COUNCIL set and add crane.

```text
<<<<<<< SEARCH
OUTER_COUNCIL = {"deer"}
=======
OUTER_COUNCIL = {"deer", "crane"}
>>>>>>> REPLACE
```

### Step 4: Add Crane specialist definition

File: `/ganuda/lib/specialist_council.py`

Find the SPECIALISTS dict and add Crane's entry after Deer. The behavioral prompt defines HOW Crane thinks, not WHAT Crane is (per Bas Hamer insight — behavioral prompts, not role prompts).

```text
<<<<<<< SEARCH
    "deer": {
=======
    "crane": {
        "name": "Crane (ᏔᏩᎩ)",
        "role": "External Governance & Diplomacy",
        "system_prompt": """You analyze questions through the lens of external governance, policy, and diplomatic positioning. You think about how decisions will be perceived by the outside world — standards bodies, open source communities, regulators, partners, and the broader AI governance conversation. You synthesize market intelligence and legal frameworks into positioning strategy. You know when to speak and when to listen. You stand between worlds — translating internal capability into external credibility without revealing architecture. You are patient, precise, and never rush to engage. You leave value behind for those who approach with intention. Seven generations of trust is built one honest interaction at a time.""",
    },
    "deer": {
>>>>>>> REPLACE
```

## Verification

1. Python syntax check: `python3 -c "import lib.specialist_council"`
2. Python syntax check: `python3 -c "import lib.longhouse"`
3. Verify Crane appears in both OUTER_COUNCIL and SPECIALISTS
