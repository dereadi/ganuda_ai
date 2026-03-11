# JR Task #1200: Research AI Governance Market Pricing and Competitive Analysis

**Date**: 2026-03-09
**Priority**: Medium
**Type**: Research (No Code)
**Output**: `/ganuda/docs/research/MARKET-PRICING-RESEARCH-MAR09-2026.md`

## Context

The Cherokee AI Federation is defining its three-tier pricing model (Community, Pro, Enterprise). Before setting prices, we need to understand how competitors price their AI governance, infrastructure, and platform offerings. This is a Sam Walton floor walk — survey the competition, understand what they charge and why, then position ourselves. The federation's differentiator is sovereign intelligence with built-in governance; pricing must reflect that without commoditizing it.

## Task

Research pricing models across three competitor categories and produce a competitive analysis with a recommended pricing strategy for the federation's three tiers. This is a research Jr task — no code.

## Steps

1. Create the output file at `/ganuda/docs/research/MARKET-PRICING-RESEARCH-MAR09-2026.md`.
2. Add a header section with document metadata: date, author (Jr executor), version (1.0), review status (DRAFT).
3. Research **AI Governance Tools** category. For each, document:
   - Weights & Biases: pricing model, entry price, enterprise price, tier differentiators
   - MLflow (Databricks managed): pricing model, entry price, enterprise price, tier differentiators
   - Neptune.ai: pricing model, entry price, enterprise price, tier differentiators
   - Note which features overlap with federation capabilities (experiment tracking, model registry, audit trails)
4. Research **AI Infrastructure** category. For each, document:
   - Anyscale: pricing model (per-compute-hour), entry price, enterprise features
   - Modal: pricing model (per-second compute), entry price, scale pricing
   - RunPod: pricing model (per-GPU-hour), entry price, reserved vs. spot pricing
   - Note how they handle multi-node orchestration (relevant to our federation topology)
5. Research **Enterprise AI Platforms** category. For each, document:
   - Dataiku: pricing model (per-seat + compute), entry price, enterprise price
   - H2O.ai: pricing model, open-source vs. enterprise split, enterprise price
   - Note how they handle governance features (approval workflows, audit trails, access control)
6. Create a **Pricing Model Comparison Table** with columns: Vendor, Category, Model Type (per-seat/compute/model), Entry Price, Enterprise Price, Governance Features Included.
7. Analyze **pricing patterns**: What is the market standard for per-seat vs. per-compute? Where do governance features land (base tier vs. premium)?
8. Write a **Recommended Pricing Strategy** section for the Cherokee AI Federation:
   - Community tier: What should be free? What limits?
   - Pro tier: Suggested price range, what unlocks at this tier
   - Enterprise tier: Suggested price range, what justifies the premium
   - Address the sovereign intelligence angle — customers pay for data staying on their infrastructure
9. Include a **Differentiation Summary**: What does the federation offer that none of these competitors do? (Governance topology, council voting, thermal memory, sacred data classification, air-gap capability)

## Acceptance Criteria

- Output file exists at `/ganuda/docs/research/MARKET-PRICING-RESEARCH-MAR09-2026.md`
- Minimum 8 competitors researched across 3 categories
- Each competitor has pricing model, entry price, and enterprise price documented
- Comparison table is present and properly formatted
- Recommended pricing strategy covers all three federation tiers
- Differentiation summary clearly states what competitors lack

## Constraints

- No code changes — research and documentation only
- Use publicly available pricing information; note when pricing is "contact sales" and estimate based on industry reports
- Don't round pennies — be specific about pricing where data is available
- Do not recommend free Enterprise tier — sovereign intelligence has value
- Keep the Tulip voice — state facts, let the architecture speak
