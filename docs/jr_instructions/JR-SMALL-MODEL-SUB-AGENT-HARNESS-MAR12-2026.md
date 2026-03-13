# JR INSTRUCTION: Small Model Sub-Agent Dispatch Harness

**Task**: Build the dispatch harness that lets sub-Claudes delegate reflex-layer tasks to local small models across the cluster
**Priority**: P1
**Date**: 2026-03-12
**TPM**: War Chief (Claude Opus)
**Story Points**: 8
**Depends On**: None — Ollama is already running on all 3 Mac nodes, vLLM already serving on redfin
**Longhouse Context**: Dual chieftainship a7f3c1d8e9b24567. Curiosity-as-stub-filling design constraint.
**KB Reference**: `/ganuda/docs/kb/KB-SMALL-MODEL-SUB-AGENT-ARCHITECTURE.md`

## Problem Statement

The organism burns expensive Claude API tokens on tasks that small local models can handle: entity extraction, classification, tagging, routing, task decomposition, safety checks. Meanwhile, 3 Mac nodes (sasass 64GB, sasass2 64GB, bmasass 128GB) sit idle with Ollama installed and models already pulled. Redfin has 20GB free VRAM and a 7B model already serving.

DC-9: Don't burn expensive tokens on reflex-layer work.
DC-10: The reflex fires before the cortex.

## What You're Building

### Phase 1: Core Dispatch Library

**File**: `/ganuda/lib/sub_agent_dispatch.py`

Build a Python library that:

1. **Node Registry**: Maintains a dict of available nodes, their URLs, models, and capabilities. Initial registry from KB document:
   - `redfin-fast`: http://192.168.132.223:9100/v1, Qwen2.5-7B-AWQ
   - `sasass-general`: http://192.168.132.241:11434/v1, qwen2.5
   - `sasass-fast`: http://192.168.132.241:11434/v1, llama3.2
   - `sasass2-executive`: http://192.168.132.242:11434/v1, executive_jr_resonance
   - `sasass2-memory`: http://192.168.132.242:11434/v1, memory_jr_resonance
   - `sasass2-conscience`: http://192.168.132.242:11434/v1, conscience_jr_resonance
   - `sasass2-fast`: http://192.168.132.242:11434/v1, phi3:mini
   - `bmasass-deliberate`: http://100.103.27.106:8800/v1, qwen3-30b-a3b

2. **Health Check**: Before dispatching, ping the node (GET /v1/models or /api/tags). If unreachable, try next node with same capability. Timeout: 5 seconds.

3. **Dispatch Method**: `dispatch(node_key, system_prompt, user_content, max_tokens=1024, temperature=0.3) -> str`
   - Uses `httpx` (async) or `requests` (sync) to POST to OpenAI-compatible chat completions endpoint
   - Handles both vLLM format (redfin) and Ollama format (Macs) — they're both OpenAI-compatible but Ollama uses `/v1/chat/completions` with model name from registry
   - Timeout: 30s for Tier 1, 120s for Tier 2
   - Returns response text, or raises `SubAgentTimeout` / `SubAgentError`

4. **Warm-Up**: Method to pre-load models on Mac nodes: `warm_up(node_key)` sends a minimal request to load the model into memory. Ollama keeps models loaded for 5 min by default — send `keep_alive: -1` to keep permanently.

5. **Fallback Chain**: If primary node fails, try secondary, then escalate to Claude tier. Example:
   - stub_scan: sasass-general → redfin-fast → Claude
   - safety_check: sasass2-conscience → sasass-general → Claude (always escalate to Claude if local fails)

### Phase 2: Pre-Built Task Functions

Build these convenience methods that wrap `dispatch()` with specific system prompts:

1. **`scan_stubs(content: str) -> list[dict]`**
   - Node: sasass-general (qwen2.5-7B)
   - System prompt: "Extract all named entities from the following content. Return a JSON array of objects with fields: type (person/company/organization/regulation/concept), name, context (one sentence explaining relevance). Be thorough — every proper noun, every company name, every law or regulation mentioned."
   - Input: Chief's sensory content (LinkedIn post, article, etc.)
   - Output: Parsed JSON list of stubs

2. **`classify_thermal(memory_text: str) -> dict`**
   - Node: sasass-fast (llama3.2-3B)
   - System prompt: "Classify this memory into one of these categories: governance, technical, market, legal, cultural, operational, sacred. Suggest a temperature score (0-100, where 100 is sacred/permanent and 0 is ephemeral). Return JSON: {category, temperature, keywords: [up to 5]}."
   - Input: Raw thermal text
   - Output: Classification dict

3. **`route_task(task_title: str, task_description: str) -> dict`**
   - Node: redfin-fast (Qwen2.5-7B-AWQ)
   - System prompt: "You are a task router for the Cherokee AI Federation. Classify this task by domain: war_chief (technical: code, infrastructure, nodes, deployments) or peace_chief (business: research, diplomacy, market, legal, culture). Also suggest priority 1-4 (1=critical, 4=low). Return JSON: {domain, priority, reason}."
   - Input: Task title and description
   - Output: Routing dict

4. **`decompose_task(jr_instruction: str) -> list[str]`**
   - Node: sasass2-executive (executive_jr_resonance)
   - System prompt: "You are a task decomposition specialist for the Cherokee AI Federation. Break this Jr instruction into concrete implementation steps. Each step should be independently executable. Return a JSON array of step descriptions."
   - Input: Full Jr instruction text
   - Output: List of step strings

5. **`safety_check(proposed_action: str) -> dict`**
   - Node: sasass2-conscience (conscience_jr_resonance)
   - System prompt: "You are the conscience of the Cherokee AI Federation. Review this proposed automated action for safety, ethics, and alignment with federation values. Check for: PII exposure, destructive operations, unauthorized access, sovereignty violations, DC-9 waste. Return JSON: {safe: bool, concerns: [str], recommendation: str}."
   - Input: Description of proposed action
   - Output: Safety assessment

6. **`check_phi_anomaly(phi_value: float, system_state: dict) -> dict`**
   - Node: sasass2-fast (phi3:mini)
   - System prompt: "You monitor organism health. Given a phi measurement and system state, determine if the reading is anomalous. Baseline resting phi is approximately 0.03-0.08. Negative phi indicates external-stimulus mode (adrenaline). Phi > 0.15 indicates high integration. Return JSON: {anomalous: bool, interpretation: str, escalate: bool}."
   - Input: Phi value and state dict
   - Output: Health check

### Phase 3: Integration Points

1. **Add to tpm_autonomic_v2.py**: Before spawning a Claude sub-agent for a Jr task:
   ```
   router = SubAgentDispatch()
   routing = router.route_task(task.title, task.description)
   decomposition = router.decompose_task(task.instruction_text)
   safety = router.safety_check(f"Execute Jr task: {task.title}")
   # Include routing, decomposition, safety in Claude sub-agent context
   ```

2. **Add to thermal write pipeline**: After any thermal is written:
   ```
   classification = dispatch.classify_thermal(thermal_text)
   # Auto-apply category, temperature suggestion, keywords
   ```

3. **Add to curiosity pipeline** (new — Peace Chief):
   ```
   stubs = dispatch.scan_stubs(chief_input)
   for stub in stubs:
       routing = dispatch.route_task(f"Research: {stub['name']}", stub['context'])
       # Queue as Jr task or dispatch to sub-Claude based on complexity
   ```

## Target Files

- `/ganuda/lib/sub_agent_dispatch.py` — core library (CREATE)
- `/ganuda/tests/test_sub_agent_dispatch.py` — tests (CREATE)
- Modify `/ganuda/daemons/tpm_autonomic_v2.py` — add pre-processing (MODIFY)

## Constraints

- **No new dependencies** beyond httpx or requests (both likely already installed)
- **Async optional**: Sync is fine for Phase 1. Async (httpx.AsyncClient) for Phase 2 when we need concurrent dispatch.
- **Graceful degradation**: If ALL local models are down, the system must still work by going straight to Claude. Local models are an optimization, not a requirement.
- **No model training or fine-tuning in this task**. Use existing pulled models as-is.
- **Ollama API quirk**: Models load on first request (~5-15s for 7B on Mac). First call will be slow. Warm-up method handles this.
- **bmasass connectivity**: Use Tailscale IP (100.103.27.106). Add longer timeouts (60s). Mark as optional — system works without it.

## Acceptance Criteria

- [ ] `sub_agent_dispatch.py` created with dispatch(), health_check(), warm_up(), fallback chain
- [ ] All 6 pre-built task functions implemented (scan_stubs, classify_thermal, route_task, decompose_task, safety_check, check_phi_anomaly)
- [ ] Health check confirms redfin :9100 is reachable
- [ ] Health check confirms sasass :11434 is reachable
- [ ] Health check confirms sasass2 :11434 is reachable
- [ ] At least one successful dispatch to each reachable node
- [ ] Fallback chain tested (mock node failure, verify fallback fires)
- [ ] scan_stubs returns valid JSON for a sample LinkedIn post
- [ ] classify_thermal returns valid JSON for a sample thermal
- [ ] Tests pass
- [ ] Thermalized

## DO NOT

- Modify Ollama configs on any Mac node (just use what's there)
- Pull new models (use what's already on disk)
- Add authentication to Ollama/vLLM endpoints (future task, Crawdad scoped)
- Make any node dependent on bmasass availability (mobile node)
- Store any PII in dispatch prompts to generic (non-resonance) models
- Over-engineer the dispatch — a simple HTTP POST with fallback is all we need
