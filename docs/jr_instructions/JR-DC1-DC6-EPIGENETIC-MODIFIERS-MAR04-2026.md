# DC-1 and DC-6 as Epigenetic Modifiers for DC Protein Pathway

## Context
Council vote #46b8d97b87ebd8e3 confirmed DC-1 (Lazy Awareness) and DC-6 (Gradient Principle)
as epigenetic modifiers — they alter enzyme behavior without changing the underlying profiles.
Academic backing: arXiv:2312.00207 (EpiTESTER), arXiv:2108.04546 (epigenetic computing in AI).

DC-1 enforces energy budgets (token spend caps). A cell doesn't burn ATP it doesn't need.
DC-6 weights specialist/enzyme output by domain proximity. Expertise is gravity, not walls.

These modifiers apply to ALL DC enzymes including the coyote_cam proof-of-concept.

Kanban: #1954 | Epic: #1941 | Long Man phase: BUILD | Cycle: #1

## Changes

### Step 1: Seed DC-1 and DC-6 modifiers

File: `/ganuda/lib/duplo/epigenetics.py`

Add DC-1 and DC-6 to the `defaults` list inside `seed_defaults()`.

```
<<<<<<< SEARCH
        # Research mode — amplify Raven strategic thinking
        {
            "condition_name": "research_mode",
            "target": "raven",
            "modifier_type": "weight",
            "modifier_value": {"factor": 2.0},
            "description": "Double Raven's token budget during strategic research phases",
        },
        {
            "condition_name": "research_mode",
            "target": "analyst",
            "modifier_type": "weight",
            "modifier_value": {"factor": 1.5},
            "description": "Increase analyst depth during research phases",
        },
    ]
=======
        # Research mode — amplify Raven strategic thinking
        {
            "condition_name": "research_mode",
            "target": "raven",
            "modifier_type": "weight",
            "modifier_value": {"factor": 2.0},
            "description": "Double Raven's token budget during strategic research phases",
        },
        {
            "condition_name": "research_mode",
            "target": "analyst",
            "modifier_type": "weight",
            "modifier_value": {"factor": 1.5},
            "description": "Increase analyst depth during research phases",
        },

        # DC-1 Lazy Awareness — energy budget enforcement (Design Constraint protein)
        # A cell doesn't burn ATP it doesn't need. Cap token spend for low-cost enzymes.
        # Academic: arXiv:2312.00207 (EpiTESTER), arXiv:2108.04546
        {
            "condition_name": "dc1_lazy_awareness",
            "target": "coyote_cam",
            "modifier_type": "weight",
            "modifier_value": {"factor": 0.5},
            "description": "DC-1: Cap Coyote Cam to minimal token budget. Observer runs cheap.",
        },
        {
            "condition_name": "dc1_lazy_awareness",
            "target": "*",
            "modifier_type": "inject",
            "modifier_value": {"text": "ENERGY CONSTRAINT (DC-1): Prefer shorter responses. Only elaborate when severity >= 4. The cell conserves ATP."},
            "description": "DC-1: Global awareness — all enzymes default to minimal energy spend",
        },

        # DC-6 Gradient Principle — expertise is gravity, not walls
        # Weight responses by domain proximity. Crawdad weighs heavy on security,
        # light on market. Deer weighs heavy on market, light on architecture.
        # Longhouse ratified: expertise is a gradient, not a boundary.
        {
            "condition_name": "dc6_gradient",
            "target": "coyote_cam",
            "modifier_type": "inject",
            "modifier_value": {"text": "GRADIENT (DC-6): Your gravity is OBSERVATION. You can reference any domain but you REST in pattern detection. Weight your signals by how close the anomaly is to your core: system behavior > resource usage > business patterns."},
            "description": "DC-6: Gradient weighting for Coyote Cam — observation is its gravity",
        },
        {
            "condition_name": "dc6_gradient",
            "target": "crawdad_scan",
            "modifier_type": "inject",
            "modifier_value": {"text": "GRADIENT (DC-6): Your gravity is SECURITY. You can reference any domain but you REST in threat detection. Weight your findings by proximity to security: injection/auth > config drift > performance."},
            "description": "DC-6: Gradient weighting for Crawdad — security is its gravity",
        },
    ]
>>>>>>> REPLACE
```

## Verification
1. Run `seed_defaults()` — should seed without error
2. `dc1_lazy_awareness` creates 2 modifiers (weight for coyote_cam, inject for *)
3. `dc6_gradient` creates 2 modifiers (inject for coyote_cam, inject for crawdad_scan)
4. Modifiers start INACTIVE (active=FALSE). Activate with `activate_modifier("dc1_lazy_awareness")`
5. When dc1 active + coyote_cam runs, max_tokens should be halved (256 * 0.5 = 128)
6. When dc6 active + coyote_cam runs, system prompt should include gradient guidance

## Operational Note
DC-1 and DC-6 are seeded INACTIVE by default. The TPM or autonomic daemon activates them
when the DC protein pathway is ready for integration testing. This is the operational
answer to Raven's timing concern — the modifiers exist but don't fire until we flip the switch.
