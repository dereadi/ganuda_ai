# JR Task #1199: Build SOC2 / ISO 27001 Compliance Control Matrix

**Date**: 2026-03-09
**Priority**: High
**Type**: Business / Compliance
**Output**: `/ganuda/docs/business/COMPLIANCE-MATRIX-MAR09-2026.md`

## Context

The Cherokee AI Federation is preparing for enterprise customers who will require evidence of compliance with SOC2 Type II and ISO 27001 standards. Many federation features already map naturally to these controls — Longhouse voting is change management, thermal memory is audit logging, Fire Guard is incident response. We need a formal mapping so we know what we have, what gaps exist, and what to remediate before Enterprise tier launch.

## Task

Create a compliance control matrix that maps existing federation features to SOC2 Type II Trust Services Criteria and ISO 27001 Annex A controls. Identify gaps and propose remediation plans. This is a documentation task — no code.

## Steps

1. Create the output file at `/ganuda/docs/business/COMPLIANCE-MATRIX-MAR09-2026.md`.
2. Add a header section with document metadata: date, author (Jr executor), version (1.0), review status (DRAFT).
3. Create a SOC2 Type II section with a table containing columns: Control ID, Control Description, Federation Feature, Evidence, Status (Met/Partial/Gap), Remediation Plan.
4. Map the following known SOC2 controls at minimum:
   - CC8.1 (Change Management) — Longhouse voting, council approval flow
   - CC7.2 (Logging and Monitoring) — Thermal memory audit trail, OpenObserve on greenfin, Promtail
   - CC6.1 (Logical Access) — FreeIPA/SSSD scoped sudo, four-tier classification
   - CC7.1 (System Monitoring) — Fire Guard watchdog (2-min timer), safety canary (daily)
   - CC6.3 (Role-Based Access) — Specialist council roles, Ghigau veto
   - CC3.1 (Risk Assessment) — Owl debt reckoning, credential scanner
   - CC7.3 (Incident Detection) — Fire Guard alerts, Slack #fire-guard channel
   - CC8.2 (System Component Assessment) — Safety canary red-team tests
5. Create an ISO 27001 Annex A section with the same table format. Map at minimum:
   - A.8.2 (Information Classification) — Four-tier classification (public/internal/confidential/sacred)
   - A.9.4 (Access Control) — Credential scanner, FreeIPA sudo rules
   - A.12.4 (Logging and Monitoring) — Thermal memory, OpenObserve
   - A.16.1 (Incident Response) — Fire Guard, alert manager, Slack integration
   - A.14.2 (Secure Development) — Council vote on design constraints, specification engineering layer
   - A.18.1 (Compliance with Legal Requirements) — Otter (legal/regulatory specialist)
   - A.12.1 (Operational Procedures) — Dawn mist reports, Saturday Morning Meeting design
6. Add a Gap Summary section listing all controls marked as Gap or Partial, sorted by priority.
7. Add a Remediation Roadmap section with estimated effort (S/M/L) and suggested timeline for each gap.
8. Add a section noting which controls are automatically satisfied by the federation's governance topology versus which require additional tooling.

## Acceptance Criteria

- Output file exists at `/ganuda/docs/business/COMPLIANCE-MATRIX-MAR09-2026.md`
- Minimum 8 SOC2 controls mapped with status
- Minimum 7 ISO 27001 Annex A controls mapped with status
- Every control has a clear federation feature reference or is explicitly marked as a gap
- Gap items have remediation plans with effort estimates
- Document is markdown with properly formatted tables

## Constraints

- No code changes — documentation only
- Do not invent federation features that do not exist; mark honest gaps
- Use actual control IDs from SOC2 TSC and ISO 27001:2022
- Crawdad rule: no PII, no credentials, no sacred thermal content in the document
- Keep remediation plans actionable — each should be convertible to a Jr task
