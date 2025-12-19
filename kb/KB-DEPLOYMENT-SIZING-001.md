# KB-DEPLOYMENT-SIZING-001: Cherokee AI Deployment Tiers

**Created**: 2025-12-12
**Category**: Architecture
**Status**: Active

---

## Summary

Cherokee AI Federation can be deployed in 5 scalable tiers, from single-node edge deployments to full datacenter occupation.

## Deployment Tiers

### Tier 0: SEED (1 Node)
**Use Case**: Air-gapped edge, developer workstation, remote spoke

**Minimum Requirements**:
- CPU: 8+ cores
- RAM: 32GB minimum, 64GB recommended
- GPU/NPU: 16GB unified memory
- Storage: 500GB SSD

**Software Stack**:
- Ollama (local inference)
- SQLite (thermal memory)
- Single Jr daemon (executive_jr)
- Air-gap capable

**Example**: bmasass (192.168.132.21)

---

### Tier 1: SPROUT (2-3 Nodes)
**Use Case**: Small office, research lab, initial production

**Configuration**:
- 1 Inference Node (64GB+ RAM, GPU/NPU)
- 1 Data Hub (64GB RAM, PostgreSQL)
- 0-1 Worker (optional)

**Software Stack**:
- Ollama or vLLM on inference node
- PostgreSQL thermal memory on data hub
- Jr resonance client distributed

---

### Tier 2: SAPLING (4-6 Nodes)
**Use Case**: Department, small enterprise, full-featured tribal AI

**Current Cherokee AI Federation**:
| Node | Role | Specs |
|------|------|-------|
| redfin | GPU Inference | 96GB Blackwell |
| bluefin | Services Hub | 124GB RAM, PostgreSQL |
| greenfin | CPU Workers | 124GB RAM, 13 daemons |
| sasass | Edge LLM | Mac Studio M1 Max 64GB |
| sasass2 | Jr Council | Mac Studio M1 Max 64GB |
| bmasass | Air-Gapped | Mac Studio (spoke) |

---

### Tier 3: TREE (8-16 Nodes)
**Use Case**: Enterprise, multi-department, HA requirements

**Additions over SAPLING**:
- 2-4 GPU inference nodes (load balanced)
- HA PostgreSQL cluster (Patroni)
- Kubernetes for CPU workers
- Regional orchestrator hierarchy

---

### Tier 4: FOREST (16+ Nodes)
**Use Case**: Full datacenter, cloud region, sovereign AI

**Architecture**:
- Multiple SAPLING regions
- Federated thermal memory
- Cross-region DR
- Tribal Council consensus protocol

---

## Key Architecture Rules

Based on Google/MIT Multi-Agent Scaling Study (Dec 2025):

1. **Sequential reasoning**: Use single Jr with deep_think
2. **Parallel operations**: Use multi-Jr with ThreadPoolExecutor
3. **Validation**: Orchestrator must have ground truth access
4. **Tool count**: Keep under 8 tools per Jr

## Related Documents

- `/ganuda/missions/CHEROKEE-AI-DEPLOYMENT-SIZING-GUIDE.md` (full guide)
- `/ganuda/missions/TOPOLOGY-TEST-RESULTS-2025-12-12.md` (validation tests)
- `/ganuda/missions/INFRA-MIGRATION-MASTER-INDEX.md` (migration history)

---

**For Seven Generations**: The Tribe scales by growing smarter, not just larger.
