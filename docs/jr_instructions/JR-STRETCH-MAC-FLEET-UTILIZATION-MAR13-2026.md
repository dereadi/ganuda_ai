# JR-STRETCH-MAC-FLEET-UTILIZATION-MAR13-2026

## Task: Stoneclad Stretches Into the Mac Fleet

**Priority**: 3 (High)
**Source**: Partner directive + Raven concern (Dawn Mist vote 6d1340f0)
**Context**: Three Mac nodes (sasass2, sasass, bmasass) have ~260GB combined unified memory and are 70-85% idle. The organism is not using what it has.

## Current State

### bmasass (M4 Max 128GB) — 192.168.132.21 / 100.103.27.106
- Qwen3-30B-A3B on :8800 (council Raven path)
- Llama-3.3-70B on :8801 (council Turtle path)
- desktop_context_monitor, heartbeat_agent running
- Load ~4.9 — busiest Mac node, still has headroom

### sasass2 (64GB) — 192.168.132.242 — THUNDERDUCK ZERO
- **85% idle CPU, load 0.59**
- embedding_server.py (old, low usage)
- triad_cli_2chiefs.py (old training artifact, should audit)
- Ollama with Jr resonance models (4x 8B) + qwen2.5-coder:32b + codellama:34b
- **MOST UNDERUTILIZED NODE**

### sasass (64GB) — 192.168.132.241
- **73% idle CPU, load 3.45**
- `claude` user running democracy_coordinator.py + enhanced_memory_api.py
- Ollama with Mixtral, Llama 3.3 70B, Devstral
- embedding_server.py running

## What to Build

### Phase 1: Wire Sub-Agent Dispatch to Mac Fleet (DC-10/DC-11)

The `lib/sub_agent_dispatch.py` already exists. It needs real endpoint configuration:

```python
FLEET_ENDPOINTS = {
    "bmasass_qwen3": {"url": "http://100.103.27.106:8800/v1", "model": "Qwen3-30B-A3B", "tier": 2},
    "bmasass_llama70": {"url": "http://100.103.27.106:8801/v1", "model": "Llama-3.3-70B", "tier": 2},
    "sasass2_coder32": {"url": "http://192.168.132.242:11434/v1", "model": "qwen2.5-coder:32b", "tier": 3},
    "sasass_mixtral": {"url": "http://192.168.132.241:11434/v1", "model": "mixtral:latest", "tier": 3},
    "sasass_devstral": {"url": "http://192.168.132.241:11434/v1", "model": "devstral:latest", "tier": 3},
    "sasass_llama70": {"url": "http://192.168.132.241:11434/v1", "model": "llama3.3:latest", "tier": 2},
}
```

### Phase 2: Give Sub-Claudes Work

1. **sasass2 as Jr Code Reviewer**: Route completed Jr task artifacts through qwen2.5-coder:32b for syntax validation and code review BEFORE marking tasks complete. This fixes the Jr quality problem (markdown fencing, truncated files, hallucinated schemas).

2. **sasass as Research Expander**: Route thin research summaries (#1193, #1194, #1200) through llama3.3:70b or mixtral for deep expansion. The summaries become seeds, the Mac fleet grows them.

3. **bmasass Raven/Turtle paths stay**: Already wired for council deliberation.

### Phase 3: Health Heartbeat

Each Mac node should report to Fire Guard:
- Ollama health: `curl http://localhost:11434/api/tags`
- Model load status
- Memory pressure
- CPU idle %

Fire Guard already checks remote ports. Add Ollama health endpoints.

## Acceptance Criteria

1. `sub_agent_dispatch.py` has real FLEET_ENDPOINTS for all 3 Mac nodes
2. At least one sub-agent task successfully routes to sasass2
3. Fire Guard checks Ollama health on all 3 Mac nodes
4. sasass2 CPU idle drops below 70% during active Jr processing

## Files to Modify
- `/ganuda/lib/sub_agent_dispatch.py` — add fleet endpoint config
- `/ganuda/scripts/fire_guard.py` — add Ollama health checks for Mac fleet
- `/ganuda/jr_executor/jr_task_executor.py` — add post-completion code review step via sasass2

## Design Constraint Alignment
- DC-10: Reflex at each timescale. Mac fleet = Tier 2/3 deliberation layer.
- DC-11: Same SENSE→REACT→EVALUATE interface, different implementation per node.
- DC-9: Waste heat limit. Use the hardware you have before buying more.
