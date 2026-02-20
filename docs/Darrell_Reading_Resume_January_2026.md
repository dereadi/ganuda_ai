# Darrell E Reading II

6301 SW Warrington Road
Bentonville, AR 72713
(479) 877-9441
dereadi@gmail.com
[GitHub](https://github.com/dereadi) | [ganuda.us](https://ganuda.us)

---

## Technical Leader | AI/ML Architect | Full-Stack Platform Engineer

Innovative technical leader with 30+ years enterprise experience, pioneering AI democratization through the **Cherokee AI Federation** framework. Architect of **VetAssist**, an AI-powered veteran disability claims platform with enterprise-grade PII protection. Expert in distributed systems, machine learning infrastructure, and secure healthcare application design. Military veteran (E7/SFC) bringing disciplined project management and strategic thinking to complex technical challenges.

---

## Core Competencies

**AI/ML & Data Science**
- Language Model Deployment (Qwen 32B/72B, LLaMA, vLLM, MLX)
- Multi-Agent AI Systems (7-Specialist Council Architecture)
- Distributed Embedding Generation (93M+ vectors)
- Neural Network Optimization (17x performance improvement)
- Thermal Memory Systems with O(1) Retrieval

**Healthcare & Security**
- HIPAA-Compliant PII Protection (Microsoft Presidio)
- Custom Veteran Data Recognizers (SSN, VA File Numbers)
- Crisis Detection ML (Suicidal Ideation Screening)
- Token Vault Architecture for Sensitive Data
- JWT/OAuth2 Authentication with VA.gov Integration

**Full-Stack Development**
- Backend: FastAPI, Python, PostgreSQL, pgvector
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Infrastructure: 6-Node Distributed Federation
- API Design: RESTful, WebSocket, Real-time Processing

**Infrastructure & DevOps**
- Multi-GPU AI Inference (RTX 6000 96GB, RTX 5070, M4 Max 128GB)
- PostgreSQL Multi-Master Logical Replication
- Prometheus/Grafana Observability Stack
- Tailscale Mesh VPN with WireGuard

---

## Featured Projects

### VetAssist - AI-Powered Veteran Claims Platform (2025-2026)
*Full-stack architect and lead developer*

**Problem**: Veterans face a complex 526-page disability claims process with 65% initial denial rate.

**Solution**: Built an AI-assisted platform combining 7-specialist Council deliberation with enterprise security.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    VetAssist Platform                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)     │  Backend (FastAPI)                │
│  - Claims Wizard           │  - 7-Specialist Council API       │
│  - VA Rating Calculator    │  - PII Protection Layer           │
│  - AI Chat Assistant       │  - Crisis Detection ML            │
│  - Veteran Dashboard       │  - CFR Condition Mapping          │
├─────────────────────────────────────────────────────────────────┤
│  Security Layer                                                 │
│  - Microsoft Presidio PII Detection                            │
│  - Custom Veteran Recognizers (SSN 0.85+, VA File #)          │
│  - Token Vault (goldfin network isolation)                     │
│  - JWT Auth + VA.gov OAuth Integration                         │
├─────────────────────────────────────────────────────────────────┤
│  AI Infrastructure                                              │
│  - vLLM with Qwen2.5-Coder-32B-AWQ (RTX 6000)                 │
│  - 7-Specialist Council (democratic consensus)                 │
│  - Thermal Memory (19,900+ memories)                           │
│  - Crisis Detection (988 Veterans Crisis Line integration)     │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features**:
- **Claims Wizard**: Multi-step forms for VA Forms 21-526EZ, 21-0781, 21-4138, 21-0966
- **CFR Mapping**: 49 conditions mapped to 38 CFR diagnostic codes with rating criteria
- **Document OCR**: AI-powered extraction of diagnoses, ICD-10 codes, nexus signals
- **Evidence Checklists**: Auto-generated per-condition evidence requirements
- **Rating Calculator**: VA Combined Ratings Table implementation
- **Crisis Detection**: Real-time veteran safety screening with severity triage

**Results**:
- 18/18 integration tests passing (100% Sprint 3)
- <20ms CFR query response time
- 100% PII detection accuracy on test dataset

---

### PII Protection System Design (2026)
*Security architect - Healthcare data protection*

Designed multi-phase PII protection for veteran healthcare data:

**Phase 1 - Detection** (Complete):
- Microsoft Presidio with spaCy NER (en_core_web_lg 750MB model)
- Custom `VeteranSSNRecognizer` (0.85 confidence threshold)
- Custom `VAFileNumberRecognizer` for C-file numbers
- Entities: SSN, Phone, Email, VA File #, Location, DOB

**Phase 2 - Integration** (Complete):
- Real-time chat endpoint PII scanning before database storage
- Original content preserved for AI processing (memory only, not persisted)
- Redacted version stored with reversible tokenization

**Phase 3 - Token Vault** (Architecture Design):
- Isolated goldfin server with network segmentation
- Token-to-PII mapping with authorized-only retrieval
- Audit trail for all PII access

**Security Stack**: bcrypt (12 rounds), JWT with SHA-256 hash storage, bleach XSS sanitization, rate limiting

---

### Cherokee Audio Studio - AI Music Processing (2024-2026)
*Lead developer - Distributed audio restoration*

Built distributed audio processing pipeline for professional music restoration:

**Beatles Black Album Project**:
- **48 tracks processed with 100% success rate**
- 4-node distributed processing (SASASS, SASASS2, REDFIN, BLUEFIN)
- 5-stage restoration: analyze, denoise, enhance, balance, master

**Technology Stack**:
- **Demucs HT-Demucs**: AI 6-stem separation (vocals, drums, bass, guitar, piano, other)
- **Composers Desktop Project (CDP)**: PVOC spectral processing (Aphex Twin techniques)
- **SoundThread v0.3.0**: Real-time audio GUI
- **FFmpeg Pipeline**: Advanced noise reduction, EQ, dynamics, mastering

**Multi-LLM Audio Specialist Coordination**:
- War Chief GPU 0: Hiss & Noise Reduction (sox, audacity-cli)
- War Chief GPU 1: Dynamic Range & Compression (ffmpeg, sox)
- Enhanced DevOps: Spectral Analysis & EQ (librosa, scipy)
- Legal Llamas: Quality Assessment & Constitutional Review

**Performance**: GPU-accelerated stem separation in <10 seconds (vs 5 minutes CPU)

---

### Distributed AI Computing Federation (2024-2026)
*Systems architect - 17x performance optimization*

**Challenge**: Processing 86 million AI embeddings at 120 mem/sec (201-hour ETA)

**Root Cause Analysis**: Identified network I/O as bottleneck (95% of cycle time, 15s fetch latency)

**Solution Architecture**:
- Deployed PostgreSQL locally on compute nodes with logical replication
- Optimized batch UPDATE operations using PostgreSQL unnest() patterns
- Implemented bidirectional sync for data consistency

**Result**: **17x performance improvement** (120 → 2,071 mem/sec, 201h → 12h ETA)

**6-Node Federation**:

| Node | Hardware | Role |
|------|----------|------|
| redfin | RTX 6000 96GB VRAM | Primary vLLM inference (32B model) |
| bluefin | 64GB RAM | PostgreSQL hub, Zammad, API services |
| greenfin | Router | Network segmentation, VLANs |
| sasass | M2 Ultra 64GB | Mac ML processing, MLX |
| sasass2 | M2 Ultra 64GB | Backup ML node |
| bmasass | M4 Max 128GB | 72B model capability, 128K context |

**Observability Stack**:
- Prometheus + Grafana with custom AI/ML exporters
- Grafana Loki centralized logging (1.2GB ingestion, <1s queries)
- Pathfinder Wisdom: AI-powered bottleneck analysis using Claude LLM
- Multi-channel alerting (Discord, email, SMS) with intelligent routing

---

## Professional Experience

### Walmart Inc. | Bentonville, AR
**Senior Infrastructure Engineer | SIMS Team**
*December 2016 - Present*

**Cherokee AI Federation (2024-2026)**:
- Architected **VetAssist** veteran claims platform with enterprise PII protection
- Deployed **6-node federated computing cluster** achieving 17x performance improvement
- Configured **RTX 6000 96GB + M4 Max 128GB** for multi-model AI inference
- Implemented **93M+ AI embeddings** with pgvector similarity search
- Built **distributed audio processing** with 100% success on 48-track Beatles restoration
- Created **thermal memory system** with 19,900+ memories and O(1) retrieval

**Quantifiable Achievements**:
- 17x embedding generation speedup (201h → 12h)
- 99% cost reduction vs cloud AI through on-premises deployment
- 100% PII detection accuracy with custom veteran recognizers
- <20ms API response time for CFR condition mapping
- 18/18 integration tests passing (VetAssist Sprint 3)

**Enterprise Infrastructure (2016-Present)**:
- Lead Oracle DBA managing mission-critical environments
- Jira/Confluence administrator and Apple/Unix/Linux SME
- Mentor junior engineers in AI/ML and distributed systems
- 24/7 on-call rotation supporting "Behind the Glass" infrastructure

**Prior Walmart Roles** (1990-2016):
- BSM Engineering Team: Remedy 8.1.02 upgrade, 40% cost reduction via virtualization
- Infrastructure Build Test: Hardware certification standards
- Open Systems Unix Engineering: Team lead, patch management
- ISD Remedy Team: Enterprise server upgrades v2.1 → v6.2

---

## Military Service

**Arkansas Army National Guard** | *August 1987 - 2013*

**Sergeant First Class (E7) | Platoon Sergeant**
- Supervised 40 soldiers as Platoon Sergeant, Alpha Battery, 1-142nd Field Artillery
- Battalion Master Gunner (weapons SME) for MLRS systems
- Deployed to Operation Iraqi Freedom IV as Squad Leader
- Retired with honors after 26 years of distinguished service

---

## Education & Certifications

**Southern New Hampshire University** | *2019 - Present*
Bachelor of Science in Cyber Security (In Progress)

**Northwest Arkansas Community College** | *1997 - 2003*
- Phi Theta Kappa International Honor Society
- Dean's List: Spring 2002, Fall 2002, Spring 2003

**Certifications**:
- NVIDIA CUDA Programming (2024)
- PyTorch Deep Learning Specialization (2024)
- Healthcare Data Privacy & Security (2025)
- Advanced PostgreSQL Administration (2024)

---

## Technical Skills Matrix

| Category | Technologies |
|----------|-------------|
| **Languages** | Python, TypeScript, JavaScript, SQL, Bash, C/C++ |
| **AI/ML** | PyTorch, vLLM, MLX, CUDA, Transformers, Presidio, Demucs |
| **Backend** | FastAPI, Django, PostgreSQL, pgvector, Redis |
| **Frontend** | Next.js 14, React, Tailwind CSS, TypeScript |
| **Security** | JWT/OAuth2, bcrypt, Presidio PII, HIPAA compliance |
| **Observability** | Prometheus, Grafana, Loki, custom exporters |
| **DevOps** | Docker, Podman, Ansible, systemd, nginx |
| **Audio** | FFmpeg, CDP, SoundThread, Demucs, librosa |
| **Networking** | Tailscale, WireGuard, VLANs, nftables |

---

## Open Source & Portfolio

- **Cherokee AI Federation**: Democratic AI governance framework
- **VetAssist**: AI-powered veteran disability claims assistant
- **Thermal Memory System**: Temperature-based knowledge retrieval
- **Pathfinder Vision**: Distributed monitoring and observability

**Portfolio**: [ganuda.us](https://ganuda.us)

---

## References

Available upon request

---

*"Building AI systems that serve veterans and honor Seven Generations of wisdom"*
