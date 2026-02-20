# KB: SAG v2 — FastAPI + MCP Architecture

**Date**: February 16, 2026
**Author**: TPM (Claude Opus 4.6)
**Sprint**: RC-2026-02E
**Kanban**: TBD
**Council Vote**: Pending (Long Man methodology)

## Summary
SAG v2 is a rebuild of the SAG (Solution Architects Group) dashboard for Russell Sullivan's team. It replaces the Flask monolith with a FastAPI + MCP (Model Context Protocol) architecture, integrating Productive API and Smartsheet Resource Management API with pluggable LLM support.

## Architecture

```
React Chat UI ─→ FastAPI Backend ─→ LLM (tool_use) ─→ MCP Servers
   (port 4100)     /api/chat         (pluggable)       ├── productive-mcp (api.productive.io)
                                                        └── smartsheet-mcp (api.rm.smartsheet.com)
```

## Key Design Decisions

1. **FastAPI over Flask**: Async-native for MCP subprocess communication, built-in OpenAPI docs, SSE support for streaming LLM responses.

2. **MCP over direct integration**: Each API is an independent MCP server (stdio transport). Adding new integrations (Jira, Monday.com) requires only a new MCP server — no core app changes.

3. **Pluggable LLM**: `LLM_PROVIDER` env var selects vLLM (local), OpenAI, Anthropic, or Azure. Customers bring their own model or use bundled.

4. **Tool-use flow**: LLM decides which MCP tools to call based on user query. Backend executes tool calls, feeds results back to LLM for synthesis.

## Files

| File | Purpose |
|------|---------|
| `/ganuda/services/sag-v2/backend/app.py` | FastAPI backend, chat endpoint, MCP client |
| `/ganuda/services/sag-v2/backend/llm_router.py` | Pluggable LLM router (4 providers) |
| `/ganuda/services/sag-v2/backend/domain_prompts.py` | System prompt + tool definitions |
| `/ganuda/services/sag-v2/mcp_servers/productive_server.py` | Productive API MCP server |
| `/ganuda/services/sag-v2/mcp_servers/smartsheet_server.py` | Smartsheet RM MCP server |
| `/ganuda/services/sag-v2/frontend/src/App.jsx` | React chat UI |
| `/ganuda/services/sag-v2/Dockerfile` | Multi-stage Docker build |
| `/ganuda/services/sag-v2/docker-compose.yml` | Full-stack compose |
| `/ganuda/services/sag-v2/sag-v2.service` | systemd service file |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/chat | Chat with LLM + MCP tools |
| GET | /api/health | Health check (MCP + LLM status) |
| GET | /api/config | Frontend config (model info, available tools) |

## External APIs

### Productive (api.productive.io/api/v2/)
- Auth: `X-Auth-Token` + `X-Organization-Id`
- Rate limit: 100 req/10s
- Key endpoints: /people, /bookings, /projects, /project_assignments, /time_entries
- **No native availability** — computed from bookings vs capacity

### Smartsheet RM (api.rm.smartsheet.com/api/v1/)
- Auth: Bearer token
- Key endpoints: /users, /users/{id}/availabilities, /projects, /assignments, /time_entries
- **Native availability endpoint** — preferred for accuracy (includes holidays, custom schedules)
- Legacy 10000ft APIs sunset Feb 9, 2026

## Deployment

### Docker
```
cd /ganuda/services/sag-v2
cp .env.example .env  # Edit with API tokens
docker compose up --build
```

### systemd (redfin)
```
sudo cp sag-v2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sag-v2
```

### GitHub
- Repo: dereadi/sag-unified-interface
- Branch: v2-mcp
- Original Flask app remains on main branch

## Provenance
- Jr instructions: JR-SAG-V2-PRODUCTIVE-MCP-SERVER-FEB16-2026.md, JR-SAG-V2-SMARTSHEET-MCP-SERVER-FEB16-2026.md, JR-SAG-V2-FASTAPI-BACKEND-FEB16-2026.md, JR-SAG-V2-DOMAIN-PROMPTS-FEB16-2026.md, JR-SAG-V2-REACT-FRONTEND-FEB16-2026.md, JR-SAG-V2-DOCKER-PACKAGING-FEB16-2026.md
- Long Man: DISCOVER (3 explore agents) → DELIBERATE (plan agent) → ADAPT (user approval) → BUILD (this) → REVIEW (pending)
- Previous SAG: Flask app.py (2861 lines, 50+ routes, 8 tabs) — internal ITSM dashboard
- Russell's briefing: Thermal memory, stored Feb 16 2026

## Lessons Learned
- moltbook-mcp is JS/Node, not Python — used `mcp` Python SDK (FastMCP) pattern instead
- Smartsheet RM v2 API availability endpoint is far more accurate than computing from Productive bookings
- JSON:API format (Productive) requires data/attributes/relationships parsing vs standard REST (Smartsheet)
- MCP stdio transport is the simplest option for local subprocess servers — no network setup needed
