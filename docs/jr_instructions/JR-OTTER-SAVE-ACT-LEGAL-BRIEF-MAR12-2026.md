# JR INSTRUCTION: Otter Legal Brief — SAVE Act Tribal ID Inconsistency

**Task**: Research and draft legal analysis of the federal inconsistency in tribal ID acceptance for voting vs employment vs travel
**Priority**: P1 — First deliverable from Longhouse c5ff6edd041beb9e (unanimous 9/9)
**Date**: 2026-03-12
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: None — this is the tip of the spear
**Longhouse Vote**: c5ff6edd041beb9e (unanimous, 9 voices, 0 dissent)

## Problem Statement

The SAVE Act (Safeguard American Voter Eligibility Act) would require proof of citizenship to register to vote. Tribal IDs, which lack a place-of-birth field, would be rejected. However, the SAME tribal IDs are currently accepted by the federal government in two other citizenship-verification contexts:

1. **TSA Real ID**: Tribal IDs are accepted for domestic air travel under Real ID Act
2. **I-9 Employment Verification**: USCIS accepts tribal IDs as dispositive proof of citizenship for employment purposes

The federal government cannot logically accept a document as proof of citizenship for employment and travel but reject it for voting. This inconsistency is the legal wedge.

## What You're Building

A legal research brief with two audiences: (1) legal challenge teams (NARF, ACLU, tribal attorneys), and (2) product requirements for sovereign identity infrastructure.

### Section 1: The Inconsistency

Research and document:
- **Real ID Act (49 USC § 30301 note)**: Which provisions accept tribal IDs? What documentation requirements exist? How was tribal ID acceptance negotiated?
- **I-9 / USCIS acceptance**: Under 8 CFR § 274a.2, tribal IDs are List B identity documents. Research the history of this acceptance — when was it added, what was the rationale?
- **SAVE Act text**: Current bill text (H.R. 22, 119th Congress). Specific provisions on acceptable documents. Where exactly does it create the inconsistency with Real ID and I-9?
- **Legal theory**: Equal protection (14th Amendment), Voting Rights Act (Section 2 disparate impact), tribal sovereignty arguments, Indian Commerce Clause

### Section 2: Tribal ID Landscape

Research:
- How many of the 574 federally recognized tribes issue tribal IDs?
- What information do tribal IDs typically contain? (Confirm: none include place-of-birth — per Jacqueline Deleón/NARF)
- What would be required for tribes to add place-of-birth to IDs? (New protocols, personnel, cost — per Deleón)
- Are there any tribes that HAVE added place-of-birth? (Deleón says none known)
- What is the estimated cost per tribe to upgrade ID systems?

### Section 3: Sovereign Identity as Solution

Frame the infrastructure angle:
- If tribes build sovereign member identity databases that include place-of-birth, the SAVE Act compliance question becomes moot
- This infrastructure also serves: enrollment management, benefits verification, census participation, federal program eligibility
- The CLOUD Act problem: tribal member data on commercial US cloud is subject to federal subpoena. Sovereign hosting is the only architecture that protects this data
- Reference: Tribal data sovereignty laws already passed by other nations (research which tribes have these)

### Section 4: Product Requirements Extract

From the legal analysis, extract concrete technical requirements:
- Data fields needed for SAVE Act compliance (place-of-birth, citizenship status, date of birth, etc.)
- Security requirements (PII protection, tribal sovereignty over data access)
- Integration points (state voter registration systems, federal verification channels)
- Audit trail requirements (who accessed what, when, for what purpose)

## Sources to Research

- **NARF (Native American Rights Fund)**: narf.org — Jacqueline Deleón is senior staff attorney, Isleta Pueblo. They have published on tribal voting rights extensively.
- **NCAI**: ncai.org — Lenny Fine Day, General Counsel. Resolutions database going back to 1944 on voting access.
- **H.R. 22 (SAVE Act)**: congress.gov — full bill text
- **Real ID Act**: DHS implementation guidance on tribal ID acceptance
- **8 CFR § 274a.2**: I-9 acceptable documents list
- **Sen. Lisa Murkowski**: Her opposition statement specifically cited Native community burden — find the statement
- **Arizona Prop 200 precedent**: Arizona already requires proof of citizenship for state elections — research how this has affected tribal voters
- **Voting Rights Act Section 2**: Disparate impact standard as applied to ID requirements
- **Shelby County v. Holder (2013)**: How the gutting of VRA preclearance enabled state-level restrictions

## Constraints

- **Otter's role**: Legal/regulatory analysis. This is research, not advocacy. Present the facts and the legal framework.
- **Coyote condition**: This research is pre-engineering. We are scouting, not building. The brief informs whether and what to build.
- **Turtle condition**: Any architecture proposed must ensure tribal data sovereignty — tribe owns data, survives federation disappearance.
- **DC-9**: Spend only what the organism earns. This is research using existing cluster resources, not billable legal work.
- **Non-partisan**: The brief analyzes legal inconsistency, not political positions. Both "the SAVE Act is wrong" and "here's how to comply" are valid framings.

## Target Files

- `/ganuda/docs/research/OTTER-SAVE-ACT-TRIBAL-ID-BRIEF.md` — the legal brief (CREATE)
- Thermal memory entries for key findings

## Acceptance Criteria

- Legal inconsistency documented with specific statute citations (Real ID Act, 8 CFR § 274a.2, SAVE Act H.R. 22)
- Tribal ID landscape summarized (how many tribes issue IDs, what they contain, cost to upgrade)
- Product requirements extracted from legal analysis (minimum 5 concrete data/security/integration requirements)
- At least 3 legal theories identified for challenging the inconsistency
- Brief is readable by both lawyers and engineers
- Thermalized

## DO NOT

- Write advocacy or position papers — this is analysis
- Contact any external organizations (that's Crane's role)
- Begin engineering work (Coyote condition)
- Store any PII or tribal member data
- Assume all tribes have the same ID systems — they don't
