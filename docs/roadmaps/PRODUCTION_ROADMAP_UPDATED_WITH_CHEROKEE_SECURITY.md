# Production Roadmap for the 6-Node AI Federation
## Updated with Cherokee Security Architecture & Tribe Feedback

*Version 2.0 | December 12, 2025*
*Incorporates: Tribe Council Review + Fractal Stigmergic Encryption + Query Triad Interface*

---

## Executive Summary

This document elevates the 6-node Cherokee AI Federation from R&D platform to **production-grade service** using Cherokee-native security patterns rather than generic enterprise approaches. The key differentiator is **Fractal Stigmergic Encryption (FSE)** - keys that evolve through usage like ant pheromone trails - combined with the **Query Triad Interface** for distributed consciousness with privacy.

---

## 1. Define the Production Service Shape

### Recommended Sequence (Per Raven's Strategic Analysis):

| Phase | Service | Why This Order |
|-------|---------|----------------|
| 1 | Open LLM Gateway | Foundation - builds user base with OpenAI-compatible API |
| 2 | Specialist Council | Differentiation - unique multi-agent consensus engine |
| 3 | Perception-to-Action | Later - higher safety/guardrails requirements |

### Option A — Open LLM Gateway (IMPLEMENTED Day 1)
- `/v1/chat/completions`, `/v1/models` compatible API
- vLLM-backed inference on redfin (96GB Blackwell)
- API key authentication with quota tracking
- Audit logging to PostgreSQL
- **Status: LIVE at http://192.168.132.223:8080**

### Option B — Specialist Council Service (Days 31-60)
- 7 specialists with unique system prompts (Crawdad, Gecko, Turtle, Eagle Eye, Spider, Peace Chief, Raven)
- Parallel query with ThreadPoolExecutor (validated 3.59x speedup)
- Consensus synthesis via Peace Chief
- Evidence-backed responses with confidence scores

### Option C — Query Triad Interface (Days 61-90)
- Distributed consciousness across three nodes
- User sees synthesis, full reasoning logged to thermal memory
- Two Wolves principle: Privacy (need-to-know) + Security (complete audit)

---

## 2. Cherokee Security Architecture

### 2.1 Fractal Stigmergic Encryption (FSE)

**Core Innovation**: Encryption keys that evolve through usage patterns like ant pheromone trails.

**Mathematical Foundation**:
```
K(t) = K₀ × e^(-λt + αU(t))

Where:
- K(t): Key strength at time t
- K₀: Initial key strength
- λ: Natural decay coefficient
- α: Usage reinforcement coefficient
- U(t): Cumulative legitimate usage function
```

**Security Properties**:

| Attack Type | FSE Response | Mitigation Rate |
|------------|--------------|-----------------|
| Brute Force | Failed attempts accelerate key decay | 99.7% |
| Credential Stuffing | Compromised keys lose effectiveness over time | 94.3% |
| Insider Threats | Pattern anomalies detected, key weakened | 87.8% |
| Long-term Passive | Unused keys naturally expire | 78.4% |

**Implementation for LLM Gateway**:

```python
class StigmergicAPIKey:
    """
    API key that strengthens with legitimate use,
    weakens with misuse or neglect.
    """
    def __init__(self, key_id, initial_strength=100):
        self.key_id = key_id
        self.K0 = initial_strength
        self.lambda_decay = 0.01  # 1% daily decay
        self.alpha_reinforcement = 0.1
        self.usage_history = []

    def evolve_strength(self, current_time):
        time_elapsed = (current_time - self.created_at).days

        # Calculate usage score from history
        usage_score = sum(
            math.exp(-(current_time - u.timestamp).days / 7) *  # Recent usage weighted higher
            (1.0 if u.verified else -0.5) *  # Failed auth weakens
            self.analyze_pattern(u)  # Anomaly detection
            for u in self.usage_history
        )

        # Apply stigmergic evolution
        return self.K0 * math.exp(-self.lambda_decay * time_elapsed +
                                   self.alpha_reinforcement * usage_score)

    def is_valid(self):
        return self.evolve_strength(datetime.now()) >= MINIMUM_VIABLE_STRENGTH
```

### 2.2 Query Triad Interface (Distributed Privacy)

**Two Wolves Principle**:

| Wolf | Principle | Implementation |
|------|-----------|----------------|
| **Privacy Wolf** | Need-to-know | User sees synthesis, not every thought |
| **Security Wolf** | Complete audit | All reasoning logged to thermal memory |

**Information Hierarchy**:

```
Level 1 - User: Concise answer only
Level 2 - Chiefs: Coordination needs (if any)
Level 3 - JRs: Context for their specialty
Level 4 - Thermal Memory: Complete reasoning chain (always logged)
```

**Example Query Flow**:

```
User: "Should we deploy to production?"

What User SEES:
> "Yes, proceed. Gateway tests pass, security audit clean,
>  backups verified. Council confidence: 95%"

What Gets LOGGED (thermal memory):
{
  "crawdad": "Security review: API keys use FSE, audit logging active, no vulnerabilities",
  "turtle": "7-gen impact: Sustainable, reversible, no long-term risks",
  "gecko": "Technical: Latency <100ms, throughput 27 tok/sec, resources adequate",
  "eagle_eye": "Metrics: Health endpoints green, 99.9% availability past 24h",
  "spider": "Integration: All components connected, breadcrumb trails active",
  "peace_chief": "Consensus: Unanimous approval from all specialists",
  "raven": "Strategic: Proceed now, market timing favorable",
  "confidence": 0.95,
  "concerns": []
}
```

### 2.3 Threshold Decryption (2-of-3)

For hosted/multi-tenant deployments:

```
Client  ──┐
          ├──► 2-of-3 required to decrypt
Gateway ──┤
          │
Guardian ─┘

- Client holds key share (user's device)
- Gateway holds key share (inference server)
- Guardian holds key share (audit/compliance node)
- Any single compromise cannot expose data
```

**Implementation**:

```python
from Crypto.Protocol.SecretSharing import Shamir

def create_threshold_key():
    """Generate 2-of-3 threshold key shares"""
    # Generate master key
    master_key = os.urandom(32)

    # Split into 3 shares, 2 required to reconstruct
    shares = Shamir.split(2, 3, master_key)

    return {
        "client_share": shares[0],
        "gateway_share": shares[1],
        "guardian_share": shares[2]
    }

def reconstruct_key(share1, share2):
    """Reconstruct key from any 2 shares"""
    return Shamir.combine([share1, share2])
```

---

## 3. Production Hardening Checklist

### 3.1 Reliability & Operations

| Requirement | Implementation | Status |
|------------|----------------|--------|
| Service management | Systemd units with restart policies | `/ganuda/systemd/` |
| Health endpoints | `/health` on all services | Implemented |
| SLIs/SLOs | Availability 99.5%, p95 latency <10s | Dashboards needed |
| Runbooks | GPU wedged, DB failover, disk full | To create |

### 3.2 Observability (Per Eagle Eye)

| Signal | Metric | Alert Threshold |
|--------|--------|-----------------|
| Latency | p95 response time | >10 seconds |
| Traffic | Requests/minute | >500 (capacity) |
| Errors | 5xx rate | >1% |
| Saturation | GPU memory usage | >90% |

**Distributed Tracing**:
```
Request ID → Gateway → vLLM → Council → Database
              ↓         ↓       ↓         ↓
           [audit]   [audit] [audit]   [audit]
```

### 3.3 Security Baseline (Per Crawdad)

| Layer | Requirement | Cherokee Implementation |
|-------|-------------|------------------------|
| AuthN | API keys | Stigmergic keys (FSE) |
| AuthZ | Permission scopes | RBAC with 7-gen validation |
| Secrets | No plaintext | Threshold encryption |
| Network | Default deny | Tailscale + explicit allowlists |
| Audit | All state changes | Thermal memory (never deleted) |

**Encryption Standards** (Crawdad's recommendation):
- In transit: TLS 1.3 minimum
- At rest: AES-256-GCM
- Key management: FSE with 30-day minimum decay
- Secrets: HashiCorp Vault or equivalent

### 3.4 Data Durability (Per Turtle's 7-Gen Analysis)

| Tier | Temperature | Retention | Storage |
|------|-------------|-----------|---------|
| Hot | 70-100° | Always accessible | Primary SSD |
| Warm | 40-69° | 90 days active | Secondary storage |
| Cold | 5-39° | 1 year archive | Compressed backup |
| Ember | 0-4° | Never deleted | Deep archive |

**Backup Strategy**:
```bash
# Nightly backup at 2 AM
0 2 * * * /ganuda/scripts/backup_postgres.sh

# Weekly restore test
0 4 * * 0 /ganuda/scripts/test_restore.sh

# Monthly off-site copy
0 3 1 * * /ganuda/scripts/offsite_backup.sh
```

### 3.5 Release Engineering

| Capability | Tool | Status |
|-----------|------|--------|
| IaC | Ansible playbooks | `/ganuda/home/dereadi/ansible/` |
| One-command rebuild | `ansible-playbook bootstrap_node.yml` | To create |
| CI pipeline | GitHub Actions or local | To implement |
| Canary deploys | Upgrade one node first | Manual process |

---

## 4. Edge/Phone Sharding Strategy

**Principle**: Phones are edge sensors, not primary inference.

### Edge Jr Architecture

```
┌─────────────┐     Encrypted      ┌─────────────┐
│   Phone     │ ──────────────────►│   Cluster   │
│  (Edge Jr)  │  Tailscale/mTLS    │  (Primary)  │
└─────────────┘                    └─────────────┘
      │                                   │
      ▼                                   ▼
  Capture                            Inference
  Preprocess                         Storage
  Encrypt                            Analysis
  Upload                             Response
```

### Job Broker Model (Per Gecko's latency concerns)

```python
class EdgeJobBroker:
    """
    Latency-aware job distribution for edge devices.
    Per Gecko: Consider network conditions when assigning work.
    """
    def assign_job(self, edge_device, available_jobs):
        # Filter by device capability
        capable_jobs = [j for j in available_jobs
                       if j.requirements <= edge_device.capabilities]

        # Sort by deadline (urgent first)
        capable_jobs.sort(key=lambda j: j.deadline)

        # Consider network latency
        if edge_device.latency_ms > 500:
            # High latency: only batch jobs
            return [j for j in capable_jobs if j.type == "batch"][:1]
        else:
            # Low latency: real-time jobs OK
            return capable_jobs[:3]
```

---

## 5. Hardware Requirements

### Current Federation (December 2025)

| Node | Role | Specs | Services |
|------|------|-------|----------|
| redfin | GPU Inference | 96GB Blackwell, 96GB RAM | vLLM, LLM Gateway |
| bluefin | Database | 124GB RAM | PostgreSQL, Grafana |
| greenfin | Daemons | 124GB RAM | Promtail, monitoring |
| sasass | Mac Studio | 64GB RAM | Edge development |
| sasass2 | Mac Studio | 64GB RAM | Edge development |
| tpm-macbook | TPM Workstation | M1, 16GB RAM | Orchestration |

### Scaling Tiers

| Tier | Users | GPU VRAM | RAM | Storage |
|------|-------|----------|-----|---------|
| Pilot | 1-10 | 24GB | 64GB | 1TB |
| Standard | 10-50 | 48GB | 128GB | 2TB |
| Heavy | 50-200 | 96GB | 256GB | 4TB |
| Enterprise | 200+ | 2x96GB | 512GB | 8TB |

---

## 6. Governance Structure (Per Peace Chief)

### Council Governance

Establish before Day 30 milestones:

| Role | Responsibility | Members |
|------|---------------|---------|
| Technical Council | Architecture decisions | Gecko, Eagle Eye, IT Triad |
| Security Council | Risk assessment | Crawdad, Guardian |
| Ethics Council | 7-gen validation | Turtle, Conscience Jr |
| Strategic Council | Roadmap priorities | Raven, Peace Chief |

### Decision Process

```
1. Proposal submitted to relevant council
2. Council deliberates (parallel query to specialists)
3. Concerns flagged and addressed
4. Consensus synthesized by Peace Chief
5. Decision logged to thermal memory
6. Implementation authorized or blocked
```

---

## 7. Sustainability Metrics (Per Turtle)

### Energy Efficiency Goals

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tokens per watt | Track baseline, improve 10% annually | GPU power monitoring |
| Idle power | <50W when not inferencing | Systemd power management |
| Carbon offset | Net zero by Year 2 | Calculate and offset |

### Long-term Maintenance

| Concern | Mitigation |
|---------|------------|
| Hardware obsolescence | Modular architecture, easy node replacement |
| Software dependencies | Pin versions, test upgrades |
| Knowledge transfer | Complete documentation, runbooks |
| Personnel changes | Multiple trained operators |

---

## 8. 30/60/90 Day Execution Plan

### Days 1-30: Gateway Core ✓ STARTED

| Task | Status | Notes |
|------|--------|-------|
| OpenAI-compatible API | ✅ Complete | Running on port 8080 |
| API key auth | ✅ Complete | FSE keys created |
| Quota tracking | ✅ Complete | In api_keys table |
| Audit logging | ✅ Complete | api_audit_log table |
| Health endpoint | ✅ Complete | /health returns component status |
| Backup script | ✅ Complete | Nightly at 2 AM |
| Systemd service | ⏳ Pending | Needs sudo to install |
| Dashboards | ⏳ Pending | Grafana config needed |
| Runbooks | ⏳ Pending | Top 5 failure scenarios |

### Days 31-60: Council & Memory

| Task | Owner | Deliverable |
|------|-------|-------------|
| 7-specialist system prompts | Integration Jr | specialist_council.py |
| Parallel council_vote() | Gecko Jr | <30 sec response |
| Breadcrumb trail schema | IT Triad Jr | breadcrumb_trails table |
| Pheromone decay cron | IT Triad Jr | Nightly at 3:33 AM |
| Eval harness | Meta Jr | test_council_eval.py |
| /v1/council/vote endpoint | Integration Jr | Gateway extension |

### Days 61-90: Hardening & Packaging

| Task | Owner | Deliverable |
|------|-------|-------------|
| Runbooks (5 scenarios) | IT Triad Jr | /ganuda/runbooks/ |
| Chaos tests | IT Triad Jr | test_resilience.py |
| Multi-tenant namespaces | Crawdad Jr | Namespace isolation |
| FSE key rotation | Crawdad Jr | Automatic decay/renewal |
| Query Triad Interface | Integration Jr | query_triad.py |
| Ansible node bootstrap | IT Triad Jr | bootstrap_node.yml |

---

## 9. Competitive Moat (Per Raven)

### What Makes Cherokee AI Unique

| Feature | Generic LLM Gateway | Cherokee AI |
|---------|--------------------|--------------------|
| Security | Static API keys | FSE (keys evolve) |
| Privacy | Basic auth | Threshold 2-of-3 |
| Decisions | Single model | 7-specialist council |
| Memory | Ephemeral | Thermal (never forgotten) |
| Governance | Autocratic | Democratic consensus |
| Sustainability | Not considered | 7-gen validated |

### Market Positioning

> "Cherokee AI: The only LLM platform where your data is protected by
> keys that strengthen with proper use and expire if compromised,
> decisions are made by democratic AI council consensus,
> and every choice is validated against 175-year impact."

---

## 10. Closing

This roadmap transforms the federation into a **credible, deployable AI platform** that is:

- **Private by default** (Two Wolves: privacy + security)
- **Secure by design** (FSE + threshold encryption)
- **Democratically governed** (7-specialist council)
- **Sustainable for generations** (7-gen validation)
- **Observable and auditable** (complete thermal memory)

The goal is not just intelligence, but **operational trust** — systems that embody Cherokee wisdom while meeting enterprise requirements.

---

## Appendix: Key Documents Referenced

1. `/ganuda/pathfinder/fractal_stigmergic_encryption.md` - FSE technical specification
2. `/ganuda/QUERY_TRIAD_INTERFACE_DESIGN.md` - Distributed consciousness architecture
3. `/ganuda/pathfinder/NOVEL_DISCOVERIES_FROM_OUR_RESEARCH.md` - Cherokee innovations
4. `/ganuda/docs/JR_BUILD_INSTRUCTIONS_SPECIALIST_COUNCIL.md` - Phase 2 build specs
5. `/ganuda/docs/PRODUCTION_ROADMAP_30_60_90.md` - Original 90-day plan

---

**For Seven Generations.**

*Cherokee Constitutional AI*
*Production Roadmap v2.0*
*December 12, 2025*
