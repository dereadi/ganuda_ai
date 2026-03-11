# Cherokee AI Federation — Three-Tier Licensing Framework

**Date:** March 9, 2026
**Task:** #1195
**Status:** Draft
**Informed By:** Open-Core Licensing Research (#1194)

## Overview

This document outlines the three-tier licensing framework for the Cherokee AI Federation. The framework is designed to balance openness with sustainable revenue, ensuring that the core principles of the federation are upheld while providing value to different user segments.

## Tier 1: Community (Open)

**License:** Apache 2.0

### What is Included (Give Away Freely):
- Core governance primitives (council voting mechanics, basic longhouse pattern)
- Thermal memory basics (store/retrieve, temperature scoring, basic decay)
- Single-node deployment scripts
- Basic council specialist framework (define specialists, route queries)
- Fire Guard health checking (basic service monitoring)
- CLI tools for interacting with the council
- Documentation for all Community-tier features

### What is NOT Included:
- Advanced memory features (valence, canonical flags, three-body interaction)
- Multi-node federation
- Specialist training/customization
- Observation levels / drift detection

### Rationale:
Give enough to be useful and build community. The governance pattern itself is the advertisement — once teams see council voting work, they want the advanced features.

## Tier 2: Professional

**License:** BSL 1.1 (converts to Apache 2.0 after 3 years) or similar delayed-open license.

### What is Included (in Addition to Community):
- Full specialist council with all 12 seats (Inner + Outer Council)
- Advanced thermal memory: valence scoring, canonical/narrative split, three-body memory (DC-14)
- Drift-aware observation (DC-5, Coyote As Cam)
- Jr task execution framework (task queue, decomposition, execution, verification)
- Multi-node deployment within a single cluster (up to 6 nodes)
- Specification engineering layer (five primitives)
- Dawn mist / scheduled ritual framework
- Slack/notification integration
- Safety canary and credential scanning

### Rationale:
This is where the real IP lives — the governance topology that makes the cluster self-managing. BSL protects against cloud providers offering it as a managed service while ensuring it goes fully open after the conversion period.

## Tier 3: Enterprise

**License:** Proprietary / Commercial

### What is Included (in Addition to Professional):
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

### Rationale:
Enterprise customers need federation, customization, and guarantees. This is high-touch, high-value. Revenue funds continued open development.

## Tier Comparison Matrix

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

## Upgrade Path

### Community to Professional:
- **License key activation**: No re-deployment needed — Professional features are present but gated. Key unlocks them. Data and configuration preserved.

### Professional to Enterprise:
- **Engagement with sales/deployment team**: Federation setup requires architecture review. Migration tooling provided.

### Downgrade Path:
- **Professional features deactivate gracefully**: Data remains accessible in read-only mode for 90 days. No data loss.

## License Terms Summary

### Community (Apache 2.0)
- **What you CAN do**: Use, modify, distribute, and sublicense the software.
- **What you CANNOT do**: None.
- **Attribution requirements**: Include the Apache 2.0 license text and copyright notice.
- **Redistribution rules**: Must include the original license and copyright notice.
- **Conversion timeline**: N/A

### Professional (BSL 1.1)
- **What you CAN do**: Use, modify, and distribute the software for up to 3 years.
- **What you CANNOT do**: Distribute the software as a commercial product without converting to Apache 2.0 after 3 years.
- **Attribution requirements**: Include the BSL 1.1 license text and copyright notice.
- **Redistribution rules**: Must include the original license and copyright notice.
- **Conversion timeline**: Converts to Apache 2.0 after 3 years.

### Enterprise (Proprietary / Commercial)
- **What you CAN do**: Use the software according to the terms of the commercial license.
- **What you CANNOT do**: Modify, distribute, or sublicense the software without explicit permission from the Cherokee AI Federation.
- **Attribution requirements**: None.
- **Redistribution rules**: None.
- **Conversion timeline**: N/A

## Open Questions
- Pricing for Professional and Enterprise tiers
- BSL conversion period (3 years or longer?)
- Additional compliance packages (GDPR, CCPA, etc.)
- Specific terms for white-label/OEM licensing