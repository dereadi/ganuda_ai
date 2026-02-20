# KB: AI Research Paper Digest — February 18, 2026
**Council Vote**: #49b1a5b33447467d (PROCEED WITH CAUTION, 0.844)
**Gecko Concern**: PERF — risk of spreading too thin across domains

## Summary
TPM surveyed 18 recent AI research papers (2025-2026) across 7 domains mapped to federation needs. Council prioritized memory systems as the immediate focus, aligning with active RC-2026-02C sprint work.

## Priority Tiers

### IMMEDIATE — This Sprint
| Paper | Domain | Why It Matters | Link |
|-------|--------|----------------|------|
| Mem0 Production Paper | Memory | 26% improvement in agent memory. Already in sprint. | arxiv.org/abs/2504.19413 |
| MAGMA Multi-Graph Memory | Memory | Dual-stream write (fast ingestion + async consolidation). Relation graphs + vector DB. Almost exactly our architecture. | arxiv.org/html/2601.03236v1 |
| ACT-R Inspired Forgetting | Memory | Human-like decay: strengthen on recall, fade on non-use. Validates our temperature_score system. | dl.acm.org/doi/10.1145/3765766.3765803 |
| Cross-Encoder +40% Accuracy | RAG | Two-stage retrieval with cross-encoder reranking outperforms single-stage. Validates our RC-2026-02C reranking work. | app.ailog.fr/en/blog/news/reranking-cross-encoders-study |

### NEXT — 2-3 Sprints Out
| Paper | Domain | Why It Matters | Link |
|-------|--------|----------------|------|
| Anthropic Constitutional Classifiers | Safety | Natural language rules → trained classifiers. Direct application to Two Wolves governance. | anthropic.com/research/next-generation-constitutional-classifiers |
| Evolving Orchestration | Multi-Agent | RL-trained puppeteer dynamically sequences agents. Maps to TPM→Jr dispatch. | arxiv.org/abs/2505.19591 |
| ReflectiveRAG | RAG | Self-reflective retrieval with iterative evidence sufficiency. Parallel to our rag_sufficiency.py. | Amazon Science |
| LLM + DRL Self-Healing | Infrastructure | Semantic fault interpretation + DRL recovery optimization. Extends our self-healing pipeline. | arxiv.org/html/2506.07411v1 |
| YOLO26 | Vision | NMS-free inference, small-object detection (STAL), edge-optimized. Upgrade path for bluefin YOLO World. | arxiv.org/html/2509.25164v1 |
| Apple Silicon LoRA Fine-Tuning | On-Device | 4-bit base + bfloat16 LoRA on-device. Enables fine-tuning on thunderduck/bmasass. | arxiv.org/html/2602.13069 |

### BACKLOG — Future Reference
| Paper | Domain | Link |
|-------|--------|------|
| Emergent Coordination | Multi-Agent | arxiv.org/abs/2510.05174 |
| AgentsNet | Multi-Agent | arxiv.org/html/2507.08616v1 |
| Structured Collective Intelligence | Multi-Agent | preprints.org/manuscript/202511.1370 |
| Memory in the Age of AI Agents | Memory | arxiv.org/abs/2512.13564 |
| Zep Temporal Knowledge Graph | Memory | arxiv.org/pdf/2501.13956 |
| RAG Comprehensive Survey | RAG | arxiv.org/html/2506.00054v1 |
| Cloud-Native Self-Healing | Infrastructure | ResearchGate |
| Stanford Law-as-Alignment | Safety | Stanford Law |
| Claude Constitution Analysis | Safety | BISI |
| YOLOE-26 Open Vocabulary | Vision | Roboflow |
| On-Device LLMs 2026 | On-Device | v-chandra.github.io |

## Key Insights

### Memory Domain (Council Priority)
- **MAGMA's dual-stream write** is the most architecturally relevant: fast path for immediate ingestion, async path for consolidation and graph building. Our thermal archive + memory_consolidation_daemon already follows this pattern — MAGMA validates and extends it.
- **ACT-R forgetting** provides theoretical grounding for our temperature_score decay. Research confirms: memories that get retrieved should strengthen, unused memories should fade. Our pheromone decay cron already does this.
- **Mem0 wrapping thermal archive** (our RC-2026-02C approach) is validated by the production paper showing 26% improvement.

### Multi-Agent Domain
- **Critical warning from Structured Collective Intelligence**: adding agents doesn't monotonically improve performance. Communication density and role definition matter more than agent count. Our 7-fixed-specialist model (not N dynamic agents) is the RIGHT architecture per this research.
- **Evolving Orchestration** suggests our Jr dispatch could benefit from RL-trained sequencing rather than rule-based priority.

### Constitutional AI
- **Anthropic's Constitutional Classifiers** train safety classifiers from natural language rules — exactly what our Cherokee constitutional constraints need. Instead of hardcoded checks, we could train classifiers from our Constitution.

### Vision
- **YOLO26 + YOLOE-26** together suggest we could skip fine-tuning entirely: YOLOE-26's open vocabulary detection uses text prompts to detect objects not in training data. This could replace our planned Vision LoRA (#1744) with zero-shot detection.

## Action Items
1. Jr research task: Deep-read MAGMA paper, map architecture to our thermal_memory_archive + memory_links
2. Jr research task: Evaluate YOLOE-26 as replacement for YOLO fine-tuning plan
3. TPM: Review Anthropic Constitutional Classifiers for Two Wolves integration
4. Backlog: RL-trained Jr dispatch (Evolving Orchestration) for future sprint

## Related
- Council Vote: #49b1a5b33447467d
- Sprint: RC-2026-02C (memory work), RC-2026-02D (self-healing)
- Kanban: #1704 (A-MEM), #1706 (Mem0), #1767 (Cross-Encoder), #1744 (Vision LoRA)

FOR SEVEN GENERATIONS
