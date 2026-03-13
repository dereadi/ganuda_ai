# JR Instruction: SAG Harness DELIBERATE Phase — MCP Adapter Decomposition

**Task ID**: #1285
**Priority**: P1
**Date**: 2026-03-12
**Council Owner**: Spider (Technical) + Deer (Market/Business)
**DC Alignment**: DC-10 (Reflex Principle), DC-11 (Macro Polymorphism), DC-6 (Gradient Principle)
**Kanban**: #2029 (SAG Harness — First External Product)

---

## Context

Russell Sullivan's Solution Architects Group uses two resource management APIs (Productive and Smartsheet RM) to manage team allocation. We built SAG v2 (`/ganuda/services/sag-v2/`) as a FastAPI + MCP proof-of-concept: the LLM decides which MCP tools to call, executes them via subprocess stdio transport, and synthesizes the result.

The problem: SAG v2 is a standalone app. It does not flow through the Graduated Harness Tiers (Tier 1 Reflex, Tier 2 Deliberation, Tier 3 Council) that are the core of the federation's architecture. This task bridges SAG v2's MCP adapter pattern into the harness so that:

1. **Tier 2 Deliberation** can dispatch MCP tool calls as part of specialist synthesis
2. The harness becomes the single entry point for SAG queries (not a separate FastAPI app)
3. Russell gets a POC that demonstrates the harness pattern — which IS the product

## Problem Statement

The SAG v2 MCP servers (Productive + Smartsheet) work but are trapped inside a standalone FastAPI app with their own `/api/chat` endpoint. The harness (`/ganuda/lib/harness/`) has three tiers but no MCP tool-calling capability. The DELIBERATE phase means: decompose the MCP adapter pattern so it can be loaded and called from within Tier 2 Deliberation, giving specialists access to real data tools.

## What Exists

| Component | Location | Status |
|-----------|----------|--------|
| Harness core (dataclasses) | `/ganuda/lib/harness/core.py` | DEPLOYED |
| Harness config (YAML-driven) | `/ganuda/lib/harness/config.py` | DEPLOYED |
| Escalation engine | `/ganuda/lib/harness/escalation.py` | DEPLOYED |
| Tier 1 Reflex | `/ganuda/lib/harness/tier1_reflex.py` | DEPLOYED |
| Tier 2 Deliberation | `/ganuda/lib/harness/tier2_deliberation.py` | DEPLOYED |
| Tier 3 Council | `/ganuda/lib/harness/tier3_council.py` | DEPLOYED |
| Harness route (Flask) | `/ganuda/sag/routes/harness_routes.py` | DEPLOYED |
| SAG v2 FastAPI backend | `/ganuda/services/sag-v2/backend/app.py` | BUILT |
| Productive MCP server | `/ganuda/services/sag-v2/mcp_servers/productive_server.py` | BUILT |
| Smartsheet MCP server | `/ganuda/services/sag-v2/mcp_servers/smartsheet_server.py` | BUILT |
| LLM Router (pluggable) | `/ganuda/services/sag-v2/backend/llm_router.py` | BUILT |
| Domain prompts + tools | `/ganuda/services/sag-v2/backend/domain_prompts.py` | BUILT |
| Sub-agent dispatch | `/ganuda/lib/sub_agent_dispatch.py` | DEPLOYED |
| SAG MCP architecture KB | `/ganuda/docs/kb/KB-SAG-V2-MCP-ARCHITECTURE-FEB16-2026.md` | REFERENCE |

## Acceptance Criteria

1. A new module `/ganuda/lib/harness/mcp_adapter.py` exists that:
   - Can start/stop MCP server subprocesses (Productive, Smartsheet, and future servers)
   - Provides an async `call_tool(server_name, tool_name, arguments)` method
   - Handles JSON-RPC over stdio communication (same protocol as SAG v2 `app.py`)
   - Has a registry of tool-name-to-server mappings
   - Includes health check capability for MCP servers
   - Is importable standalone with no FastAPI dependency

2. Tier 2 Deliberation (`/ganuda/lib/harness/tier2_deliberation.py`) is extended:
   - A new specialist domain "resource_manager" is added for resource/allocation/scheduling queries
   - When resource_manager specialist is selected, it can invoke MCP tools to get real data
   - Tool results are included in the specialist's response context
   - The existing specialist selection and synthesis logic is unchanged

3. Config support in `/ganuda/lib/harness/config.yaml`:
   - New `mcp_servers` section listing available MCP servers and their scripts
   - Configurable via YAML, not hardcoded paths

4. The existing SAG v2 standalone app is NOT removed — it continues to work for direct access

5. Tests: a smoke test script `/ganuda/scripts/test_harness_mcp.py` that:
   - Starts the MCP adapter
   - Calls a Productive tool (list_people) and verifies JSON response
   - Calls the harness with a resource query and verifies Tier 2 handles it
   - Cleans up MCP subprocesses

## Constraints

- **No new pip dependencies** — use `mcp` SDK (already installed) and `httpx` (already available)
- **Async where MCP is involved** — MCP subprocess communication is async (asyncio). The harness Tier 2 is sync (ThreadPoolExecutor). Bridge this with `asyncio.run()` or a dedicated event loop in the MCP adapter
- **Secrets via secrets_loader** — API tokens for Productive and Smartsheet must use `/ganuda/lib/secrets_loader.py`, never hardcoded
- **DC-9 waste heat** — MCP servers should be lazy-started (only spawn when first needed) and can be shut down after idle timeout
- **Crawdad**: Validate all tool arguments before sending to MCP. Sanitize responses (strip PII if present)

## Decomposition (Steps)

### Step 1: Create `/ganuda/lib/harness/mcp_adapter.py`

Extract the MCP subprocess management from `/ganuda/services/sag-v2/backend/app.py` into a standalone, reusable module.

Key methods:
```python
class MCPAdapter:
    async def start_server(self, name: str, script_path: str) -> None
    async def stop_server(self, name: str) -> None
    async def stop_all(self) -> None
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> dict
    async def health_check(self) -> dict  # {server_name: "running"|"stopped"|"error"}
    def get_available_tools(self) -> list  # Returns tool definitions for LLM consumption
```

Config-driven server registry loaded from `config.yaml`:
```yaml
mcp_servers:
  productive:
    script: "/ganuda/services/sag-v2/mcp_servers/productive_server.py"
    enabled: true
    idle_timeout_seconds: 300
  smartsheet:
    script: "/ganuda/services/sag-v2/mcp_servers/smartsheet_server.py"
    enabled: true
    idle_timeout_seconds: 300
```

### Step 2: Add resource_manager specialist to Tier 2

Add to `SPECIALIST_DOMAINS` in `tier2_deliberation.py`:

```python
"resource_manager": SpecialistDomain(
    key="resource_manager",
    name="Resource Manager",
    domain="resource/allocation",
    keywords=[
        "resource", "allocation", "availability", "booking", "schedule",
        "utilization", "capacity", "team", "staff", "assign", "workload",
        "productive", "smartsheet", "project", "time entry", "hours",
    ],
    system_prompt=(
        "You are a Resource Management specialist. Your domain is team allocation, "
        "availability tracking, and workload optimization. You have access to real "
        "data from Productive and Smartsheet Resource Management APIs via MCP tools. "
        "Use the tools to answer with real data, never guess."
    ),
),
```

Add `"resource": "resource_manager"` to `DOMAIN_ANCHORS`.

### Step 3: Wire MCP tool calls into specialist query flow

When the resource_manager specialist is selected in `_query_specialists_parallel`, instead of (or in addition to) calling a plain LLM endpoint, the specialist flow should:

1. Send the user query to the LLM with tool definitions from `MCPAdapter.get_available_tools()`
2. If the LLM returns tool_use calls, execute them via `MCPAdapter.call_tool()`
3. Feed tool results back to the LLM for synthesis (same loop as SAG v2 `process_tool_calls`)
4. Return the final synthesized text as the specialist response

This is the key integration point. The `_call_endpoint` method needs a variant that supports the tool-use loop.

### Step 4: Update config.yaml

Add the `mcp_servers` section to `/ganuda/lib/harness/config.yaml`.

### Step 5: Write smoke test

`/ganuda/scripts/test_harness_mcp.py` — standalone script that exercises the integration end-to-end.

## Evaluation Criteria

- MCPAdapter starts/stops servers without orphan processes
- Tool calls return valid JSON from Productive API (requires API tokens configured)
- Harness query with "who is available next week" routes to Tier 2, selects resource_manager specialist, and returns real data
- No regression in existing harness behavior (non-MCP queries work unchanged)
- Clean shutdown — no zombie MCP processes after test

## Russell Sullivan POC Goal

The end-state for Russell is: he sends a natural language query to the harness endpoint (`POST /v1/harness/query`), and the system automatically routes it through Tier 1 (quick answer from local model) to Tier 2 (resource_manager specialist calls Productive + Smartsheet via MCP), returning real availability data with specialist confidence scoring. No separate SAG v2 app needed — the harness IS the product.

## References

- KB: `/ganuda/docs/kb/KB-SAG-V2-MCP-ARCHITECTURE-FEB16-2026.md`
- Harness code: `/ganuda/lib/harness/`
- SAG v2 code: `/ganuda/services/sag-v2/`
- Roadmap ticket: #2029 (SAG Harness — First External Product)
- SAG v2 ticket: #1792
