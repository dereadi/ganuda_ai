# Cherokee AI Federation — Tiered Support Model

**Date:** March 9, 2026
**Task:** #1197
**Status:** Draft
**Related:** Licensing Framework (#1195)

## Overview
The Cherokee AI Federation offers a tiered support model designed to cater to different customer needs, from community-driven support to premium enterprise-level assistance. This model leverages the unique capabilities of the AI council to provide council-assisted diagnostics, ensuring that customers receive timely and effective support.

## Support Tiers
### Tier 1: Community Support
**Channels:**
- GitHub Issues (public, searchable, community-contributed)
- Community forum / GitHub Discussions
- Self-serve documentation (see #1198 Public Docs Strategy)
- FAQ and troubleshooting guide

**What is included:**
- Bug reports accepted and triaged (best-effort, no SLA)
- Community members can answer each other
- Monthly community office hours (optional, Chief or team member)
- Access to all PUBLIC and AUDITABLE documentation

**What is NOT included:**
- Direct email/chat support
- Guaranteed response times
- Council-assisted diagnostics
- Private issue handling

**Response expectation:** Best-effort. Community contributions welcome. Critical security issues get priority regardless of tier.

### Tier 2: Professional Support
**Channels:**
- Email support (support@ganuda.us)
- Private GitHub issue label (professional-support)
- Council-assisted diagnostics (automated first pass)

**What is included:**
- 48-hour SLA for initial response (business hours, M-F)
- Council-assisted diagnostics: customer's own cluster runs a diagnostic council session on the error, generates a structured report, attaches it to the support ticket automatically
- Up to 5 support incidents per month included
- Access to INTERNAL documentation (architecture details, advanced configuration)
- Quarterly "Owl Pass" review: automated health/debt assessment of customer's cluster

**Council-Assisted Diagnostics flow for Professional:**
1. Customer triggers diagnostic: `ganuda support diagnose --issue "description"`
2. Council session runs: Spider checks dependencies, Coyote flags anomalies, Owl reviews recent changes, Turtle checks for reversibility
3. Diagnostic report written to thermal memory with tag `support_diagnostic`
4. Report auto-attached to support ticket (if email integration configured)
5. Human support reviews diagnostic report, responds within SLA

**Escalation:** If council diagnostic is insufficient, escalate to human support engineer. Professional tier gets one live debugging session per quarter.

### Tier 3: Enterprise Support
**Channels:**
- Dedicated Slack/Teams channel with support team
- Phone support for critical issues
- Direct specialist council access for debugging
- Named support engineer assigned to account

**What is included:**
- 4-hour SLA for critical issues (P1: system down, data at risk)
- 24-hour SLA for high issues (P2: degraded functionality)
- 48-hour SLA for medium/low issues (P3/P4)
- Unlimited support incidents
- Council-assisted diagnostics with FULL specialist access: support team can invoke customer's council directly (with customer permission) to diagnose in real-time
- Quarterly architecture review: 1-hour session reviewing cluster health, growth patterns, thermal memory trends, governance drift
- Priority feature requests (reviewed in next sprint planning)
- Early access to new features and migration support
- Custom specialist configuration assistance

**Direct Council Access flow for Enterprise:**
1. Customer grants temporary access token (time-limited, scoped)
2. Support engineer connects to customer's council gateway
3. Runs diagnostic session with full specialist panel
4. Specialists analyze thermals, vote histories, Jr task failures, Fire Guard history
5. Live findings shared in dedicated channel
6. Follow-up action items tracked in customer's own Jr task queue (if desired)

## Council-Assisted Diagnostics
The AI council consists of specialists like Spider, Coyote, Owl, and Turtle, who can analyze various aspects of the system to diagnose issues. This process is automated for Professional and Enterprise tiers, providing structured reports that help resolve issues more efficiently.

## Escalation Paths