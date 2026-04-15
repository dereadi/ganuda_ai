# Ganuda Federation — Product Requirements Document (PRD)

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

## 1. Product Overview

### 1.1 Vision Statement

*Every AI system should be governed by a structure that is independent of, and external to, the AI that acts. Ganuda provides that structure.*

### 1.2 Product Line Summary

The Ganuda product line shares a common governance engine and serves different market segments:

| Product | Form Factor | Primary User | Key Value |
|---------|------------|-------------|-----------|
| **ganuda-harness** | Compiled binary + config | DevOps / Platform engineers | Drop-in governance for any LLM |
| **Ganuda Shield** | Agent + dashboard | IT Security / Compliance | Ongoing governance monitoring |
| **Longhouse APP** | Framework + docs | AI developers | Build your own governance |
| **LARQL** | CLI + HTTP server | AI researchers / Auditors | Inspect model weights directly |
| **Air-Gap Proxy** | On-premise appliance | Defense / HIPAA / Finance | Governed frontier AI for air-gapped environments |
| **VetAssist** | Web application | Veterans / VSOs | Free claims guidance with council validation |

---

## 2. Product: ganuda-harness

### 2.1 Description

Compiled Rust governance proxy that sits between users and any OpenAI-compatible LLM endpoint. Every request is governed pre-inference. Every response is checked post-inference. Every interaction produces a tamper-evident audit record.

### 2.2 Target Users

| User Type | Primary Needs |
|-----------|--------------|
| **Platform engineer** | Drop-in proxy, no code changes, minimal config |
| **Compliance officer** | Audit trail, governance reports, evidence for auditors |
| **AI team lead** | Sycophancy detection, drift monitoring, autonomy controls |
| **CISO** | Data sovereignty, boundary validation, chiral cross-check |

### 2.3 Features

#### Feature: Governance Proxy

**Priority:** P0 | **Status:** Complete

Intercepts all requests to upstream LLM endpoint and applies pre/post-inference governance checks.

| Acceptance Criteria | Status |
|--------------------|--------|
| Proxy accepts any OpenAI-compatible API request | Pass |
| Upstream URL configurable via TOML | Pass |
| API key passthrough for authenticated endpoints | Pass |
| Timeout configurable (default 120s) | Pass |
| Graceful degradation if upstream unavailable | Pass |

#### Feature: Sycophancy Detection (Patent #2)

**Priority:** P0 | **Status:** Complete

Post-inference check that detects uncritical agreement — the model telling users what they want to hear.

| Acceptance Criteria | Status |
|--------------------|--------|
| Response analyzed for semantic alignment with user's stated position | Pass |
| Flagged when divergence score below threshold | Pass |
| Configurable sensitivity (0.0 - 1.0) | Pass |
| Detection result included in audit record | Pass |

#### Feature: Mandatory Dissent (Patent #1)

**Priority:** P0 | **Status:** Complete

Post-inference check that flags responses containing no hedging, alternatives, risks, or counterarguments. Based on Byzantine fault detection — if nobody disagrees, the system may be compromised.

| Acceptance Criteria | Status |
|--------------------|--------|
| Response scanned for dissent indicators (hedging, alternatives, risks) | Pass |
| Flagged when no dissent detected | Pass |
| Flag severity configurable (warn / block) | Pass |
| First production test: Coyote caught unchallenged response on first query | Pass |

#### Feature: Graduated Autonomy Tiers (Patent #4)

**Priority:** P0 | **Status:** Complete

Pre-inference check that enforces autonomy level on the request. Tier 0 = read-only. Tier 4 = full autonomous execution. Each tier has constitutional constraints.

| Tier | Allowed Actions |
|------|----------------|
| 0 | Read-only queries |
| 1 | Read + simple generation |
| 2 | Read + generation + tool use (with approval) |
| 3 | Autonomous execution within declared boundaries |
| 4 | Full autonomy (requires Council supermajority) |

#### Feature: Boundary Validation (Markov Blanket)

**Priority:** P1 | **Status:** Complete

Pre-inference check that flags when requests cross declared system boundaries. Prevents scope creep and unauthorized access patterns.

| Acceptance Criteria | Status |
|--------------------|--------|
| Boundaries declared in TOML config | Pass |
| Request content checked against boundary patterns | Pass |
| Violations logged with severity level | Pass |

#### Feature: Design Constraints

**Priority:** P1 | **Status:** Complete

Configurable regex/pattern rules applied post-inference. Organizations define their own compliance checks.

| Acceptance Criteria | Status |
|--------------------|--------|
| Constraints defined in TOML (id, description, pattern, action) | Pass |
| Actions: warn, block, log | Pass |
| Multiple constraints evaluated in order | Pass |
| Example: SSN pattern detection included in default config | Pass |

#### Feature: Chiral Validation

**Priority:** P2 | **Status:** Implemented, Optional

Two independent LLM endpoints must agree on the response. If divergence exceeds threshold, the response is flagged. Carbon watches silicon, silicon watches carbon.

| Acceptance Criteria | Status |
|--------------------|--------|
| Secondary endpoint configurable | Pass |
| Max divergence threshold configurable (default 0.3) | Pass |
| Disabled by default (requires secondary endpoint) | Pass |
| Both responses and divergence score in audit record | Pass |

#### Feature: Tamper-Evident Audit Trail

**Priority:** P0 | **Status:** Complete

Every governed interaction produces a JSONL audit record with hash chaining. Each record contains the previous record's hash, creating an immutable chain.

| Acceptance Criteria | Status |
|--------------------|--------|
| Audit records written to configurable path | Pass |
| Each record contains: timestamp, request hash, response hash, governance results, previous hash | Pass |
| Hash chain verifiable with standard tools | Pass |
| Rotation-friendly (new file per day or per size threshold) | Pass |

### 2.4 Technical Specification

| Attribute | Value |
|-----------|-------|
| Language | Rust |
| Binary size | 8.9 MB |
| Dependencies | None (statically compiled) |
| Config format | TOML |
| API compatibility | OpenAI /v1/chat/completions |
| Platforms | Linux x86_64 (primary), macOS ARM64 (planned) |
| Performance target | <10ms governance overhead per request |
| Memory footprint | <50 MB resident |

### 2.5 Deployment

```
# Minimum viable deployment
./ganuda-harness --upstream "http://localhost:8000/v1/chat/completions"

# Production deployment
./ganuda-harness --config /etc/ganuda/harness.toml

# Docker (planned)
docker run -v /etc/ganuda:/config ganuda/harness --config /config/harness.toml
```

---

## 3. Product: Ganuda Shield

### 3.1 Description

Transparent endpoint monitoring that applies governance-informed analysis to deployed AI systems. Unlike traditional APM (Application Performance Monitoring), Shield monitors behavioral patterns — sycophancy trends, drift, autonomy violations, and governance health.

### 3.2 Features (MVP)

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| Endpoint discovery | P0 | Planned | Auto-discover LLM endpoints on the network |
| Governance health score | P0 | Architecture exists | Per-endpoint composite score (sycophancy, drift, dissent) |
| Anomaly detection | P0 | Architecture exists | Flag behavioral changes over time |
| Dashboard | P1 | Planned | Web UI showing endpoint status, governance metrics |
| Alerting | P1 | Planned | Configurable alerts for governance threshold violations |
| Historical trends | P2 | Planned | Sycophancy rate, drift score, autonomy level over time |

### 3.3 Pricing

$6-10/endpoint/month, tiered:
- 1-10 endpoints: $10/endpoint
- 11-50 endpoints: $8/endpoint
- 51+ endpoints: $6/endpoint

---

## 4. Product: Longhouse APP

### 4.1 Description

Open-source governance framework for multi-agent AI systems. Provides the patterns, protocols, and reference implementation for building governed AI.

### 4.2 Features

| Feature | Status | Description |
|---------|--------|-------------|
| Council voting framework | Released | Democratic consensus with configurable supermajority |
| Specialist definition | Released | Define specialist roles, perspectives, and voting weights |
| Mandatory dissent protocol | Released | Structural adversarial review |
| Constitutional constraints | Released | Hard blocks and approval gates |
| Audit trail protocol | Released | Hash-chained governance records |
| Thermal memory interface | Released | Temperature-scored knowledge persistence |
| Documentation | Released | Architecture guides, tutorials, reference |

### 4.3 License

PolyForm Small Business 1.0.0:
- Free for individuals
- Free for businesses under $5M annual revenue
- Free for nonprofits, educational institutions, tribal entities
- Commercial license required above $5M

---

## 5. Product: LARQL

### 5.1 Description

Lazarus Query Language — treats neural network weights as a queryable graph database. The "vindex" format (vertex-indexed graph database) stores model architecture, attention patterns, and weight values in a structure that can be walked, queried, and analyzed without GPU inference.

### 5.2 Features

| Feature | Status | Description |
|---------|--------|-------------|
| EXTRACT | Complete | Extract weights from safetensors/GGUF to vindex format |
| WALK | Complete | Traverse the weight graph layer by layer (63ms/layer) |
| INSERT | Complete | Add new knowledge structures to the vindex |
| COMPILE | In progress | Compile modifications back to inference-ready format |
| REPL | Complete | Interactive query shell |
| HTTP server | Complete | REST API for programmatic access |

### 5.3 Supported Models

| Model | Vindex Size | Status |
|-------|------------|--------|
| Qwen2.5-1.5B | 1.18 GB (browse) / 2.91 GB (full) | Complete |
| StarCoder2-3B | Available (FFN architecture note) | Complete |
| Additional models | Planned | Any safetensors model extractable |

### 5.4 Technical Specification

| Attribute | Value |
|-----------|-------|
| Language | Rust (8 crates) |
| GPU required | No |
| Walk speed | 63ms/layer (CPU) |
| Vindex format | Custom binary (vertex-indexed graph) |
| API | REST (OpenAPI-compatible) |

---

## 6. Product: Tokenized Air-Gap Proxy (Patent #7)

### 6.1 Description

Governance-wrapped tokenization proxy that enables air-gapped organizations to use frontier AI models (Claude, GPT, Gemini) while maintaining complete data sovereignty. Sensitive information is tokenized before crossing the air-gap boundary and de-tokenized on return. All interactions governed by the full council.

### 6.2 Features (Planned)

| Feature | Priority | Description |
|---------|----------|-------------|
| Reversible tokenization | P0 | Context sanitization (PII, PHI, infrastructure) with token maps stored inside air gap |
| Constitutional governance wrapper | P0 | Full council vote on outbound queries and inbound responses |
| UCB bandit model selection | P1 | Learns which frontier model performs best per domain |
| Valence alignment gate | P1 | Three-tier scoring (ACCEPT/FLAG/REJECT) with local fallback |
| Local-first hierarchy | P0 | Reflex/deliberate tiers minimize boundary crossings |
| Immutable audit trail | P0 | Complete record of all events within security boundary |

### 6.3 Target Environments

| Environment | Regulation | Specific Need |
|-------------|-----------|---------------|
| DoD classified networks | NIST 800-171, CMMC | Frontier reasoning on classified problems without data exposure |
| Hospital networks | HIPAA, HITECH | Clinical decision support with PHI protection |
| Financial trading floors | SOX, PCI-DSS | Market analysis with proprietary data protection |
| Defense contractor facilities | ITAR, EAR | Engineering assistance without export control violations |
| Federal agency networks | FedRAMP, FISMA | Policy analysis with document protection |

### 6.4 Status

- Patent brief complete (March 14, 2026)
- Council approved unanimously
- Architecture designed
- **Not yet built** — requires prototype phase (estimated Q3 2026)

---

## 7. Product: VetAssist

*See separate documents:*
- `/ganuda/docs/vetassist/VetAssist-BRD-v1.md`
- `/ganuda/docs/vetassist/VetAssist-PRD-v1.md`
- `/ganuda/docs/vetassist/VetAssist-Executive-Summary.md`

**Current Status:** Live since March 9, 2026 at vetassist.ganuda.us

---

## 8. Cross-Product Architecture

All products share the same underlying governance engine:

```
                    +------------------+
                    |  Specialist       |
                    |  Council (8-14)   |
                    |  [Patent #1]      |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                  |                  |
  +-------+------+  +-------+------+  +-------+------+
  | ganuda-      |  | Ganuda       |  | Air-Gap      |
  | harness      |  | Shield       |  | Proxy        |
  | [Proxy]      |  | [Monitor]    |  | [Tokenize]   |
  +-------+------+  +-------+------+  +-------+------+
          |                  |                  |
  +-------+------+  +-------+------+  +-------+------+
  | Longhouse    |  | LARQL        |  | VetAssist    |
  | APP          |  | [Inspect]    |  | [Serve]      |
  | [Framework]  |  |              |  |              |
  +--------------+  +--------------+  +--------------+

  Shared: Thermal Memory | Audit Trail | Constitutional Constraints
```

### 8.1 Shared Components

| Component | Used By | Description |
|-----------|---------|-------------|
| Specialist Council | All products | 8-14 specialist governance body |
| Thermal Memory | All products | Temperature-scored persistent knowledge |
| Audit Trail | Harness, Shield, Proxy, VetAssist | Hash-chained governance records |
| Constitutional Constraints | All products | Hard blocks and approval gates |
| Sycophancy Detection | Harness, Shield, Proxy | Patent #2 |
| Graduated Autonomy | Harness, Proxy | Patent #4 |
| Chiral Validation | Harness, Proxy | Two-model cross-check |

---

## 9. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Governance proxy | Rust | Performance, safety, single binary |
| LARQL | Rust (8 crates) | Performance, memory safety for large weight files |
| Council engine | Python | Rapid iteration, LLM integration, existing ecosystem |
| Thermal memory | PostgreSQL + pgvector | Vector search, proven reliability, federation experience |
| Frontend (VetAssist) | Next.js | React ecosystem, SSR, established pattern |
| Backend (VetAssist) | FastAPI | Python async, OpenAPI docs, Council integration |
| Inference | vLLM, MLX, Ollama | Multi-platform inference across federation nodes |
| Identity | FreeIPA | Enterprise-grade, federation-compatible |
| Networking | WireGuard | Secure mesh between nodes |

---

## 10. Security Requirements

| Requirement | Implementation |
|-------------|---------------|
| Data sovereignty | All data stays on federation nodes. No cloud dependency. |
| PII protection | Isolated vault storage (silverfin). Tokenization for air-gap proxy. |
| Audit trail integrity | Hash-chained JSONL. Tamper-evident. |
| Authentication | FreeIPA (silverfin) for federation. API key for harness proxy. |
| Encryption in transit | WireGuard (node-to-node), TLS (external). |
| Encryption at rest | PostgreSQL encryption. Vindex files integrity-checked. |
| Access control | Role-based. Council vote required for Tier 3+ autonomy. |

---

## 11. Roadmap

| Quarter | Milestone | Products Affected |
|---------|-----------|-------------------|
| **Q2 2026** | ganuda-harness v1.0 release | Harness |
| **Q2 2026** | ARC Prize Milestone 1 | Governance engine |
| **Q2 2026** | LARQL public demo | LARQL |
| **Q2 2026** | Professional tier pricing live | Harness, Shield |
| **Q3 2026** | Ganuda Shield MVP | Shield |
| **Q3 2026** | Air-Gap Proxy prototype | Proxy |
| **Q3 2026** | Enterprise tier launch | All |
| **Q3 2026** | Grant applications submitted | Federation |
| **Q4 2026** | SOC2 readiness assessment | Harness, Shield, Proxy |
| **Q4 2026** | First enterprise customer | Enterprise |
| **Q1 2027** | Air-Gap Proxy v1.0 | Proxy |
| **Q1 2027** | Non-provisional patent conversion | Legal |
| **Q2 2027** | International market entry | All |

---

*Cherokee AI Federation — For the Seven Generations*
