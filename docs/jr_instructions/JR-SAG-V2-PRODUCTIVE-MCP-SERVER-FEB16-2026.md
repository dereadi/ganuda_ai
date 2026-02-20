# Jr Instruction: SAG v2 Productive MCP Server

**Task ID**: SAG-V2-MCP-PRODUCTIVE
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Sprint**: RC-2026-02E
**Dependencies**: None
**use_rlm**: false

## Objective
Create an MCP (Model Context Protocol) server that wraps the Productive API (api.productive.io/api/v2/) for resource management queries. This server will be consumed by the SAG v2 FastAPI backend via stdio transport.

## Step 1: Create requirements.txt

Create `/ganuda/services/sag-v2/requirements.txt`

```text
# SAG v2 - FastAPI + MCP Architecture
# MCP servers
mcp>=1.0.0
httpx>=0.27.0

# FastAPI backend
fastapi>=0.115.0
uvicorn>=0.34.0
pydantic>=2.0.0
sse-starlette>=2.0.0

# LLM clients
openai>=1.50.0
anthropic>=0.40.0
```

## Step 2: Create productive_mcp.py

Create `/ganuda/services/sag-v2/mcp_servers/productive_mcp.py`

```python
"""
SAG v2 — Productive API MCP Server
====================================
MCP server exposing Productive (api.productive.io) resource management tools.

Transport: stdio (spawned by FastAPI backend)
Auth: X-Auth-Token + X-Organization-Id from environment
Rate limit: 100 requests per 10 seconds (token bucket)

Usage:
    # Direct test
    python productive_mcp.py

    # As MCP server (spawned by parent)
    Communicates via stdin/stdout using MCP protocol
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent paths for secrets_loader
sys.path.insert(0, '/ganuda/lib')
try:
    from secrets_loader import get_secret
except ImportError:
    get_secret = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('productive-mcp')

# --- Configuration ---
BASE_URL = "https://api.productive.io/api/v2"

def _get_token():
    """Resolve Productive API token from secrets or env."""
    if get_secret:
        try:
            return get_secret("PRODUCTIVE_API_TOKEN")
        except RuntimeError:
            pass
    return os.environ.get("PRODUCTIVE_API_TOKEN", "")

def _get_org_id():
    """Resolve Productive organization ID from secrets or env."""
    if get_secret:
        try:
            return get_secret("PRODUCTIVE_ORG_ID")
        except RuntimeError:
            pass
    return os.environ.get("PRODUCTIVE_ORG_ID", "")


# --- Rate Limiter ---
class TokenBucket:
    """Simple token bucket rate limiter: 100 requests per 10 seconds."""
    def __init__(self, rate=100, period=10.0):
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


# --- API Client ---
async def productive_request(path: str, params: Optional[dict] = None) -> dict:
    """Make an authenticated request to the Productive API."""
    await rate_limiter.acquire()
    token = _get_token()
    org_id = _get_org_id()
    if not token or not org_id:
        return {"error": "PRODUCTIVE_API_TOKEN or PRODUCTIVE_ORG_ID not configured"}

    headers = {
        "Content-Type": "application/vnd.api+json",
        "X-Auth-Token": token,
        "X-Organization-Id": org_id,
    }
    url = f"{BASE_URL}{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params or {})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Productive API error: %s %s", e.response.status_code, e.response.text[:200])
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.RequestError as e:
            logger.error("Productive API request failed: %s", e)
            return {"error": str(e)}


def _extract_attributes(data_list: list) -> list:
    """Extract attributes from JSON:API data array, including id."""
    results = []
    for item in data_list:
        record = {"id": item.get("id")}
        record.update(item.get("attributes", {}))
        results.append(record)
    return results


# --- MCP Server ---
server = Server("productive-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_people",
            description="List people/team members from Productive. Filter by status (active/archived) or search by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: active, archived. Default: active", "default": "active"},
                    "search": {"type": "string", "description": "Search by name (optional)"},
                    "page_size": {"type": "integer", "description": "Results per page (max 200)", "default": 50},
                },
            },
        ),
        Tool(
            name="get_person_details",
            description="Get detailed information about a specific person by their Productive ID, including their project assignments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "The Productive person ID"},
                },
                "required": ["person_id"],
            },
        ),
        Tool(
            name="list_bookings",
            description="List resource bookings (scheduled work). Filter by date range, person, or project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_after": {"type": "string", "description": "Start date (YYYY-MM-DD). Default: today"},
                    "date_before": {"type": "string", "description": "End date (YYYY-MM-DD). Default: 30 days from now"},
                    "person_id": {"type": "string", "description": "Filter by person ID (optional)"},
                    "project_id": {"type": "string", "description": "Filter by project ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_availability",
            description="Calculate a person's availability for a date range. Shows booked hours vs capacity (8h/day) per day.",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "The Productive person ID"},
                    "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD). Default: today"},
                    "date_to": {"type": "string", "description": "End date (YYYY-MM-DD). Default: 14 days from now"},
                    "daily_capacity": {"type": "number", "description": "Hours per day capacity. Default: 8", "default": 8},
                },
                "required": ["person_id"],
            },
        ),
        Tool(
            name="list_projects",
            description="List projects from Productive. Filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter: active, archived, all. Default: active", "default": "active"},
                    "search": {"type": "string", "description": "Search by project name (optional)"},
                    "page_size": {"type": "integer", "description": "Results per page (max 200)", "default": 50},
                },
            },
        ),
        Tool(
            name="list_project_assignments",
            description="List project assignments — who is assigned to which project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "Filter by person (optional)"},
                    "project_id": {"type": "string", "description": "Filter by project (optional)"},
                },
            },
        ),
        Tool(
            name="get_time_entries",
            description="Get time tracking entries for a person or project within a date range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "Filter by person (optional)"},
                    "project_id": {"type": "string", "description": "Filter by project (optional)"},
                    "date_after": {"type": "string", "description": "Start date (YYYY-MM-DD). Default: 30 days ago"},
                    "date_before": {"type": "string", "description": "End date (YYYY-MM-DD). Default: today"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    logger.info("Tool call: %s(%s)", name, json.dumps(arguments)[:200])

    if name == "list_people":
        params = {"filter[status]": arguments.get("status", "active"), "page[size]": arguments.get("page_size", 50)}
        if arguments.get("search"):
            params["filter[search]"] = arguments["search"]
        data = await productive_request("/people", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        people = _extract_attributes(data.get("data", []))
        return [TextContent(type="text", text=json.dumps(people, indent=2, default=str))]

    elif name == "get_person_details":
        pid = arguments["person_id"]
        data = await productive_request(f"/people/{pid}", {"include": "project_assignments"})
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        person = {"id": data["data"]["id"]}
        person.update(data["data"].get("attributes", {}))
        included = data.get("included", [])
        person["project_assignments"] = _extract_attributes(included)
        return [TextContent(type="text", text=json.dumps(person, indent=2, default=str))]

    elif name == "list_bookings":
        today = date.today()
        params = {
            "filter[after]": arguments.get("date_after", today.isoformat()),
            "filter[before]": arguments.get("date_before", (today + timedelta(days=30)).isoformat()),
            "page[size]": 200,
        }
        if arguments.get("person_id"):
            params["filter[person_id]"] = arguments["person_id"]
        if arguments.get("project_id"):
            params["filter[project_id]"] = arguments["project_id"]
        data = await productive_request("/bookings", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        bookings = _extract_attributes(data.get("data", []))
        return [TextContent(type="text", text=json.dumps(bookings, indent=2, default=str))]

    elif name == "get_availability":
        pid = arguments["person_id"]
        today = date.today()
        date_from = date.fromisoformat(arguments.get("date_from", today.isoformat()))
        date_to = date.fromisoformat(arguments.get("date_to", (today + timedelta(days=14)).isoformat()))
        capacity = arguments.get("daily_capacity", 8)

        # Fetch bookings for the person in the date range
        params = {
            "filter[person_id]": pid,
            "filter[after]": date_from.isoformat(),
            "filter[before]": date_to.isoformat(),
            "page[size]": 200,
        }
        data = await productive_request("/bookings", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]

        # Build day-by-day availability
        bookings = data.get("data", [])
        booked_hours = {}
        for b in bookings:
            attrs = b.get("attributes", {})
            b_start = attrs.get("started_on", "")
            b_end = attrs.get("ended_on", b_start)
            hours = attrs.get("total_time", 0) or 0
            if b_start:
                # Distribute hours across booking days
                try:
                    bs = date.fromisoformat(b_start)
                    be = date.fromisoformat(b_end) if b_end else bs
                    days = max(1, (be - bs).days + 1)
                    daily = hours / days
                    d = bs
                    while d <= be:
                        booked_hours[d.isoformat()] = booked_hours.get(d.isoformat(), 0) + daily
                        d += timedelta(days=1)
                except (ValueError, TypeError):
                    pass

        # Generate availability report
        result = {"person_id": pid, "date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "daily_capacity": capacity, "days": []}
        d = date_from
        total_available = 0
        total_booked = 0
        while d <= date_to:
            if d.weekday() < 5:  # Mon-Fri only
                booked = round(booked_hours.get(d.isoformat(), 0), 2)
                available = round(max(0, capacity - booked), 2)
                result["days"].append({"date": d.isoformat(), "booked": booked, "available": available, "capacity": capacity})
                total_available += available
                total_booked += booked
            d += timedelta(days=1)

        result["total_available_hours"] = round(total_available, 2)
        result["total_booked_hours"] = round(total_booked, 2)
        result["utilization_pct"] = round(total_booked / max(1, total_booked + total_available) * 100, 1)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "list_projects":
        params = {"page[size]": arguments.get("page_size", 50)}
        status = arguments.get("status", "active")
        if status != "all":
            params["filter[status]"] = status
        if arguments.get("search"):
            params["filter[search]"] = arguments["search"]
        data = await productive_request("/projects", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        projects = _extract_attributes(data.get("data", []))
        return [TextContent(type="text", text=json.dumps(projects, indent=2, default=str))]

    elif name == "list_project_assignments":
        params = {"page[size]": 200}
        if arguments.get("person_id"):
            params["filter[person_id]"] = arguments["person_id"]
        if arguments.get("project_id"):
            params["filter[project_id]"] = arguments["project_id"]
        data = await productive_request("/project_assignments", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        assignments = _extract_attributes(data.get("data", []))
        return [TextContent(type="text", text=json.dumps(assignments, indent=2, default=str))]

    elif name == "get_time_entries":
        today = date.today()
        params = {
            "filter[after]": arguments.get("date_after", (today - timedelta(days=30)).isoformat()),
            "filter[before]": arguments.get("date_before", today.isoformat()),
            "page[size]": 200,
        }
        if arguments.get("person_id"):
            params["filter[person_id]"] = arguments["person_id"]
        if arguments.get("project_id"):
            params["filter[project_id]"] = arguments["project_id"]
        data = await productive_request("/time_entries", params)
        if "error" in data:
            return [TextContent(type="text", text=json.dumps(data))]
        entries = _extract_attributes(data.get("data", []))
        return [TextContent(type="text", text=json.dumps(entries, indent=2, default=str))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def main():
    logger.info("Starting Productive MCP server (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

## Manual Steps (TPM)
- Add `PRODUCTIVE_API_TOKEN` and `PRODUCTIVE_ORG_ID` to `/ganuda/config/secrets.env` once Russell provides API credentials
- Test: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python productive_mcp.py`
