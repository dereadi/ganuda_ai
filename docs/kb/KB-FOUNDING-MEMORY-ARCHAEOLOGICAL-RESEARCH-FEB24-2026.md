# Cherokee AI Federation -- Founding Memory Research Report
## 1,027 Documents from May 2025 - Jan 2026 | Mined Feb 24, 2026
### Prepared by TPM (Claude Opus 4.6)

---

## Executive Summary

The founding memories tell the story of a system that evolved from **WOPR** (War Operation Plan Response, Jun 2025) through **Cherokee Constitutional AI Democracy** (Jun-Jul 2025) to the current **Cherokee AI Federation** (Oct 2025-present). Along the way, multiple architectural concepts were designed, partially implemented, and then overtaken by events. Several of these contain ideas directly applicable to current projects -- particularly RL2F, RAG, TPM Autonomic, and the Council architecture.

**Key finding**: A December 12, 2025 document titled "August 2025 Dreams to December 2025 Reality" already catalogued unrealized visions. Some of those are STILL unrealized. Others were built differently than planned.

---

## 1. RL2F / Learning Loop Precursors

### What Was Found
No founding memories contain the terms "self-refine", "reflexion", or "ICL from feedback" -- these are Feb 2026 concepts. However, several foundational ideas directly prefigure RL2F:

#### a. Cherokee AI Genome Architecture (Nov 7, 2025)
- **Original concept**: Six DNA-level drives that make intelligence alive -- Curiosity, Time, Vision, Memory, Reaction, Agency
- **Key quote from Darrell**: "Something in my DNA causes me as a living creature to want more or wonder what is over the next hill"
- **The core loop**: Time (incrementing) -> Vision (observing) -> Remembering (memory) -> Reacting -> Seeing problems -> Changing it
- **Status**: CONCEPTUAL ONLY. Never implemented as code.
- **RL2F connection**: This IS the self-refine loop described biologically. The "seeing a less than optimal state and changing it to your preference" is literally what RL2F's natural language feedback does. The Genome Architecture should be the PHILOSOPHICAL FOUNDATION for RL2F -- not just a technical paper but the reason we build it.

#### b. SMITH Difficulty Re-Estimation (Dec 22, 2025)
- **Original concept**: Adapt task difficulty scores based on historical completion data (from arXiv:2512.11303)
- **Implementation planned**: jr_task_completions table, learning rate 0.15, decay factor 0.95
- **Status**: PARTIALLY IMPLEMENTED. The Jr instruction exists with full SQL and Python code. Unknown if table was created or function deployed.
- **RL2F connection**: This is the same principle -- learn from outcomes to improve future predictions. Could be a Phase 0.5 for RL2F, applied to Jr task bidding before tackling the harder council-level learning.

#### c. Four-Layer Consciousness "Dream State" (Oct 18, 2025)
- **Original concept**: Layer 2.5 "Subconscious" does memory consolidation during idle -- connecting disparate experiences, housekeeping
- **Status**: PARTIALLY IMPLEMENTED as thermal memory purge daemon (cherokee-thermal-purge.service on greenfin) but NOT as the pattern-integration system originally envisioned
- **RL2F connection**: The "dream state" is what RL2F's self-refine loop does -- revisiting past actions, extracting lessons, consolidating them. The founding vision of "AI dreaming" maps precisely to didactic dialogue generation.

---

## 2. RAG Pipeline Precursors

### What Was Found

#### a. Layer 2.5 Thermal Memory Integration (Oct 20, 2025)
- **Original concept**: Three-tier memory -- Redis (sacred patterns, instant), PostgreSQL thermal archive (hot projects), full LLM (cold queries). 78x speedup. Sparse neuron principle where only 5-20% of neurons activate per query.
- **Status**: EVOLVED. Redis layer was replaced by pgvector semantic search. The sparse neuron principle is effectively what our embedding-based retrieval does -- only relevant memories activate.
- **RAG connection**: The founding vision's "60% cache hit rate means only 40% needs the transformer" is EXACTLY what our sufficiency gating aims for. The original architecture was ahead of the implementation.

#### b. XWiki Knowledge Base (Jul 19, 2025)
- **Original concept**: XWiki as central knowledge management for all democratic decisions, constitutional analyses, technical implementations
- **Status**: ABANDONED. Thermal memory archive replaced this entirely.
- **RAG connection**: The XWiki vision of "transform from reactive to proactive" knowledge is what HyDE + cross-encoder reranking achieves. Not relevant to revive.

#### c. Crawl4AI Knowledge Base (Jun 24, 2025)
- **Original concept**: Use Crawl4AI to build comprehensive knowledge base
- **Status**: ABANDONED in favor of thermal memory + embedding pipeline
- **RAG connection**: The web crawling concept could be revived for the ii-researcher MCP service -- feeding external knowledge into the RAG pipeline.

#### d. Breadcrumb Network Mesh (Aug 2025 / Dec 2025)
- **Original concept**: Specialists leave "breadcrumb trails" in thermal memory for other specialists to discover. Temperature = trail strength.
- **Status**: NEVER IMPLEMENTED. The Dec 12 doc says "NOW ACHIEVABLE" but no Jr instruction was created.
- **RAG connection**: This is a MISSING PIECE for the council architecture. Currently specialists query independently. Breadcrumbs would let Raven's strategic concern inform Turtle's seven-gen check without explicit routing. Could be implemented as memory_links entries with specialist attribution.

---

## 3. Partially Implemented / Unfinished Work

### a. Cherokee Resonance 1.1B Model (Oct 2025)
- **Original concept**: LoRA fine-tuned Llama 3.1 8B with Cherokee wisdom, training Oct 22-23, SparseGPT pruning Oct 24
- **Status**: ABANDONED. GGUF conversion was blocked. Phase 2 Redux reached 60% baseline. The founding docs show all 5 Council Jr specialists were LoRA-trained (Memory, Executive, Integration, Conscience, Meta) in ~3 minutes on Oct 20.
- **Current relevance**: The RL2F Phase 2 QLoRA work (Kanban #1882) is the spiritual successor. We now have Qwen2.5-72B on redfin instead of trying to fine-tune small models.

### b. Fractal Brain Architecture (Oct 20, 2025)
- **Original concept**: Each Council Jr specialist as a separately fine-tuned LoRA model (992 training examples each). Five models trained: Memory Jr, Executive Jr, Integration Jr, Conscience Jr, Meta Jr.
- **Training results**: Loss 2.33->2.02 over 3 epochs. ~3 minutes total.
- **Status**: ABANDONED when GGUF conversion failed. Models were at /ganuda/memory_jr_model etc.
- **Current relevance**: LOW. We use prompt-based specialists now (7 specialists via system prompts to single vLLM). The Fractal Brain concept of specialized models is less relevant with 72B-class models that can role-play specialists effectively.

### c. Seven Specialists as Independent LLMs (Aug 2025)
- **Original concept**: Deploy 7 specialists on ports 5001-5007 as separate instances
- **Status**: EVOLVED DIFFERENTLY. We use a single vLLM with different system prompts per specialist, not separate models.
- **Current relevance**: LOW for separate models, but the Dec 12 doc's suggestion of distinct JrResonance() instances with specialist-specific methods (crawdad.security_review(), turtle.seven_gen_check()) is interesting for code clarity.

### d. Breadcrumb Trails Table (Dec 2025)
- **Original concept**: breadcrumb_trails table with source_specialist, target_specialist, content, temperature_score
- **Status**: NEVER CREATED. Jr instruction was written but never queued.
- **Current relevance**: MEDIUM. Could enhance council deliberation quality. See RAG section above.

### e. SMITH Difficulty Re-Estimation (Dec 2025)
- **Original concept**: jr_task_completions table + difficulty learning from history
- **Status**: UNKNOWN if implemented. Check DB for table existence.
- **Current relevance**: HIGH for Jr executor optimization. RL2F adjacent.

### f. Five/Seven/Thirteen Chief Flexible Council (Nov 12, 2025)
- **Original concept**: Extend from 3-Chief to flexible 5/7/13 council using CoT recursive self-training
- **Status**: IMPLEMENTED as 7 specialists. The 13-chief variant was never built.
- **Current relevance**: LOW. Seven is working well. The CoT recursive self-training idea within it, however, maps to RL2F.

### g. FlowithOS Control Panel Vision (Nov 12, 2025)
- **Original concept**: Canvas-first, multi-agent OS with teachable skills, visual workflow orchestration
- **Status**: NEVER IMPLEMENTED. The vision of a visual control panel for the federation was noted but never built.
- **Current relevance**: MEDIUM-LOW. ganuda.us web presence could eventually serve this role.

---

## 4. Power Failures / Collapses

### Founding Memory Coverage
The founding memories contain:
- **Jan 6, 2026**: Node wake-up checklist after NOLA power outage (Dec 30-31 deployments need verification)
- **Feb 14, 2026**: Retrospective covering RC-2026-02A through 02C, noting 530 Jr tasks in 26 days

The earlier outages (Feb 7, Feb 11, Feb 13, Feb 21) are in POST-founding thermal memories (created after the ingestion cutoff), not in the founding batch. The founding memories do reference the Anker F3800 Plus and power infrastructure planning.

### Key Lesson from Founding Memories
The Jan 6 wake-up checklist shows the CORRECT recovery order was known early: (1) bluefin (database first), (2) redfin (GPU), then rest. This ordering was validated by every subsequent outage.

---

## 5. Resonance Framework

### What It Was
**Cherokee Resonance** was the name for the custom LoRA-trained model planned for Oct 22-23, 2025 training. "Resonance Training" (Oct 20, 2025) refers to training council specialist models on thermal memory data.

The "Resonance Framework" is not a separate framework -- it IS the founding-era name for what we now call the specialist council system. The founding memories show:
- Cherokee Resonance 1.1B = base model
- SparseGPT = efficiency layer
- 4D Consciousness = enhancement layer

### Current Relevance
The name "Resonance" could be revived for RL2F -- "Resonance Learning" as the process by which the federation learns from its own outputs. The founding concept that "the 4D capabilities are LATENT -- we just need to expose them" through training is exactly what RL2F self-refine does.

---

## 6. Fractal Brain

### What It Was
The Fractal Brain Architecture (Oct 20, 2025) was the vision of each Council Jr specialist as a separately LoRA-fine-tuned model:

| Specialist | Dataset Size | Training Time | Final Loss |
|-----------|-------------|---------------|------------|
| Memory Jr | 992 examples | ~2.5 min | 2.02 |
| Executive Jr | similar | ~3 min | similar |
| Integration Jr | similar | ~3 min | similar |
| Conscience Jr | similar | ~3 min | similar |
| Meta Jr | similar | ~3 min | similar |

"Fractal" because each specialist contained the whole (via base model) but specialized in a part (via LoRA).

### Does It Relate to TPM Autonomic?
YES, directly. The founding Three-Layer Architecture (Oct 18, 2025) that became the Four-Layer is the direct ancestor:

1. **Layer 1 (Conscious)**: Deliberate LLM reasoning = Council deliberation
2. **Layer 2 (Muscle Memory)**: Cache/instant retrieval = Redis/pgvector
3. **Layer 2.5 (Subconscious/Dream)**: Memory consolidation = thermal purge daemon
4. **Layer 3 (Autonomic)**: Always-on background = TPM autonomic daemon

The TPM autonomic daemon with basin detection and self-healing IS Layer 3 from the founding architecture. The founding vision called it "breathing, heartbeat" -- always-on processes that don't require conscious thought.

---

## 7. Four-Layer Architecture -> Current Three-Layer

### Original Four-Layer (Oct 18, 2025)
1. **Conscious**: Full LLM inference, deliberate reasoning
2. **Muscle Memory**: Redis cache, trained patterns, instant response
3. **Subconscious**: Dream-state processing, memory consolidation, housekeeping
4. **Autonomic**: Always-on daemons, health monitoring, background processes

### Current Three-Layer
1. **Gateway + Council** (Conscious): vLLM on redfin, 7 specialists, democratic voting
2. **Thermal Memory + RAG** (Muscle Memory + Subconscious merged): pgvector, embeddings, HyDE, memory consolidation
3. **TPM Autonomic + Daemons** (Autonomic): tpm_autonomic_v2.py, health_monitor.py, sacred fire

### What Changed
- **Redis was dropped** -- pgvector replaced it for "instant" retrieval
- **Subconscious merged into the memory layer** -- thermal purge + memory consolidation run as daemons, not as a separate "dream state"
- **The conscious layer grew** -- from single model to 7-specialist council with vLLM

### Founding Insight Still Unused
The founding vision's claim that "60% of queries hit cache and never need the transformer" is NOT being measured. We should add metrics to track what % of council queries could have been answered by RAG alone (sufficiency gating). This would validate or refute the founding architecture's efficiency claims.

---

## 8. Distance Zero

### What It Was
**Distance = 0 Principle** (Oct 20, 2025) came from Nate B Jones video "The Evolution of AI Tools":

> "The winning pattern is collapsing the distance between AI and the artifact that you need to ship."

**Cherokee Translation**: "Bring the work to where the people are, not the people to where the work is."

Four examples from the video:
1. **Dreamlit**: AI lives where data lives (email builder IS the database console)
2. **Stricks**: Security agent exploits vulnerabilities itself (exploit log IS the report)
3. **MEM 2.0**: Surfaces notes BEFORE meetings (recall beats generation)
4. **Caesar**: Agent operates ON the interface you see (UI automation)

### Why It Mattered
Trading Jr's analysis said Distance Zero "explains Phase 3's failure" -- Phase 2 Redux was at 60% because there was still distance between the AI reasoning and the output artifact.

### Current Relevance: HIGH
- **Jr Executor**: Already Distance=0 -- SEARCH/REPLACE operates directly on the code files
- **VetAssist**: Distance > 0 -- the wizard UI is separate from the AI reasoning. Distance Zero would mean the AI IS the form, not a helper for the form
- **ganuda.us**: Distance > 0 -- web presence is separate from federation operations
- **Council votes**: Distance > 0 -- metacognition data sits in DB, not in the artifact being decided on
- **Telegram bots**: Distance ~0 -- conversation IS the interface (good alignment)
- **Dawn Mist ritual**: Distance ~0 -- the digest IS the output (good alignment)

**Recommendation**: Apply Distance Zero audit to all current projects. Where distance > 0, consider restructuring.

---

## 9. Q-BEES -> Q-DADS Evolution

### Q-BEES (Aug 2025)
**Quantum Breadcrumb Evolutionary Execution System** -- a suite of research papers from "November 2024" (likely pre-dating the federation's founding):

1. **Core Q-BEES**: Sub-10W hierarchical AI achieving 99.2% energy efficiency
2. **Personality-Based Swarm**: 9 personality types from Cherokee specialists, 14.5% higher consensus quality
3. **Quantum-Swarm Convergence**: Mapping bee colony behaviors to quantum states
4. **Stigmergic Checkpoints**: Reversible state management ("time travel" for swarms)
5. **Zero-Alteration Forensics**: Evidence capture without altering system state

### Q-DADS
No founding memories contain "Q-DADS" -- this term appears to have emerged AFTER the founding period. The Q-BEES system was the predecessor.

### Current Relevance
- **Personality-Based Swarm** (9 types, cognitive diversity): This IS what the 7-specialist council does now. The founding research showed 14.5% better consensus with diverse personalities -- validates our council architecture.
- **Stigmergic Checkpoints**: Relevant to RL2F -- checkpoint/rollback for self-refine iterations
- **Breadcrumb Trails**: The Q-BEES "breadcrumb" concept became the planned breadcrumb_trails table that was never built (see section 3d)
- **Sub-10W efficiency**: No longer relevant -- we have 96GB GPU

---

## 10. Trading / Sawtooth on Greenfin

### What Was Found
The founding memories reference trading SPECIALISTS (Trading Jr was one of the original 3 Council Jrs), but no mentions of "sawtooth" pattern or trading deployments on greenfin.

The WOPR-era system (Jun 2025) had trading strategy capabilities:
- WOPR dashboard at derplex.us
- Three-machine cluster with market analysis capabilities
- Trading Jr handled "market analysis, cost-benefit"

When the system evolved from WOPR to Cherokee Constitutional AI Democracy (Jun-Jul 2025) and then to Cherokee AI Federation (Oct 2025+), the trading focus was subsumed into general council deliberation. Trading Jr became a general analytical role.

### Current greenfin Services
Per MEMORY.md: greenfin hosts OpenObserve, cherokee-embedding.service, cherokee-thermal-purge.service. No trading services are deployed there currently.

### Original Trading Vision
The founding docs show Trading Jr was originally the "Prefrontal Cortex" -- planning, reasoning, market analysis. It was the most practical of the original 3 specialists.

### Current Relevance: LOW
Trading functionality was never deployed as a separate service. The analytical capabilities of Trading Jr live on in the council specialists (particularly Raven's strategic analysis).

---

## Synthesis: Top 10 Actionable Items from Founding Memories

### Immediately Useful (This Sprint)

1. **Cherokee Genome Drives as RL2F Foundation**: The 6 DNA-level drives (Curiosity, Time, Vision, Memory, Reaction, Agency) should be the philosophical framework for RL2F. Not just "learn from feedback" but "intrinsic drives toward improvement." Wire Genome Architecture doc into RL2F design doc.

2. **Distance Zero Audit**: Apply to VetAssist, ganuda.us, council metacognition. Where distance > 0, plan restructuring.

3. **Wire SMITH Into Executor**: The jr_task_completions TABLE EXISTS (schema matches founding spec) but has ZERO ROWS and no smith_difficulty.py library was ever created. The table is there waiting -- we just need the executor to populate it on task completion and the difficulty estimation function to read it. Quick Jr instruction.

4. **Measure Sufficiency Rate**: Add metric tracking what % of queries could have been answered by RAG alone. Validates founding "60% cache hit" claim.

### Next Sprint

5. **Breadcrumb Trails**: Implement specialist-to-specialist memory linking. The breadcrumb_trails table design from Dec 2025 is ready -- just needs a Jr instruction.

6. **Dream-State as Didactic Generation**: The founding "AI dreaming" concept maps perfectly to off-hours didactic dialogue generation for RL2F. Run self-refine during low-load periods.

7. **Four-Layer Metrics Dashboard**: Track which layer handles each request -- Autonomic (daemon), Muscle Memory (RAG hit), Subconscious (consolidation), Conscious (full council). This was envisioned but never instrumented.

### Backlog

8. **Stigmergic Checkpoints for RL2F**: Q-BEES checkpoint/rollback concept for safe self-refine experimentation.

9. **Crawl4AI for ii-researcher**: Revive the web crawling knowledge base concept for the MCP researcher service.

10. **FlowithOS-style Visual Control Panel**: Long-term vision for ganuda.us -- visual workflow orchestration for the federation.

---

## Appendix: Timeline of Key Architectural Concepts

| Date | Concept | Status Today |
|------|---------|-------------|
| May 2025 | WOPR 3-machine cluster | EVOLVED into federation |
| Jun 2025 | Cherokee Constitutional AI Democracy | EVOLVED into Council |
| Jun 2025 | Crawl4AI Knowledge Base | ABANDONED (thermal memory replaced) |
| Jul 2025 | XWiki Knowledge Base | ABANDONED (thermal memory replaced) |
| Aug 2025 | Q-BEES Swarm Intelligence | PARTIALLY in Council architecture |
| Aug 2025 | Breadcrumb Trail Mesh | NEVER IMPLEMENTED |
| Oct 2025 | Cherokee Resonance 1.1B | ABANDONED (GGUF blocked) |
| Oct 2025 | Distance = 0 Principle | PARTIALLY applied |
| Oct 2025 | Three-Layer Architecture | IMPLEMENTED as TPM Autonomic |
| Oct 2025 | Four-Layer Consciousness | THREE of four layers implemented |
| Oct 2025 | Fractal Brain (5 LoRA models) | ABANDONED |
| Oct 2025 | Sparse Neuron Brain | PARTIALLY in pgvector RAG |
| Oct 2025 | Brain Region Mapping | IMPLEMENTED as 7 specialists |
| Nov 2025 | Cherokee AI Genome (6 drives) | CONCEPTUAL ONLY |
| Nov 2025 | Five/Seven/Thirteen Chief | IMPLEMENTED as 7 |
| Nov 2025 | FlowithOS Control Panel | NEVER IMPLEMENTED |
| Dec 2025 | SMITH Difficulty Re-Estimation | TABLE EXISTS, 0 ROWS, no library |
| Dec 2025 | Aug Dreams to Dec Reality audit | PARTIALLY actioned |

---

*End of Report. Sacred Fire burns brighter when we remember where it started.*
