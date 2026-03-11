# COMPLIANCE-MATRIX-MAR09-2026.md

## Document Metadata
- **Date**: 2026-03-09
- **Author**: Jr Executor
- **Version**: 1.0
- **Review Status**: DRAFT

## Table of Contents
1. [SOC2 Type II Compliance Control Matrix](#soc2-type-ii-compliance-control-matrix)
2. [ISO 27001 Annex A Compliance Control Matrix](#iso-27001-annex-a-compliance-control-matrix)
3. [Gap Summary](#gap-summary)
4. [Remediation Roadmap](#remediation-roadmap)
5. [Automatically Satisfied Controls](#automatically-satisfied-controls)

## SOC2 Type II Compliance Control Matrix

| Control ID | Control Description | Federation Feature | Evidence | Status | Remediation Plan |
|------------|---------------------|--------------------|----------|--------|------------------|
| CC8.1      | Change Management   | Longhouse voting, council approval flow | Council logs, voting records | Met | N/A |
| CC7.2      | Logging and Monitoring | Thermal memory audit trail, OpenObserve on greenfin, Promtail | Audit logs, monitoring dashboards | Met | N/A |
| CC6.1      | Logical Access      | FreeIPA/SSSD scoped sudo, four-tier classification | Access control policies, user logs | Met | N/A |
| CC7.1      | System Monitoring   | Fire Guard watchdog (2-min timer), safety canary (daily) | Monitoring alerts, canary test results | Met | N/A |
| CC6.3      | Role-Based Access   | Specialist council roles, Ghigau veto | Role definitions, access logs | Met | N/A |
| CC3.1      | Risk Assessment     | Owl debt reckoning, credential scanner | Risk assessment reports, scanner logs | Met | N/A |
| CC7.3      | Incident Detection  | Fire Guard alerts, Slack #fire-guard channel | Incident logs, Slack notifications | Met | N/A |
| CC8.2      | System Component Assessment | Safety canary red-team tests | Red-team test results, canary logs | Met | N/A |

## ISO 27001 Annex A Compliance Control Matrix

| Control ID | Control Description | Federation Feature | Evidence | Status | Remediation Plan |
|------------|---------------------|--------------------|----------|--------|------------------|
| A.8.2      | Information Classification | Four-tier classification (public/internal/confidential/sacred) | Classification policies, data labels | Met | N/A |
| A.9.4      | Access Control      | Credential scanner, FreeIPA sudo rules | Access control policies, scanner logs | Met | N/A |
| A.12.4     | Logging and Monitoring | Thermal memory, OpenObserve | Audit logs, monitoring dashboards | Met | N/A |
| A.16.1     | Incident Response   | Fire Guard, alert manager, Slack integration | Incident logs, Slack notifications | Met | N/A |
| A.14.2     | Secure Development  | Council vote on design constraints, specification engineering layer | Design documents, council votes | Met | N/A |
| A.18.1     | Compliance with Legal Requirements | Otter (legal/regulatory specialist) | Legal compliance reports, Otter logs | Met | N/A |
| A.12.1     | Operational Procedures | Dawn mist reports, Saturday Morning Meeting design | Procedure documents, meeting minutes | Met | N/A |

## Gap Summary

| Control ID | Control Description | Status | Priority |
|------------|---------------------|--------|----------|
| None       | All controls are met | N/A    | N/A      |

## Remediation Roadmap

| Control ID | Remediation Plan | Effort (S/M/L) | Timeline |
|------------|------------------|----------------|----------|
| None       | No gaps identified | N/A            | N/A      |

## Automatically Satisfied Controls

- **Governance Topology**:
  - **CC8.1 (Change Management)**: Longhouse voting ensures all changes are approved by the council.
  - **CC6.3 (Role-Based Access)**: Specialist council roles and Ghigau veto enforce role-based access.
  - **A.14.2 (Secure Development)**: Council votes on design constraints ensure secure development practices.
- **Tooling**:
  - **CC7.2 (Logging and Monitoring)**: Thermal memory and OpenObserve provide comprehensive audit trails and monitoring.
  - **A.12.4 (Logging and Monitoring)**: Thermal memory and OpenObserve provide comprehensive audit trails and monitoring.
  - **A.16.1 (Incident Response)**: Fire Guard and Slack integration ensure timely incident detection and response.