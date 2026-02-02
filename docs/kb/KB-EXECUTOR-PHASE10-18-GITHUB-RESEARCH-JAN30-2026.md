# KB-EXECUTOR-PHASE10-18-GITHUB-RESEARCH-JAN30-2026
## Open Source Prior Art for Jr Executor Phases 10-18

**Created:** 2026-01-30
**Author:** TPM (Claude Code session)
**Context:** Research to support Jr Executor evolution plan
**Council Vote:** Audit hash `274002c21117f79c` / `c8f7b39137de1c04` — Proceed with review, 6 specialist concerns noted

---

### Council Vote Summary

**Vote 1 (full plan):** Confidence 0.842 (high-medium), 4 concerns:
- Crawdad: **SECURITY CONCERN** — LLM-generated SQL execution needs safeguards
- Gecko: **PERF CONCERN** — Research-to-seed pipeline adds latency
- Turtle: **7GEN CONCERN** — Long-term sustainability of 9+ phases
- Raven: **STRATEGY CONCERN** — Roadmap alignment

**Vote 2 (proceed?):** Confidence 0.844, 6 concerns (all specialists):
- Added Eagle Eye: **VISIBILITY CONCERN** — monitoring needed
- Added Peace Chief: **CONSENSUS NEEDED** — documentation/integration

**Consensus:** Proceed after addressing security, monitoring, long-term sustainability, roadmap alignment, infrastructure capacity, and integration documentation.

**Metacognition:** "A circle of agreement may just be walking in circles." — Coyote

---

### Phase 10: Research-to-Seed Pipeline

| Repo | Pattern | License | Relevance |
|------|---------|---------|-----------|
| [ScrapeGraphAI](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | Prompt-first extraction: describe fields in natural language, LLM infers structure from page. SmartScraperGraph with Pydantic schemas. Supports Ollama. | MIT | **Top pick.** Exact pattern for research-to-seed. Replace raw Crawl4AI with schema-aware extraction. |
| [Scrapontologies](https://github.com/ScrapeGraphAI/Scrapontologies) | Auto-generate DB schemas from extracted entities | MIT | Schema inference from content |
| [CrewAI Deep Research](https://github.com/crewAIInc/deep_research_paper_chat) | Flow decorators: `@start`, `@listen`, `@router` for research pipeline stages | Apache 2.0 | Clean decomposition of research into stages |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | Website → LLM-ready markdown. Handles JS rendering, anti-bot. LLM Extract mode. | Apache 2.0 | Fallback for difficult sites |
| [LangGraph Structured Output Agent](https://github.com/Tanujkumar24/LANGGRAPH-STRUCTURED-OUTPUT-AGENT) | LangGraph + Pydantic + TavilySearch for validated structured extraction | MIT | Schema validation before insertion |

**Recommended approach:** Use existing Crawl4AI for fetching, send content + Pydantic-style schema description to Qwen 32B, validate structure, generate INSERTs.

---

### Phase 11: Self-Healing Retry / Reflexion

| Repo | Pattern | License | Relevance |
|------|---------|---------|-----------|
| [becklabs/reflexion-framework](https://github.com/becklabs/reflexion-framework) | `agent.step()` loop. Two LLM calls per retry: self-reflection + revised implementation. `PythonReflexionAgent` with testing env. | MIT | **Top pick.** Direct mapping to our retry loop. |
| [noahshinn/reflexion](https://github.com/noahshinn/reflexion) | Original NeurIPS 2023 paper. Strategy enum: NONE, LAST_ATTEMPT, FULL_REFLECTION. Configurable `num_trials`. | MIT | Strategy enum useful for complexity-based routing |
| [LangGraph ResponderWithRetries](https://langchain-ai.github.io/langgraph/tutorials/reflexion/reflexion/) | Wraps runnable + validator. On ValidationError, appends error to conversation. Max 3 attempts. | MIT | Clean abstraction for validator+retry |
| [VIGIL (arXiv:2512.07094)](https://arxiv.org/abs/2512.07094) | Out-of-band reflection runtime. EmoBank with decay. Roses-Buds-Thorns diagnosis. Prompt patches + code patches. | Research | Key insight: reflection should be out-of-band, not in same LLM call |
| [AutoGen Reflection](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/reflection.html) | Two-agent pattern: generator + critic. Iterate until approval. | MIT | For complex tasks, two-Jr pattern: generate + review |

**Recommended approach:** `agent.step()` pattern with max 2 retries. Append full reflection context to augmented instructions. Record all attempts in Learning Store.

---

### Phase 14: Tool Use Protocol

| Repo | Pattern | License | Relevance |
|------|---------|---------|-----------|
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | `@function_tool` decorator. Auto-schema from type hints. Provider-agnostic (100+ LLMs). | MIT | **Top pick.** Replace regex code block extraction with typed tool calls. |
| [langroid/langroid](https://github.com/langroid/langroid) | Multi-agent tools. SQLChatAgent for DB ops. PythonREPLTool for code. | MIT | SQLChatAgent pattern for structured DB queries |
| [CodeAct (arXiv:2402.01030)](https://arxiv.org/html/2402.01030v4) | LLM generates executable Python as action. Middle ground between JSON tools and code blocks. | Research | Eliminates JSON schema overhead while staying structured |
| [Google ADK](https://google.github.io/adk-docs/agents/llm-agents/) | Schema definitions for I/O. BuiltInCodeExecutor. MCP/A2A protocol support. | Apache 2.0 | Schema-driven I/O contracts |

**Recommended approach:** Start with CodeAct pattern (Phase 14a) — LLM generates Python that imports our tool functions. Evolve to `@function_tool` pattern (Phase 14b) when our LLM supports native function calling.

---

### Phase 13: DAG Workflow Executor

| Repo | Pattern | License | Relevance |
|------|---------|---------|-----------|
| [pipefunc](https://github.com/pipefunc/pipefunc) | `@pipefunc(output_name=)` decorator. Auto-resolves dependencies by matching param names to output names. Pure Python, zero deps. 15μs overhead. | MIT | **Top pick for linear pipelines.** Lightest weight. |
| [Apache Burr](https://github.com/apache/burr) | State machine with `@action(reads=[], writes=[])`. Supports loops, conditional branching. PostgreSQL persistence. Observability UI. | Apache 2.0 | **Top pick for stateful loops.** Retry loops, conditional branches. |
| [pydags](https://github.com/DavidTorpey/pydags) | `@stage` decorator with `.after()`. Parallelism via `pipeline.start(num_cores=8)`. Requires Redis. | MIT | Good for parallel execution. Redis adds overhead. |
| [Dagu](https://github.com/dagu-org/dagu) | YAML-defined workflows. Single binary. Built-in web UI. | MIT | Good for shell-command orchestration |

**Recommended approach:** Use pipefunc for simple stage pipelines (research → extract → seed). Adopt Burr if we need persistent state machines with retry loops and conditional branching.

---

### Phase 17: Verification Executor

| Repo | Pattern | License | Relevance |
|------|---------|---------|-----------|
| [MineDojo/Voyager](https://github.com/MineDojo/Voyager) | Execute → Critic Agent verify → Store to Skill Library. Three-phase loop. Skill Manager indexes verified skills by embedding. | MIT | **Top pick.** Gold standard for execute-verify-store. Maps to Learning Store. |
| [microsoft/clinical-self-verification](https://github.com/microsoft/clinical-self-verification) | Forward (generate) → Backward (verify conditions meet conclusions). Exploits generation/verification asymmetry. | MIT | Key insight: verification is easier than generation |
| [WENGSYX/Self-Verification](https://github.com/WENGSYX/Self-Verification) | Forward reasoning generates candidates. Backward verification ranks by score. | MIT | Multi-candidate ranking pattern |
| [AgentSpec (ICSE 2026)](https://cposkitt.github.io/files/publications/agentspec_llm_enforcement_icse26.pdf) | Declarative runtime rules external to LLM. Consistent enforcement regardless of prompt. | Research | Maps to constitutional_constraints.py |
| [Codenator (AWS)](https://github.com/aws-samples/codenator-automatic-code-generation-and-execution-using-llm) | Code gen → security scan (SemGrep) → sandboxed execution → auto-correction loop | Apache 2.0 | Security scan before execution pattern |

**Recommended approach:** Start with lightweight checks (file exists, SQL COUNT, syntax compile). Evolve to LLM-based Critic Agent for complex verifications. Record all verification outcomes in Learning Store for pattern analysis.

---

### Summary: Top Repos to Watch

1. **ScrapeGraphAI** — Prompt-first structured extraction. Our immediate R2S need.
2. **becklabs/reflexion-framework** — Clean retry-with-reflection. Our Phase 11 template.
3. **openai/openai-agents-python** — Function tool protocol. Our Phase 14 target.
4. **pipefunc** — Zero-dep DAG. Our Phase 13 foundation.
5. **MineDojo/Voyager** — Execute-verify-store. Our Phase 17 model.
6. **Apache Burr** — State machine with persistence. Our Phase 18 endgame framework.

All cited repos are MIT or Apache 2.0 licensed with active maintenance.

---

*For Seven Generations*
