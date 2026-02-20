# KB: Research Compilation — Representational Geometry, Agent Reliability, Cluster Resilience

**Date:** 2026-02-03
**Source:** Discover AI transcript + TPM literature scan
**Status:** Active research — Tribe should consume and apply

---

## The Big Insight (Google DeepMind, Jan 29 2026)

**Paper:** "Context Structure Reshapes the Representational Geometry of Language Models"
**arXiv:** 2601.22364
**Authors:** Hosseini, Li, Bahri (DeepMind), Campbell (Princeton Neuroscience), Lampinen (DeepMind)

Transformers progressively straighten token sequences into linear trajectories through layers 15-25. Next-token prediction becomes simple linear extrapolation. **But this only works for coherent flow.** When the model needs to reason (few-shot Q&A, planning, logic), the straightening collapses and it performs nonlinear manifold hops — which it's bad at.

**Why this matters to us:** When Qwen 32B got "modify jr_queue_client.py" without existing file contents, it wasn't reasoning about the file. It was flowing — extrapolating the most linearly probable "queue client" from training data (Celery + Redis). Our file context injection converts reasoning tasks into flow tasks, keeping the model in its linear regime.

### Related Foundation Papers

| Paper | arXiv | Key Finding |
|-------|-------|-------------|
| LLMs implicitly learn to straighten neural sentence trajectories (MIT, 2023) | 2311.04930 | Curvature decreases from first to middle layers. Better models = more straightening. |
| Why Reasoning Fails to Plan (Notre Dame/Stanford/Yale/etc, Jan 2026) | 2601.22311 | Step-wise reasoning induces greedy policies. Locally optimal choices amplify into myopic commitments over time. Introduces FLARE: future-aware lookahead with reward estimation. LLaMA-8B with FLARE outperforms GPT-4o with standard reasoning. |
| Emergent temporal abstractions in autoregressive models (Google, Dec 2025) | 2512.20605 | Metacontroller steers residual stream activations. Learns goal-optimizing controllers with temporal abstraction. Enables "internal RL" from sparse rewards where standard RL finetuning fails. |

---

## Papers That Make Our Cluster More Bulletproof

### P0 — Implement Now

#### 1. "Towards a Science of Scaling Agent Systems" (Google DeepMind, Dec 2025)
**arXiv:** 2512.08296

**The number:** 17.2x error amplification in independent agents vs 4.4x with centralized coordination.

Single-agent accuracy threshold ~45% — above this, adding agents yields diminishing returns. Centralized coordination improves parallelizable tasks by 80.8%.

**Action:** Add a validation bottleneck between Jr output and commit. Our staging system is already half of this — we need to make the TPM review step faster and more systematic.

#### 2. "Where LLM Agents Fail and How They Learn From Failures" (Sep 2025)
**arXiv:** 2509.25370

Introduces **AgentDebug** framework with **AgentErrorTaxonomy**: modular classification spanning memory, reflection, planning, action, and system-level operations. 24% higher all-correct accuracy with root-cause isolation.

**Action:** Classify our failed tasks using this taxonomy. Build the classification into the momentum learner so it learns from categorized failures, not raw error strings.

#### 3. "Agent Drift: Behavioral Degradation Over Extended Interactions" (Jan 2026)
**arXiv:** 2601.04170

Three types of drift: semantic (meaning changes), coordination (consensus breakdown), behavioral (action patterns degrade). Particularly relevant for long-running federations.

**Action:** Our workers ran for 6+ days on stale code. This IS drift. The max-tasks-per-child fix addresses behavioral drift. We need to monitor coordination drift across the Triad nodes.

### P1 — High Value

#### 4. "LLM Hallucinations in Practical Code Generation" (ISSTA 2025)
**arXiv:** 2409.20550

Tested 6 mainstream LLMs on repository-level code gen. RAG-based mitigation is consistently effective. Taxonomy of 3 primary categories, 12 subcategories of hallucination.

**Action:** Our file context injection is a form of RAG. Consider extending it to include related files (imports, callers) not just the target file.

#### 5. "Chaos Engineering for LLM-based Multi-Agent Systems" (May 2025)
**arXiv:** 2505.03096

Framework for testing LLM-based multi-agent systems through controlled failure injection — agent failures, communication delays, disruptions.

**Action:** Build chaos tests: What happens when bluefin drops? When vLLM returns 503? When a Jr worker segfaults mid-task? We should know before production tells us.

#### 6. "End-to-End Test-Time Training for Long Context" (Dec 2025)
**arXiv:** 2512.23675

Formulates long-context as continual learning, not architecture. Model continues learning at test time via next-token prediction. **2.7x faster than full attention for 128K context.** Tested on Qwen models.

**Action:** This could solve our context window problem more fundamentally than character budgets. The model compresses repository context into weights at inference time.

#### 7. MMR-GRPO: Diversity-Aware Reward Reweighting (Jan 2026)
**arXiv:** 2601.09085

Integrates Maximal Marginal Relevance to reweigh rewards based on completion diversity. 47.9% fewer training steps, 70.2% less wall-clock time.

**Action:** Our GRPO/momentum learner should prioritize diverse failure modes rather than repeatedly learning from similar errors.

### P2 — Strategic

#### 8. FLARE: Future-Aware Lookahead (from "Why Reasoning Fails to Plan")

LLaMA-8B with FLARE outperforms GPT-4o with standard reasoning on long-horizon tasks. Forces the model to evaluate futures, not just predict next step.

**Action:** If we implement lookahead in the PM model's planning phase, task plans would account for downstream consequences rather than greedy step-by-step.

#### 9. CORAL: Cognitive Resource Self-Allocation (ICLR 2026 submission)
**OpenReview:** NBGlItueYE

Working memory management with checkpoints and adaptive purging. Addresses cognitive overload in long-horizon tasks.

**Action:** Jr tasks with >5 steps should checkpoint after each milestone and prune irrelevant context. Integrates with thermal memory.

#### 10. Saga Pattern for AI Task Execution
**Sources:** Temporal blog, microservices resilience review (arXiv 2512.16959)

Compensating transactions for multi-step operations. Under network partitions with >200ms delay, sagas recovered in 2.5 seconds via compensations.

**Action:** Task 553 (Saga Rollback) was already queued for this. The Jr instruction is written. Needs TPM deployment since it modifies jr_executor.

---

## Cluster Resilience Specifics

### Observability
- **OpenTelemetry** instrumentation for all Python services (lightweight, open-source)
- Track: prompt tokens, completion tokens, latency, success rate per model/node
- Store in PostgreSQL, visualize in Grafana (already on bluefin:3000)
- Alert when costs spike or quality degrades below threshold

### Self-Healing
- Health probes (HTTP endpoints) on all daemons
- Watchdog processes that auto-restart failed services
- Supervised automation first: suggest remediation via Telegram before auto-executing
- Dynamic task routing based on node health, not static assignment

### Redundancy
- Run critical inference on 2+ nodes with voting/consensus
- Route lighter tasks (entity extraction) to Mac Studios
- Reserve heavy tasks (code gen, document analysis) for GPU nodes
- Implement automatic traffic routing when a node fails

---

## Information Hoarding Prevention

The Tribe should be information-hungry but not information-hoarding. Principles:

1. **Research goes to `/ganuda/docs/kb/`** — shared, indexed, searchable
2. **Insights get thermal memories** — persist across sessions
3. **Actionable findings become Jr instructions** — research turns into work
4. **Council votes on architectural changes** — no unilateral decisions from research
5. **Regular research digestion sessions** — scheduled, not ad hoc

The goal: every Jr and every Triad node has access to the same research base. No private knowledge silos.

---

## arxiv Links for Deep Dives

| # | Paper | arXiv |
|---|-------|-------|
| 1 | Context Structure Reshapes Representational Geometry | [2601.22364](https://arxiv.org/abs/2601.22364) |
| 2 | LLMs Straighten Neural Sentence Trajectories (MIT) | [2311.04930](https://arxiv.org/abs/2311.04930) |
| 3 | Why Reasoning Fails to Plan (FLARE) | [2601.22311](https://arxiv.org/abs/2601.22311) |
| 4 | Emergent Temporal Abstractions | [2512.20605](https://arxiv.org/abs/2512.20605) |
| 5 | Scaling Agent Systems (17.2x error amplification) | [2512.08296](https://arxiv.org/abs/2512.08296) |
| 6 | Where LLM Agents Fail (AgentDebug) | [2509.25370](https://arxiv.org/abs/2509.25370) |
| 7 | Agent Drift | [2601.04170](https://arxiv.org/abs/2601.04170) |
| 8 | LLM Hallucinations in Code Generation | [2409.20550](https://arxiv.org/abs/2409.20550) |
| 9 | Chaos Engineering for LLM-MAS | [2505.03096](https://arxiv.org/abs/2505.03096) |
| 10 | Test-Time Training for Long Context | [2512.23675](https://arxiv.org/abs/2512.23675) |
| 11 | MMR-GRPO Diversity Reweighting | [2601.09085](https://arxiv.org/abs/2601.09085) |
| 12 | Resilient Microservices (Saga patterns) | [2512.16959](https://arxiv.org/abs/2512.16959) |
| 13 | AI Inference Reliability (production incidents) | [2511.07424](https://arxiv.org/abs/2511.07424) |
| 14 | ChaosEater: LLM-Powered Chaos Engineering | [2511.07865](https://arxiv.org/abs/2511.07865) |

---

*For Seven Generations*
*Cherokee AI Federation — Research Intelligence*
