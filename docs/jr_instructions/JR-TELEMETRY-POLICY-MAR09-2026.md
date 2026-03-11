# JR Task #1201: Draft Telemetry and Phone-Home Policy Document

**Date**: 2026-03-09
**Priority**: High
**Type**: Business / Policy
**Output**: `/ganuda/docs/business/TELEMETRY-POLICY-MAR09-2026.md`

## Context

The Cherokee AI Federation's north star is sovereign intelligence for those who build it. Any telemetry or phone-home behavior must respect that sovereignty absolutely. Enterprise customers will scrutinize what data leaves their infrastructure. Community users deserve the same respect. This policy document defines what we collect, why, and how users control it. Trust is the product — telemetry must never undermine it.

## Task

Create a telemetry and phone-home policy document that defines data collection boundaries, user controls, and air-gap support. This is a policy document — no code.

## Steps

1. Create the output file at `/ganuda/docs/business/TELEMETRY-POLICY-MAR09-2026.md`.
2. Add a header section with document metadata: date, author (Jr executor), version (1.0), review status (DRAFT), classification (PUBLIC — this document itself should be publishable).
3. Write a **Philosophy** section. State the principle: sovereign intelligence means your data is yours. Telemetry exists to improve the product, never to surveil the user. Reference the north star.
4. Write a **What We Collect** section. Allowed telemetry data points:
   - Cluster health metrics (node count, uptime, service status — aggregate only)
   - Feature usage counts (number of council votes, Jr tasks executed, thermal writes — counts only, never content)
   - Error rates and error categories (crash counts, timeout counts — never stack traces containing user data)
   - Software version and update channel
   - Hardware tier (CPU/GPU class — not serial numbers or identifiers)
5. Write a **What We NEVER Collect** section. Explicitly list:
   - Thermal memory content (NEVER)
   - Sacred data or sacred thermals (NEVER)
   - PII of any kind (NEVER)
   - Council vote content or rationale (NEVER — only aggregate vote counts)
   - Prompt content, model outputs, or inference data (NEVER)
   - Credential or secret material (NEVER)
   - Network topology details beyond node count (NEVER)
6. Write a **Consent Model** section:
   - Community tier: telemetry is OFF by default (opt-in)
   - Pro tier: telemetry is configurable, OFF by default, encouraged for support purposes
   - Enterprise tier: telemetry is OFF by default, fully configurable, air-gap mode available
   - All tiers: single configuration flag to disable all telemetry (`telemetry.enabled: false`)
7. Write a **Data Handling** section:
   - Retention: 90 days maximum, then hard delete
   - Storage: Cherokee AI Federation infrastructure only (specify which node class)
   - Encryption: TLS in transit, encrypted at rest
   - Access: Only federation operations team, logged access
   - No third-party data sharing, no selling, no advertising use
8. Write a **How to Disable** section with exact configuration steps:
   - Configuration file method
   - Environment variable method
   - CLI flag method
   - Verification method (how to confirm telemetry is actually off)
9. Write an **Air-Gap Mode** section:
   - Enterprise tier feature
   - Zero network egress — no DNS lookups, no HTTP calls, no NTP to external servers
   - Updates via signed USB/offline bundle (reference update delivery system design)
   - Verification: network audit tool to prove zero egress
10. Write a **Compliance** section noting how this policy maps to: GDPR (data minimization, right to erasure), SOC2 CC6.1 (logical access), CCPA, and HIPAA (for healthcare deployments).

## Acceptance Criteria

- Output file exists at `/ganuda/docs/business/TELEMETRY-POLICY-MAR09-2026.md`
- NEVER-collect list is explicit and comprehensive
- Consent model clearly states default-off for all tiers
- Air-gap mode is fully described
- Configuration steps are specific (not vague "contact support")
- Compliance mapping references at least GDPR, SOC2, and CCPA
- Document tone is trustworthy and transparent — a customer should feel safe reading this

## Constraints

- No code changes — policy document only
- Default must be opt-OUT (off) for all tiers — this is non-negotiable
- Do not promise features that require code not yet built; mark future items as PLANNED
- Crawdad rule applies to this document itself — no real credentials or PII in examples
- This document may become public-facing; write accordingly
