# Darrell E Reading II

6301 SW Warrington Road
Bentonville, AR 72713
(479) 877-9441
dereadi@gmail.com
[GitHub](https://github.com/dereadi) | [ganuda.us](https://ganuda.us)

---

## Technical Leader | AI/ML Architect | Full-Stack Engineer

Innovative technical leader with 30+ years enterprise experience, pioneering AI democratization through the **Cherokee AI Federation** framework. Architect of **VetAssist**, an AI-powered veteran disability claims platform with enterprise-grade PII protection. Expert in distributed systems, machine learning infrastructure, and secure healthcare application design. Military veteran (E7/SFC) bringing disciplined project management and strategic thinking to complex technical challenges.

---

## Core Competencies

**AI/ML & Data Science**
- Language Model Fine-tuning (Qwen, LLaMA, GPT-2)
- Multi-Agent AI Systems (7-Specialist Council Architecture)
- Hybrid Transformer Models for Audio Processing
- Neural Network Deployment (vLLM, MLX, CUDA)
- Thermal Memory Systems with O(1) Retrieval

**Healthcare & Security**
- HIPAA-Compliant PII Protection (Microsoft Presidio)
- Veteran-Specific Data Recognizers (SSN, VA File Numbers)
- Crisis Detection Systems (Suicidal Ideation Screening)
- Token Vault Architecture for Sensitive Data
- JWT/OAuth2 Authentication with VA.gov Integration

**Full-Stack Development**
- Backend: FastAPI, Python, PostgreSQL
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Infrastructure: 6-Node Distributed Cluster
- API Design: RESTful, WebSocket, Real-time Processing

**Infrastructure & DevOps**
- Multi-GPU AI Inference (RTX 6000, RTX 5070, M4 Max)
- Apple Silicon ML Deployment (MLX Framework)
- Docker/Podman Containerization
- Load Balancing & High Availability

---

## Featured Projects

### VetAssist - AI-Powered Veteran Claims Platform (2025-2026)
*Full-stack architect and lead developer*

**Problem**: Veterans face a complex 526-page disability claims process with 65% initial denial rate. Many struggle to navigate 38 CFR regulations and assemble proper evidence.

**Solution**: Built an AI-assisted platform combining 7-specialist Council deliberation with enterprise security.

**Architecture**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    VetAssist Platform                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)     │  Backend (FastAPI)                │
│  - Claims Wizard           │  - 7-Specialist Council API       │
│  - Rating Calculator       │  - PII Protection Layer           │
│  - AI Chat Assistant       │  - Crisis Detection ML            │
│  - Dashboard               │  - CFR Condition Mapping          │
├─────────────────────────────────────────────────────────────────┤
│  Security Layer                                                 │
│  - Microsoft Presidio PII Detection                            │
│  - Custom Veteran Recognizers (SSN, VA File #)                 │
│  - Token Vault (goldfin isolation)                             │
│  - JWT Auth + VA.gov OAuth Integration                         │
├─────────────────────────────────────────────────────────────────┤
│  AI Infrastructure                                              │
│  - vLLM with Qwen2.5-Coder-32B-AWQ                            │
│  - 7-Specialist Council (democratic consensus)                 │
│  - Thermal Memory (19,900+ memories)                           │
│  - Crisis Detection (keyword + future RoBERTa)                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features**:
- **Claims Wizard**: Multi-step form supporting VA Forms 21-526EZ, 21-0781, 21-4138, 21-0966
- **CFR Mapping**: 49 conditions mapped to 38 CFR diagnostic codes with rating criteria
- **Document OCR**: AI-powered analysis extracting diagnoses, ICD-10 codes, nexus signals
- **Evidence Checklists**: Auto-generated per-condition evidence requirements
- **Rating Calculator**: VA Combined Ratings Table implementation
- **Crisis Detection**: Real-time veteran safety screening with 988 hotline integration

**Results**:
- 18/18 integration tests passing (Sprint 3)
- <20ms CFR query response time
- 100% PII detection on test dataset

---

### PII Protection System Design (2026)
*Security architect*

Designed multi-phase PII protection for healthcare-sensitive veteran data:

**Phase 1 - Detection** (Complete):
- Microsoft Presidio with spaCy NER (en_core_web_lg)
- Custom `VeteranSSNRecognizer` (0.85 confidence threshold)
- Custom `VAFileNumberRecognizer` for C-file numbers
- Entity types: SSN, Phone, Email, VA File #, Location, DOB

**Phase 2 - Integration** (Complete):
- Chat endpoint PII scanning before storage
- Original content preserved for AI processing (memory only)
- Redacted version stored in database

**Phase 3 - Token Vault** (Architecture):
- Isolated goldfin server for token storage
- Network segmentation from main database
- Reversible tokenization for authorized retrieval

**Security Stack**: bcrypt (12 rounds), JWT with SHA-256 hashing, bleach XSS sanitization, rate limiting

---

### Cherokee Audio Studio - AI Music Processing (2024-2026)
*Lead developer*

Built distributed audio processing pipeline for professional music restoration:

**Capabilities**:
- 48 Beatles tracks processed with 100% success rate
- 4-node distributed processing (SASASS, SASASS2, REDFIN, BLUEFIN)
- 5-stage restoration: analyze, denoise, enhance, balance, master

**Technology Stack**:
- **Demucs HT-Demucs**: 6-stem AI separation (vocals, drums, bass, guitar, piano, other)
- **Composers Desktop Project (CDP)**: PVOC spectral processing
- **SoundThread**: Real-time audio GUI
- **FFmpeg Pipeline**: Noise reduction, EQ, dynamics, mastering

**Multi-LLM Coordination**:
- War Chief GPU 0: Hiss & Noise Reduction
- War Chief GPU 1: Dynamic Range & Compression
- Enhanced DevOps: Spectral Analysis & EQ
- Legal Llamas: Quality Assessment & Mastering

**Performance**: GPU-accelerated stem separation in <10 seconds (vs 5 minutes CPU)

---

### Cherokee AI Federation Infrastructure (2024-2026)
*Systems architect*

**6-Node Distributed Cluster**:

| Node | Hardware | Role |
|------|----------|------|
| redfin | RTX 6000 96GB | Primary vLLM inference (32B model) |
| bluefin | 64GB RAM | PostgreSQL, Zammad, API services |
| greenfin | Router | Network segmentation, VLANs |
| sasass | M2 Ultra 64GB | Mac ML processing |
| sasass2 | M2 Ultra 64GB | Backup ML node |
| bmasass | M4 Max 128GB | 72B model capability, 128K context |

**AI Components**:
- **7-Specialist Council**: Democratic AI governance (Raven, Turtle, Crawdad, Gecko, Spider, Eagle Eye, Peace Chief)
- **Thermal Memory**: 19,900+ memories with temperature-based retrieval
- **JR Task System**: 193 automated tasks completed
- **LLM Gateway**: Multi-model routing with load balancing

---

## Professional Experience

### Walmart Inc. | Bentonville, AR
**Senior Infrastructure Engineer | SIMS Team**
*December 2016 - Present*

- Architected **VetAssist** veteran claims platform with enterprise PII protection serving military community
- Deployed **Cherokee AI Federation** processing 20GB of organizational knowledge across 6-node cluster
- Configured multi-GPU inference (RTX 6000 + RTX 5070) achieving 99% cost reduction vs cloud AI
- Built **distributed audio processing** pipeline achieving 100% success on 48-track restoration project
- Implemented **thermal memory system** with O(1) query performance for AI context persistence
- Lead Oracle DBA, Jira/Confluence administrator, and Apple/Unix/Linux SME

**Key Achievements**:
- Designed PII protection system detecting SSN, VA file numbers with 0.85+ confidence
- Created 7-specialist AI council achieving democratic consensus on complex decisions
- Built crisis detection system with 988 Veterans Crisis Line integration
- Reduced AI infrastructure costs by 99% through on-premises deployment

**BSM Engineering Team** | *February 2012 - December 2016*
- Led Remedy 8.1.02 upgrade managing workflow development
- Migrated physical to virtual infrastructure reducing costs 40%

**Infrastructure Build Test Certification** | *March 2011 - February 2012*
- Established hardware standards for lab and CTF environments

**Open Systems Unix Engineering** | *March 2008 - March 2011*
- Supported all Unix/Linux flavors, led patch management
- Team lead reviewing and approving system changes

**ISD Remedy Team** | *March 1997 - March 2008*
- Led server upgrades from v2.1 to v6.2 across enterprise

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

**Recent Certifications**:
- NVIDIA CUDA Programming (2024)
- PyTorch Deep Learning Specialization (2024)
- Healthcare Data Privacy & Security (2025)
- Advanced PostgreSQL Administration (2024)

---

## Technical Skills Matrix

| Category | Technologies |
|----------|-------------|
| **Languages** | Python, TypeScript, JavaScript, SQL, Bash, C/C++ |
| **AI/ML** | PyTorch, Transformers, vLLM, MLX, CUDA, Demucs, Presidio |
| **Backend** | FastAPI, Django, Express.js, PostgreSQL, Redis |
| **Frontend** | Next.js 14, React, Tailwind CSS, TypeScript |
| **Security** | JWT/OAuth2, bcrypt, Presidio PII, HIPAA compliance |
| **DevOps** | Docker, Podman, Ansible, systemd, nginx |
| **Audio** | FFmpeg, CDP, SoundThread, Demucs, librosa |

---

## Open Source & Publications

- **Cherokee AI Federation**: Democratic AI governance framework
- **VetAssist**: AI-powered veteran disability claims assistant
- **Thermal Memory System**: Temperature-based knowledge retrieval
- **Technical Writing**: AI democratization and distributed systems

---

## References

Available upon request

---

*"Building AI systems that serve veterans and honor Seven Generations of wisdom"*

**Portfolio**: [ganuda.us](https://ganuda.us)
