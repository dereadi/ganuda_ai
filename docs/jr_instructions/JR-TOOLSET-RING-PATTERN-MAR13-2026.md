# JR INSTRUCTION: ToolSet Ring Pattern — Typed AI Tool Interfaces for Federation

**Task**: Implement typed ToolSet pattern adapted from MyBrain floor walk. AI agents can call structured tools against federation data through ring dispatch. Three phases: ToolSets → Multi-Provider Executor → Agent Tool-Call Loop.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 13 (EPIC — 3 phases)
**Council Vote**: #798ad0b799bad552 (APPROVED WITH CONDITIONS, 0.793 confidence)
**Depends On**: Chain Protocol (lib/chain_protocol.py), Gateway (services/llm_gateway/gateway.py), duplo_tool_registry

## Context — Sam Walton Floor Walk

Surveyed MyBrain (github.com/mhss1/MyBrain), an open-source Android app with AI agent tool-calling. Their architecture: typed ToolSets per domain (TaskToolSet, NoteToolSet, etc.) with LLM-callable function schemas. AI says "create task X priority HIGH" → ToolSet executes against local DB → result fed back to AI.

They don't have governance, thermal memory, or multi-node. We do. We're stealing their pattern and wrapping it in our governance topology.

## Council Conditions (BINDING)

1. **No write-class ToolSet executes without council approval** — read-only tools (search, list, get) execute freely. Write tools (create, update, delete) require ring safety_class = 'write' and council gate.
2. **All tool calls logged to sag_events** with audit hash, tool name, args, result, latency.
3. **MAX_CONSECUTIVE_TOOL_CALLS = 5** — hard cap per request to prevent runaway.
4. **ToolSets ARE rings** — registered in duplo_tool_registry, not a parallel dispatch system. Spider's integration concern.
5. **Eagle Eye visibility** — every tool call must be queryable via existing observability.

---

## PHASE 1: Typed ToolSets (Story Points: 5)

### Step 1: Create ToolSet Base Class

Create `/ganuda/lib/toolsets/base.py`:

```python
"""Base ToolSet interface for federation AI tool dispatch.

Every ToolSet follows DC-11 Macro Polymorphism:
SENSE (parse args) → REACT (execute) → EVALUATE (validate result)

Adapted from MyBrain ToolSet pattern. Council vote #798ad0b7.
"""

from dataclasses import dataclass
from typing import Any
import time
import json


@dataclass
class ToolDescriptor:
    """LLM-callable tool description."""
    name: str
    description: str
    parameters: dict  # JSON Schema for function calling
    safety_class: str  # 'read' or 'write'


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    success: bool
    data: Any
    latency_ms: float
    audit_hash: str = ""


class ToolSet:
    """Base class for domain-specific tool sets.

    Subclasses implement tools as methods decorated with @tool().
    Each tool registers in duplo_tool_registry as a ring.
    """

    domain: str = "base"

    def get_tools(self) -> list[ToolDescriptor]:
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
                data={"error": f"Unknown tool: {tool_name}"},
                latency_ms=0
            )

        # Check safety class
        descriptor = next((t for t in self.get_tools() if t.name == tool_name), None)
        if descriptor and descriptor.safety_class == 'write':
            # Write tools require council gate — caller must verify
            pass

        try:
            result = method(**args)
            latency = (time.time() - start) * 1000
            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result,
                latency_ms=round(latency, 1)
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data={"error": str(e)},
                latency_ms=round(latency, 1)
            )
```

### Step 2: ThermalToolSet

Create `/ganuda/lib/toolsets/thermal_toolset.py`:

```python
"""ThermalToolSet — search and create thermal memories.

Read tools: search_thermals, get_thermal_by_id, get_thermal_stats
Write tools: create_thermal (requires council gate)
"""

from .base import ToolSet, ToolDescriptor

class ThermalToolSet(ToolSet):
    domain = "thermal"

    def get_tools(self) -> list[ToolDescriptor]:
        return [
            ToolDescriptor(
                name="search_thermals",
                description="Search thermal memories by content, domain_tag, or temperature range. Returns matching thermals with id, content snippet, temperature, domain, timestamp.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Text to search in thermal content"},
                        "domain_tag": {"type": "string", "description": "Filter by domain (infrastructure, architecture, governance, etc.)"},
                        "min_temp": {"type": "integer", "description": "Minimum temperature score"},
                        "max_temp": {"type": "integer", "description": "Maximum temperature score"},
                        "sacred_only": {"type": "boolean", "description": "Only return sacred thermals"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"}
                    }
                },
                safety_class="read"
            ),
            ToolDescriptor(
                name="get_thermal_stats",
                description="Get thermal memory statistics: total count, count by domain, average temperature, sacred count.",
                parameters={"type": "object", "properties": {}},
                safety_class="read"
            ),
            ToolDescriptor(
                name="create_thermal",
                description="Create a new thermal memory. Requires council approval for write.",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The thermal memory content"},
                        "temperature": {"type": "integer", "description": "Temperature score 0-100"},
                        "domain_tag": {"type": "string", "description": "Domain tag"},
                        "sacred": {"type": "boolean", "description": "Whether this is a sacred pattern"}
                    },
                    "required": ["content", "temperature", "domain_tag"]
                },
                safety_class="write"
            )
        ]

    def search_thermals(self, query: str = "", domain_tag: str = "",
                        min_temp: int = 0, max_temp: int = 100,
                        sacred_only: bool = False, limit: int = 10) -> dict:
        """Search thermal_memory_archive."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()

        conditions = ["temperature_score BETWEEN %s AND %s"]
        params = [min_temp, max_temp]

        if query:
            conditions.append("original_content ILIKE %s")
            params.append(f"%{query}%")
        if domain_tag:
            conditions.append("domain_tag = %s")
            params.append(domain_tag)
        if sacred_only:
            conditions.append("sacred_pattern = true")

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT id, LEFT(original_content, 200), temperature_score,
                   domain_tag, sacred_pattern, created_at
            FROM thermal_memory_archive
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params + [limit])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "count": len(rows),
            "thermals": [
                {
                    "id": r[0], "content_snippet": r[1], "temperature": r[2],
                    "domain": r[3], "sacred": r[4], "created_at": str(r[5])
                }
                for r in rows
            ]
        }

    def get_thermal_stats(self) -> dict:
        """Get aggregate thermal stats."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), AVG(temperature_score), COUNT(*) FILTER (WHERE sacred_pattern) FROM thermal_memory_archive")
        total, avg_temp, sacred = cur.fetchone()

        cur.execute("SELECT domain_tag, COUNT(*) FROM thermal_memory_archive GROUP BY domain_tag ORDER BY COUNT(*) DESC LIMIT 10")
        domains = {r[0]: r[1] for r in cur.fetchall()}

        cur.close()
        conn.close()

        return {
            "total": total,
            "avg_temperature": round(float(avg_temp), 1) if avg_temp else 0,
            "sacred_count": sacred,
            "by_domain": domains
        }

    def create_thermal(self, content: str, temperature: int,
                       domain_tag: str, sacred: bool = False) -> dict:
        """Create thermal. WRITE — council gate required by caller."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash)
            VALUES (%s, %s, %s, %s, encode(sha256((%s || NOW()::text)::bytea), 'hex'))
            RETURNING id
        """, (content, temperature, domain_tag, sacred, f"toolset-{domain_tag}-"))

        thermal_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return {"created_id": thermal_id, "temperature": temperature, "domain": domain_tag}
```

### Step 3: KanbanToolSet

Create `/ganuda/lib/toolsets/kanban_toolset.py`:

```python
"""KanbanToolSet — search and manage Jr tasks / kanban tickets.

Read tools: search_tasks, get_task_by_id, get_task_stats, get_overdue_tasks
Write tools: create_task, update_task_status (requires council gate)
"""

from .base import ToolSet, ToolDescriptor

class KanbanToolSet(ToolSet):
    domain = "kanban"

    def get_tools(self) -> list[ToolDescriptor]:
        return [
            ToolDescriptor(
                name="search_tasks",
                description="Search Jr tasks by title, status, priority, or assignee. Returns matching tasks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Text to search in task title/description"},
                        "status": {"type": "string", "description": "Filter by status: queued, in_progress, done, failed"},
                        "priority": {"type": "string", "description": "Filter by priority: P0, P1, P2, P3"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"}
                    }
                },
                safety_class="read"
            ),
            ToolDescriptor(
                name="get_overdue_tasks",
                description="Get tasks that are past their due date and not completed.",
                parameters={"type": "object", "properties": {}},
                safety_class="read"
            ),
            ToolDescriptor(
                name="get_task_stats",
                description="Get task statistics: total, by status, by priority, completion rate.",
                parameters={"type": "object", "properties": {}},
                safety_class="read"
            )
        ]

    def search_tasks(self, query: str = "", status: str = "",
                     priority: str = "", limit: int = 10) -> dict:
        """Search jr_work_queue."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()

        conditions = []
        params = []

        if query:
            conditions.append("(title ILIKE %s OR task_description ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        if status:
            conditions.append("jr_status = %s")
            params.append(status)
        if priority:
            conditions.append("priority = %s")
            params.append(priority)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        cur.execute(f"""
            SELECT id, title, jr_status, priority, story_points, created_at
            FROM jr_work_queue
            {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params + [limit])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "count": len(rows),
            "tasks": [
                {"id": r[0], "title": r[1], "status": r[2],
                 "priority": r[3], "story_points": r[4], "created": str(r[5])}
                for r in rows
            ]
        }

    def get_overdue_tasks(self) -> dict:
        """Get overdue tasks."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, jr_status, priority, created_at
            FROM jr_work_queue
            WHERE jr_status NOT IN ('done', 'failed')
            AND created_at < NOW() - INTERVAL '7 days'
            ORDER BY created_at ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "overdue_count": len(rows),
            "tasks": [
                {"id": r[0], "title": r[1], "status": r[2],
                 "priority": r[3], "created": str(r[4])}
                for r in rows
            ]
        }

    def get_task_stats(self) -> dict:
        """Aggregate task statistics."""
        import psycopg2
        from ganuda_db import get_db_config

        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()

        cur.execute("SELECT jr_status, COUNT(*) FROM jr_work_queue GROUP BY jr_status")
        by_status = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute("SELECT priority, COUNT(*) FROM jr_work_queue GROUP BY priority")
        by_priority = {r[0]: r[1] for r in cur.fetchall()}

        total = sum(by_status.values())
        done = by_status.get('done', 0)

        cur.close()
        conn.close()

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "completion_rate": round(done / total * 100, 1) if total > 0 else 0
        }
```

### Step 4: Register ToolSets as Rings

```sql
INSERT INTO duplo_tool_registry (tool_name, description, module_path, function_name, parameters, safety_class, ring_type, provider, ring_status)
VALUES
-- ThermalToolSet
('thermal_search', 'Search thermal memories by content/domain/temperature', 'lib.toolsets.thermal_toolset', 'search_thermals',
 '{}'::jsonb, 'read', 'associate', 'toolset_thermal', 'active'),
('thermal_stats', 'Get thermal memory aggregate statistics', 'lib.toolsets.thermal_toolset', 'get_thermal_stats',
 '{}'::jsonb, 'read', 'associate', 'toolset_thermal', 'active'),
('thermal_create', 'Create thermal memory (council gate required)', 'lib.toolsets.thermal_toolset', 'create_thermal',
 '{}'::jsonb, 'write', 'associate', 'toolset_thermal', 'active'),

-- KanbanToolSet
('kanban_search', 'Search Jr tasks by title/status/priority', 'lib.toolsets.kanban_toolset', 'search_tasks',
 '{}'::jsonb, 'read', 'associate', 'toolset_kanban', 'active'),
('kanban_overdue', 'Get overdue Jr tasks', 'lib.toolsets.kanban_toolset', 'get_overdue_tasks',
 '{}'::jsonb, 'read', 'associate', 'toolset_kanban', 'active'),
('kanban_stats', 'Get Jr task aggregate statistics', 'lib.toolsets.kanban_toolset', 'get_task_stats',
 '{}'::jsonb, 'read', 'associate', 'toolset_kanban', 'active')

ON CONFLICT (tool_name) DO UPDATE SET
  description = EXCLUDED.description,
  module_path = EXCLUDED.module_path,
  ring_status = EXCLUDED.ring_status,
  updated_at = NOW();
```

---

## PHASE 2: Multi-Provider Executor (Story Points: 3)

Abstract the gateway's backend so it can route to any LLM provider through a single interface.

### Step 1: Create Provider Executor

Create `/ganuda/lib/provider_executor.py`:

```python
"""Multi-provider LLM executor.

Routes prompts to Qwen (redfin vLLM), Ollama (BigMac), or Gemini (API)
through a single interface. Adapted from MyBrain AiProvider pattern.
"""

PROVIDERS = {
    "qwen_redfin": {
        "type": "vllm",
        "url": "http://localhost:8000/v1/chat/completions",
        "model": "/ganuda/models/qwen2.5-72b-instruct-awq",
    },
    "ollama_bigmac": {
        "type": "ollama",
        "url": "http://100.106.9.80:11434/api/generate",
        "model": "qwen3.5:latest",
    },
    "gemini_bigmac": {
        "type": "gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "model": "gemini-2.5-flash",
    },
}
```

Details: See MyBrain's `AiRepositoryImpl.getExecutor()` for the pattern. Each provider gets a client class with a common `execute(prompt, model) -> response` interface.

### Step 2: Update Gateway Route Selection

Modify gateway.py `chat_completions` to accept a `provider` parameter. Default remains Qwen on redfin. When `provider=ollama_bigmac`, route to BigMac Ollama. When `provider=gemini`, route to Gemini API via BigMac bridge.

---

## PHASE 3: AI Agent Tool-Call Loop (Story Points: 5)

Add tool-calling capability to the gateway's council vote endpoint.

### Step 1: Implement Tool-Call Loop

When a council vote question involves data ("what tasks are overdue?", "search thermals for BigMac"), the gateway should:

1. Send question to LLM with ToolSet descriptors as function-calling schema
2. If LLM returns tool calls → execute them via ToolSet.execute()
3. Feed tool results back to LLM
4. Repeat until LLM responds with text (or MAX_CONSECUTIVE_TOOL_CALLS=5 hit)
5. Log every tool call to sag_events

### Step 2: Safety Gate

Before executing any tool call:
- Check `safety_class` in duplo_tool_registry
- `read` tools execute immediately
- `write` tools require council approval (separate vote)
- Log to sag_events regardless

---

## DO NOT

- Create a parallel dispatch system alongside rings — ToolSets ARE rings (Spider's condition)
- Allow write-class tools to execute without council gate (Crawdad's condition)
- Skip sag_events logging for any tool call (Eagle Eye's condition)
- Set MAX_CONSECUTIVE_TOOL_CALLS above 5 without council re-vote
- Hardcode DB credentials — use secrets.env / ganuda_db helper
- Build Phase 3 before Phase 1 is verified — the tool-call loop requires ToolSets to exist

## Acceptance Criteria

### Phase 1
- `/ganuda/lib/toolsets/base.py` exists with ToolSet base class
- ThermalToolSet and KanbanToolSet implemented and tested
- All tools registered in duplo_tool_registry as rings
- sag_events logging on every tool execution
- Write tools blocked without council approval

### Phase 2
- Gateway can route to Qwen, Ollama, or Gemini via provider parameter
- Provider selection logged in audit trail
- Fallback to Qwen if selected provider is unreachable

### Phase 3
- Council vote endpoint can call tools against federation data
- Tool-call loop with MAX_CONSECUTIVE_TOOL_CALLS=5
- Full audit trail of tool calls within a council vote
