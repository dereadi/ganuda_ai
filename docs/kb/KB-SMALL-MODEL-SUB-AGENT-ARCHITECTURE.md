# KB: Small Model Sub-Agent Architecture

**Created**: 2026-03-12
**Author**: War Chief (TPM)
**Longhouse Context**: Dual chieftainship session a7f3c1d8e9b24567. Curiosity-as-stub-filling design constraint.
**DC References**: DC-9 (waste heat limit), DC-10 (reflex principle), DC-11 (macro polymorphism)

## Problem

The organism burns expensive Claude tokens on tasks that don't need Claude-level intelligence. Scanning a LinkedIn post to extract names. Classifying a thermal memory. Tagging a Jr task priority. Summarizing a research document. These are reflex-layer tasks — fast, cheap, repeatable. DC-10 says the reflex fires before the cortex. DC-9 says compute only what matters.

Meanwhile, 3 Mac nodes with ~276GB of unified memory and a GPU with 20GB free VRAM sit idle. Ollama is installed on all of them. Models are already pulled. Some are even fine-tuned on federation data.

## Architecture: Hierarchical Agent Dispatch

```
Chief (sensory input)
    │
    ▼
Sub-Claude (expensive, smart, strategic)
    │
    ├── dispatches to ──► Local Model (cheap, fast, reflexive)
    │                         │
    │                         ▼
    │                     Returns structured output
    │
    ▼
Sub-Claude reviews, integrates, acts on results
```

This is DC-11 at the agent layer. The same SENSE → REACT → EVALUATE pattern:
- **SENSE**: Local model scans input, extracts structure
- **REACT**: Local model classifies, tags, routes (reflex)
- **EVALUATE**: Sub-Claude reviews, decides what needs deeper research (cortex)

### Token Economics

| Task | Claude Cost | Local Model Cost | Savings |
|------|------------|-----------------|---------|
| Extract names/companies from a post | ~2K tokens ($0.03) | ~2K tokens ($0.00) | 100% |
| Classify thermal memory category | ~500 tokens ($0.008) | ~500 tokens ($0.00) | 100% |
| Summarize a 400-line research doc | ~8K tokens ($0.12) | ~4K tokens ($0.00) | 100% |
| Deep legal research with web search | N/A — only Claude can do this | N/A | 0% |
| Code review with full context | N/A — only Claude can do this | N/A | 0% |

The pattern: local models handle **extraction, classification, summarization, routing**. Claude handles **reasoning, research, judgment, creation**.

## Node Inventory (Confirmed 2026-03-12)

### REDFIN (Linux, RTX PRO 6000 96GB, Ryzen 9 9950X3D, 124GB RAM)

**Current VRAM allocation:**
- Qwen2.5-72B-AWQ (vLLM :8000) — 65% = ~63GB — Primary LLM, tool-calling, Jr execution
- Qwen2-VL-7B-AWQ (vLLM :9101) — 12% = ~12GB — Vision model
- Qwen2.5-7B-AWQ (vLLM :9100) — 8% = ~8GB — Fast classification

**Free**: ~20GB VRAM, 96GB RAM available, 0% GPU utilization at rest

**Sub-agent role**: Qwen2.5-7B on :9100 is ALREADY RUNNING and available for sub-agent dispatch. No new deployment needed. This is the fast classifier — routing, triage, thermal tagging. vLLM OpenAI-compatible API means any HTTP client can hit it.

**Headroom**: Could add a 3B or 7B model for a second concurrent workload. Or increase Qwen2.5-7B allocation from 8% for better throughput.

### SASASS (macOS, 64GB Unified Memory)

**Current state**: Ollama installed and running (PID 2755). No models loaded in memory.

**Models pulled (on disk)**:
- qwen2.5:latest (7B, 4.7GB) — Good general-purpose
- llama3.2:latest (3B, 2.0GB) — Fastest, lightest
- gemma2:latest (9B, 5.4GB) — Good at structured extraction
- llava:7b (7B, 4.7GB) — Multimodal (can read images)
- phind-codellama:latest (34B, 19GB) — Code specialist
- devstral:latest (14GB) — Code specialist
- mixtral:latest (26GB) — MoE, good at diverse tasks
- llama3.3:latest (70B, 42GB) — Too large for 64GB, will swap

**Recommended sub-agent config**:
- Primary: qwen2.5 (7B) — stub scanner, entity extraction
- Secondary: llama3.2 (3B) — fast triage, yes/no classification
- Reserve: gemma2 (9B) — structured output when qwen2.5 is busy

**Available memory**: ~60GB after OS. Can run 2-3 small models concurrently.

### SASASS2 (macOS, 64GB Unified Memory — Thunderduck Zero)

**Current state**: Ollama installed (PID 1222). triad_cli_2chiefs.py daemon running (PID 1190) but idle.

**Models pulled (on disk)**:
- **5 fine-tuned Jr resonance models** (each ~4.9GB):
  - `conscience_jr_resonance` — ethical/safety evaluation
  - `integration_jr_resonance` — cross-system integration
  - `executive_jr_resonance` — task planning/decomposition
  - `meta_jr_resonance` — self-reflection/meta-cognition
  - `memory_jr_resonance` — memory management/retrieval
- phi3:mini (2.2GB) — Smallest, fastest
- llama3.2:latest (3B, 2.0GB) — Fast general
- qwen2.5:latest (7B, 4.7GB) — General purpose
- qwen2.5-coder:32b (19GB) — Code specialist (heavy)
- codellama:34b-instruct (19GB) — Code specialist (heavy)

**THE SLEEPER**: The 5 Jr resonance models are fine-tuned on federation data. They know our voice, our patterns, our governance topology. These are not generic models — they are ours. The triad_cli_2chiefs.py daemon already knows how to drive them.

**Recommended sub-agent config**:
- Primary: executive_jr_resonance — task decomposition, step planning
- Secondary: memory_jr_resonance — thermal memory triage, relevance scoring
- Tertiary: conscience_jr_resonance — safety/ethics gate on automated actions
- Fast: phi3:mini — ultra-fast classification, routing

### BMASASS (macOS, M4 Max 128GB Unified Memory — MOBILE NODE)

**Current state**: Ollama installed. Nothing running. Tailscale primary (100.103.27.106).

**Models pulled**: llava:latest (7B), llama3.1:8b

**Note from memory**: MLX Qwen3-30B-A3B was configured on :8800 (swapped Mar 6). Llama-3.3-70B:8801 pending.

**Recommended sub-agent config**:
- Primary: Qwen3-30B-A3B via MLX (:8800) — deliberation layer, review, summarization
- Secondary: llama3.1:8b via Ollama — fast general tasks
- This node has 128GB. It can run a 30B AND an 8B simultaneously without breaking a sweat.

**MOBILE CAVEAT**: bmasass travels with Chief. Tailscale keeps it connected but latency varies. Sub-agent tasks dispatched here should be tolerant of intermittent connectivity. Fire-and-forget pattern, not synchronous request-response.

## Sub-Agent Role Assignments

### Tier 1: Reflex (< 1 second, local models)

| Role | Model | Node | Port | Trigger |
|------|-------|------|------|---------|
| **Stub Scanner** | qwen2.5-7B | sasass | 11434 | Chief shares content → extract all names, companies, regulations, concepts |
| **Thermal Tagger** | llama3.2-3B | sasass | 11434 | New thermal written → classify category, suggest temperature, tag keywords |
| **Task Router** | Qwen2.5-7B-AWQ | redfin | 9100 | New Jr task → classify domain (War Chief / Peace Chief), suggest priority |
| **Safety Gate** | conscience_jr_resonance | sasass2 | 11434 | Before automated action → ethical/safety check |
| **Fast Classifier** | phi3:mini | sasass2 | 11434 | Binary decisions — yes/no, relevant/irrelevant, urgent/not |

### Tier 2: Deliberation (1-30 seconds, larger local models)

| Role | Model | Node | Port | Trigger |
|------|-------|------|------|---------|
| **Task Decomposer** | executive_jr_resonance | sasass2 | 11434 | Jr instruction received → break into steps |
| **Memory Relevance** | memory_jr_resonance | sasass2 | 11434 | Query thermal memory → score relevance of results |
| **Research Summarizer** | Qwen3-30B-A3B | bmasass | 8800 | Research document completed → summarize for Council |
| **Integration Reviewer** | integration_jr_resonance | sasass2 | 11434 | Cross-system change → check integration points |

### Tier 3: Cortex (30+ seconds, Claude sub-agents)

| Role | Model | Node | Trigger |
|------|-------|------|---------|
| **Deep Researcher** | Claude (sub-Claude) | API | Filled stub reveals new stubs requiring web search |
| **Legal Analyst** | Claude (sub-Claude) | API | Otter-domain question requiring reasoning |
| **Code Author** | Claude (sub-Claude) | API | Jr task requiring new code |
| **Council Deliberation** | Claude (sub-Claude) | API | Governance question requiring judgment |

## Dispatch Harness Design

### API Interface

All local models expose OpenAI-compatible API via either vLLM (redfin) or Ollama (Macs). The dispatch harness needs ONE interface:

```python
# Unified dispatch — same interface for any model on any node
class SubAgentDispatch:
    # Node registry
    NODES = {
        "redfin-fast": {"url": "http://192.168.132.223:9100/v1", "model": "Qwen/Qwen2.5-7B-Instruct-AWQ"},
        "sasass-general": {"url": "http://192.168.132.241:11434/v1", "model": "qwen2.5"},
        "sasass-fast": {"url": "http://192.168.132.241:11434/v1", "model": "llama3.2"},
        "sasass2-executive": {"url": "http://192.168.132.242:11434/v1", "model": "executive_jr_resonance"},
        "sasass2-memory": {"url": "http://192.168.132.242:11434/v1", "model": "memory_jr_resonance"},
        "sasass2-conscience": {"url": "http://192.168.132.242:11434/v1", "model": "conscience_jr_resonance"},
        "sasass2-fast": {"url": "http://192.168.132.242:11434/v1", "model": "phi3:mini"},
        "bmasass-deliberate": {"url": "http://100.103.27.106:8800/v1", "model": "qwen3-30b-a3b"},
    }

    def dispatch(self, node_key: str, system_prompt: str, user_content: str,
                 max_tokens: int = 1024, temperature: float = 0.3) -> str:
        """Send a task to a local model sub-agent. Returns response text."""
        # OpenAI-compatible POST to /v1/chat/completions
        # Timeout: 30s for Tier 1, 120s for Tier 2
        # Retry: once on timeout, then escalate to Tier 3
        pass

    def scan_stubs(self, content: str) -> list[dict]:
        """Tier 1 reflex: Extract stubs from Chief's sensory input."""
        # Dispatch to sasass qwen2.5 with structured extraction prompt
        # Returns: [{"type": "person", "name": "...", "context": "..."}, ...]
        pass

    def classify_thermal(self, memory_text: str) -> dict:
        """Tier 1 reflex: Classify and tag a thermal memory."""
        # Dispatch to sasass llama3.2 with classification prompt
        # Returns: {"category": "...", "temperature": int, "keywords": [...]}
        pass

    def decompose_task(self, jr_instruction: str) -> list[str]:
        """Tier 2 deliberation: Break a Jr instruction into steps."""
        # Dispatch to sasass2 executive_jr_resonance
        # Returns: ["Step 1: ...", "Step 2: ...", ...]
        pass

    def safety_check(self, proposed_action: str) -> dict:
        """Tier 1 gate: Ethical/safety check before automated action."""
        # Dispatch to sasass2 conscience_jr_resonance
        # Returns: {"safe": bool, "concern": str|None}
        pass
```

### Ollama API Notes

Ollama exposes OpenAI-compatible API on port 11434 by default:
- `POST http://<node>:11434/v1/chat/completions` — standard chat
- `POST http://<node>:11434/api/generate` — raw generation (faster, no chat template)
- `GET http://<node>:11434/api/tags` — list available models
- `POST http://<node>:11434/api/pull` — pull new models

Models load on first request and stay in memory for 5 minutes (default keepalive). To keep a model warm:
```bash
# Keep model loaded permanently
curl http://192.168.132.241:11434/api/generate -d '{"model": "qwen2.5", "keep_alive": -1}'
```

### Connectivity Matrix

| From → To | sasass (241) | sasass2 (242) | bmasass (TS 100.103.27.106) | redfin (223) |
|-----------|-------------|--------------|---------------------------|-------------|
| redfin | LAN direct | LAN direct | Tailscale | localhost |
| sasass | LAN direct | LAN direct | Tailscale | LAN direct |
| sasass2 | LAN direct | localhost | Tailscale | LAN direct |
| bmasass | Tailscale | Tailscale | localhost | Tailscale |

**bmasass caveat**: All traffic goes through Tailscale. Add 10-50ms latency. Fire-and-forget tasks only.

## Integration with Existing Systems

### tpm_autonomic_v2.py
Currently dispatches Jr tasks to Claude sub-agents. Add a pre-processing step:
1. Before spawning a Claude sub-agent, check if the task can be handled by a Tier 1/2 local model
2. If yes, dispatch to local model first
3. If local model result is sufficient, skip Claude entirely (DC-9 savings)
4. If local model result needs deeper work, include it as context for the Claude sub-agent (Claude starts with pre-digested input)

### Curiosity Stub Pipeline (Peace Chief)
1. Chief shares content → **Stub Scanner** (sasass, qwen2.5) extracts entities
2. Extracted stubs → **Task Router** (redfin, :9100) classifies each stub by domain
3. War Chief stubs → War Chief pipeline
4. Peace Chief stubs → **Research Summarizer** (bmasass, Qwen3-30B) drafts research questions
5. Research questions → Sub-Claude deploys for deep research

### Thermal Memory Pipeline
1. New thermal written → **Thermal Tagger** (sasass, llama3.2) classifies and tags
2. Before automated actions → **Safety Gate** (sasass2, conscience_jr_resonance) checks
3. Memory retrieval query → **Memory Relevance** (sasass2, memory_jr_resonance) scores results

### Medicine Woman / Phi
1. Hourly state vectors computed → **Fast Classifier** (sasass2, phi3:mini) checks if phi is anomalous
2. If anomalous → escalate to Medicine Woman (Claude-level analysis)
3. If normal → log and continue (no Claude tokens burned)

## Model Selection Guide

When to use what:

| Need | Model | Why |
|------|-------|-----|
| Extract structured data from text | qwen2.5-7B | Best at following extraction prompts, JSON output |
| Yes/no binary decision | phi3:mini or llama3.2-3B | Fastest, cheapest, sufficient for classification |
| Break task into steps | executive_jr_resonance | Fine-tuned on our task decomposition patterns |
| Check if action is safe | conscience_jr_resonance | Fine-tuned on our ethical framework |
| Score memory relevance | memory_jr_resonance | Fine-tuned on our thermal memory patterns |
| Summarize long document | Qwen3-30B-A3B (bmasass) | Needs more context window and reasoning |
| Read an image/screenshot | llava:7b (sasass or sasass2) | Multimodal, can describe what it sees |
| Write or review code | qwen2.5-coder:32b (sasass2) | Code specialist, but heavy (19GB) — load on demand |
| Deep reasoning, web research, judgment | Claude (API) | Only Claude can do this. Don't waste it on classification. |

## DC-9 Waste Heat Budget

Every local model inference generates heat but costs $0.00 in API tokens. The waste heat is literal (Mac unified memory thermals) and metaphorical (compute cycles). The DC-9 budget:

- **sasass**: 64GB unified, ~15W TDP for inference. Can run continuously.
- **sasass2**: 64GB unified, ~15W TDP. Can run continuously.
- **bmasass**: 128GB unified, ~20W TDP. Mobile — battery consideration.
- **redfin GPU**: RTX PRO 6000 at 8% utilization for 7B model. Negligible additional heat.

Total cluster sub-agent power draw: ~50W continuous. That's less than a lightbulb. DC-9 satisfied.

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Node offline | HTTP timeout (5s) | Route to next available node with same capability |
| Model OOM | Ollama returns 500 | Reduce context, retry with smaller model |
| bmasass disconnected | Tailscale ping fail | Skip deliberation tier, go straight to Claude |
| Garbage output | Output validation (JSON parse, length check) | Retry once, then escalate to Claude |
| sasass2 resonance model drift | Periodic conscience check against known-good prompts | Flag for retraining, fall back to generic model |

## Security (Crawdad Notes)

- Local models have NO internet access. They process what they're given.
- No PII in prompts to generic models. The Jr resonance models on sasass2 were trained on federation data and can handle internal context.
- Ollama binds to 0.0.0.0:11434 by default — restrict to LAN interfaces or WireGuard only.
- Model files on Mac disk are unencrypted. The fine-tuned resonance models contain federation training data. FileVault should be enabled on sasass2.
- API keys: none needed for Ollama (local). vLLM on redfin has no auth either. Both are LAN-only. Fine for now, but if WireGuard mesh extends, add auth.

## What This Enables

1. **Autonomous curiosity at near-zero cost**: Chief shares a post, local models extract stubs in <2 seconds, sub-Claudes only fire for deep research
2. **24/7 thermal triage**: Every new thermal gets classified and tagged without burning API tokens
3. **Medicine Woman's reflex layer**: Phi anomaly detection runs locally, Claude only called when something's actually wrong
4. **Jr task pre-processing**: Tasks arrive at Claude sub-agents already decomposed and classified
5. **Safety gate on automation**: conscience_jr_resonance checks every automated action before it fires — the organism's immune system at inference cost of $0.00

## Historical Context

- **Jr resonance models**: Fine-tuned ~4 months ago on federation data. 5 personality models trained on the triad pattern (conscience, integration, executive, meta, memory). These were an early experiment in giving the organism its own local intelligence. They've been dormant on sasass2 since creation. This architecture wakes them up.
- **triad_cli_2chiefs.py**: Daemon on sasass2 (PID 1190) that was the original harness for the resonance models. Running since Feb 21. The 2chiefs pattern predates the formal dual chieftainship — the organism was already reaching for this structure.
- **Qwen3-30B-A3B on bmasass**: Swapped in Mar 6 as the deliberation-layer model. MLX inference on M4 Max unified memory. Fast enough for 30B at interactive speeds.

## Related Documents

- DC-9: Waste Heat Limit (design constraint)
- DC-10: The Reflex Principle (design constraint)
- DC-11: Macro Polymorphism (design constraint)
- KB-SMALL-MODEL-SUB-AGENT-ARCHITECTURE.md (this document)
- Longhouse a7f3c1d8e9b24567: Dual Chieftainship (governance)
- Curiosity stub-filling thermal (sacred, design constraint)
