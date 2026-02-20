# Jr Instruction: SAG v2 Docker Packaging + GitHub

**Task ID**: SAG-V2-PACKAGING
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sprint**: RC-2026-02E
**Dependencies**: SAG-V2-FRONTEND
**use_rlm**: false

## Objective
Create Docker packaging, environment template, systemd service, and README for SAG v2. Prepare for GitHub push to dereadi/sag-unified-interface on v2-mcp branch.

## Step 1: Create .env.example

Create `/ganuda/services/sag-v2/.env.example`

```text
# SAG v2 Configuration
# Copy to .env and fill in your values

# --- LLM Provider ---
# Options: vllm, openai, anthropic, azure
LLM_PROVIDER=vllm
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=
LLM_API_KEY=

# For OpenAI
# LLM_PROVIDER=openai
# LLM_API_KEY=sk-...
# LLM_MODEL=gpt-4o

# For Anthropic
# LLM_PROVIDER=anthropic
# LLM_API_KEY=sk-ant-...
# LLM_MODEL=claude-sonnet-4-5-20250929

# --- Productive API ---
PRODUCTIVE_API_TOKEN=
PRODUCTIVE_ORG_ID=

# --- Smartsheet Resource Management API ---
SMARTSHEET_RM_TOKEN=

# --- Server ---
SAG_V2_PORT=4100
```

## Step 2: Create Dockerfile

Create `/ganuda/services/sag-v2/Dockerfile`

```text
# SAG v2 — Multi-stage build
# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY app.py llm_router.py prompts.py ./
COPY mcp_servers/ ./mcp_servers/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Default port
ENV SAG_V2_PORT=4100
EXPOSE 4100

CMD ["python", "app.py"]
```

## Step 3: Create docker-compose.yml

Create `/ganuda/services/sag-v2/docker-compose.yml`

```yaml
version: "3.8"

services:
  sag-v2:
    build: .
    ports:
      - "${SAG_V2_PORT:-4100}:4100"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4100/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Step 4: Create systemd service file

Create `/ganuda/services/sag-v2/sag-v2.service`

```ini
[Unit]
Description=SAG v2 Resource Allocation Assistant
After=network.target vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/sag-v2
EnvironmentFile=/ganuda/config/secrets.env
Environment=LLM_PROVIDER=vllm
Environment=LLM_BASE_URL=http://localhost:8000/v1
Environment=SAG_V2_PORT=4100
ExecStart=/ganuda/home/dereadi/cherokee_venv/bin/python app.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Step 5: Create README.md

Create `/ganuda/services/sag-v2/README.md`

```text
# SAG v2 — Resource Allocation Assistant

AI-powered resource allocation assistant for Solution Architects teams.
Built with FastAPI + MCP (Model Context Protocol) + pluggable LLM.

## Architecture

```
Chat UI -> FastAPI backend -> LLM (tool_use) -> MCP servers
                                                 |-- productive-mcp (Productive API)
                                                 |-- smartsheet-mcp (Smartsheet RM API)
```

## Quick Start

### 1. Configure
```
cp .env.example .env
# Edit .env with your API tokens
```

### 2. Run with Docker
```
docker compose up --build
```

### 3. Run without Docker
```
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python app.py
```

### 4. Open
Visit http://localhost:4100

## LLM Providers

| Provider | Config |
|----------|--------|
| Local vLLM | `LLM_PROVIDER=vllm LLM_BASE_URL=http://localhost:8000/v1` |
| OpenAI | `LLM_PROVIDER=openai LLM_API_KEY=sk-...` |
| Anthropic | `LLM_PROVIDER=anthropic LLM_API_KEY=sk-ant-...` |
| Azure OpenAI | `LLM_PROVIDER=azure LLM_BASE_URL=https://your-resource.openai.azure.com/... LLM_API_KEY=...` |

## API Tokens Needed

- **Productive**: Get from Settings > API tokens in productive.io
- **Smartsheet RM**: Get from Settings > API in rm.smartsheet.com

## Example Queries

- "Who is available next week?"
- "Show me Bob's project load for Q2"
- "Find 3 senior architects available in March"
- "What's our team utilization rate?"
- "Compare bookings across all active projects"

## Cherokee AI Federation
Part of the ganuda ecosystem. For Seven Generations.
```

## Manual Steps (TPM)
- Copy sag-v2.service to /ganuda/scripts/systemd/ for deployment
- Push to GitHub: `cd /ganuda/services/sag-v2 && git init && git remote add origin git@github.com:dereadi/sag-unified-interface.git && git checkout -b v2-mcp && git add . && git commit -m "SAG v2: FastAPI + MCP architecture" && git push -u origin v2-mcp`
