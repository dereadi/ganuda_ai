# Jr Instruction: Wire Langfuse Traces into Gateway + Jr Executor

**Epic**: LANGFUSE-EPIC (Cognitive Gaps Mar 15 2026)
**Depends On**: Langfuse v2.30.0 running on greenfin (DONE — http://192.168.132.224:3100)
**Estimated SP**: 5
**Target Files**:
- `/ganuda/services/llm_gateway/gateway.py` (redfin)
- `/ganuda/jr_executor/jr_task_executor.py` (redfin)

---

## Objective

Instrument the LLM gateway and Jr task executor with Langfuse traces so we can answer Coyote's three questions:

1. **What does each council vote cost in tokens?**
2. **Which Jr tasks are the most expensive?**
3. **Are we wasting tokens on low-value queries?**

## Langfuse Connection Details

```
Host: http://192.168.132.224:3100
Public Key: pk-lf-1f281f24-e575-4c62-b208-84b71544ad33
Secret Key: sk-lf-ba2b2dea-9392-4c59-b2c5-901d9853bb96
Project: stoneclad
```

## Prerequisites

Install the Langfuse Python SDK on redfin:

```bash
/ganuda/services/llm_gateway/venv/bin/pip install langfuse
/ganuda/jr_executor/venv/bin/pip install langfuse
```

If venvs don't exist, install system-wide: `pip3 install langfuse`

---

## Part 1: Gateway Instrumentation (`gateway.py`)

### Step 1.1: Initialize Langfuse Client

Near the top of `gateway.py` (after existing imports, before SPECIALISTS dict), add:

```python
from langfuse import Langfuse

langfuse = Langfuse(
    host="http://192.168.132.224:3100",
    public_key="pk-lf-1f281f24-e575-4c62-b208-84b71544ad33",
    secret_key="sk-lf-ba2b2dea-9392-4c59-b2c5-901d9853bb96",
)
```

### Step 1.2: Instrument `query_vllm_sync()`

Find the `query_vllm_sync()` function. This is the lowest-level LLM call function in the gateway. Wrap it to emit Langfuse generations.

**Before the existing return statement**, add token extraction and Langfuse logging:

```python
def query_vllm_sync(system_prompt, user_prompt, max_tokens=500, temperature=0.7,
                     trace_id=None, trace_name=None, generation_name=None, metadata=None):
    # ... existing code that calls vLLM and gets response ...

    # After getting response_data (the JSON from vLLM):
    usage = response_data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)

    # Log to Langfuse if trace context provided
    if trace_id:
        try:
            trace = langfuse.trace(id=trace_id, name=trace_name or "gateway_query", metadata=metadata or {})
            trace.generation(
                name=generation_name or "vllm_query",
                model=response_data.get('model', 'qwen2.5-72b'),
                input=[{"role": "system", "content": system_prompt[:500]},
                       {"role": "user", "content": user_prompt[:500]}],
                output=content[:500],  # content = the extracted response text
                usage={"input": prompt_tokens, "output": completion_tokens},
                metadata=metadata or {},
            )
        except Exception as e:
            logger.warning(f"Langfuse trace failed: {e}")

    # ... existing return ...
```

**IMPORTANT**: Do NOT change the function signature for existing callers. Add `trace_id=None, trace_name=None, generation_name=None, metadata=None` as keyword args with defaults so all existing calls continue to work unchanged.

### Step 1.3: Instrument Council Votes

In the council vote endpoint (the function that queries all specialists), this is the highest-value instrumentation point.

**At the start of the council vote handler**, create a Langfuse trace:

```python
import uuid

# At the start of the council vote function:
vote_trace_id = str(uuid.uuid4())
vote_trace = langfuse.trace(
    id=vote_trace_id,
    name="council_vote",
    metadata={
        "vote_hash": audit_hash,  # the existing vote hash
        "query": request.query[:200],
    },
)
```

**When querying each specialist** (in the ThreadPoolExecutor loop), pass the trace context:

```python
# For each specialist query:
specialist_generation = vote_trace.generation(
    name=f"specialist_{specialist_id}",
    model="qwen2.5-72b",
    input=[{"role": "system", "content": spec["system_prompt"][:300]},
           {"role": "user", "content": query[:300]}],
    output=specialist_response[:500],
    usage={"input": prompt_tokens, "output": completion_tokens},
    metadata={"specialist": specialist_id, "concern_flag": spec.get("concern_flag", "")},
)
```

**After the synthesis/consensus step**, add a generation for that too:

```python
synthesis_generation = vote_trace.generation(
    name="synthesis",
    model="qwen2.5-72b",
    input=[{"role": "user", "content": synthesis_prompt[:300]}],
    output=consensus[:500],
    usage={"input": synth_prompt_tokens, "output": synth_completion_tokens},
    metadata={"specialist_count": len(specialists_queried)},
)
```

**After self-refine rounds** (if applicable), log each refinement as a separate generation under the same trace.

### Step 1.4: Instrument Chat Completions

In the `/v1/chat/completions` endpoint, create a trace per request:

```python
chat_trace = langfuse.trace(
    name="chat_completion",
    metadata={
        "model_requested": request.model,
        "client_ip": str(request_obj.client.host),
    },
)

# After getting the response:
chat_trace.generation(
    name="completion",
    model=response_data.get('model', request.model),
    input=request.messages[-1].get('content', '')[:300],
    output=response_content[:500],
    usage={"input": prompt_tokens, "output": completion_tokens},
)
```

### Step 1.5: Flush on Shutdown

Add to the FastAPI shutdown event:

```python
@app.on_event("shutdown")
async def shutdown_langfuse():
    langfuse.flush()
```

---

## Part 2: Jr Executor Instrumentation (`jr_task_executor.py`)

### Step 2.1: Initialize Langfuse Client

Near the top of `jr_task_executor.py` (after existing imports):

```python
from langfuse import Langfuse

langfuse = Langfuse(
    host="http://192.168.132.224:3100",
    public_key="pk-lf-1f281f24-e575-4c62-b208-84b71544ad33",
    secret_key="sk-lf-ba2b2dea-9392-4c59-b2c5-901d9853bb96",
)
```

### Step 2.2: Create Per-Task Trace

In the `execute_task()` method, create a trace at the start and close it at the end:

```python
def execute_task(self, task):
    task_id = task.get('task_id')
    task_type = task.get('task_type', 'unknown')

    # Create Langfuse trace for entire task
    trace = langfuse.trace(
        name=f"jr_task_{task_type}",
        metadata={
            "task_id": task_id,
            "task_type": task_type,
            "agent_id": self.agent_id,
            "node": self.node_name,
            "step_count": self._estimate_step_count(task.get('task_content', '')),
        },
    )
    self._current_trace = trace  # Store for use in _call_llm

    # ... existing execute logic ...

    # At end (success or failure):
    trace.update(metadata={
        "task_id": task_id,
        "success": success,
        "duration_s": round(time.time() - start_time, 2),
    })
    self._current_trace = None
```

### Step 2.3: Instrument `_call_llm()` and `_call_llm_routed()`

In `_call_llm()` (~line 627), after getting the response, extract usage and log:

```python
def _call_llm(self, prompt, max_tokens=1500):
    # ... existing POST to gateway ...
    data = response.json()

    # Extract token usage from response
    usage = data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)

    # Log to Langfuse
    if hasattr(self, '_current_trace') and self._current_trace:
        try:
            self._current_trace.generation(
                name="llm_call",
                model=data.get('model', 'default'),
                input=prompt[:500],
                output=data['choices'][0]['message']['content'][:500],
                usage={"input": prompt_tokens, "output": completion_tokens},
            )
        except Exception:
            pass  # Don't break task execution for telemetry

    return data['choices'][0]['message']['content']
```

Same pattern for `_call_llm_routed()` (~line 649), but include the routing metadata:

```python
    model_used = data.get('routing', {}).get('model_used', 'auto')
    if hasattr(self, '_current_trace') and self._current_trace:
        try:
            self._current_trace.generation(
                name="llm_call_routed",
                model=model_used,
                input=prompt[:500],
                output=content[:500],
                usage={"input": prompt_tokens, "output": completion_tokens},
                metadata={"routing": data.get('routing', {})},
            )
        except Exception:
            pass
```

### Step 2.4: Instrument PreFlect

In `_preflect_critique()` (~line 451), log the PreFlect call:

```python
    if hasattr(self, '_current_trace') and self._current_trace:
        try:
            self._current_trace.generation(
                name="preflect",
                model="qwen2.5-72b-local",
                input=prompt[:500],
                output=llm_text[:500],
                usage={"input": usage.get('prompt_tokens', 0),
                       "output": usage.get('completion_tokens', 0)},
                metadata={"action": action},  # PASS, MODIFY, or FLAG
            )
        except Exception:
            pass
```

---

## Part 3: Verify

After deploying, restart both services:

```bash
sudo systemctl restart llm-gateway
sudo systemctl restart jr-task-executor
```

### Test 1: Council Vote Trace

```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"query": "Should we add Langfuse observability?", "context": "Testing trace instrumentation"}'
```

Then check Langfuse UI at `http://192.168.132.224:3100` — you should see a `council_vote` trace with 7+ specialist generations nested under it.

### Test 2: Jr Task Trace

Queue a simple Jr task and let the executor pick it up. Check Langfuse for a `jr_task_*` trace with generation(s) nested under it.

### Test 3: Coyote's Three Questions

In the Langfuse dashboard:
1. **Cost per council vote**: Filter traces by name=`council_vote`, view total tokens per trace
2. **Most expensive Jr tasks**: Filter by name prefix `jr_task_`, sort by total tokens descending
3. **Waste identification**: Sort all traces by token count descending, look for high-cost low-value patterns

---

## Council Concerns

- **Crawdad**: Langfuse is LAN-only (192.168.132.224:3100, nftables enforced). Prompt/response content truncated to 500 chars in traces — no full PII exposure. Telemetry disabled.
- **Turtle**: If Langfuse is down, all instrumentation is wrapped in try/except — gateway and executor continue to function normally. Zero coupling.
- **Coyote**: Must answer the three questions within 1 week. If it can't, pull the instrumentation.
- **DC-9**: Langfuse SDK is async flush — negligible overhead on hot path. No extra LLM calls.
- **Gecko**: SDK memory footprint is minimal. Traces batch-flush every 15s by default.

## What NOT To Do

- Do NOT log full prompts/responses — truncate to 500 chars max (Crawdad)
- Do NOT make Langfuse a hard dependency — all trace calls MUST be in try/except
- Do NOT instrument the email daemon or arxiv crawler yet — gateway and Jr executor only in this task
- Do NOT change the existing `log_audit()` or `atp_counter` paths — Langfuse is additive
- Do NOT store API keys in code — but for Phase 1, hardcoded is acceptable since Langfuse is LAN-only. Phase 2: move to secrets_loader.py
