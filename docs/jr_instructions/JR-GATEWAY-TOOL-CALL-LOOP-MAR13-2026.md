# JR INSTRUCTION: Gateway Tool-Call Loop — The Nervous System

**Task**: Add iterative tool-calling to the gateway so the LLM can call ToolSets against federation data, get results, and continue reasoning. When someone asks "what tasks are overdue?" the LLM calls `kanban_overdue`, gets the data, and answers grounded in real results. This is Phase 3 of the ToolSet EPIC.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: #798ad0b799bad552 (ToolSet pattern, APPROVED)
**Depends On**: ToolSets (DONE), chat sessions schema (DONE), gateway.py

## Context

Right now the gateway's `/v1/chat/completions` is a dumb proxy to vLLM — it passes the user's message, gets a response, returns it. The LLM can't reach into our data. With the tool-call loop, the LLM sees available tools (thermal_search, kanban_stats, summarize_topic, etc.), decides which to call, gets results back, and formulates a grounded answer.

This is the MyBrain `sendMessage` pattern: prompt → tool calls → execute → feed back → repeat until text response. Safety cap at MAX_CONSECUTIVE_TOOL_CALLS = 5.

## Step 1: Create Tool-Call Executor

Create `/ganuda/lib/tool_executor.py`:

```python
"""Tool-call executor for gateway LLM requests.

Manages the loop: LLM response → extract tool calls → execute via ToolSets →
feed results back → repeat until LLM gives text or MAX_CALLS hit.

Council vote #798ad0b7. MAX_CONSECUTIVE_TOOL_CALLS = 5.
"""

import json
import httpx
import time
from toolsets.base import MAX_CONSECUTIVE_TOOL_CALLS
from toolsets.thermal_toolset import ThermalToolSet
from toolsets.kanban_toolset import KanbanToolSet

# Registry of available ToolSets
TOOLSETS = {
    "thermal": ThermalToolSet(),
    "kanban": KanbanToolSet(),
}

# Build combined tool list for LLM
ALL_TOOLS = []
TOOL_MAP = {}  # function_name → (toolset, method_name)
for domain, ts in TOOLSETS.items():
    for desc in ts.get_tools():
        # Only expose read tools to auto-dispatch; write requires council gate
        if desc.safety_class == "read":
            full_name = f"{domain}_{desc.name}"
            ALL_TOOLS.append({
                "type": "function",
                "function": {
                    "name": full_name,
                    "description": desc.description,
                    "parameters": desc.parameters,
                },
            })
            TOOL_MAP[full_name] = (ts, desc.name)


async def execute_with_tools(messages: list, backend_url: str, backend_model: str,
                             max_tokens: int = 500, temperature: float = 0.7) -> dict:
    """Execute a chat request with tool-calling loop.

    Returns: {"content": str, "tool_calls": list, "iterations": int}
    """
    current_messages = list(messages)
    iterations = 0
    all_tool_calls = []

    async with httpx.AsyncClient() as client:
        while iterations < MAX_CONSECUTIVE_TOOL_CALLS:
            # Send to LLM with tools
            resp = await client.post(
                f"{backend_url}/v1/chat/completions",
                json={
                    "model": backend_model,
                    "messages": current_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "tools": ALL_TOOLS if iterations == 0 or ALL_TOOLS else None,
                    "tool_choice": "auto",
                },
                timeout=120.0,
            )

            if resp.status_code != 200:
                return {"content": f"Backend error: {resp.status_code}", "tool_calls": [], "iterations": iterations}

            result = resp.json()
            choice = result["choices"][0]
            message = choice["message"]

            # Check for tool calls
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # LLM gave a text response — we're done
                return {
                    "content": message.get("content", ""),
                    "tool_calls": all_tool_calls,
                    "iterations": iterations,
                    "usage": result.get("usage", {}),
                }

            # Execute each tool call
            iterations += 1
            current_messages.append(message)  # Add assistant's tool-call message

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                if func_name in TOOL_MAP:
                    toolset, method_name = TOOL_MAP[func_name]
                    tool_result = toolset.execute(method_name, args)
                    result_content = json.dumps(tool_result.data) if tool_result.success else json.dumps({"error": tool_result.error})
                    all_tool_calls.append({
                        "name": func_name,
                        "args": args,
                        "success": tool_result.success,
                        "latency_ms": tool_result.latency_ms,
                    })
                else:
                    result_content = json.dumps({"error": f"Unknown tool: {func_name}"})

                # Feed tool result back to LLM
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_content,
                })

    # Hit MAX_CONSECUTIVE_TOOL_CALLS
    return {
        "content": "[Tool call limit reached. Partial results above.]",
        "tool_calls": all_tool_calls,
        "iterations": iterations,
    }
```

## Step 2: Wire into Gateway chat_completions

Modify `/ganuda/services/llm_gateway/gateway.py` — add tool-calling mode:

```python
# At top of gateway.py, after sys.path setup:
from tool_executor import execute_with_tools, ALL_TOOLS

# In chat_completions endpoint, after building backend_url/model:
# Check if tools should be enabled (opt-in via parameter or auto-detect)
use_tools = getattr(request, 'tools', None) is not None or should_use_tools(request.messages)

if use_tools:
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    result = await execute_with_tools(
        messages=messages,
        backend_url=backend_url,
        backend_model=backend_model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    # Format as OpenAI-compatible response
    return {
        "id": f"chatcmpl-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": backend_model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": result["content"]},
            "finish_reason": "stop",
        }],
        "usage": result.get("usage", {}),
        "tool_calls_made": result["tool_calls"],
        "tool_iterations": result["iterations"],
    }


def should_use_tools(messages: list) -> bool:
    """Auto-detect if the request would benefit from tool calling."""
    if not messages:
        return False
    last_msg = messages[-1].content.lower()
    triggers = [
        "what tasks", "overdue", "how many", "search thermal",
        "what do we know", "summarize", "find thermal", "task stats",
        "completion rate", "sacred", "kanban", "status of",
    ]
    return any(t in last_msg for t in triggers)
```

## Step 3: Add tools Parameter to ChatRequest

```python
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 500
    temperature: float = 0.7
    model: Optional[str] = None
    session_id: Optional[str] = None
    tools: Optional[bool] = None  # Explicit tool-calling toggle
```

## Step 4: Test from BigMac

```bash
# Should auto-detect and use kanban tools
ask.sh "What tasks are overdue?"

# Should auto-detect and use thermal search + summarize
ask.sh "What do we know about DC-10?"

# Explicit tool mode
curl -s http://100.116.27.89:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"messages": [{"role": "user", "content": "How many sacred thermals do we have?"}], "tools": true}'
```

## DO NOT

- Allow write-class tools in auto-dispatch — only read tools (council condition)
- Set MAX_CONSECUTIVE_TOOL_CALLS above 5 without council re-vote
- Skip sag_events logging — ToolSet.execute() handles this automatically
- Make tool-calling the default for ALL requests — use auto-detect or explicit opt-in
- Call tools in the council vote endpoint yet — that's a separate integration

## Acceptance Criteria

- tool_executor.py deployed with ThermalToolSet + KanbanToolSet wired
- Gateway auto-detects data questions and routes through tool-call loop
- "What tasks are overdue?" returns real data from jr_work_queue
- "What do we know about BigMac?" returns summarize_topic synthesis
- tool_calls_made in response shows which tools were invoked
- MAX_CONSECUTIVE_TOOL_CALLS = 5 enforced
- No regression on non-tool requests (standard chat still works)
