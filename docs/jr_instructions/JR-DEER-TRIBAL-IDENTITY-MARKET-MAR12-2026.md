# JR INSTRUCTION: Deer Market Assessment — Tribal Member Identity Management

**Task**: Assess the market need, size, and competitive landscape for sovereign tribal member identity infrastructure
**Priority**: P1 — Longhouse c5ff6edd041beb9e resolution #3 (unanimous 9/9)
**Date**: 2026-03-12
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: None — parallel with Otter legal brief and Crane outreach map
**Longhouse Vote**: c5ff6edd041beb9e (unanimous, 9 voices, 0 dissent)

## Problem Statement

574 federally recognized tribes in the US. ~3.7 million enrolled tribal members. Each tribe manages enrollment and identity independently. The SAVE Act would create a new compliance requirement (place-of-birth on tribal IDs) that no known tribal ID system currently meets. The CLOUD Act means tribal member data on commercial cloud is subject to federal subpoena.

What is the actual market for sovereign tribal identity infrastructure? Who currently serves this space? What do they charge? What are the pain points? Is there pull?

## What You're Building

A market assessment document. Deer's domain: business intelligence, competitive landscape, sizing, pricing.

### Section 1: Current State of Tribal Enrollment Systems

Research:
- How do tribes currently manage enrollment? (Paper, spreadsheets, custom software, vendor solutions?)
- Which vendors serve this space? (Research: tribal enrollment software, tribal ID systems, tribal membership management)
- What do they charge? (Per-tribe licensing, per-member, SaaS?)
- What are the common complaints? (Vendor lock-in, data access, customization limits, cost, sovereignty concerns)
- How many tribes issue their own IDs? What does that process look like?

### Section 2: The SAVE Act Demand Signal

- If SAVE Act passes: 574 tribes need place-of-birth on IDs. What's the upgrade cost per tribe with current vendors?
- If SAVE Act fails: the underlying need for modern enrollment infrastructure remains. What drives that need? (Federal program eligibility, census, healthcare, education benefits)
- Arizona Prop 200 already requires proof of citizenship for state elections — what happened to tribal ID systems there? Did any tribe upgrade? At what cost?

### Section 3: Sovereign Hosting Market

- Connect to existing Jr #1287 research (FrostByte/Frode Nilssen, Sovereign Cloud Stack)
- What is the market for hosting that is NOT subject to CLOUD Act?
- Tribal sovereign immunity as legal substrate — is anyone offering this?
- Cherokee Nation Businesses, Mohegan Digital, other tribal enterprise arms in tech — what exists?

### Section 4: Competitive Landscape

Map existing players:
- **Tribal enrollment software vendors**: Who are they? (Research terms: "tribal enrollment management system", "tribal membership database", "tribal ID card system")
- **Government ID vendors**: L-1 Identity Solutions (now IDEMIA), Thales, etc. — do any serve tribal markets?
- **Sovereign cloud providers**: FrostByte, Sovereign Cloud Stack, tribal enterprise IT arms
- **Open source alternatives**: Any open-source tribal enrollment systems?

For each competitor: product, pricing (if available), tribal customers (if public), strengths, weaknesses.

### Section 5: Market Sizing

- 574 federally recognized tribes (US)
- 630+ First Nations in Canada (parallel market)
- ~3.7M enrolled tribal members in US
- Segment by tribe size: large (Cherokee 450K, Navajo 400K), medium (10K-100K), small (<10K)
- Pricing model analysis: what could sovereign identity infrastructure cost per tribe? Per member?
- Total addressable market estimate (even rough order of magnitude)

### Section 6: Go-to-Market Considerations

- Coyote condition: market pull required. What evidence exists of tribes actively seeking new identity infrastructure?
- Trust barrier: tribes are understandably cautious about outside tech vendors. How have successful vendors built trust?
- Consortium model: could multiple tribes share infrastructure (like NCAI's consortium model for advocacy)?
- Cherokee Nation as first partner: advantages (Chief's nation, largest tribe, existing tech enterprise) and risks (perception of favoritism)

## Sources to Research

- Bureau of Indian Affairs tribal directory (bia.gov)
- NCAI publications on tribal data sovereignty
- Native Governance Center
- Tribal enrollment vendor websites (search for them)
- FrostByte / Frode Nilssen (existing federation research from Jr #1287)
- Cherokee Nation Businesses (cnb.com)
- Published articles on tribal identity challenges
- GAO reports on tribal programs and data management

## Constraints

- **Deer's role**: Market intelligence. Numbers, competitors, opportunities. Not legal analysis (Otter) or outreach (Crane).
- **Public sources only.** No proprietary data, no scraping tribal enrollment records.
- **DC-9**: This is research, not a proposal. Don't spend where we haven't earned.
- **Respect sovereignty**: Each tribe is a separate nation. Don't aggregate as if they're one market.
- **Coyote condition**: Identify evidence of market pull, not just our assumption that the market exists.

## Target Files

- `/ganuda/docs/research/DEER-TRIBAL-IDENTITY-MARKET-ASSESSMENT.md` — market assessment (CREATE)
- Thermal entries for key findings

## Acceptance Criteria

- At least 3 existing tribal enrollment/ID vendors identified with product descriptions
- Market size estimate (order of magnitude) for US tribal identity infrastructure
- SAVE Act demand signal quantified (cost to upgrade per tribe, if available)
- Canadian parallel market noted
- Go-to-market considerations documented
- Evidence of market pull (or lack thereof) explicitly addressed for Coyote
- Thermalized

## DO NOT

- Contact vendors, tribes, or organizations (Crane's role)
- Make revenue projections for the federation (premature)
- Recommend a specific product or architecture (Spider/engineering's role)
- Treat tribes as a monolithic market — they are 574 separate nations
- Store any PII or tribal member data
