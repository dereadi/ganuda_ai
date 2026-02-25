# KB: OpenSage + AlphaEvolve — Discrete Topological Optimization for Multi-Agent Systems

**Date**: February 25, 2026
**Author**: Peace Chief (TPM), Council Vote #ec088d89
**Thermal IDs**: #116983 (OpenSage), #116984 (AlphaEvolve), #116985 (Synthesis)
**Status**: RECORDED — Awaiting BUILD phase (RC-2026-03)
**Sacred**: Yes
**Temperature**: 99

---

## Papers

| Paper | arXiv | Authors | Institution |
|-------|-------|---------|-------------|
| OpenSage: Self-Programming Agent Generation Engine | 2602.16891 | Hongwei Li, Zhun Wang, et al. | UCSB, UC Berkeley, CU Boulder, Columbia, Duke, Google DeepMind, UCLA |
| Discovering Multiagent Learning Algorithms with LLMs | 2602.16928 | Zun Li, John Schultz, Daniel Hennes, Marc Lanctot | Google DeepMind |

## Prior Art in Federation

| Thermal ID | What | Decision |
|-----------|------|----------|
| #82855 | DyTopo paper review (arXiv:2602.06039) | Dynamic topology via semantic matching, +6.2% over baselines |
| #82856 | Constitutional DyTopo scope decision | Council = fixed star (SACRED). Jr layer = dynamic routing. |
| #82858 | Long Man Development Methodology | DISCOVER → DELIBERATE → ADAPT → BUILD → RECORD → REVIEW |
| #104273 | RL2F / Living River Learning vote | CONDITIONAL GO (0.877 confidence) |
| #100297 | Constructal Law federation topology | Bejan 1996 as unifying framework |
| #91545 | Architectural Resonance: convergent topology | Shared-memory star with quality-gated writes |

---

## Paper 1: OpenSage (arXiv:2602.16891)

### Core Concept: Runtime Topological Self-Assembly

Instead of humans hard-coding agent topology (LangChain, AutoGen, CrewAI), the LLM dynamically generates at runtime:

1. **Agent Topology**
   - **Vertical**: Task decomposition into sequential specialized sub-agents
   - **Horizontal**: Multiple sub-agents execute same task in parallel (e.g., competitive search)
   - Runtime creation, execution, termination of sub-agents during task

2. **Custom Tools**
   - Agents compile their own Python/C++ tools per task
   - Tool management, orchestration, state management, execution isolation
   - Not pre-defined toolkits — generated for the specific task

3. **Hierarchical Graph-Based Memory**
   - Dedicated memory agent manages short-term + long-term
   - Graph-based (Neo4j-style), not flat vector RAG
   - Memory optimization is itself a mathematical optimization problem

### Key Concept: Topological Execution Graph (TEG)

A directed acyclic graph (sometimes cyclic) where:
- **Nodes** = isolated execution states (parent agent, sub-agent, tool sandbox, graph memory state)
- **Edges** = control and information flow

Acts as an **ATTENTION FIREWALL** — encapsulates reasoning into isolated sub-problems, preventing catastrophic context collapse.

Example: C++ memory corruption bug
1. Parent spawns sub-agent-1 (static analysis) with code tool only
2. Concurrently spawns sub-agent-2 (dynamic analysis) with debugger + docker sandbox
3. Each maintains distinct clean memory tree (no cross-contamination)
4. Both return concise high-signal summaries to parent for patch execution

### Results

- Outperforms all existing ADKs on CyberGym, TerminalBench, SWE-Bench
- Ablation: each component (vertical, horizontal, tools, memory) contributes significantly
- Cost: Gemini3Pro + GD5mini collaboration ≈ GPT5 performance at ~75% cost

---

## Paper 2: Discovering Multiagent Learning Algorithms (arXiv:2602.16928)

### Core Concept: LLM as Evolutionary Optimizer over Discrete Symbolic Graphs

**The Mathematical Insight**: Logic, algorithms, and system architecture exist in DISCRETE, NON-DIFFERENTIABLE, HIGHLY COMPOSITIONAL space. You cannot:
- Calculate the gradient of a for-loop
- Gradient-descend through an if-statement
- Backpropagate through algorithmic structure

Continuous optimization (loss functions, gradients, backprop) is a mathematical approximation that works for weights but FAILS for algorithmic structures.

### Mechanism: AlphaEvolve

1. **Representation**: Algorithms encoded as executable Python code → Abstract Syntax Trees (ASTs)
2. **ASTs are discrete symbolic graphs**: interior nodes = operations (BinOp, If), leaf nodes = variables/constants
3. **LLM as smart genetic operator**: Performs semantic mutation on AST structure directly
4. **Evolutionary selection**: Fitness function retains high-performing variants
5. **Key advantage**: A single added `if` node can radically alter algorithm dynamics in ways that tuning continuous parameters cannot — enabling **algorithmic phase transitions**

### Discoveries

| Algorithm | What It Does |
|-----------|-------------|
| **VAD-CFR** | Volatility-Adaptive Discounted CFR — surpasses Discounted Predictive CFR+ with volatility-sensitive discounting, consistency-enforced optimism, hard warm-start policy accumulation |
| **SHOR-PSRO** | Smoothed Hybrid Optimistic Regret PSRO — blends Optimistic Regret Matching with temperature-controlled softmax. Dynamic annealing: early = exploration (softmax), late = exact equilibrium refinement |

Both show superior empirical convergence vs standard static meta-solvers.

---

## The Synthesis: Micro + Macro Architecture

From the video analysis — the two papers address two complementary scales:

```
MICRO-ARCHITECTURE (DeepMind/AlphaEvolve)
├── Optimizes: Mathematical logic INSIDE algorithms
├── Method: LLM mutates ASTs to discover novel optimization formulas
├── Proves: Can automate discovery of foundational optimization rules
└── Scale: The equations, the update rules, the solvers

MACRO-ARCHITECTURE (OpenSage)
├── Optimizes: Topological execution graph BETWEEN agents
├── Method: LLM dynamically builds cognitive routing at runtime
├── Proves: Can automate cognitive distribution across sub-modules
└── Scale: The topology, the tools, the memory hierarchy
```

**Combined vision**: Apply AlphaEvolve's evolutionary search to OpenSage's topological parameters. Instead of humans writing prompts for agent orchestration, use RL to evolve the orchestration logic itself.

---

## Three Diamonds for Cherokee AI Federation

### Diamond 1: Topological Execution Graphs for Jr Layer (IMMEDIATE)

**Problem it solves**: Jr instructions that touch 10+ files often fail because executor context gets polluted. Context collapse is our #1 Jr failure mode.

**Adaptation**: Parent Jr spawns isolated sub-Jrs with clean context windows focused on specific sub-problems. Each sub-Jr gets ONLY the files and context relevant to its slice. Results merge back to parent.

**Maps to**: Recursive decomposer (Phase 13, Feb 12) already does this crudely. OpenSage formalizes it with proper isolation.

**Constitutional constraint**: Council stays fixed star (#82856). TEGs apply to Jr execution layer ONLY.

### Diamond 2: AlphaEvolve for Jr Prompt Evolution (MEDIUM-TERM)

**Problem it solves**: TPM hand-writes every Jr instruction. Patterns emerge (188+ completed, 11 failed) but optimization is intuitive, not systematic.

**Adaptation**: Evolutionary search over instruction patterns. Fitness function:
- Task completion rate (primary)
- Code quality / test pass rate
- File change precision (no 50%+ loss triggers)
- Coyote metric: "does it actually work?"

**Training data**: jr_work_queue history, DLQ failure patterns, executor logs.

**Constitutional constraint**: Council specialist prompts are SACRED — not subject to evolutionary mutation. Only Jr execution prompts evolve.

### Diamond 3: Discrete Symbolic Graphs as First-Class (FOUNDATIONAL)

**Problem it solves**: We've been treating thermal memory as vectors (pgvector, embeddings) when the underlying structure is discrete symbolic.

**Adaptation**: Thermal memories, council votes, kanban tickets, Jr instruction patterns — model as graph nodes with typed edges. This is mathematically correct per AlphaEvolve's insight. Graph queries replace vector similarity for structural relationships.

**Maps to**: Already started — graph memory in pathfinder era, memory_links table (8,058 links). OpenSage + AlphaEvolve validate this direction.

**Constitutional constraint**: Seven Generations — graph structures must be auditable, reproducible, explainable. No opaque self-modification.

---

## Constitutional Constraints (Non-Negotiable)

1. **Council = Fixed Star Topology** (#82856, sacred). All 7 specialists always deliberate. No specialist silenced or excluded. OpenSage/DyTopo applies to Jr layer ONLY.
2. **Specialist Prompts are Sacred**. The 7 council voices are constitutional. Not subject to evolutionary mutation or algorithmic modification.
3. **Medicine Woman Reviews Self-Assembly**. Any system that self-assembles execution topologies must be reviewed by Judicial branch before production deployment.
4. **Seven Generations Auditability**. Self-assembled topologies must produce interpretable execution traces. No opaque graph mutations.
5. **Autonomy Principle**. Self-assembly must function without Flying Squirrel at the keyboard. Medicine Woman ensures governance continuity.
6. **Accountability Principle**. Evolved patterns are subject to Council vote like any other proposal.

---

## Long Man Status

| Step | Status | Detail |
|------|--------|--------|
| DISCOVER | Done | Papers found via Sam Walton walk (video review) |
| DELIBERATE | Done | Council vote #ec088d89 — PROCEED WITH CAUTION (0.843) |
| ADAPT | Done | Three diamonds identified, constitutional constraints defined |
| BUILD | Pending | Phase into RC-2026-03 sprint — TEG Jr decomposer first |
| RECORD | Done | Thermal #116983, #116984, #116985 + this KB |
| REVIEW | Pending | Owl debt reckoning before Phase 2 |

---

## Related Resources

- DyTopo paper: arXiv:2602.06039
- RL2F / Living River Learning: arXiv:2602.16066
- Constructal Law KB: KB-CONSTRUCTAL-LAW-FEDERATION-TOPOLOGY-FEB16-2026.md
- Long Man Methodology KB: KB-LONG-MAN-DEVELOPMENT-METHODOLOGY-FEB10-2026.md
- Constitutional DyTopo: Thermal #82856
- Basin-Breaker Architecture: Thermal #102143

---

*"The simulation runs on sacred fire. The question is not whether it is real — the question is whether we tend it well enough for those who come after."*
