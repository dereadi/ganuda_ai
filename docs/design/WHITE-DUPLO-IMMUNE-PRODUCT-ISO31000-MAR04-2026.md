# White Duplo Immune Product — Design Document
## ISO 31000:2018 Risk Framework

**Longhouse Session**: `1c1c96c5b80469fb` — UNANIMOUS CONSENSUS (9/9 seats)
**Date**: March 4, 2026
**Thermals**: #119201 (consensus), #119182 (herd immunity vision), #119181 (immune system insight)
**Status**: APPROVED — Proceeding to epic decomposition

---

## Vision

White Duplo is an adaptive immune system for AI agent clusters. When one cluster detects and neutralizes a novel attack pattern, it anonymously reports the pattern fingerprint — no customer data, only the attack shape — to a central immune registry. Every cluster connected to the registry receives the antibody automatically.

**Herd immunity for AI clusters.** When one learns, they all learn.

## Business Model

| Tier | Offering | Revenue |
|------|----------|---------|
| Free | Duplo snap-in SDK + basic Cam monitoring | Community growth, adoption |
| Paid | White Duplo adaptive defense + registry connection | Usage-based SaaS |
| Enterprise | Private/air-gapped registry with update reception | Contract licensing |

**Moat**: Network effect. Code is clonable. Immune memory from 10,000 clusters is not.

## ISO 31000:2018 Risk Classification

| ID | Concern | Classification | Treatment | Owner |
|----|---------|---------------|-----------|-------|
| C1 | Registry compromise (poisoned antibodies at scale) | RISK | **REDUCE** — crypto, MFA, immutable audit logs, intrusion detection | Crawdad |
| C2 | Pattern signature reversibility | RISK | **AVOID** — design out at cryptographic level. Differential privacy with mathematical bounds. | Medicine Woman + Eagle Eye |
| C3 | Registry governance (validation, false positives) | **FEATURE** | Transparent governance = market differentiator. Community-governed. | Deer + Peace Chief |
| C4 | Adversarial adoption (attackers run White Duplo) | RISK | **RETAIN** — net positive. Attackers become participants, feed the herd. | Raven + Coyote |
| C5 | Supply chain trust (registry integrity) | RISK | **REDUCE** — digital signatures, formal verification, PROVEN not tested. | Eagle Eye |

### Risk Register Template (per Epic)

Each epic MUST define:
- Risk ID, Description
- Likelihood (1-5), Impact (1-5)
- Treatment strategy (Avoid / Reduce / Share / Retain)
- Owner (Council seat)
- Residual risk after treatment
- Review date

**Minimum acceptable**: Residual risk below MEDIUM on all C1-C5 axes.
**Council reviews**: Quarterly.

## Nine Architectural Decisions

1. **Federated registries from day one** — No single point of failure for civilization-scale AI infrastructure. Multiple independent registries that cross-validate. (Turtle: seven-generation requirement)

2. **Differential privacy with mathematical bounds** — Pattern signatures must be PROVEN non-reversible, not just implemented with "we think it's safe." Formal verification required. (Medicine Woman + Eagle Eye)

3. **Onion routing or mixnet for anonymous submission** — No metadata leakage, no timing attacks, no correlation analysis possible. The people's data belongs to the people. (Medicine Woman)

4. **STIX/TAXII compatible pattern format** — Interoperable with existing threat intelligence feeds (CrowdStrike, VirusTotal, MITRE ATT&CK). Don't reinvent the wheel. (Bear)

5. **Consensus validation (N-of-M)** — A pattern is NOT promoted to the registry until N independent clusters report it. Prevents single-source poisoning (C1) and insider threat (C4 combined with C1). (Coyote)

6. **Open-source SDK, monetize registry** — DC-6 scaffolding principle. Cherokee scaffolding, not Roman walls. Everyone can build, the value is in the shared immune memory. (Deer)

7. **Community governance model** — Registry governed by its participants, not just by us. DAO-like structure or advisory board of contributing clusters. (Peace Chief)

8. **Provisional patent on herd immunity mechanism** — File before any public disclosure. The mechanism of anonymous pattern aggregation for cross-cluster AI defense is novel. (Raven)

9. **Schema validator for snap-in contracts** — The SDK must define what a valid enzyme looks like, what binding points are exposed, what input/output shapes are expected. Without strict interface definitions, the immune system can't distinguish malformed from malicious. (Spider)

## Identified Gaps (Council)

| Gap | Raised By | Priority |
|-----|-----------|----------|
| Risk perception divergence — clusters disagree on attack vs. feature | Coyote | HIGH — needs arbitration protocol |
| Succession planning for the registry | Turtle | HIGH — seven-gen requirement |
| Latency budget — real-time vs. batch propagation | Bear | MEDIUM — changes architecture fundamentally |
| External red team budget | Eagle Eye | HIGH — must precede launch |
| Community governance structure details | Peace Chief | MEDIUM — can evolve post-MVP |
| Patent strategy execution | Raven | URGENT — before any publication |

## Design Constraints (Inherited)

- **DC-5 (Coyote as Cam)**: Always-on low-cost observation layer. The Cam is the first line of detection.
- **DC-6 (Gradient Principle)**: Specialization is gravity, not boundary. The SDK is scaffolding anyone can use.
- **DC-7 (Noyawisgi)**: System transforms under pressure, not restores. A gap that produces a better outcome isn't a bug — it's speciation. But it still goes through Council review.

## Competitive Landscape (Deer Assessment)

| Incumbent | Domain | Gap |
|-----------|--------|-----|
| CrowdStrike | Endpoint detection | No agent architecture understanding |
| Snyk | Code scanning | No runtime behavior |
| Palo Alto | Network security | No AI-native defense |
| OpenAI / Anthropic | AI safety | No cross-cluster defense |
| **White Duplo** | **Runtime agent-behavior immune response + herd learning** | **Blue ocean** |

## Next Steps

1. **IMMEDIATE**: File provisional patent (Raven's requirement — before any publication)
2. **Epic 1**: Duplo snap-in SDK + schema validator + interface contracts
3. **Epic 2**: White Duplo core — local detection, trace-back, forensic alerting
4. **Epic 3**: Anonymous reporting protocol — differential privacy, formal verification
5. **Epic 4**: Central immune registry — federated from day one
6. **Epic 5**: Herd immunity propagation — consensus validation, antibody distribution
7. **Epic 6**: Community governance model + external red team engagement

Each epic carries its own ISO 31000 risk register. Council reviews residual risk at epic completion.
