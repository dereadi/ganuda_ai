# JR Instruction: Duplo Tool Registry

**Task**: DUPLO-REGISTRY-001
**Title**: Create Duplo Tool Registry (Enzyme Amino Acids)
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.

## Context

The Duplo enzyme system needs a tool registry — the catalog of atomic capabilities (amino acids) that enzymes are assembled from. This is the foundation layer. Composer, pipeline, and ATP counter all depend on this.

The registry must:
1. Discover and catalog tool functions from federation modules
2. Validate tool signatures before registration
3. Enforce safety classifications (read/write/execute/admin)
4. Be queryable by name, safety class, and capability

## Files

Create `lib/duplo/__init__.py`

```python
"""
Duplo Enzyme System — The Living Cell Architecture
Cherokee AI Federation

Duplos are NOT agents. They are enzymes.
An enzyme catalyzes a specific reaction and is done.
The cell (harness) decides which enzymes to deploy.
The nucleus (governance) regulates which enzymes are active.
"""
```

Create `lib/duplo/registry.py`

```python
"""
Duplo Tool Registry — Amino Acid Catalog
Cherokee AI Federation — The Living Cell Architecture

Every tool function in the federation is an amino acid.
The registry catalogs them with signatures, descriptions,
and safety classifications. Enzymes (Duplos) are assembled
from these building blocks.

Safety classes:
  - read: Query-only, no side effects (thermal search, DB read, health check)
  - write: Creates/modifies data (thermal write, file write, DB insert)
  - execute: Runs code or system commands (Jr executor, bash)
  - admin: Infrastructure changes (service restart, config deploy)

Usage:
    from lib.duplo.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register_tool(
        name="query_thermal",
        description="Search thermal memory by keyword",
        module_path="lib.specialist_council",
        function_name="query_thermal_memory_semantic",
        parameters={
            "question": {"type": "str", "required": True, "description": "Search query"},
            "limit": {"type": "int", "required": False, "description": "Max results"},
            "min_temperature": {"type": "float", "required": False, "description": "Min temp filter"},
        },
        return_type="list",
        safety_class="read",
    )

    # Get a callable tool by name
    tool = registry.get_tool("query_thermal")
    results = tool(question="duplo architecture", limit=5)
"""

import importlib
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("duplo.registry")


class ToolSpec:
    """Specification for a registered tool — immutable after creation."""

    __slots__ = (
        "name", "description", "module_path", "function_name",
        "parameters", "return_type", "safety_class", "requires_auth",
    )

    VALID_SAFETY_CLASSES = ("read", "write", "execute", "admin")

    def __init__(
        self,
        name: str,
        description: str,
        module_path: str,
        function_name: str,
        parameters: Dict[str, Dict],
        return_type: str = "any",
        safety_class: str = "read",
        requires_auth: bool = False,
    ):
        if safety_class not in self.VALID_SAFETY_CLASSES:
            raise ValueError(f"Invalid safety_class '{safety_class}'. Must be one of {self.VALID_SAFETY_CLASSES}")
        self.name = name
        self.description = description
        self.module_path = module_path
        self.function_name = function_name
        self.parameters = parameters
        self.return_type = return_type
        self.safety_class = safety_class
        self.requires_auth = requires_auth

    def to_dict(self) -> dict:
        return {attr: getattr(self, attr) for attr in self.__slots__}


class ToolRegistry:
    """
    Catalog of atomic tool functions available to Duplo enzymes.

    Thread-safe for reads. Registration should happen at startup.
    """

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._resolved: Dict[str, Callable] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        module_path: str,
        function_name: str,
        parameters: Optional[Dict[str, Dict]] = None,
        return_type: str = "any",
        safety_class: str = "read",
        requires_auth: bool = False,
    ) -> None:
        """Register a tool function in the catalog."""
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")
        spec = ToolSpec(
            name=name,
            description=description,
            module_path=module_path,
            function_name=function_name,
            parameters=parameters or {},
            return_type=return_type,
            safety_class=safety_class,
            requires_auth=requires_auth,
        )
        self._tools[name] = spec
        self._resolved.pop(name, None)  # clear cached callable
        logger.info(f"Registered tool: {name} [{safety_class}] from {module_path}.{function_name}")

    def get_spec(self, name: str) -> Optional[ToolSpec]:
        """Return the ToolSpec for a named tool, or None."""
        return self._tools.get(name)

    def get_tool(self, name: str) -> Callable:
        """
        Resolve and return the callable for a named tool.
        Imports the module lazily on first access.
        Raises KeyError if tool not registered, ImportError if module not found.
        """
        if name in self._resolved:
            return self._resolved[name]
        spec = self._tools.get(name)
        if spec is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        module = importlib.import_module(spec.module_path)
        func = getattr(module, spec.function_name)
        self._resolved[name] = func
        return func

    def list_tools(self, safety_class: Optional[str] = None) -> List[Dict]:
        """List all tools, optionally filtered by safety class."""
        tools = self._tools.values()
        if safety_class:
            tools = [t for t in tools if t.safety_class == safety_class]
        return [t.to_dict() for t in tools]

    def get_tool_set(self, names: List[str]) -> Dict[str, Callable]:
        """Resolve a set of tools by name. Returns {name: callable}."""
        result = {}
        for name in names:
            result[name] = self.get_tool(name)
        return result

    def validate_tool(self, name: str) -> bool:
        """
        Validate that a tool can be resolved and its function signature
        matches the declared parameters.
        """
        spec = self._tools.get(name)
        if spec is None:
            return False
        try:
            func = self.get_tool(name)
            sig = inspect.signature(func)
            # Check that all required params exist in the function signature
            func_params = set(sig.parameters.keys())
            for param_name, param_info in spec.parameters.items():
                if param_info.get("required", False) and param_name not in func_params:
                    logger.error(f"Tool '{name}': required param '{param_name}' not in function signature")
                    return False
            return True
        except (ImportError, AttributeError) as e:
            logger.error(f"Tool '{name}' validation failed: {e}")
            return False

    def sync_to_db(self) -> int:
        """
        Persist current registry state to duplo_tool_registry table.
        Returns count of tools synced.
        """
        from lib.ganuda_db import get_connection
        import json

        conn = get_connection()
        try:
            cur = conn.cursor()
            count = 0
            for spec in self._tools.values():
                cur.execute("""
                    INSERT INTO duplo_tool_registry
                    (tool_name, description, module_path, function_name,
                     parameters, return_type, safety_class, requires_auth, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (tool_name) DO UPDATE SET
                        description = EXCLUDED.description,
                        module_path = EXCLUDED.module_path,
                        function_name = EXCLUDED.function_name,
                        parameters = EXCLUDED.parameters,
                        return_type = EXCLUDED.return_type,
                        safety_class = EXCLUDED.safety_class,
                        requires_auth = EXCLUDED.requires_auth,
                        updated_at = NOW()
                """, (
                    spec.name, spec.description, spec.module_path,
                    spec.function_name, json.dumps(spec.parameters),
                    spec.return_type, spec.safety_class, spec.requires_auth,
                ))
                count += 1
            conn.commit()
            logger.info(f"Synced {count} tools to duplo_tool_registry")
            return count
        finally:
            conn.close()


# ============================================================
# Federation Tool Catalog — seed the registry with known tools
# ============================================================

def build_federation_registry() -> ToolRegistry:
    """
    Build and return a ToolRegistry pre-loaded with federation tools.
    Called once at startup by the composer or gateway.
    """
    reg = ToolRegistry()

    # --- READ tools ---
    reg.register_tool(
        name="query_thermal_semantic",
        description="Search thermal memory using semantic RAG pipeline (HyDE + pgvector + rerank)",
        module_path="lib.specialist_council",
        function_name="query_thermal_memory_semantic",
        parameters={
            "question": {"type": "str", "required": True, "description": "Search query"},
            "limit": {"type": "int", "required": False, "description": "Max results (default 5)"},
            "min_temperature": {"type": "float", "required": False, "description": "Min temperature filter"},
        },
        return_type="list",
        safety_class="read",
    )

    reg.register_tool(
        name="execute_db_query",
        description="Execute a read-only SQL query and return results as list of dicts",
        module_path="lib.ganuda_db",
        function_name="execute_query",
        parameters={
            "sql": {"type": "str", "required": True, "description": "SQL query string"},
            "params": {"type": "tuple", "required": False, "description": "Query parameters"},
        },
        return_type="list",
        safety_class="read",
    )

    reg.register_tool(
        name="check_backend_health",
        description="Check if an LLM backend (vLLM/MLX) is responding",
        module_path="lib.specialist_council",
        function_name="check_backend_health",
        parameters={
            "backend": {"type": "dict", "required": True, "description": "Backend config dict with url key"},
        },
        return_type="bool",
        safety_class="read",
    )

    # --- WRITE tools ---
    reg.register_tool(
        name="write_thermal",
        description="Write a memory to the thermal archive with temperature and sacred flag",
        module_path="lib.ganuda_db",
        function_name="safe_thermal_write",
        parameters={
            "content": {"type": "str", "required": True, "description": "Memory content"},
            "temperature": {"type": "float", "required": False, "description": "Temperature score (default 60)"},
            "source": {"type": "str", "required": False, "description": "Source identifier"},
            "sacred": {"type": "bool", "required": False, "description": "Mark as sacred pattern"},
            "metadata": {"type": "dict", "required": False, "description": "Additional metadata"},
        },
        return_type="bool",
        safety_class="write",
    )

    reg.register_tool(
        name="embed_text",
        description="Generate a 1024d embedding vector for text via greenfin embedding service",
        module_path="lib.duplo._builtin_tools",
        function_name="embed_text",
        parameters={
            "text": {"type": "str", "required": True, "description": "Text to embed"},
        },
        return_type="list",
        safety_class="read",
    )

    reg.register_tool(
        name="query_vllm",
        description="Send a prompt to the local vLLM instance and return completion text",
        module_path="lib.specialist_council",
        function_name="query_vllm_sync",
        parameters={
            "system_prompt": {"type": "str", "required": True, "description": "System prompt"},
            "user_message": {"type": "str", "required": True, "description": "User message"},
            "max_tokens": {"type": "int", "required": False, "description": "Max output tokens"},
        },
        return_type="str",
        safety_class="read",
    )

    return reg
```

Create `lib/duplo/_builtin_tools.py`

```python
"""
Built-in tool functions for the Duplo enzyme system.
Functions here are lightweight wrappers that don't belong in
existing modules but are needed by enzymes.
"""

import requests
import logging

logger = logging.getLogger("duplo.tools")

EMBEDDING_URL = "http://192.168.132.224:8003/embed"


def embed_text(text: str) -> list:
    """Generate a 1024d embedding vector via greenfin embedding service."""
    try:
        resp = requests.post(
            EMBEDDING_URL,
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("embedding", [])
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []
```

## Verification

1. From redfin with cherokee_venv active:
   - `python3 -c "from lib.duplo.registry import ToolRegistry; r = ToolRegistry(); print('OK')"` — imports clean
   - `python3 -c "from lib.duplo.registry import build_federation_registry; r = build_federation_registry(); print(len(r.list_tools()), 'tools registered')"` — should show 6 tools
   - `python3 -c "from lib.duplo.registry import build_federation_registry; r = build_federation_registry(); print(r.validate_tool('write_thermal'))"` — should print True

2. After DB migration is run on bluefin:
   - `python3 -c "from lib.duplo.registry import build_federation_registry; r = build_federation_registry(); r.sync_to_db(); print('synced')"` — persists to DB
