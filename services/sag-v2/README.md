# SAG v2 — Resource Allocation Assistant

AI-powered resource allocation assistant for Solution Architects teams. Built with FastAPI + MCP (Model Context Protocol) + pluggable LLM backends.

## Overview

SAG v2 is a complete rewrite providing:
- **Pluggable LLM Support**: vLLM (local), OpenAI, Anthropic, Azure OpenAI
- **MCP Tool Servers**: Productive.io & Smartsheet Resource Management integrations
- **Modern Frontend**: React + Vite with streaming response support
- **Production Ready**: Docker, systemd service, health checks

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ React Frontend (port 3000)                          │
│ - Chat interface with streaming                     │
│ - Tool call visualization                           │
│ - Resource allocation workflows                     │
└──────────────┬──────────────────────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────────────────────┐
│ FastAPI Backend (port 4100)                         │
│ - LLM router (vLLM / OpenAI / Anthropic)           │
│ - MCP protocol server                               │
│ - Tool orchestration                                │
└──────────────┬──────────────────────────────────────┘
               │ stdio (MCP)
       ┌───────┴────────┬─────────────────┐
       │                │                 │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│ Productive  │  │ Smartsheet  │  │ Domain      │
│ MCP Server  │  │ MCP Server  │  │ Prompts     │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Directory Structure

```
sag-v2/
├── backend/                     # FastAPI application
│   ├── app.py                   # Main FastAPI app + /api/chat endpoint
│   ├── llm_router.py           # Pluggable LLM router
│   └── domain_prompts.py       # System prompt + tool definitions
├── mcp_servers/                 # MCP tool servers (stdio-based)
│   ├── productive_server.py    # Productive.io resource tools
│   └── smartsheet_server.py    # Smartsheet RM resource tools
├── frontend/                    # React + Vite app
│   ├── src/
│   │   ├── main.jsx            # React entry point
│   │   └── App.jsx             # Main chat component
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite config
│   └── index.html              # HTML template
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml          # Full stack compose
├── .env.example                # Environment template
├── sag-v2.service              # systemd service
└── requirements.txt            # Python dependencies
```

## Quick Start

### Local Development

1. **Python Backend**
```bash
cd /ganuda/services/sag-v2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Terminal 1: Start FastAPI
export LLM_PROVIDER=vllm
export VLLM_BASE_URL=http://localhost:8000
export SAG_V2_PORT=4100
python backend/app.py

# Terminal 2: Start MCP servers
python mcp_servers/productive_server.py &
python mcp_servers/smartsheet_server.py &
```

2. **React Frontend**
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173
```

### Docker

```bash
cd /ganuda/services/sag-v2
docker-compose up --build
# Frontend: http://localhost:3000
# API: http://localhost:4100/api/chat
```

### systemd (Production)

```bash
sudo cp sag-v2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sag-v2.service
sudo systemctl status sag-v2.service

# Logs
journalctl -u sag-v2.service -f
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LLM Provider (vllm, openai, anthropic, azure)
LLM_PROVIDER=vllm
LLM_MODEL=qwen2.5-72b-instruct-awq

# vLLM (local)
VLLM_BASE_URL=http://192.168.132.221:8000
VLLM_API_KEY=sk-default

# OR OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# OR Anthropic
ANTHROPIC_API_KEY=sk-...

# Resource APIs
PRODUCTIVE_API_TOKEN=...
SMARTSHEET_API_TOKEN=...
SMARTSHEET_RM_TOKEN=...

# Server
SAG_V2_PORT=4100
```

## API Endpoints

### Chat (Streaming)
```
POST /api/chat
Content-Type: application/json

{
  "message": "Allocate 200 hours to John for Q1 projects",
  "session_id": "optional-uuid",
  "include_tools": ["productive", "smartsheet"]
}

Response: Server-Sent Events (streaming text)
```

### Health Check
```
GET /api/health
Response: {"status": "ok", "llm": "ready", "mcp_servers": [...]}
```

## File Breakdown

### Backend Files

- **app.py** (252 lines)
  - FastAPI app with /api/chat endpoint
  - SSE streaming responses
  - MCP subprocess management
  - Health checks

- **llm_router.py** (172 lines)
  - Abstract LLMRouter class
  - Implementations: vLLM, OpenAI, Anthropic, Azure
  - Tool call parsing (function-calling format)

- **domain_prompts.py** (223 lines)
  - System prompt for resource allocation
  - Tool definitions (allocate, query, update)
  - OpenAI function schema

### MCP Servers

- **productive_server.py** (376 lines)
  - Tools: list_projects, list_resources, allocate_hours
  - Productive.io API integration (api.productive.io)

- **smartsheet_server.py** (271 lines)
  - Tools: list_portfolios, list_resources, update_allocation
  - Smartsheet RM API integration (api.rm.smartsheet.com)

### Frontend Files

- **App.jsx** (133 lines)
  - Chat interface with streaming
  - Tool call visualization
  - Session management

- **main.jsx** (9 lines)
  - React entry point

- **package.json** (22 lines)
  - React, Vite, react-markdown dependencies

## Integration Points

### Productive.io
- **Endpoint**: api.productive.io
- **Token**: `PRODUCTIVE_API_TOKEN`
- **Tools**: Projects, resources, hour allocation

### Smartsheet RM
- **Endpoint**: api.rm.smartsheet.com
- **Tokens**: 
  - `SMARTSHEET_API_TOKEN` (Portfolio API)
  - `SMARTSHEET_RM_TOKEN` (Resource Management)
- **Tools**: Portfolios, resources, allocations

### LLM Backends
- **vLLM**: Local inference (default)
- **OpenAI**: GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 3 family
- **Azure**: Azure OpenAI service

## Requirements

### Python
```
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.27.0
mcp>=1.0.0
pydantic>=2.5.0
openai>=1.50.0
anthropic>=0.40.0
```

### Node.js
```
React 18.3.0
Vite 5.4.0
react-markdown 9.0.1
```

## Health & Monitoring

### Health Endpoint
```bash
curl http://localhost:4100/api/health
```

### Logs (Docker)
```bash
docker-compose logs -f sag-v2
```

### Logs (systemd)
```bash
journalctl -u sag-v2.service -f
```

## Development Notes

- **MCP Protocol**: Uses stdio-based communication with subprocess servers
- **Streaming**: Frontend handles SSE (Server-Sent Events) responses
- **Error Handling**: Tool failures don't break the conversation loop
- **Tool Calls**: Parsed from LLM response in OpenAI function format
- **Session Management**: Optional session_id for multi-turn context

## Troubleshooting

### "MCP server not responding"
- Check that productive_server.py and smartsheet_server.py are running
- Verify PRODUCTIVE_API_TOKEN and SMARTSHEET_RM_TOKEN are set

### "LLM connection refused"
- Check VLLM_BASE_URL points to running vLLM service
- Verify LLM_PROVIDER matches your setup

### Frontend blank page
- Clear browser cache and rebuild: `npm run build`
- Check VITE_API_URL points to /api endpoint

## Next Steps

1. **Deploy MCP servers**: Run in production background processes
2. **Add more tool servers**: Custom domain-specific MCP servers
3. **Implement authentication**: Token validation in /api/chat
4. **Add persistence**: Store conversations in database
5. **Monitor**: Wire to OpenObserve / Prometheus

---

**Generated**: February 16, 2026
**Status**: Ready for deployment
