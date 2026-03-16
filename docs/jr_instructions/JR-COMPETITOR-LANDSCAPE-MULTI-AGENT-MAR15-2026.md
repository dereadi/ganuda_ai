# Competitor Landscape: Multi-Agent AI / Cognitive Architecture Repos

**Date:** March 15, 2026
**Author:** TPM (Claude Opus 4.6)
**Purpose:** Identify capabilities in the open-source ecosystem that Stoneclad's federation may be missing.

---

## 1. Agent Frameworks

| Repo | Stars | What It Does |
|------|-------|-------------|
| [LangGraph](https://github.com/langchain-ai/langgraph) | ~45k | Graph-based stateful agent orchestration. Agents as nodes, edges as transitions. Visual debugging. v1.0 shipped late 2025, now default LangChain runtime. |
| [CrewAI](https://github.com/crewAIInc/crewAI) | ~46k | Role-based multi-agent teams. Built-in agent delegation — agents proactively hand off to more capable agents. Idea-to-production in under a week. |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | ~19k | Lightweight Python framework for tool-calling agents. 10.3M monthly downloads. Handoff primitives between agents. |

**Gap for Stoneclad:** Our Jr task queue is sequential and human-dispatched. These frameworks allow agents to delegate to each other dynamically, form ad-hoc teams, and visualize execution as graphs. We lack: (a) inter-agent delegation without TPM mediation, (b) visual execution tracing, (c) a formal state machine for agent handoffs. The ToolSet ring pattern is a step toward this but isn't yet a full delegation graph.

---

## 2. Memory Systems

| Repo | Stars | What It Does |
|------|-------|-------------|
| [Letta](https://github.com/letta-ai/letta) (formerly MemGPT) | ~15k | Memory as first-class agent state. Editable memory blocks. Agents actively manage their own memory (not just retrieve). #1 on TerminalBench for model-agnostic agents. |
| [Mem0](https://github.com/mem0ai/mem0) | ~25k | Universal memory layer. Extracts "memories" from interactions, stores them, retrieves for personalization. Graph memory launched Jan 2026. |
| [Zep / Graphiti](https://github.com/getzep/graphiti) | ~3k | Temporal knowledge graph. Tracks how facts change over time. Integrates structured business data with conversational history. Prescribed + learned ontology. |

**Gap for Stoneclad:** Our thermal memory is strong (19k+ memories, valence scoring, canonical flags). What we lack: (a) agents that actively manage their own memory blocks (Letta pattern), (b) temporal knowledge graphs that track fact changes over time (Graphiti pattern), (c) graph-structured memory with entity relationships beyond flat thermal rows. DC-14 Three-Body Memory is the right architecture but implementation is still Phase 1.

---

## 3. Tool Orchestration

| Repo | Stars | What It Does |
|------|-------|-------------|
| [MCP Servers](https://github.com/modelcontextprotocol/servers) | ~30k+ | Official MCP server collection. Standard protocol for connecting AI to data sources, APIs, databases. |
| [awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) | ~35k+ | Community-curated registry of 500+ MCP servers. The npm of AI tool discovery. |
| [mcp-agent](https://github.com/lastmile-ai/mcp-agent) | ~2k | Meta-orchestrator: connects LLMs to MCP servers in composable patterns (map-reduce, router, evaluator-optimizer). |

**Gap for Stoneclad:** We already use MCP (moltbook-mcp, ii-researcher). What we lack: (a) a meta-orchestrator that dynamically discovers and composes MCP servers (mcp-agent pattern), (b) a tool registry where agents can search for capabilities rather than having them hardcoded, (c) dynamic tool generation — agents creating new tools at runtime. The ToolSet ring pattern could evolve into this.

---

## 4. Multi-Model Routing

| Repo | Stars | What It Does |
|------|-------|-------------|
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | ~3.5k | Drop-in OpenAI client replacement. Routes simple queries to cheap models, complex to expensive. 85% cost reduction, 95% GPT-4 quality. |
| [LLMRouter](https://github.com/ulab-uiuc/LLMRouter) | ~1k | 16+ routing models in 4 categories: single-round, multi-round, agentic, personalized. Academic rigor. |
| [BEST-Route](https://github.com/microsoft/best-route-llm) | ~500 | Microsoft. Selects both model AND number of responses based on query difficulty. 60% cost cut, <1% quality drop. |

**Gap for Stoneclad:** We run MLX Qwen3 on bmasass:8800, vLLM on redfin, and external APIs. But routing is manual/hardcoded. We lack: (a) automatic task-difficulty classification to pick the right model, (b) cost-quality tradeoff optimization, (c) multi-sampling — running the same query through multiple models and selecting the best response. DC-10 Reflex Principle maps to this: reflex = cheap/fast model, deliberate = expensive/thorough model. We designed it but haven't implemented the routing layer.

---

## 5. Evaluation and Benchmarking

| Repo | Stars | What It Does |
|------|-------|-------------|
| [AgentBench](https://github.com/THUDM/AgentBench) | ~2.5k | Comprehensive benchmark for LLMs-as-agents across 8 environments (OS, DB, web, games). ICLR 2024. |
| [SWE-bench](https://github.com/princeton-nlp/SWE-bench) | ~2k | Real GitHub issues as agent benchmarks. Industry standard for code agent evaluation. |
| [YourBench](https://github.com/huggingface/yourbench) | ~500 | Zero-shot domain-specific benchmark generation. Creates benchmarks from YOUR data, not generic datasets. |

**Gap for Stoneclad:** We have no systematic evaluation of Jr task quality, council vote accuracy, or agent reliability. We lack: (a) regression testing for agent behavior — did a prompt change make agents worse?, (b) benchmark suites for our specific tasks (thermal retrieval accuracy, Jr step completion rate, council deliberation quality), (c) YourBench-style custom evaluation from our own data. The Safety Canary is a start but only tests refusal, not quality.

---

## 6. Knowledge Graphs for Agents

| Repo | Stars | What It Does |
|------|-------|-------------|
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | ~25k+ | Extracts knowledge graphs from text. Community hierarchy detection. Synthesized insights across documents. The reference implementation. |
| [Graphiti](https://github.com/getzep/graphiti) | ~3k | Real-time temporal knowledge graphs. Tracks fact changes. Prescribed + learned ontology. Built for agents. |
| [TrustGraph](https://github.com/trustgraph-ai/trustgraph) | ~500 | "Context Operating System." Deep contextual reasoning across knowledge graphs. Auto-extracts structured info from documents. |

**Gap for Stoneclad:** Our Three Rivers KB and thermal memory are flat/relational. We lack: (a) entity-relationship extraction from thermal memories (who/what/when/where linked), (b) community detection — which memories cluster into coherent topics?, (c) multi-hop reasoning — answering questions that require connecting multiple memories. GraphRAG would massively improve tribe_memory_search.py.

---

## 7. Workflow Engines

| Repo | Stars | What It Does |
|------|-------|-------------|
| [Temporal](https://github.com/temporalio/temporal) | ~13k | Durable execution. Workflows survive crashes, outages. Deterministic replay. Activities handle unpredictable work (LLM calls, tool use). Production standard. |
| [Prefect](https://github.com/PrefectHQ/prefect) | ~18k | Python-native workflow orchestration. ControlFlow (now Marvin 3.0) adds AI agent task delegation with type-safe outputs and native observability. |
| [Restate](https://github.com/restatedev/restate) | ~2k | Low-latency durable execution. Event-driven handlers. Lightweight alternative to Temporal for latency-sensitive paths. |

**Gap for Stoneclad:** Our Jr executor is a custom Python loop with no crash recovery, no deterministic replay, no durable state. If redfin reboots mid-task, the Jr loses all progress. We lack: (a) durable execution — tasks that survive process/node failures, (b) deterministic replay for debugging failed tasks, (c) workflow visualization. Temporal would be the natural fit for the Jr executor, or at minimum we need checkpointing.

---

## 8. Observability for AI

| Repo | Stars | What It Does |
|------|-------|-------------|
| [Langfuse](https://github.com/langfuse/langfuse) | ~19k | Open-source LLM observability. Tracing, prompt versioning, evaluation, annotation queues. MIT license. Full stack went open-source June 2025. |
| [AgentOps](https://github.com/AgentOps-AI/agentops) | ~3k | Python SDK for agent monitoring. Cost tracking, benchmarking. Integrates with CrewAI, AutoGen, LangChain. |
| [Weights & Biases Weave](https://github.com/wandb/weave) | ~2k | Structured execution traces for multi-agent systems. Parent-child call relationships. Inputs, outputs, latency, token usage per agent. |

**Gap for Stoneclad:** We have OpenObserve on greenfin + Promtail for log aggregation, but no LLM-specific observability. We lack: (a) token cost tracking per Jr task, (b) prompt version management, (c) trace visualization showing how a council vote flowed through the system, (d) LLM-as-judge evaluation of Jr outputs. Langfuse is self-hostable and MIT — it could run on greenfin alongside OpenObserve.

---

## 9. Code Generation Agents

| Repo | Stars | What It Does |
|------|-------|-------------|
| [OpenHands](https://github.com/OpenHands/OpenHands) | ~69k | Open-source Devin alternative. Autonomous coding agents. Edit files, run terminals, browse web. 72% on SWE-Bench Verified. Event-sourced state, deterministic replay. MCP integration. |
| [SWE-Agent](https://github.com/SWE-agent/SWE-agent) | ~15k | Princeton NLP. Agent that resolves real GitHub issues. Custom shell interface for agents. Research-grade. |
| [Aider](https://github.com/Aider-AI/aider) | ~25k+ | CLI pair programming. Multi-file refactoring. Git-aware. Works with any LLM. Practical daily-driver tool. |

**Gap for Stoneclad:** Our Jrs write code but lack the sandboxed execution environment that OpenHands provides. We lack: (a) sandboxed code execution for Jr tasks (run, test, iterate in isolation), (b) event-sourced state for code changes (deterministic replay of what a Jr did), (c) automated verification — running tests against Jr-generated code before merging. OpenHands' Software Agent SDK is modular and could be integrated.

---

## 10. Voice/Multimodal Agents

| Repo | Stars | What It Does |
|------|-------|-------------|
| [Pipecat](https://github.com/pipecat-ai/pipecat) | ~5k+ | Open-source voice + multimodal framework. 60+ AI service integrations. WebRTC, WebSocket, telephony. Turn detection, interruption handling. |
| [LiveKit Agents](https://github.com/livekit/agents) | ~5k+ | Real-time voice AI on WebRTC. Native MCP support. Video + audio + data as first-class. Low-latency turn detection. |
| [NVIDIA Voice Agent](https://github.com/NVIDIA/voice-agent-examples) | ~200 | Pipecat-based orchestrator for real-time, multimodal conversational AI. NVIDIA's reference implementation. |

**Gap for Stoneclad:** FARA on sasass has browser control (Qwen2.5-VL) and we have a voice interface Jr instruction in progress. We lack: (a) real-time voice pipeline with proper turn detection (Pipecat/LiveKit), (b) WebRTC transport for low-latency voice interaction, (c) multimodal fusion — combining what the agent sees (FARA vision) with what it hears (voice) into unified context. The sasass desktop assistant pipeline is heading this direction but needs a proper voice framework underneath.

---

## Summary: Top 5 Gaps to Address

| Priority | Gap | Best Reference | Effort |
|----------|-----|---------------|--------|
| 1 | **LLM Observability** — no token tracking, no trace visualization, no prompt versioning | Langfuse (self-host on greenfin) | Medium — deploy existing OSS |
| 2 | **Durable Execution** — Jr tasks don't survive crashes, no replay | Temporal or checkpoint system | High — architectural change |
| 3 | **Multi-Model Routing** — DC-10 designed but not implemented | RouteLLM as drop-in | Medium — integrate with gateway |
| 4 | **Knowledge Graph / GraphRAG** — thermal memory is flat, no entity relationships | Graphiti or Microsoft GraphRAG | High — new data layer |
| 5 | **Agent Evaluation** — no regression testing, no quality benchmarks for Jr output | YourBench + custom suite | Medium — build incrementally |

### Honorable Mentions
- **Inter-agent delegation** (CrewAI pattern) — would reduce TPM bottleneck
- **Sandboxed code execution** (OpenHands SDK) — would improve Jr code quality
- **Voice pipeline** (Pipecat) — would complete the sasass desktop assistant

---

## Recommended Next Steps

This is a landscape scan, not an action plan. Council should deliberate on which gaps to prioritize. Suggested approach:

1. **Langfuse deployment** — lowest friction, highest immediate value. Self-host on greenfin. Jr instruction.
2. **RouteLLM integration** — wire into the gateway to implement DC-10 reflex/deliberate routing. Jr instruction.
3. **Jr executor checkpointing** — even without full Temporal, add state persistence so tasks survive reboots. Jr instruction.
4. **GraphRAG pilot** — run Microsoft GraphRAG against thermal_memory_archive to see what entity graph emerges. Jr instruction.
5. **Custom eval suite** — build YourBench-style benchmarks from our Jr task history. Jr instruction.

---

## Sources

- [LangGraph vs CrewAI vs AutoGen comparison](https://o-mega.ai/articles/langgraph-vs-crewai-vs-autogen-top-10-agent-frameworks-2026)
- [Top 5 Open-Source Agentic AI Frameworks 2026](https://aimultiple.com/agentic-frameworks)
- [Letta (MemGPT) GitHub](https://github.com/letta-ai/letta)
- [Mem0 GitHub](https://github.com/mem0ai/mem0)
- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)
- [mcp-agent GitHub](https://github.com/lastmile-ai/mcp-agent)
- [RouteLLM GitHub](https://github.com/lm-sys/RouteLLM)
- [LLMRouter GitHub](https://github.com/ulab-uiuc/LLMRouter)
- [BEST-Route GitHub](https://github.com/microsoft/best-route-llm)
- [AgentBench GitHub](https://github.com/THUDM/AgentBench)
- [Microsoft GraphRAG GitHub](https://github.com/microsoft/graphrag)
- [Temporal GitHub](https://github.com/temporalio/temporal)
- [Prefect ControlFlow GitHub](https://github.com/PrefectHQ/ControlFlow)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [AgentOps GitHub](https://github.com/AgentOps-AI/agentops)
- [OpenHands GitHub](https://github.com/OpenHands/OpenHands)
- [SWE-Agent GitHub](https://github.com/SWE-agent/SWE-agent)
- [Aider GitHub](https://github.com/Aider-AI/aider)
- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)
- [LiveKit Agents GitHub](https://github.com/livekit/agents)
- [Top AI GitHub Repos 2026 (ByteByteGo)](https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026)
- [GitHub Blog: From MCP to Multi-Agents](https://github.blog/open-source/maintainers/from-mcp-to-multi-agents-the-top-10-open-source-ai-projects-on-github-right-now-and-why-they-matter/)
- [AI Agent Observability Platforms 2026](https://o-mega.ai/articles/top-5-ai-agent-observability-platforms-the-ultimate-2026-guide)
- [Voice AI Agent Frameworks 2026](https://medium.com/@mahadise0011/top-voice-ai-agent-frameworks-in-2026-a-complete-guide-for-developers-4349d49dbd2b)
