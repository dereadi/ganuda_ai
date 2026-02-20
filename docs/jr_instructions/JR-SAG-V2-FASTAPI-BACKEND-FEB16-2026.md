# Jr Instruction: SAG v2 FastAPI Backend + LLM Router

**Task ID**: SAG-V2-FASTAPI
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Sprint**: RC-2026-02E
**Dependencies**: SAG-V2-MCP-PRODUCTIVE, SAG-V2-MCP-SMARTSHEET
**use_rlm**: false

## Objective
Create the FastAPI backend that serves as the core of SAG v2. It spawns MCP servers, routes chat to a pluggable LLM, handles tool_use calls, and serves the frontend.

## Step 1: Create LLM Router

Create `/ganuda/services/sag-v2/llm_router.py`

```python
"""
SAG v2 — Pluggable LLM Router
================================
Supports: vLLM (local), OpenAI, Anthropic, Azure OpenAI.
Selected via LLM_PROVIDER env var.

All providers implement the same interface: chat(messages, tools) -> response
"""

import os
import sys
import json
import logging
from typing import Optional

import httpx

sys.path.insert(0, '/ganuda/lib')
try:
    from secrets_loader import get_secret
except ImportError:
    get_secret = None

logger = logging.getLogger('sag-v2.llm_router')


def _secret(key: str, default: str = "") -> str:
    if get_secret:
        try:
            return get_secret(key)
        except RuntimeError:
            pass
    return os.environ.get(key, default)


class LLMRouter:
    """Routes LLM requests to the configured provider."""

    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "vllm").lower()
        self.model = os.environ.get("LLM_MODEL", "")
        self.base_url = os.environ.get("LLM_BASE_URL", "")
        self.api_key = _secret("LLM_API_KEY", "not-needed")
        self._configure()

    def _configure(self):
        if self.provider == "vllm":
            self.base_url = self.base_url or "http://localhost:8000/v1"
            self.model = self.model or os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
        elif self.provider == "openai":
            self.base_url = self.base_url or "https://api.openai.com/v1"
            self.model = self.model or "gpt-4o"
            self.api_key = self.api_key or _secret("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            self.base_url = self.base_url or "https://api.anthropic.com"
            self.model = self.model or "claude-sonnet-4-5-20250929"
            self.api_key = self.api_key or _secret("ANTHROPIC_API_KEY")
        elif self.provider == "azure":
            self.model = self.model or "gpt-4o"
            self.api_key = self.api_key or _secret("AZURE_OPENAI_API_KEY")
        logger.info("LLM Router: provider=%s model=%s base_url=%s", self.provider, self.model, self.base_url)

    async def chat(self, messages: list, tools: Optional[list] = None, system: str = "") -> dict:
        """Send chat completion request. Returns OpenAI-format response."""
        if self.provider in ("vllm", "openai", "azure"):
            return await self._openai_compatible(messages, tools, system)
        elif self.provider == "anthropic":
            return await self._anthropic_chat(messages, tools, system)
        else:
            return {"error": f"Unknown provider: {self.provider}"}

    async def _openai_compatible(self, messages: list, tools: Optional[list], system: str) -> dict:
        """OpenAI-compatible API (works with vLLM, OpenAI, Azure)."""
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "not-needed":
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Prepend system message if provided
        full_messages = messages.copy()
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error("LLM error: %s %s", e.response.status_code, e.response.text[:300])
                return {"error": f"LLM HTTP {e.response.status_code}", "detail": e.response.text[:300]}
            except httpx.RequestError as e:
                logger.error("LLM request failed: %s", e)
                return {"error": str(e)}

    async def _anthropic_chat(self, messages: list, tools: Optional[list], system: str) -> dict:
        """Anthropic Messages API — converts to/from OpenAI format."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Convert OpenAI tool format to Anthropic format
        anthropic_tools = []
        if tools:
            for t in tools:
                func = t.get("function", t)
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        if anthropic_tools:
            payload["tools"] = anthropic_tools

        url = f"{self.base_url}/v1/messages"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Convert Anthropic response to OpenAI format
                return self._anthropic_to_openai(data)
            except httpx.HTTPStatusError as e:
                return {"error": f"Anthropic HTTP {e.response.status_code}", "detail": e.response.text[:300]}
            except httpx.RequestError as e:
                return {"error": str(e)}

    def _anthropic_to_openai(self, data: dict) -> dict:
        """Convert Anthropic Messages response to OpenAI format."""
        content_blocks = data.get("content", [])
        text_parts = []
        tool_calls = []
        for i, block in enumerate(content_blocks):
            if block.get("type") == "text":
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", f"call_{i}"),
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block.get("input", {})),
                    },
                })

        message = {"role": "assistant", "content": "\n".join(text_parts) if text_parts else None}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": data.get("stop_reason", "stop")}]}

    def get_info(self) -> dict:
        return {"provider": self.provider, "model": self.model, "base_url": self.base_url}
```

## Step 2: Create FastAPI app

Create `/ganuda/services/sag-v2/app.py`

```python
"""
SAG v2 — FastAPI Backend
===========================
Resource allocation chat interface powered by MCP tool servers.

Endpoints:
    POST /api/chat     — Chat with LLM (SSE streaming text, tool calls inline)
    GET  /api/health   — Health check
    GET  /api/config   — Frontend config

MCP servers are spawned as subprocesses communicating via stdio.
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from llm_router import LLMRouter
from prompts import SYSTEM_PROMPT, build_tool_definitions

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('sag-v2')

# MCP server processes
mcp_processes = {}
MCP_DIR = Path(__file__).parent / "mcp_servers"


async def start_mcp_server(name: str, script: str):
    """Spawn an MCP server subprocess."""
    script_path = MCP_DIR / script
    if not script_path.exists():
        logger.warning("MCP server script not found: %s", script_path)
        return
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(script_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    mcp_processes[name] = proc
    logger.info("Started MCP server: %s (PID %d)", name, proc.pid)


async def stop_mcp_servers():
    for name, proc in mcp_processes.items():
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            logger.info("Stopped MCP server: %s", name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await start_mcp_server("productive", "productive_mcp.py")
    await start_mcp_server("smartsheet", "smartsheet_mcp.py")
    yield
    # Shutdown
    await stop_mcp_servers()


app = FastAPI(title="SAG v2", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = LLMRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[list] = None


async def mcp_call_tool(server_name: str, tool_name: str, arguments: dict) -> str:
    """Call a tool on an MCP server via JSON-RPC over stdio."""
    proc = mcp_processes.get(server_name)
    if not proc or proc.returncode is not None:
        return json.dumps({"error": f"MCP server '{server_name}' not running"})

    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": 1,
    }
    request_bytes = (json.dumps(request) + "\n").encode()

    try:
        proc.stdin.write(request_bytes)
        await proc.stdin.drain()
        response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=30.0)
        response = json.loads(response_line.decode())
        result = response.get("result", {})
        if isinstance(result, dict) and "content" in result:
            texts = [c.get("text", "") for c in result["content"] if c.get("type") == "text"]
            return "\n".join(texts)
        return json.dumps(result)
    except asyncio.TimeoutError:
        return json.dumps({"error": "MCP call timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Map tool names to MCP server names
TOOL_SERVER_MAP = {
    "list_people": "productive",
    "get_person_details": "productive",
    "list_bookings": "productive",
    "get_availability": "productive",
    "list_projects_productive": "productive",
    "list_project_assignments": "productive",
    "get_time_entries_productive": "productive",
    "list_users": "smartsheet",
    "get_user_availability": "smartsheet",
    "list_projects_smartsheet": "smartsheet",
    "list_assignments": "smartsheet",
    "get_time_entries_smartsheet": "smartsheet",
}


async def process_tool_calls(response: dict, messages: list) -> dict:
    """Handle tool_use calls from LLM, execute via MCP, and continue conversation."""
    max_rounds = 5
    for _ in range(max_rounds):
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            return response

        # Add assistant message with tool calls
        messages.append(message)

        # Execute each tool call
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

            server = TOOL_SERVER_MAP.get(tool_name, "productive")
            # Strip suffix for actual MCP call (e.g., list_projects_productive -> list_projects)
            actual_name = tool_name.replace("_productive", "").replace("_smartsheet", "")
            result = await mcp_call_tool(server, actual_name, arguments)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result,
            })

        # Send tool results back to LLM
        tool_defs = build_tool_definitions()
        response = await llm.chat(messages, tools=tool_defs, system=SYSTEM_PROMPT)
        if "error" in response:
            return response

    return response


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Process a chat message through the LLM with MCP tool access."""
    messages = req.history or []
    messages.append({"role": "user", "content": req.message})

    tool_defs = build_tool_definitions()
    response = await llm.chat(messages, tools=tool_defs, system=SYSTEM_PROMPT)

    if "error" in response:
        return JSONResponse(status_code=502, content=response)

    # Process tool calls if any
    response = await process_tool_calls(response, messages)

    if "error" in response:
        return JSONResponse(status_code=502, content=response)

    # Extract final text
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})
    text = message.get("content", "")

    return JSONResponse(content={
        "response": text,
        "conversation_id": req.conversation_id,
        "model": llm.get_info(),
    })


@app.get("/api/health")
async def health():
    """Health check — verify MCP servers and LLM are reachable."""
    mcp_status = {}
    for name, proc in mcp_processes.items():
        mcp_status[name] = "running" if proc.returncode is None else f"exited({proc.returncode})"

    llm_info = llm.get_info()

    return JSONResponse(content={
        "status": "ok",
        "mcp_servers": mcp_status,
        "llm": llm_info,
    })


@app.get("/api/config")
async def config():
    """Return frontend configuration."""
    return JSONResponse(content={
        "version": "2.0.0",
        "llm": llm.get_info(),
        "available_tools": list(TOOL_SERVER_MAP.keys()),
    })


# Serve frontend static files (if built)
frontend_dir = Path(__file__).parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SAG_V2_PORT", "4100"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Manual Steps (TPM)
- Set env vars: `LLM_PROVIDER=vllm`, `LLM_BASE_URL=http://localhost:8000/v1`, `SAG_V2_PORT=4100`
- Install: `pip install -r requirements.txt`
- Run: `python app.py`
