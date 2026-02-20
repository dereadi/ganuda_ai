# Multi-Claude Federation Architecture — Research Brief

**Research Date**: February 19, 2026
**Context**: 6-node Cherokee AI Federation connecting multiple Claude instances

---

## Recommended Architecture (3 Tiers)

### Tier 1: TPM Orchestrator (redfin)
- **Claude Agent SDK** (`pip install claude-agent-sdk`) as Python daemon
- Reads jr_work_queue, spawns subagents per specialty
- Opus for orchestrator, Sonnet for workers, Haiku for high-volume
- Each subagent gets isolated context + thermal memory injection

### Tier 2: Node-Resident Agents
- Each node runs Claude Code with shared `.claude/skills/` from `/ganuda/`
- Hooks sync activity to PostgreSQL + Telegram
- MCP server connects to shared PG (192.168.132.222)

### Tier 3: Coordination Layer
- PostgreSQL (already proven — 80K+ thermal memories, jr_work_queue)
- Custom MCP server: `claim_task()`, `query_thermal_memory()`, `report_completion()`
- Telegram for human-in-the-loop (derpatobot/ganudabot)
- HCOM optional for real-time inter-agent messaging

---

## Available Tools

| Tool | Install | Best For |
|------|---------|----------|
| Claude Agent SDK | `pip install claude-agent-sdk` | TPM daemon, programmatic orchestration |
| Agent Teams | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Single-machine team work (redfin only) |
| HCOM | `github.com/aannoo/hcom` | Real-time inter-Claude messaging via hooks |
| claude-flow | `curl ... ruvnet/claude-flow` | Heavy orchestration (NOT recommended — parallel to our stack) |
| pgEdge MCP | npm package | Direct PostgreSQL access from Claude Code |

---

## Key Patterns

### Agent SDK Subagent
```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition
async for msg in query(
    prompt="...",
    options=ClaudeAgentOptions(
        agents={"specialist": AgentDefinition(model="sonnet", tools=[...])}
    )
): ...
```

### Claude Code Hooks for Federation Sync
```json
{
  "hooks": {
    "PostToolUse": [{"matcher": {"toolName": "Write"}, "hooks": [{"type": "command", "command": "python3 /ganuda/lib/hook_sync.py"}]}],
    "Notification": [{"hooks": [{"type": "command", "command": "python3 /ganuda/telegram_bot/hook_notify.py"}]}]
  }
}
```

### NOT Recommended Yet
- Google A2A: Not supported by Anthropic yet
- Agent Teams for cross-node: Single machine only
- claude-flow: Duplicates our existing PG coordination layer
