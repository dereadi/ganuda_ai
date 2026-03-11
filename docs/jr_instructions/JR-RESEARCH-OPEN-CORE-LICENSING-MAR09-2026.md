# Jr Instruction: Research Open-Core Licensing Models in AI Infrastructure

**Task ID:** #1194
**Date:** March 9, 2026
**Priority:** 2 (Business scaffolding — research)
**Type:** Research (no code changes)

## Context

The Cherokee AI Federation is exploring commercialization paths. Before drafting our own licensing
framework, we need to understand how existing AI/ML infrastructure companies handle the open-core
vs proprietary split. This research will inform Task #1195 (Licensing Framework).

Companies to examine: Elastic (Elasticsearch), MongoDB, HashiCorp (Terraform/Vault), Hugging Face,
LangChain/LangSmith, Weights & Biases, MinIO, Grafana Labs, Ollama, and others in the AI infra space.

## Task

Research existing open-core licensing models used by AI/ML infrastructure companies. Produce a
comprehensive research document at `/ganuda/docs/research/OPEN-CORE-LICENSING-RESEARCH-MAR09-2026.md`.

## Steps

### Step 1: Create the research document skeleton

Create file `/ganuda/docs/research/OPEN-CORE-LICENSING-RESEARCH-MAR09-2026.md` with the following
top-level sections:

```
# Open-Core Licensing Models in AI Infrastructure — Research

**Date:** March 9, 2026
**Task:** #1194
**Author:** Jr Researcher
**Status:** Draft

## Executive Summary
## License Types Overview
## Company Case Studies
## Revenue Model Analysis
## Risk Assessment
## Recommendations for Cherokee AI Federation
## Sources
```

### Step 2: Populate License Types Overview

Research and document these license types with a comparison table:

- **Apache 2.0** — permissive, no copyleft, patent grant
- **AGPL v3** — strong copyleft, network use triggers distribution
- **BSL (Business Source License)** — time-delayed open source (MariaDB origin)
- **SSPL (Server Side Public License)** — MongoDB's response to cloud providers
- **Apache 2.0 + Commons Clause** — restricts selling the software as-a-service
- **Elastic License v2 (ELv2)** — Elastic's custom non-compete license
- **Functional Source License (FSL)** — HashiCorp's BSL variant

For each: what it permits, what it restricts, who uses it, and known legal controversies.

### Step 3: Populate Company Case Studies

For each company, document:

1. **Elastic** — Journey from Apache 2.0 to SSPL to ELv2. What triggered each change (AWS forking).
   What stayed open vs. what went proprietary. Revenue impact.
2. **MongoDB** — SSPL creation story. Community reaction. Atlas (managed service) as revenue driver.
3. **HashiCorp** — BSL pivot (Aug 2023). Terraform fork (OpenTofu). What they kept open vs. restricted.
   Community backlash. IBM acquisition context.
4. **Hugging Face** — Apache 2.0 core, Hub as proprietary SaaS. Model hosting monetization.
5. **Grafana Labs** — AGPL for Grafana, proprietary for Grafana Cloud features. Successful open-core.
6. **LangChain** — Open framework + LangSmith (proprietary observability). Split strategy.
7. **MinIO** — AGPL for object storage, proprietary enterprise features.

### Step 4: Populate Revenue Model Analysis

Document common revenue patterns:

- Open-core with proprietary features (Grafana, Elastic)
- Open-source + managed cloud service (MongoDB Atlas, HuggingFace Hub)
- Open-source + enterprise support/SLA (Red Hat model)
- Delayed open-source / time-bomb licenses (BSL converts to open after N years)
- Dual licensing (GPL + commercial, MySQL legacy model)

Include a comparison matrix: license type vs. revenue model vs. company size vs. cloud risk.

### Step 5: Populate Risk Assessment

Document risks specific to our situation:

- **Cloud provider forking** — AWS/Azure/GCP offering managed versions without contributing back
- **Community fracture** — HashiCorp/OpenTofu scenario where license change triggers hostile fork
- **License compatibility** — AGPL contamination concerns for enterprise adopters
- **Enforcement difficulty** — cost and complexity of enforcing copyleft or custom licenses
- **Perception risk** — "bait and switch" narrative damaging brand trust

### Step 6: Populate Recommendations

Based on findings, recommend 2-3 licensing approaches that fit the Cherokee AI Federation's values:
sovereign intelligence, community-first, governance transparency. Reference DC-6 (Gradient Principle)
and DC-7 (Noyawisgi) as architectural values that should be reflected in the license structure.

## Acceptance Criteria

- [ ] Document exists at `/ganuda/docs/research/OPEN-CORE-LICENSING-RESEARCH-MAR09-2026.md`
- [ ] All 7 company case studies are populated with specifics (not generic summaries)
- [ ] License comparison table is present with at least 7 license types
- [ ] Revenue model matrix is present
- [ ] Risk assessment includes at least 5 named risks with mitigation strategies
- [ ] Recommendations section references Cherokee AI Federation architecture (DCs, governance)
- [ ] All claims cite sources (URLs, blog posts, announcements)
- [ ] Document is at least 800 words

## Constraints

- **No code changes.** This is a pure research task.
- **Use web search** to find current information — licensing landscapes change frequently.
- **Cite sources.** Every company case study should link to the relevant announcement or blog post.
- Create parent directory `/ganuda/docs/research/` if it does not exist (it should already exist).
- Do not editorialize — present facts, then recommendations clearly labeled as such.
