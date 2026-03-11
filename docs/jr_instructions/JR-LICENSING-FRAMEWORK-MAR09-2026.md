# Jr Instruction: Draft Three-Tier Licensing Framework Document

**Task ID:** #1195
**Date:** March 9, 2026
**Priority:** 2 (Business scaffolding — framework)
**Type:** Document creation (no code changes)
**Depends On:** #1194 (Open-Core Licensing Research) — read that document first

## Context

The Cherokee AI Federation needs a licensing framework that balances openness with sustainable
revenue. Our architecture has natural tier boundaries: basic governance primitives are simple
enough to give away; advanced features like valence memory, drift-aware observation, and
multi-cluster federation represent significant IP. The framework must reflect our values
(DC-6 Gradient Principle — specialization is gravity, not boundary) while protecting what
funds continued development.

## Task

Create a three-tier licensing framework document at
`/ganuda/docs/business/LICENSING-FRAMEWORK-MAR09-2026.md`.

## Steps

### Step 1: Create the document with header and overview

Create file `/ganuda/docs/business/LICENSING-FRAMEWORK-MAR09-2026.md` with:

```
# Cherokee AI Federation — Three-Tier Licensing Framework

**Date:** March 9, 2026
**Task:** #1195
**Status:** Draft
**Informed By:** Open-Core Licensing Research (#1194)

## Overview
## Tier 1: Community (Open)
## Tier 2: Professional
## Tier 3: Enterprise
## Tier Comparison Matrix
## Upgrade Path
## License Terms Summary
## Open Questions
```

### Step 2: Populate Tier 1 — Community (Open)

**License:** Apache 2.0

What is included (give away freely):

- Core governance primitives (council voting mechanics, basic longhouse pattern)
- Thermal memory basics (store/retrieve, temperature scoring, basic decay)
- Single-node deployment scripts
- Basic council specialist framework (define specialists, route queries)
- Fire Guard health checking (basic service monitoring)
- CLI tools for interacting with the council
- Documentation for all Community-tier features

What is NOT included:

- Advanced memory features (valence, canonical flags, three-body interaction)
- Multi-node federation
- Specialist training/customization
- Observation levels / drift detection

Rationale: Give enough to be useful and build community. The governance pattern itself is the
advertisement — once teams see council voting work, they want the advanced features.

### Step 3: Populate Tier 2 — Professional

**License:** BSL 1.1 (converts to Apache 2.0 after 3 years) or similar delayed-open license.

What is included (in addition to Community):

- Full specialist council with all 12 seats (Inner + Outer Council)
- Advanced thermal memory: valence scoring, canonical/narrative split, three-body memory (DC-14)
- Drift-aware observation (DC-5, Coyote As Cam)
- Jr task execution framework (task queue, decomposition, execution, verification)
- Multi-node deployment within a single cluster (up to 6 nodes)
- Specification engineering layer (five primitives)
- Dawn mist / scheduled ritual framework
- Slack/notification integration
- Safety canary and credential scanning

Rationale: This is where the real IP lives — the governance topology that makes the cluster
self-managing. BSL protects against cloud providers offering it as managed service while
ensuring it goes fully open after the conversion period.

### Step 4: Populate Tier 3 — Enterprise

**License:** Proprietary / Commercial

What is included (in addition to Professional):

- Multi-cluster federation (multiple independent clusters coordinating)
- Custom specialist training (bring your own specialists, fine-tune council behavior)
- Cross-cluster thermal memory sharing with PII controls
- Enterprise SSO/LDAP integration (FreeIPA, Okta, Azure AD)
- SLA-backed support (see Support Model #1197)
- Dedicated deployment engineering
- Quarterly architecture reviews with the development team
- Priority feature requests
- White-label / OEM licensing options
- Compliance packages (SOC2 readiness, HIPAA considerations)

Rationale: Enterprise customers need federation, customization, and guarantees. This is
high-touch, high-value. Revenue funds continued open development.

### Step 5: Create Tier Comparison Matrix

Add a markdown table comparing all three tiers across these dimensions:

| Feature | Community | Professional | Enterprise |
|---|---|---|---|
| License | Apache 2.0 | BSL 1.1 | Proprietary |
| Council Seats | 4 (basic) | 12 (full) | 12+ (custom) |
| Thermal Memory | Basic | Full (valence+canonical) | Full + cross-cluster |
| Nodes | 1 | Up to 6 | Unlimited |
| Clusters | 1 | 1 | Unlimited |
| Jr Task Execution | No | Yes | Yes + priority queue |
| Drift Detection | No | Yes | Yes + custom thresholds |
| Support | Community | Email (48hr SLA) | Dedicated (4hr SLA) |
| Price | Free | $X/month/node | Custom |

(Leave price as placeholder — Chief decides pricing.)

### Step 6: Document Upgrade Path

Describe how a customer moves between tiers:

1. **Community to Professional**: License key activation. No re-deployment needed — Professional
   features are present but gated. Key unlocks them. Data and configuration preserved.
2. **Professional to Enterprise**: Engagement with sales/deployment team. Federation setup requires
   architecture review. Migration tooling provided.
3. **Downgrade path**: Professional features deactivate gracefully. Data remains accessible in
   read-only mode for 90 days. No data loss.

### Step 7: Add License Terms Summary

For each tier, summarize in plain English (not legalese):

- What you CAN do
- What you CANNOT do
- Attribution requirements
- Redistribution rules
- Conversion timeline (for BSL tier)

## Acceptance Criteria

- [ ] Document exists at `/ganuda/docs/business/LICENSING-FRAMEWORK-MAR09-2026.md`
- [ ] All three tiers are fully described with specific feature lists
- [ ] Comparison matrix table is present and complete
- [ ] Upgrade/downgrade path is documented
- [ ] License terms summary is in plain English
- [ ] References to DCs (DC-6, DC-7, DC-14) are included where relevant
- [ ] Open questions section captures unresolved decisions (pricing, BSL conversion period, etc.)
- [ ] Document is at least 1000 words

## Constraints

- **No code changes.** This is a document-creation task.
- Create parent directory `/ganuda/docs/business/` if it does not exist.
- Reference the research document (#1194) for license type details — do not duplicate that content.
- Leave pricing as placeholders — Chief sets pricing, not Jrs.
- The tier boundaries should feel natural, not arbitrary. Features that depend on each other
  should be in the same tier.
