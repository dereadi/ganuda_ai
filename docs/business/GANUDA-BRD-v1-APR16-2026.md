# Ganuda Federation — Business Requirements Document (BRD)

## Document Control

| Item | Details |
|------|---------|
| **Document Version** | 1.0 |
| **Date** | April 16, 2026 |
| **Author** | Stoneclad (TPM), Cherokee AI Federation |
| **Product Owner** | Darrell Reading II |
| **Status** | Active Development |
| **Prepared For** | Dr. Joe Dorn, Erika Hammontree |
| **Classification** | Confidential — NDA Required |

---

## 1. Executive Summary

Ganuda is a product line of AI governance tools built on a constitutional governance topology. The federation sells structured oversight for AI systems — sycophancy detection, mandatory dissent, graduated autonomy, and tamper-evident audit trails — to organizations that need AI but cannot deploy it without governance guarantees.

The product line spans five offerings at different price points, serving individual developers (free), small businesses, and enterprises. All products share the same underlying governance engine, which has processed 99,000+ decisions in production on consumer hardware.

### 1.1 Business Opportunity

- **$65B+ AI compliance/governance TAM** by 2028 (35%+ CAGR)
- **Zero competitors** offer a compiled governance proxy with mandatory adversarial dissent
- **Regulatory pressure accelerating**: EU AI Act, NIST AI RMF, OMB M-24-10, SEC AI guidance
- **Air-gap market unserved**: DoD, HIPAA, ITAR organizations have no governed bridge to frontier AI

### 1.2 Value Proposition

| For Customers | For the Federation |
|---------------|-------------------|
| Deploy AI with governance guarantees their compliance team accepts | Sustainable commercial revenue funding community work |
| Drop-in proxy — no model changes, no re-training, no vendor lock-in | First-mover advantage in structural AI governance |
| Audit trail that satisfies SOC2, HIPAA, FedRAMP auditors | Patent-protected IP (4 filed, 6+ candidates) |
| Consumer hardware — no cloud dependency, full data sovereignty | Defensible architecture validated by 99,000+ production decisions |

---

## 2. Business Objectives

### 2.1 Primary Objectives

| Objective | Metric | Target |
|-----------|--------|--------|
| Establish first commercial revenue | Annual Recurring Revenue | $70K-$332K Year 1 |
| Prove governance proxy market fit | Paying customers | 5+ organizations in 6 months |
| Convert patent portfolio | Non-provisional filings | All 4 by March 8, 2027 |
| Enter ARC Prize 2026 | Competition result | Milestone 1 by June 30 |
| Maintain zero security incidents | Data breaches / compliance violations | Zero |

### 2.2 Secondary Objectives

- Establish Ganuda as the recognized standard for AI governance infrastructure
- Build reusable governance engine that serves all product lines from one codebase
- Create thermal memory knowledge base of governance patterns across industries
- Partner with Cherokee Federal for defense/government market entry
- Attract grant funding (NSF SBIR, DARPA) for air-gap proxy research

---

## 3. Stakeholders

### 3.1 Primary Stakeholders

| Stakeholder | Role | Interest |
|-------------|------|----------|
| **Darrell Reading II** | Founder / Chief | Product vision, architecture, patent inventor |
| **Dr. Joe Dorn** | Technical Advisor | Testing, market feedback, business development |
| **Erika Hammontree** | Business Advisor | Business viability, market positioning, operational structure |
| **Stoneclad (TPM)** | Technical Program Manager | Execution, council governance, sprint cadence |
| **Brandon Foust** | Engineering | Implementation capacity |
| **Kenzie** | Engineering | Monitoring, measurement, portal development |

### 3.2 Target Customers

| Segment | Profile | Primary Need | Price Sensitivity |
|---------|---------|-------------|-------------------|
| **Individual developers** | Solo builders, startups | Basic governance for side projects | Free (Community tier) |
| **SMB tech teams** | 5-50 person companies using LLMs | Audit trail, sycophancy detection | Low-medium ($50-200/mo) |
| **Enterprise IT/compliance** | 500+ person orgs, regulated industries | Full governance, SLA, compliance packages | Low ($5K-60K+/yr) |
| **Defense/government** | DoD, IC, federal agencies | Air-gap proxy, FedRAMP path, data sovereignty | Budget-driven (contract) |
| **Healthcare** | Hospitals, insurers, pharma | HIPAA compliance, PII protection | Medium ($2K-20K/yr) |
| **Veterans / nonprofits** | VSOs, tribal entities, educational | Free access via PolyForm license | Free |

### 3.3 Anti-Stakeholders (Awareness)

| Entity | Concern |
|--------|---------|
| Cloud AI vendors (OpenAI, Google, Anthropic) | May view governance proxy as friction on their platform |
| "AI safety" companies with behavioral approaches | Compete on narrative; our structural approach challenges their methodology |
| Organizations selling AI without governance | Governance standard raises the bar they must meet |

---

## 4. Product Line Scope

### 4.1 Product: ganuda-harness

| Attribute | Details |
|-----------|---------|
| **Description** | Compiled Rust governance proxy for any OpenAI-compatible LLM endpoint |
| **Form factor** | Single binary (8.9 MB), one TOML config file |
| **Status** | v0.1 demo-ready |
| **Revenue** | Per-node licensing (Professional / Enterprise) |
| **Target** | Any organization using LLMs that needs governance |
| **Key differentiator** | Zero code changes to existing stack. Drop-in proxy. |

### 4.2 Product: Ganuda Shield

| Attribute | Details |
|-----------|---------|
| **Description** | Transparent endpoint monitoring with governance-informed anomaly detection |
| **Form factor** | Agent-based monitoring, dashboard, alerting |
| **Status** | Positioning (architecture exists, productization in progress) |
| **Revenue** | $6-10/endpoint/month tiered |
| **Target** | Organizations with deployed AI endpoints needing ongoing monitoring |
| **Key differentiator** | Governance-informed monitoring (not just uptime — behavioral drift, sycophancy trends) |

### 4.3 Product: Longhouse APP

| Attribute | Details |
|-----------|---------|
| **Description** | Open-source governance framework for multi-agent AI systems |
| **Form factor** | Software framework (Python), documentation, reference architecture |
| **Status** | Launched April 9, 2026 |
| **Revenue** | PolyForm Small Business 1.0.0 (free under $5M, commercial above) |
| **Target** | Developers and organizations building their own governance |
| **Key differentiator** | Only open-source framework with mandatory dissent and constitutional constraints |

### 4.4 Product: LARQL

| Attribute | Details |
|-----------|---------|
| **Description** | Neural network weights as queryable graph database (Lazarus Query Language) |
| **Form factor** | Rust CLI + HTTP server, vindex format |
| **Status** | Demo-ready (Qwen vindexes walkable, 63ms/layer) |
| **Revenue** | Bundled with Enterprise tier; standalone licensing TBD |
| **Target** | AI researchers, interpretability teams, compliance auditors |
| **Key differentiator** | No other tool queries model weights as a graph database. No GPU required. |

### 4.5 Product: Tokenized Air-Gap Proxy (Patent #7)

| Attribute | Details |
|-----------|---------|
| **Description** | Governance-wrapped tokenization proxy for air-gapped frontier AI access |
| **Form factor** | On-premise appliance + governance layer |
| **Status** | Patent brief complete, architecture designed, not yet built |
| **Revenue** | Enterprise custom pricing ($20K-100K+) |
| **Target** | DoD, HIPAA, ITAR, FedRAMP organizations |
| **Key differentiator** | Only product that provides governed frontier AI access while maintaining complete data sovereignty |

### 4.6 Product: VetAssist

| Attribute | Details |
|-----------|---------|
| **Description** | AI-powered veteran disability claims guidance platform |
| **Form factor** | Web application (Next.js frontend, FastAPI backend) |
| **Status** | Live since March 9, 2026 |
| **Revenue** | Free for veterans; VSO tiers ($49-499/mo) |
| **Target** | U.S. veterans, VSOs, VA-accredited attorneys |
| **Key differentiator** | Council-validated responses, free for veterans, self-hosted (no data leaves infrastructure) |

---

## 5. Business Requirements

### 5.1 Revenue Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-001 | First paying customer within 6 months of this session | P0 |
| BR-002 | Professional tier pricing finalized with real dollar amounts | P0 |
| BR-003 | Enterprise tier pricing framework with 3+ reference engagements | P1 |
| BR-004 | PolyForm license validated by attorney for enforceability | P1 |
| BR-005 | Grant application submitted (NSF SBIR or equivalent) | P2 |

### 5.2 Legal/IP Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-010 | Mutual NDA executed with all session participants | P0 |
| BR-011 | Non-provisional patent conversion for all 4 provisionals by Mar 8, 2027 | P0 |
| BR-012 | Patent drawings/flowcharts completed for Hulsey (4 provisionals) | P0 |
| BR-013 | Unfiled patent candidates triaged: file, defer, or trade-secret | P1 |
| BR-014 | B-corp or equivalent mission-lock structure researched | P2 |

### 5.3 Technical Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-020 | ganuda-harness v1.0 release (stable, documented, downloadable) | P0 |
| BR-021 | Ganuda Shield MVP (endpoint monitoring + governance checks) | P1 |
| BR-022 | Air-Gap Proxy prototype (tokenization + governance + model selection) | P1 |
| BR-023 | SOC2 readiness assessment completed | P2 |
| BR-024 | HIPAA compliance assessment completed | P2 |

### 5.4 Operational Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-030 | Support model operational for Professional tier (48hr SLA) | P1 |
| BR-031 | Demo environment accessible to prospects (sanitized, time-limited) | P0 |
| BR-032 | Marketing website updated with product line positioning | P1 |
| BR-033 | Customer onboarding process documented | P1 |

---

## 6. Success Criteria

| Timeframe | Criterion | Metric |
|-----------|-----------|--------|
| 90 days | ganuda-harness v1.0 released | Binary downloadable, docs complete |
| 90 days | 3+ organizations testing the harness | Beta agreements signed |
| 6 months | First paying customer | Revenue received |
| 6 months | ARC Prize M1 submitted | Competition entry validated |
| 12 months | $70K+ ARR | Recurring revenue established |
| 12 months | All 4 patents converted to non-provisional | Filings confirmed |
| 18 months | Enterprise customer signed | Contract executed |
| 24 months | Community deployment funded from revenue | First community project launched |

---

## 7. Budget

### 7.1 Invested to Date

| Category | Amount |
|----------|--------|
| Hardware (6-node cluster, solar, battery, fiber) | $30,000+ |
| Patent filing fees (4 provisionals) | $520 |
| Domains, services, operations | ~$3,000 |
| **Total invested** | **~$33,500** |

### 7.2 Near-Term Needs

| Category | Estimated Cost | Priority |
|----------|---------------|----------|
| Patent attorney (non-provisional conversion, 4 apps) | $8,000-15,000 | P0 |
| Patent attorney (new filings, 2-3 candidates) | $3,000-8,000 | P1 |
| Legal (B-corp formation, NDA templates) | $2,000-5,000 | P1 |
| Marketing (website, content, conference) | $1,000-3,000 | P2 |
| Operations (12 months) | $6,000 | P0 |
| **Total near-term** | **$20,000-$37,000** |

### 7.3 Funding Strategy

| Source | Amount | Timeline |
|--------|--------|----------|
| Founder capital (continued) | As needed | Ongoing |
| First commercial revenue | $70K-332K | 6-12 months |
| NSF SBIR Phase I | $275K | Application Q3 2026 |
| DARPA (if applicable) | Variable | Research needed |
| Strategic partnership | Variable | Opportunistic |

---

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Patent conversion deadline missed | Low | High | Calendar alerts, attorney engaged (Hulsey), drawings in progress |
| No paying customers in 6 months | Medium | High | Multiple product lines, multiple markets, low price entry |
| Competitor launches governance proxy | Medium | Medium | 4 patents filed, trade secrets, 99K+ decision head start |
| Key person risk (founder) | Low | Critical | Federation architecture designed for autonomy; TPM + Council can operate independently |
| Regulatory change invalidates approach | Low | Medium | Constitutional governance is regulation-friendly, not regulation-dependent |
| Jr executor instability blocks development | Medium | Medium | Direct development path as fallback; executor fixes in progress |

---

## 9. Constraints

| Constraint | Impact |
|------------|--------|
| Founder-bootstrapped (no external capital) | Limits hiring speed; all development is federation-built |
| Non-provisional deadline March 8, 2027 | Hard date. Cannot be extended. |
| PolyForm license commitment | Revenue from organizations <$5M = zero (by design) |
| Community purpose commitment | Acquisition offers from extraction companies will be declined |
| Consumer hardware architecture | Limits max model size; compensated by multi-model governance |

---

## 10. Appendices

### A. Related Documents

| Document | Location |
|----------|----------|
| Executive Summary | docs/business/GANUDA-EXECUTIVE-SUMMARY-APR16-2026.md |
| Product Requirements (PRD) | docs/business/GANUDA-PRD-v1-APR16-2026.md |
| Market Analysis | docs/business/GANUDA-MARKET-ANALYSIS-APR16-2026.md |
| Licensing Framework | docs/business/LICENSING-FRAMEWORK-MAR09-2026.md |
| Support Model | docs/business/SUPPORT-MODEL-MAR09-2026.md |
| VetAssist BRD (reference pattern) | docs/vetassist/VetAssist-BRD-v1.md |
| Patent Briefs | docs/patents/ |

### B. Glossary

| Term | Definition |
|------|-----------|
| **ganuda-harness** | Compiled Rust governance proxy binary |
| **Council** | 8-specialist AI governance body with democratic consensus |
| **Coyote** | Adversarial dissent specialist (mandatory dissent role) |
| **Thermal memory** | Persistent knowledge store with temperature-based relevance decay |
| **Chiral validation** | Two independent models cross-checking each other |
| **vindex** | Vertex-indexed graph database of neural network weights (LARQL format) |
| **Jr** | Autonomous task executor in the federation |
| **Longhouse** | Governance framework named for Cherokee council house |
| **PolyForm** | License that's free for small businesses, paid for large ones |

---

*Cherokee AI Federation — For the Seven Generations*
