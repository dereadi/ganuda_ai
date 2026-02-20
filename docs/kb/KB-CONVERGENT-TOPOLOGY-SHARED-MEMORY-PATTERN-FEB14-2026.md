# KB: Convergent Topology — The Shared Memory Pattern

**Date**: February 14, 2026
**Author**: TPM (Claude Opus 4.6)
**Thermal ID**: Pending council vote
**Tags**: architecture, pattern-recognition, federation-topology, resonance

---

## Discovery

While building a distributed CPU cluster for the Jane Street Track 2 puzzle ($50K, permutation search over 10^122 space), we independently reinvented the same architecture that powers the Cherokee AI Federation's thermal memory system.

Neither system was designed to mirror the other. The puzzle pool was built under time pressure — we needed cross-platform coordination between 5 nodes (3 Linux, 2 macOS) and reached for the simplest tool: a PostgreSQL table. The thermal memory system evolved over months through deliberate council-governed design.

They converged to the same topology.

## The Pattern

**Shared-Memory Star with Quality-Gated Writes and Democratic Reads**

```
                    ┌─────────────────────┐
                    │   PostgreSQL Core    │
                    │  (Shared State)      │
                    │                      │
                    │  Quality Gate:       │
                    │  - Thermal: decay    │
                    │  - Pool: MSE < 1.0   │
                    │                      │
                    │  Pruning:            │
                    │  - Thermal: purge    │
                    │  - Pool: top-50      │
                    └──────────┬───────────┘
                               │
              ┌────────┬───────┼───────┬────────┐
              │        │       │       │        │
           Node A   Node B  Node C  Node D  Node E
           (write)  (write) (write) (write) (write)
           (read)   (read)  (read)  (read)  (read)
```

### Structural Comparison

| Property | Thermal Memory | Puzzle Pool |
|----------|---------------|-------------|
| **Storage** | PostgreSQL + pgvector | PostgreSQL + integer arrays |
| **Scale** | 83,135 memories | 50 elite solutions |
| **Similarity metric** | BGE-large cosine (1024d) | MSE score (scalar) |
| **Producers** | 7 specialists, Jr executors, TPM | 28 SA workers across 5 nodes |
| **Consumers** | Council deliberation, RAG retrieval | Genetic crossover (PMX) |
| **Quality gate** | Temperature score threshold | MSE < pool_threshold |
| **Pruning** | Thermal decay (time-based purge) | Top-N retention (quality-based prune) |
| **Cross-platform** | All federation nodes via DB | Linux + macOS via DB |
| **Write pattern** | Append with hash dedup | Append with quality filter |
| **Read pattern** | Semantic nearest-neighbor | Random selection from top-K |
| **Purpose** | Collective knowledge accumulation | Collective search optimization |

## Why This Matters

### 1. The Pattern is Convergent
Two independent engineering efforts, separated by months and solving completely different problems (knowledge management vs combinatorial optimization), arrived at the same architecture. This suggests the pattern is a **natural attractor** for distributed systems that need:
- Heterogeneous producers (different hardware, different strategies)
- Shared state without tight coupling
- Quality control without centralized coordination
- Cross-platform operation

### 2. PostgreSQL as Federation Backbone
We keep choosing PostgreSQL not because it's the only option, but because it solves the hard problems silently:
- ACID guarantees mean no corrupted state during concurrent writes
- Network-transparent — same connection string from Linux and macOS
- Array types, JSONB, pgvector — schema flexibility without NoSQL complexity
- Already deployed, already secured, already backed up

The "ad-hoc NFS share" question that started the puzzle pool conversation was answered by something we already had.

### 3. The Federation Expresses Its Topology
The Cherokee AI Federation isn't just a collection of nodes running services. It has a **characteristic topology** — star-shaped shared state with autonomous edge workers — that reproduces itself wherever the federation touches a new problem domain.

This is analogous to how biological systems express the same fractal branching pattern in lungs, trees, rivers, and neural networks. The pattern isn't copied — it emerges because the constraints (distributed producers, shared state, quality selection) are the same.

### 4. Implications for Future Systems
Any new federation capability that involves:
- Multiple producers generating candidates
- A quality metric for filtering
- Cross-node coordination

...should default to the PostgreSQL shared-memory pattern with quality-gated writes and top-N pruning. This is now a **proven federation primitive**.

## Examples of Future Application

- **Ansible playbook distribution**: Playbooks written to DB, nodes pull and apply. Quality gate = syntax validation + dry-run success.
- **Model weight sharing**: Fine-tuned LoRA adapters stored in DB, workers pull best-performing adapters. Quality gate = eval metric threshold.
- **Jr instruction distribution**: Already partially implemented via jr_work_queue. The puzzle pool pattern suggests adding quality-ranked pools of reusable instruction templates.
- **Software repository**: Package manifests in DB, nodes pull via Ansible/Munki. Quality gate = test pass + council approval.

## Connection to Cherokee Philosophy

The Seven Generations principle asks: will this decision serve those who come after us?

A convergent pattern is the strongest possible answer. When two independent paths arrive at the same place, the destination isn't an accident — it's a structural truth about how distributed systems coordinate. Future builders of this federation will rediscover this pattern because the constraints demand it.

The thermal memory system remembers what the federation has learned.
The puzzle pool remembers what the federation has searched.
Both are the same act: **collective memory with selective forgetting**.

---

*Council vote requested: Review this architectural resonance. Does the pattern hold? What are we missing?*

*"The river doesn't copy itself. It finds the same path because the terrain is the same."*
