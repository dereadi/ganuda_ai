# Jr Instruction: Draft Tiered Support Model with Council-Assisted Diagnostics

**Task ID:** #1197
**Date:** March 9, 2026
**Priority:** 2 (Business scaffolding — support model)
**Type:** Document creation (no code changes)

## Context

The Cherokee AI Federation has a unique advantage for customer support: the cluster's own AI
council can participate in diagnosing issues. When a customer hits a problem, the council
specialists (Spider for dependency analysis, Coyote for anomaly detection, Owl for tech debt)
can review error thermals and suggest fixes before a human even looks at the ticket. This is
"council-assisted diagnostics" — the product helps debug itself.

This support model must cover Community (free), Professional (paid), and Enterprise (premium)
tiers to match the licensing framework (#1195).

## Task

Create a support model document at `/ganuda/docs/business/SUPPORT-MODEL-MAR09-2026.md`.

## Steps

### Step 1: Create the document skeleton

Create file `/ganuda/docs/business/SUPPORT-MODEL-MAR09-2026.md` with:

```
# Cherokee AI Federation — Tiered Support Model

**Date:** March 9, 2026
**Task:** #1197
**Status:** Draft
**Related:** Licensing Framework (#1195)

## Overview
## Support Tiers
### Tier 1: Community Support
### Tier 2: Professional Support
### Tier 3: Enterprise Support
## Council-Assisted Diagnostics
## Escalation Paths
## SLA Definitions
## Support Tooling
## Metrics and Reporting
## Open Questions
```

### Step 2: Populate Tier 1 — Community Support

Document the free support tier:

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

**Response expectation:** Best-effort. Community contributions welcome. Critical security
issues get priority regardless of tier.

### Step 3: Populate Tier 2 — Professional Support

Document the paid support tier:

**Channels:**
- Email support (support@ganuda.us)
- Private GitHub issue label (professional-support)
- Council-assisted diagnostics (automated first pass)

**What is included:**
- 48-hour SLA for initial response (business hours, M-F)
- Council-assisted diagnostics: customer's own cluster runs a diagnostic council session
  on the error, generates a structured report, attaches it to the support ticket automatically
- Up to 5 support incidents per month included
- Access to INTERNAL documentation (architecture details, advanced configuration)
- Quarterly "Owl Pass" review: automated health/debt assessment of customer's cluster

**Council-Assisted Diagnostics flow for Professional:**
1. Customer triggers diagnostic: `ganuda support diagnose --issue "description"`
2. Council session runs: Spider checks dependencies, Coyote flags anomalies, Owl reviews
   recent changes, Turtle checks for reversibility
3. Diagnostic report written to thermal memory with tag `support_diagnostic`
4. Report auto-attached to support ticket (if email integration configured)
5. Human support reviews diagnostic report, responds within SLA

**Escalation:** If council diagnostic is insufficient, escalate to human support engineer.
Professional tier gets one live debugging session per quarter.

### Step 4: Populate Tier 3 — Enterprise Support

Document the premium support tier:

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
- Council-assisted diagnostics with FULL specialist access: support team can invoke
  customer's council directly (with customer permission) to diagnose in real-time
- Quarterly architecture review: 1-hour session reviewing cluster health, growth patterns,
  thermal memory trends, governance drift
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

### Step 5: Document Escalation Paths

Create an escalation flow:

```
Level 0: Self-serve docs / FAQ / community forum
    |
    v (unresolved after self-serve attempt)
Level 1: Council-assisted diagnostics (automated)
    |
    v (diagnostic insufficient or customer needs human help)
Level 2: Support engineer review (within SLA)
    |
    v (requires architecture expertise or code change)
Level 3: Senior engineer / development team
    |
    v (critical: data loss risk, security breach, multi-cluster impact)
Level 4: Emergency response — Chief + senior team, all-hands
```

For each level, document:
- Who handles it
- Target resolution time
- What triggers escalation to next level
- What information must be gathered before escalating

### Step 6: Define SLA Terms

Create an SLA table:

| Priority | Definition | Professional SLA | Enterprise SLA |
|---|---|---|---|
| P1 - Critical | System down, data loss risk | 48hr response | 4hr response, 24hr resolution target |
| P2 - High | Major feature broken, workaround exists | 48hr response | 24hr response |
| P3 - Medium | Minor feature issue, low impact | Best effort | 48hr response |
| P4 - Low | Question, enhancement request | Best effort | Best effort |

Define:
- **Response** = first human acknowledgment with initial assessment
- **Resolution target** = fix deployed or workaround provided (not guaranteed, target)
- **Business hours** = Monday-Friday, 8AM-6PM CT (Professional), 24/7 for P1 (Enterprise)
- **SLA credits** = if SLA missed, credit toward next billing cycle (percentage TBD)

### Step 7: Document Support Tooling

Specify the tools needed to run this support model:

- **Ticket system:** GitHub Issues (Community) + email-to-issue bridge (Professional/Enterprise)
- **Council diagnostic CLI:** `ganuda support diagnose` command (to be built)
- **Diagnostic report format:** Structured markdown with specialist findings, confidence scores
- **Access token system:** Time-limited, scoped tokens for Enterprise remote debugging
- **Metrics dashboard:** Track SLA compliance, diagnostic hit rate, escalation frequency

### Step 8: Define Metrics and Reporting

Specify what to measure:

- **Diagnostic hit rate:** % of issues where council-assisted diagnostics provided the fix
  without human intervention (target: 40% within 6 months)
- **SLA compliance:** % of tickets responded to within SLA (target: 95%)
- **Escalation rate:** % of tickets that escalate beyond Level 2 (target: <15%)
- **Customer satisfaction:** Post-resolution survey (target: 4.5/5)
- **Mean time to resolution:** Track by priority level and tier

## Acceptance Criteria

- [ ] Document exists at `/ganuda/docs/business/SUPPORT-MODEL-MAR09-2026.md`
- [ ] All three support tiers are fully described with specific offerings
- [ ] Council-assisted diagnostics flow is described for both Professional and Enterprise
- [ ] Escalation path is documented with 5 levels
- [ ] SLA table covers all 4 priority levels for Professional and Enterprise
- [ ] Support tooling section specifies what needs to be built
- [ ] Metrics section defines targets for at least 4 KPIs
- [ ] Document is at least 1000 words

## Constraints

- **No code changes.** This is a document-creation task.
- Create parent directory `/ganuda/docs/business/` if it does not exist.
- SLA times should be realistic for a small team — do not promise what we cannot deliver.
- Council-assisted diagnostics must respect customer data privacy — diagnostics stay local
  to the customer's cluster unless they explicitly share.
- Reference existing specialist roles by name (Spider, Coyote, Owl, Turtle, etc.).
- Leave pricing placeholders — Chief decides support pricing.
