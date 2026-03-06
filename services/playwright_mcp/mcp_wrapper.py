#!/usr/bin/env python3
"""
Playwright MCP Wrapper — Council Web Browsing Capability
Council Vote: #69d636ba (7/7 unanimous, 0.844)

Wraps @anthropic/playwright-mcp to provide a simple HTTP API:
  POST /browse  {"url": "...", "prompt": "..."} → {"content": "..."}

The wrapper:
1. Launches Playwright MCP as a subprocess
2. Communicates via MCP protocol (stdin/stdout JSON-RPC)
3. Exposes HTTP endpoint for the Gateway

Usage:
  python3 mcp_wrapper.py --port 8095
"""

import os
import sys
import json
import asyncio
import subprocess
import logging
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-Wrapper] %(levelname)s %(message)s"
)
logger = logging.getLogger("mcp-wrapper")

MCP_SERVER_CMD = ["npx", "@anthropic/playwright-mcp@latest", "--headless"]
PORT = int(os.environ.get("MCP_WRAPPER_PORT", "8095"))


class PlaywrightMCPClient:
    """Communicates with the Playwright MCP server via stdio JSON-RPC."""

    def __init__(self):
        self.process = None
        self.request_id = 0

    async def start(self):
        """Start the MCP server subprocess."""
        logger.info(f"Starting MCP server: {' '.join(MCP_SERVER_CMD)}")
        self.process = await asyncio.create_subprocess_exec(
            *MCP_SERVER_CMD,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.info(f"MCP server started (PID: {self.process.pid})")

        # Initialize MCP connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ganuda-mcp-wrapper", "version": "1.0.0"}
        })
        logger.info("MCP initialized")

    async def _send_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request to the MCP server."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        line = json.dumps(request) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode())
        return {"error": "No response from MCP server"}

    async def navigate(self, url: str) -> dict:
        """Navigate to a URL and return page content."""
        result = await self._send_request("tools/call", {
            "name": "browser_navigate",
            "arguments": {"url": url}
        })
        return result

    async def get_content(self) -> str:
        """Get the current page content as text."""
        result = await self._send_request("tools/call", {
            "name": "browser_snapshot",
            "arguments": {}
        })
        if "result" in result:
            content_blocks = result["result"].get("content", [])
            return "\n".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return str(result)

    async def close(self):
        """Shut down the MCP server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP server stopped")


async def handle_browse(request_data: dict, client: PlaywrightMCPClient) -> dict:
    """Handle a /browse request."""
    url = request_data.get("url", "")
    if not url:
        return {"error": "url is required"}

    try:
        await client.navigate(url)
        content = await client.get_content()
        return {
            "url": url,
            "content": content[:10000],
            "truncated": len(content) > 10000
        }
    except Exception as e:
        logger.error(f"Browse error: {e}")
        return {"error": str(e)}


async def run_server():
    """Run the HTTP wrapper server."""
    from aiohttp import web

    client = PlaywrightMCPClient()
    await client.start()

    async def browse_handler(request):
        data = await request.json()
        result = await handle_browse(data, client)
        return web.json_response(result)

    async def health_handler(request):
        return web.json_response({"status": "ok", "mcp_pid": client.process.pid if client.process else None})

    app = web.Application()
    app.router.add_post("/browse", browse_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"MCP Wrapper listening on port {PORT}")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await client.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(run_server())