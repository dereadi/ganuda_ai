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

# Add lib to path
sys.path.insert(0, '/ganuda/lib')

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get(
    'TELEGRAM_BOT_TOKEN',
    '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
)
DEFAULT_CHAT_ID = os.environ.get('TELEGRAM_ALERT_CHAT_ID', '-1003439875431')


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


def send_alert(title: str, message: str, severity: str = "medium", source: str = "mcp") -> bool:
    """Send formatted alert to Telegram."""
    try:
        from alert_manager import send_alert as _send_alert
        return _send_alert(title, message, severity, source)
    except Exception as e:
        # Fallback to direct send
        emoji = {'critical': '🚨', 'high': '🔴', 'medium': '🟡', 'low': '🔵', 'info': 'ℹ️'}.get(severity, '⚠️')
        text = f"{emoji} *{title}*\n_{severity.upper()} | {source}_\n\n{message}"
        result = send_telegram(DEFAULT_CHAT_ID, text, "Markdown")
        return result.get("success", False)


def trigger_research(query: str, max_steps: int = 5) -> dict:
    """Queue research via ii-researcher."""
    try:
        from research_dispatcher import ResearchDispatcher
        dispatcher = ResearchDispatcher()
        job_id = dispatcher.queue_research(
            query=query,
            requester_type="mcp",
            requester_id="claude-code",
            max_steps=max_steps
        )
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        return {"error": str(e)}


def query_council(question: str, high_stakes: bool = False) -> dict:
    """Query the 7-Specialist Council."""
    try:
        from specialist_council import council_vote_first
        result = council_vote_first(question, high_stakes=high_stakes)
        return {
            "decision": result.get("decision"),
            "vote_counts": result.get("vote_counts"),
            "deliberation": result.get("deliberation", "")[:500]
        }
    except Exception as e:
        return {"error": str(e)}


# MCP Server implementation
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server

    server = Server("telegram-cherokee")

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
                        "chat_id": {"type": "string", "description": "Telegram chat ID"},
                        "message": {"type": "string", "description": "Message text"}
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
                        "title": {"type": "string", "description": "Alert title"},
                        "message": {"type": "string", "description": "Alert details"},
                        "severity": {"type": "string", "enum": ["info", "low", "medium", "high", "critical"]}
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
                        "query": {"type": "string", "description": "Research question"},
                        "max_steps": {"type": "integer", "description": "Max research steps"}
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
                        "question": {"type": "string", "description": "Question for the Council"},
                        "high_stakes": {"type": "boolean", "description": "Use high-stakes mode"}
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
            result = send_alert(
                arguments.get("title", "Alert"),
                arguments.get("message", ""),
                arguments.get("severity", "medium")
            )
            return [TextContent(type="text", text=json.dumps({"sent": result}))]

        elif name == "trigger_research":
            result = trigger_research(
                arguments.get("query", ""),
                arguments.get("max_steps", 5)
            )
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "query_council":
            result = query_council(
                arguments.get("question", ""),
                arguments.get("high_stakes", False)
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def main():
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError:
    # MCP not installed - provide standalone functions only
    print("MCP SDK not installed. Functions available for direct import.")

    if __name__ == "__main__":
        print("To use as MCP server: pip install mcp")
        print("Available functions: send_telegram, send_alert, trigger_research, query_council")
