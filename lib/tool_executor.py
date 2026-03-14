"""Tool-call executor for gateway LLM requests.

Manages the loop: LLM response → extract tool calls → execute via ToolSets →
feed results back → repeat until LLM gives text or MAX_CALLS hit.

Council vote #798ad0b7. MAX_CONSECUTIVE_TOOL_CALLS = 5.
"""

import json
import httpx
import time
import logging
from toolsets.base import MAX_CONSECUTIVE_TOOL_CALLS
from toolsets.thermal_toolset import ThermalToolSet
from toolsets.kanban_toolset import KanbanToolSet

logger = logging.getLogger("tool_executor")

# Registry of available ToolSets
TOOLSETS = {
    "thermal": ThermalToolSet(),
    "kanban": KanbanToolSet(),
}

# Build combined tool list for LLM (read-only tools for auto-dispatch)
ALL_TOOLS = []
TOOL_MAP = {}  # function_name → (toolset, method_name)
for _domain, _ts in TOOLSETS.items():
    for _desc in _ts.get_tools():
        if _desc.safety_class == "read":
            _full_name = f"{_domain}_{_desc.name}"
            ALL_TOOLS.append({
                "type": "function",
                "function": {
                    "name": _full_name,
                    "description": _desc.description,
                    "parameters": _desc.parameters,
                },
            })
            TOOL_MAP[_full_name] = (_ts, _desc.name)

logger.info(f"[TOOL_EXECUTOR] Loaded {len(ALL_TOOLS)} read tools from {len(TOOLSETS)} ToolSets")


# Auto-detect triggers for tool routing
TOOL_TRIGGERS = [
    "what tasks", "overdue", "how many tasks", "search thermal",
    "what do we know", "summarize", "find thermal", "task stats",
    "completion rate", "sacred", "kanban", "status of", "thermal stats",
    "how many thermals", "pending tasks", "jr tasks", "work queue",
    "tell me about", "what is", "knowledge on", "search for",
]


def should_use_tools(messages: list) -> bool:
    """Auto-detect if the request would benefit from tool calling."""
    if not messages:
        return False
    last_msg = messages[-1].get("content", "").lower() if isinstance(messages[-1], dict) else ""
    return any(t in last_msg for t in TOOL_TRIGGERS)


async def execute_with_tools(messages: list, backend_url: str, backend_model: str,
                             max_tokens: int = 500, temperature: float = 0.7) -> dict:
    """Execute a chat request with tool-calling loop.

    Returns: {"content": str, "tool_calls_made": list, "iterations": int, "usage": dict}
    """
    current_messages = list(messages)
    iterations = 0
    all_tool_calls = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async with httpx.AsyncClient() as client:
        while iterations < MAX_CONSECUTIVE_TOOL_CALLS:
            # Build request — include tools on every iteration
            request_payload = {
                "model": backend_model,
                "messages": current_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tools": ALL_TOOLS,
                "tool_choice": "auto",
            }

            start = time.time()
            try:
                resp = await client.post(
                    f"{backend_url}/v1/chat/completions",
                    json=request_payload,
                    timeout=120.0,
                )
            except httpx.TimeoutException:
                return {
                    "content": "[Tool-call loop: backend timeout]",
                    "tool_calls_made": all_tool_calls,
                    "iterations": iterations,
                    "usage": total_usage,
                }

            if resp.status_code != 200:
                error_detail = resp.text[:200] if resp.text else str(resp.status_code)
                return {
                    "content": f"[Backend error: {error_detail}]",
                    "tool_calls_made": all_tool_calls,
                    "iterations": iterations,
                    "usage": total_usage,
                }

            result = resp.json()
            latency_ms = int((time.time() - start) * 1000)

            # Accumulate usage
            usage = result.get("usage", {})
            for k in total_usage:
                total_usage[k] += usage.get(k, 0)

            choice = result["choices"][0]
            message = choice["message"]

            # Check for tool calls
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # LLM gave a text response — done
                logger.info(f"[TOOL_EXECUTOR] Completed after {iterations} tool iterations, {len(all_tool_calls)} calls")
                return {
                    "content": message.get("content", ""),
                    "tool_calls_made": all_tool_calls,
                    "iterations": iterations,
                    "usage": total_usage,
                }

            # Execute each tool call
            iterations += 1
            current_messages.append(message)  # Add assistant's tool-call message

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                except (json.JSONDecodeError, TypeError):
                    args = {}

                tc_start = time.time()
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
                    logger.info(f"[TOOL_EXECUTOR] {func_name}({list(args.keys())}) → {'OK' if tool_result.success else 'FAIL'} ({tool_result.latency_ms}ms)")
                else:
                    result_content = json.dumps({"error": f"Unknown tool: {func_name}"})
                    all_tool_calls.append({
                        "name": func_name,
                        "args": args,
                        "success": False,
                        "latency_ms": int((time.time() - tc_start) * 1000),
                    })

                # Feed tool result back to LLM
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_content,
                })

    # Hit MAX_CONSECUTIVE_TOOL_CALLS
    logger.warning(f"[TOOL_EXECUTOR] Hit max iterations ({MAX_CONSECUTIVE_TOOL_CALLS})")
    return {
        "content": "[Tool call limit reached. Partial results above.]",
        "tool_calls_made": all_tool_calls,
        "iterations": iterations,
        "usage": total_usage,
    }
