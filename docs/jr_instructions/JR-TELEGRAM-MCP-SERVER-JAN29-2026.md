# JR Instruction: Telegram MCP Server

**JR ID:** JR-TELEGRAM-MCP-SERVER-JAN29-2026
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-TELEGRAM-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE (Turtle, Crawdad, Raven recommended MCP)
**Depends On:** JR-TELEGRAM-STREAMING-CHUNKING-JAN29-2026

---

## Objective

Expose Telegram bot capabilities as MCP (Model Context Protocol) tools so Claude Code can send alerts, trigger research, and interact with users via Telegram.

---

## Use Cases

1. **Claude Code sends alert:** After completing a task, notify TPM via Telegram
2. **Claude Code triggers research:** Queue deep research and get results
3. **Claude Code queries Council:** Get specialist input during planning
4. **Claude Code sends status:** Notify on long-running job completion

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Claude Code                        │
│                       │                              │
│                       ▼                              │
│              MCP Client Interface                    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│            telegram_mcp_server.py                    │
│                                                      │
│  Tools:                                              │
│  ├─ send_telegram_message(chat_id, text)            │
│  ├─ send_telegram_alert(title, message, severity)   │
│  ├─ trigger_research(query)                         │
│  └─ query_council(question)                         │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              Telegram Bot API                        │
│              research_dispatcher                     │
│              specialist_council                      │
└─────────────────────────────────────────────────────┘
```

---

## Implementation

### Step 1: Install MCP SDK

```bash
pip install mcp
```

### Step 2: Create MCP Server

Create `/ganuda/telegram_bot/telegram_mcp_server.py`:

```python
#!/usr/bin/env python3
"""
Telegram MCP Server - Expose Telegram bot as MCP tools.
Cherokee AI Federation - For Seven Generations
"""

import os
import sys
import json
import asyncio
import requests
from typing import Optional

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Add lib to path
sys.path.insert(0, '/ganuda/lib')

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get(
    'TELEGRAM_BOT_TOKEN',
    '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
)
DEFAULT_CHAT_ID = os.environ.get('TELEGRAM_ALERT_CHAT_ID', '-1003439875431')

# Create MCP server
server = Server("telegram-cherokee")


def send_telegram(chat_id: str, text: str, parse_mode: str = None) -> dict:
    """Send message via Telegram Bot API."""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            },
            timeout=10
        )
        return {"success": response.status_code == 200, "response": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="send_telegram_message",
            description="Send a message to a Telegram chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Telegram chat ID (default: TPM alert channel)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text to send"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="send_telegram_alert",
            description="Send a formatted alert to TPM via Telegram",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Alert title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Alert details"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["info", "low", "medium", "high", "critical"],
                        "description": "Alert severity level"
                    }
                },
                "required": ["title", "message"]
            }
        ),
        Tool(
            name="trigger_research",
            description="Queue deep research via ii-researcher",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Research question"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Max research steps (default: 5)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="query_council",
            description="Get 7-Specialist Council input on a question",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question for the Council"
                    },
                    "high_stakes": {
                        "type": "boolean",
                        "description": "Use high-stakes deliberation mode"
                    }
                },
                "required": ["question"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a tool."""

    if name == "send_telegram_message":
        chat_id = arguments.get("chat_id", DEFAULT_CHAT_ID)
        message = arguments.get("message", "")
        result = send_telegram(chat_id, message)
        return [TextContent(type="text", text=json.dumps(result))]

    elif name == "send_telegram_alert":
        from alert_manager import send_alert
        title = arguments.get("title", "Alert")
        message = arguments.get("message", "")
        severity = arguments.get("severity", "medium")

        result = send_alert(title, message, severity, source="claude-code")
        return [TextContent(type="text", text=json.dumps({"sent": result}))]

    elif name == "trigger_research":
        from research_dispatcher import ResearchDispatcher
        query = arguments.get("query", "")
        max_steps = arguments.get("max_steps", 5)

        dispatcher = ResearchDispatcher()
        job_id = dispatcher.queue_research(
            query=query,
            requester_type="mcp",
            requester_id="claude-code",
            max_steps=max_steps
        )
        return [TextContent(type="text", text=json.dumps({
            "job_id": job_id,
            "status": "queued",
            "message": "Research queued. Results in 3-5 minutes."
        }))]

    elif name == "query_council":
        from specialist_council import council_vote_first
        question = arguments.get("question", "")
        high_stakes = arguments.get("high_stakes", False)

        result = council_vote_first(question, high_stakes=high_stakes)

        # Return summary
        summary = {
            "decision": result.get("decision"),
            "vote_counts": result.get("vote_counts"),
            "deliberation": result.get("deliberation", "")[:500]
        }
        return [TextContent(type="text", text=json.dumps(summary))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Create Claude Code Config

Add to `~/.claude/claude_code_config.json`:

```json
{
  "mcpServers": {
    "telegram-cherokee": {
      "command": "python3",
      "args": ["/ganuda/telegram_bot/telegram_mcp_server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8",
        "PYTHONPATH": "/ganuda/lib"
      }
    }
  }
}
```

### Step 4: Test MCP Tools

From Claude Code:
```
Use the send_telegram_alert tool to notify TPM that the deployment is complete.
```

Expected:
- Claude Code invokes MCP tool
- TPM receives Telegram alert

---

## Testing

1. **Send Message:**
   ```
   mcp call telegram-cherokee send_telegram_message '{"message": "Test from MCP"}'
   ```

2. **Send Alert:**
   ```
   mcp call telegram-cherokee send_telegram_alert '{"title": "Test Alert", "message": "MCP integration working", "severity": "info"}'
   ```

3. **Query Council:**
   ```
   mcp call telegram-cherokee query_council '{"question": "Should we migrate to Kubernetes?"}'
   ```

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/telegram_bot/telegram_mcp_server.py` | CREATE |
| `~/.claude/claude_code_config.json` | MODIFY - add MCP server config |

---

## Security Notes

- MCP server runs locally, not exposed externally
- Uses existing bot token (no new credentials)
- Rate limiting handled by alert_manager
- Council queries logged for audit

---

FOR SEVEN GENERATIONS
