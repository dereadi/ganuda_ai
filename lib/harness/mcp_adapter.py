"""
MCP Adapter — Manages MCP server subprocesses for harness tool calls.

Extracted from /ganuda/services/sag-v2/backend/app.py into a standalone,
reusable module with no FastAPI dependency. Any harness tier can use this
to call MCP tools.

DC-9: Lazy-start servers (only when first needed).
DC-10: MCP tools are the reflex data layer — fast, real, no hallucination.
Crawdad: Validate arguments, sanitize responses.

Usage:
    adapter = MCPAdapter.from_config()
    await adapter.call_tool("productive", "list_people", {"status": "active"})
    await adapter.stop_all()
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("harness.mcp_adapter")


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    script: str
    enabled: bool = True
    idle_timeout_seconds: int = 300


@dataclass
class MCPAdapterConfig:
    """Configuration for the MCP adapter."""
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MCPAdapterConfig":
        servers = {}
        for name, cfg in d.items():
            servers[name] = MCPServerConfig(
                name=name,
                script=cfg.get("script", ""),
                enabled=cfg.get("enabled", True),
                idle_timeout_seconds=cfg.get("idle_timeout_seconds", 300),
            )
        return cls(servers=servers)


# Tool-name to MCP server mapping.
# Keys are tool names as seen by the LLM; values are server names.
TOOL_SERVER_MAP: Dict[str, str] = {
    # Productive tools
    "list_people": "productive",
    "get_person_details": "productive",
    "list_bookings": "productive",
    "get_availability": "productive",
    "list_projects_productive": "productive",
    "list_project_assignments": "productive",
    "get_time_entries_productive": "productive",
    # Smartsheet RM tools
    "list_users": "smartsheet",
    "get_user_availability": "smartsheet",
    "list_projects_smartsheet": "smartsheet",
    "list_assignments": "smartsheet",
    "get_time_entries_smartsheet": "smartsheet",
}


class MCPAdapter:
    """Manages MCP server subprocesses and routes tool calls.

    Servers are lazy-started on first tool call (DC-9).
    Subprocess communication uses JSON-RPC over stdio.
    """

    def __init__(self, config: Optional[MCPAdapterConfig] = None):
        self._config = config or MCPAdapterConfig()
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
        self._last_activity: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> "MCPAdapter":
        """Create an MCPAdapter from the harness config YAML.

        Reads the 'mcp_servers' section from config.yaml.
        Falls back to default paths if no config found.
        """
        if config_path is None:
            config_path = os.environ.get(
                "HARNESS_CONFIG_PATH",
                "/ganuda/lib/harness/config.yaml",
            )

        config = MCPAdapterConfig()

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    raw = yaml.safe_load(f) or {}
                mcp_section = raw.get("mcp_servers", {})
                if mcp_section:
                    config = MCPAdapterConfig.from_dict(mcp_section)
                    logger.info(
                        "Loaded MCP config: %d servers from %s",
                        len(config.servers), config_path,
                    )
            except Exception as e:
                logger.error("Failed to load MCP config from %s: %s", config_path, e)

        # Fallback defaults if no config
        if not config.servers:
            config = MCPAdapterConfig(servers={
                "productive": MCPServerConfig(
                    name="productive",
                    script="/ganuda/services/sag-v2/mcp_servers/productive_server.py",
                ),
                "smartsheet": MCPServerConfig(
                    name="smartsheet",
                    script="/ganuda/services/sag-v2/mcp_servers/smartsheet_server.py",
                ),
            })
            logger.info("Using default MCP server config (no YAML found)")

        return cls(config)

    # ------------------------------------------------------------------
    # Server Lifecycle
    # ------------------------------------------------------------------

    async def start_server(self, name: str) -> bool:
        """Start an MCP server subprocess.

        Returns True if the server started (or was already running).
        """
        async with self._lock:
            # Already running?
            proc = self._processes.get(name)
            if proc is not None and proc.returncode is None:
                return True

            server_cfg = self._config.servers.get(name)
            if not server_cfg:
                logger.error("Unknown MCP server: %s", name)
                return False
            if not server_cfg.enabled:
                logger.info("MCP server %s is disabled in config", name)
                return False

            script_path = Path(server_cfg.script)
            if not script_path.exists():
                logger.error("MCP server script not found: %s", script_path)
                return False

            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(script_path),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                self._processes[name] = proc
                self._last_activity[name] = time.monotonic()
                logger.info("Started MCP server: %s (PID %d)", name, proc.pid)
                return True
            except Exception as e:
                logger.error("Failed to start MCP server %s: %s", name, e)
                return False

    async def stop_server(self, name: str) -> None:
        """Stop a specific MCP server subprocess."""
        proc = self._processes.pop(name, None)
        if proc is None:
            return
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
            logger.info("Stopped MCP server: %s", name)
        self._last_activity.pop(name, None)

    async def stop_all(self) -> None:
        """Stop all running MCP server subprocesses."""
        names = list(self._processes.keys())
        for name in names:
            await self.stop_server(name)

    async def _ensure_server(self, name: str) -> bool:
        """Lazy-start a server if not already running (DC-9)."""
        proc = self._processes.get(name)
        if proc is not None and proc.returncode is None:
            self._last_activity[name] = time.monotonic()
            return True
        return await self.start_server(name)

    # ------------------------------------------------------------------
    # Tool Calls
    # ------------------------------------------------------------------

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> dict:
        """Call a tool on an MCP server via JSON-RPC over stdio.

        Args:
            server_name: The MCP server to call (e.g., "productive").
            tool_name: The MCP tool name (e.g., "list_people").
            arguments: Tool arguments dict.

        Returns:
            Parsed result dict, or {"error": "..."} on failure.
        """
        # Crawdad: validate arguments
        if not isinstance(arguments, dict):
            return {"error": "arguments must be a dict"}

        if not await self._ensure_server(server_name):
            return {"error": f"MCP server '{server_name}' could not be started"}

        proc = self._processes.get(server_name)
        if proc is None or proc.returncode is not None:
            return {"error": f"MCP server '{server_name}' not running"}

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
            response_line = await asyncio.wait_for(
                proc.stdout.readline(), timeout=30.0
            )
            if not response_line:
                return {"error": "Empty response from MCP server"}

            response = json.loads(response_line.decode())

            # Handle JSON-RPC error
            if "error" in response:
                return {"error": response["error"]}

            # Extract text content from MCP result
            result = response.get("result", {})
            if isinstance(result, dict) and "content" in result:
                texts = [
                    c.get("text", "")
                    for c in result["content"]
                    if c.get("type") == "text"
                ]
                combined = "\n".join(texts)
                # Try to parse as JSON for structured data
                try:
                    return json.loads(combined)
                except json.JSONDecodeError:
                    return {"text": combined}
            return result

        except asyncio.TimeoutError:
            logger.warning("MCP call to %s/%s timed out", server_name, tool_name)
            return {"error": f"MCP call to {server_name}/{tool_name} timed out (30s)"}
        except Exception as e:
            logger.error(
                "MCP call to %s/%s failed: %s", server_name, tool_name, e
            )
            return {"error": str(e)}

    async def call_tool_by_name(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool by its LLM-facing name, auto-routing to the correct server.

        Handles the name suffix convention (e.g., list_projects_productive ->
        server=productive, actual_tool=list_projects).
        """
        server_name = TOOL_SERVER_MAP.get(tool_name)
        if not server_name:
            return {"error": f"Unknown tool: {tool_name}"}

        # Strip suffix for actual MCP call
        actual_name = (
            tool_name
            .replace("_productive", "")
            .replace("_smartsheet", "")
        )
        return await self.call_tool(server_name, actual_name, arguments)

    # ------------------------------------------------------------------
    # Health & Introspection
    # ------------------------------------------------------------------

    async def health_check(self) -> Dict[str, str]:
        """Check status of all configured MCP servers.

        Returns {server_name: "running"|"stopped"|"disabled"|"missing_script"}.
        """
        report = {}
        for name, cfg in self._config.servers.items():
            if not cfg.enabled:
                report[name] = "disabled"
                continue
            if not Path(cfg.script).exists():
                report[name] = "missing_script"
                continue
            proc = self._processes.get(name)
            if proc is not None and proc.returncode is None:
                report[name] = "running"
            else:
                report[name] = "stopped"
        return report

    def get_available_tools(self) -> List[dict]:
        """Return tool definitions in OpenAI function-calling format.

        These can be passed directly to an LLM that supports tool_use.
        Imports from domain_prompts to avoid duplication.
        """
        try:
            sys.path.insert(0, "/ganuda/services/sag-v2/backend")
            from domain_prompts import build_tool_definitions
            return build_tool_definitions()
        except ImportError:
            logger.warning(
                "Could not import domain_prompts; returning empty tool list"
            )
            return []
        finally:
            # Clean up sys.path
            try:
                sys.path.remove("/ganuda/services/sag-v2/backend")
            except ValueError:
                pass

    def get_tool_server_map(self) -> Dict[str, str]:
        """Return the tool-name to server-name mapping."""
        return dict(TOOL_SERVER_MAP)

    # ------------------------------------------------------------------
    # Idle Cleanup (DC-9)
    # ------------------------------------------------------------------

    async def cleanup_idle_servers(self) -> List[str]:
        """Stop servers that have been idle beyond their timeout.

        Returns list of server names that were stopped.
        """
        stopped = []
        now = time.monotonic()
        for name, last in list(self._last_activity.items()):
            cfg = self._config.servers.get(name)
            if cfg and (now - last) > cfg.idle_timeout_seconds:
                await self.stop_server(name)
                stopped.append(name)
                logger.info(
                    "Stopped idle MCP server %s (idle %.0fs > %ds)",
                    name, now - last, cfg.idle_timeout_seconds,
                )
        return stopped
