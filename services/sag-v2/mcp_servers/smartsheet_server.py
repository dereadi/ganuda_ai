"""
SAG v2 — Smartsheet Resource Management MCP Server
=====================================================
MCP server exposing Smartsheet RM (api.rm.smartsheet.com) resource tools.

Transport: stdio (spawned by FastAPI backend)
Auth: Bearer token from environment
Base URL: https://api.rm.smartsheet.com/api/v1/

Key advantage over Productive: Native /users/{id}/availabilities endpoint.

Usage:
    python smartsheet_mcp.py
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import date, timedelta
from typing import Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.insert(0, '/ganuda/lib')
try:
    from secrets_loader import get_secret
except ImportError:
    get_secret = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('smartsheet-mcp')

BASE_URL = "https://api.rm.smartsheet.com/api/v1"


def _get_token():
    """Resolve Smartsheet RM API token."""
    if get_secret:
        try:
            return get_secret("SMARTSHEET_RM_TOKEN")
        except RuntimeError:
            pass
    return os.environ.get("SMARTSHEET_RM_TOKEN", "")


# --- Rate Limiter ---
class TokenBucket:
    """Token bucket: Smartsheet RM allows ~40 req/10s."""
    def __init__(self, rate=40, period=10.0):
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_refill = time.monotonic()

    async def acquire(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.period))
        self.last_refill = now
        if self.tokens < 1:
            wait = (1 - self.tokens) * (self.period / self.rate)
            await asyncio.sleep(wait)
            self.tokens = 0
        else:
            self.tokens -= 1

rate_limiter = TokenBucket()


async def sm_request(path: str, params: Optional[dict] = None) -> dict:
    """Make an authenticated request to the Smartsheet RM API."""
    await rate_limiter.acquire()
    token = _get_token()
    if not token:
        return {"error": "SMARTSHEET_RM_TOKEN not configured"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"{BASE_URL}{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params or {})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Smartsheet RM error: %s %s", e.response.status_code, e.response.text[:200])
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.RequestError as e:
            logger.error("Smartsheet RM request failed: %s", e)
            return {"error": str(e)}


# --- MCP Server ---
server = Server("smartsheet-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_users",
            description="List users (team members) from Smartsheet Resource Management. Can filter by role or search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Filter by role (optional)"},
                    "per_page": {"type": "integer", "description": "Results per page (max 50)", "default": 50},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                },
            },
        ),
        Tool(
            name="get_user_availability",
            description="Get a user's availability (native Smartsheet endpoint). Returns daily available hours for a date range. This is the most accurate availability data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Smartsheet RM user ID"},
                    "from_date": {"type": "string", "description": "Start date (YYYY-MM-DD). Default: today"},
                    "to_date": {"type": "string", "description": "End date (YYYY-MM-DD). Default: 14 days from now"},
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="list_projects",
            description="List projects from Smartsheet Resource Management.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_field": {"type": "string", "description": "Field to filter on (optional)"},
                    "filter_value": {"type": "string", "description": "Value to filter for (optional)"},
                    "per_page": {"type": "integer", "description": "Results per page", "default": 50},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                },
            },
        ),
        Tool(
            name="list_assignments",
            description="List assignments (who is assigned to what). Filter by user or project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Filter by user (optional)"},
                    "project_id": {"type": "string", "description": "Filter by project (optional)"},
                    "from_date": {"type": "string", "description": "Start date filter (YYYY-MM-DD)"},
                    "to_date": {"type": "string", "description": "End date filter (YYYY-MM-DD)"},
                    "per_page": {"type": "integer", "default": 50},
                },
            },
        ),
        Tool(
            name="get_time_entries",
            description="Get time entries (actual logged hours). Filter by user, project, or date range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Filter by user (optional)"},
                    "project_id": {"type": "string", "description": "Filter by project (optional)"},
                    "from_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "to_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                    "per_page": {"type": "integer", "default": 50},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info("Tool call: %s(%s)", name, json.dumps(arguments)[:200])

    if name == "list_users":
        params = {"per_page": arguments.get("per_page", 50), "page": arguments.get("page", 1)}
        if arguments.get("role"):
            params["role"] = arguments["role"]
        data = await sm_request("/users", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        # Smartsheet returns {"data": [...]} or a flat list
        users = data.get("data", data) if isinstance(data, dict) else data
        return [TextContent(type="text", text=json.dumps(users, indent=2, default=str))]

    elif name == "get_user_availability":
        uid = arguments["user_id"]
        today = date.today()
        params = {
            "from": arguments.get("from_date", today.isoformat()),
            "to": arguments.get("to_date", (today + timedelta(days=14)).isoformat()),
        }
        data = await sm_request(f"/users/{uid}/availabilities", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]

        # Summarize availability
        avail_list = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(avail_list, list):
            total_available = sum(float(a.get("available_hours", 0)) for a in avail_list)
            result = {
                "user_id": uid,
                "from": params["from"],
                "to": params["to"],
                "total_available_hours": round(total_available, 2),
                "days": avail_list,
            }
        else:
            result = data
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    elif name == "list_projects":
        params = {"per_page": arguments.get("per_page", 50), "page": arguments.get("page", 1)}
        if arguments.get("filter_field") and arguments.get("filter_value"):
            params[f"filter[{arguments['filter_field']}]"] = arguments["filter_value"]
        data = await sm_request("/projects", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        projects = data.get("data", data) if isinstance(data, dict) else data
        return [TextContent(type="text", text=json.dumps(projects, indent=2, default=str))]

    elif name == "list_assignments":
        params = {"per_page": arguments.get("per_page", 50)}
        if arguments.get("user_id"):
            params["user_id"] = arguments["user_id"]
        if arguments.get("project_id"):
            params["project_id"] = arguments["project_id"]
        if arguments.get("from_date"):
            params["from"] = arguments["from_date"]
        if arguments.get("to_date"):
            params["to"] = arguments["to_date"]
        data = await sm_request("/assignments", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        assignments = data.get("data", data) if isinstance(data, dict) else data
        return [TextContent(type="text", text=json.dumps(assignments, indent=2, default=str))]

    elif name == "get_time_entries":
        params = {"per_page": arguments.get("per_page", 50)}
        if arguments.get("user_id"):
            params["user_id"] = arguments["user_id"]
        if arguments.get("project_id"):
            params["project_id"] = arguments["project_id"]
        if arguments.get("from_date"):
            params["from"] = arguments["from_date"]
        if arguments.get("to_date"):
            params["to"] = arguments["to_date"]
        data = await sm_request("/time_entries", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        entries = data.get("data", data) if isinstance(data, dict) else data
        return [TextContent(type="text", text=json.dumps(entries, indent=2, default=str))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    logger.info("Starting Smartsheet RM MCP server (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())