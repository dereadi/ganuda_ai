"""Base ToolSet interface for federation AI tool dispatch.

Every ToolSet follows DC-11 Macro Polymorphism:
SENSE (parse args) → REACT (execute) → EVALUATE (validate result)

Adapted from MyBrain ToolSet pattern. Council vote #798ad0b7.
"""

import time
import hashlib
import json
import psycopg2
from dataclasses import dataclass, field
from typing import Any, Optional

# Max tool calls per request (safety limit from MyBrain)
MAX_CONSECUTIVE_TOOL_CALLS = 5


def _get_db_config() -> dict:
    """Load DB config from secrets.env."""
    config = {
        "host": os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
        "port": 5432,
        "dbname": "zammad_production",
        "user": "claude",
    }
    try:
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                if "DB_PASS=" in line and not line.startswith("#"):
                    config["password"] = line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    return config


def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(**_get_db_config())


@dataclass
class ToolDescriptor:
    """LLM-callable tool description."""
    name: str
    description: str
    parameters: dict
    safety_class: str  # 'read' or 'write'


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    success: bool
    data: Any
    latency_ms: float
    audit_hash: str = ""
    error: str = ""


class ToolSet:
    """Base class for domain-specific tool sets.

    Subclasses implement tools as methods and register descriptors.
    Each tool registers in duplo_tool_registry as a ring.
    """

    domain: str = "base"

    def get_tools(self) -> list:
        """Return all tool descriptors for LLM function-calling schema."""
        raise NotImplementedError

    def execute(self, tool_name: str, args: dict) -> ToolResult:
        """Execute a tool by name with args. Logs to sag_events."""
        start = time.time()

        method = getattr(self, tool_name, None)
        if not method:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                latency_ms=0,
                error=f"Unknown tool: {tool_name}"
            )

        # Check safety class
        descriptor = next((t for t in self.get_tools() if t.name == tool_name), None)
        if descriptor and descriptor.safety_class == "write":
            # Write tools require council gate — caller must have verified
            pass

        try:
            result = method(**args)
            latency = (time.time() - start) * 1000
            audit = hashlib.sha256(
                f"{tool_name}-{json.dumps(args, sort_keys=True)}-{time.time()}".encode()
            ).hexdigest()[:16]

            tr = ToolResult(
                tool_name=tool_name,
                success=True,
                data=result,
                latency_ms=round(latency, 1),
                audit_hash=audit,
            )

            # Log to sag_events (Eagle Eye visibility condition)
            self._log_tool_call(tr, args)
            return tr

        except Exception as e:
            latency = (time.time() - start) * 1000
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                latency_ms=round(latency, 1),
                error=str(e),
            )

    def _log_tool_call(self, result: ToolResult, args: dict):
        """Log tool execution to sag_events for observability."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sag_events (event_type, event_data, source_node, created_at)
                VALUES ('tool_call', %s, 'redfin', NOW())
            """, (json.dumps({
                "domain": self.domain,
                "tool": result.tool_name,
                "success": result.success,
                "latency_ms": result.latency_ms,
                "audit_hash": result.audit_hash,
                "args_keys": list(args.keys()),
                "error": result.error or None,
            }),))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass  # Don't fail tool execution because logging failed

    def to_openai_tools(self) -> list:
        """Convert tool descriptors to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": f"{self.domain}_{t.name}",
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.get_tools()
        ]
