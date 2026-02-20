# Jr Instruction: Council Hybrid Backend Routing (Long Man Pattern)

**Task ID:** COUNCIL-HYBRID-ROUTE-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** #8486 (approved, hybrid of options b+c)
**Date:** February 8, 2026

## Objective

Modify `specialist_council.py` so that each specialist can route to a different inference backend based on (1) their nature and (2) whether the vote is high-stakes. This is the "Long Man" pattern — the river flows according to the terrain.

## Current State

- File: `/ganuda/lib/specialist_council.py`
- Line 28: `VLLM_URL = "http://localhost:8000/v1/chat/completions"` (hardcoded, all specialists use this)
- Line 29: `VLLM_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"`
- Function `query_vllm_sync()` at line 35 always uses `VLLM_URL` and `VLLM_MODEL`

## Required Changes

### 1. Add backend configuration constants (after line 29)

```python
# Backend configuration — Long Man pattern (Council Vote #8486)
QWEN_BACKEND = {
    "url": "http://localhost:8000/v1/chat/completions",
    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
    "timeout": 60,
    "description": "Fast path — Qwen2.5-Coder-32B on redfin RTX 6000"
}

DEEPSEEK_BACKEND = {
    "url": "http://192.168.132.21:8800/v1/chat/completions",
    "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    "timeout": 120,
    "description": "Deep path — DeepSeek-R1-32B on bmasass M4 Max"
}

# Specialist → default backend mapping (normal flow)
SPECIALIST_BACKENDS = {
    "raven": DEEPSEEK_BACKEND,      # Strategic Planning — needs depth
    "turtle": DEEPSEEK_BACKEND,     # Seven Generations — needs reflection
    "crawdad": QWEN_BACKEND,        # Security — needs speed and precision
    "gecko": QWEN_BACKEND,          # Technical Integration — needs speed
    "eagle_eye": QWEN_BACKEND,      # Monitoring — speed by default
    "spider": QWEN_BACKEND,         # Cultural Integration — speed by default
    "peace_chief": QWEN_BACKEND,    # Democratic Coordination — speed by default
}
```

### 2. Modify query_vllm_sync() to accept backend parameter

Change the function signature from:
```python
def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
```

To:
```python
def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300, backend: dict = None) -> str:
```

Inside the function, replace the hardcoded `VLLM_URL` and `VLLM_MODEL` references:
```python
    b = backend or QWEN_BACKEND
    try:
        response = requests.post(
            b["url"],
            json={
                "model": b["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=b["timeout"]
        )
```

### 3. Modify the vote methods to pass backend per specialist

In the `vote()` method (and `vote_with_trails()`, `vote_first()`), where specialists are queried — find where `query_vllm_sync` is called for each specialist and pass the appropriate backend:

```python
# Determine backend for this specialist
if high_stakes:
    backend = DEEPSEEK_BACKEND  # High-stakes: all go deep
else:
    backend = SPECIALIST_BACKENDS.get(specialist_name, QWEN_BACKEND)

response = query_vllm_sync(system_prompt, user_message, max_tokens, backend=backend)
```

### 4. Add logging for backend selection

When each specialist is queried, log which backend was selected:
```python
print(f"[COUNCIL] {specialist_name} → {backend['description']} (high_stakes={high_stakes})")
```

### 5. Update INFRASTRUCTURE_CONTEXT

Replace the stale infrastructure context (around line 68) to include bmasass:
```
| bmasass | 192.168.132.21 | Mac Hybrid | MLX DeepSeek-R1-32B (8800) |
```

Update the vLLM line to reflect current model:
```
- vLLM: Qwen2.5-Coder-32B-AWQ on 96GB Blackwell RTX PRO 6000 (~65 tok/sec)
```

Update gateway version reference to v1.6.0.

### 6. Update max_tokens for DeepSeek-R1 specialists

DeepSeek-R1 uses chain-of-thought reasoning that consumes tokens before the visible answer. When a specialist uses DEEPSEEK_BACKEND, increase max_tokens:
```python
if backend == DEEPSEEK_BACKEND:
    max_tokens = max(max_tokens, 500)  # Reasoning chain needs room
```

## 7. Two Wolves Audit Trail (MANDATORY — Security + Privacy)

The Two Wolves must be fed equally. Every council vote that crosses the network to bmasass must be fully auditable, and data sovereignty must be maintained. This is not optional.

### 7a. Add `backend_routing` to council_votes responses

When building the `responses` jsonb that gets stored in `council_votes`, include the backend each specialist used. Currently the `responses` column stores specialist text. Wrap each entry to include routing metadata:

```python
# When storing specialist responses in council_votes
specialist_result = {
    "response": response_text,
    "backend": backend["description"],
    "backend_url": backend["url"],
    "backend_model": backend["model"],
    "response_time_ms": elapsed_ms,
    "high_stakes": high_stakes,
    "data_crossed_wire": backend != QWEN_BACKEND  # True if data left redfin
}
```

### 7b. Add `routing_manifest` to council_votes

Before the INSERT into `council_votes`, build a routing manifest that summarizes the data flow for the entire vote:

```python
routing_manifest = {
    "vote_type": "high_stakes" if high_stakes else "normal",
    "backends_used": list(set(b["description"] for b in backends_selected)),
    "specialists_on_redfin": [s for s, b in routing.items() if b == QWEN_BACKEND],
    "specialists_on_bmasass": [s for s, b in routing.items() if b == DEEPSEEK_BACKEND],
    "data_sovereignty": {
        "question_left_redfin": any(b != QWEN_BACKEND for b in backends_selected),
        "destination_nodes": list(set(b["url"].split("//")[1].split(":")[0] for b in backends_selected)),
        "timestamp": datetime.now().isoformat()
    }
}
```

Store this in the `metacognition` jsonb field alongside existing metacognition data:
```python
metacognition["routing_manifest"] = routing_manifest
```

### 7c. Log to api_audit_log with backend info

After each specialist query completes, log an audit entry so we have a per-specialist, per-backend record:

```python
log_audit(
    key_id="council-internal",
    endpoint=f"/council/specialist/{specialist_name}",
    method="POST",
    status_code=200,
    response_time_ms=elapsed_ms,
    tokens_used=0,
    client_ip=backend["url"]  # Use backend URL as "client" to track data flow
)
```

### 7d. Health check both wolves before voting

Before a vote begins, health-check both backends. If the deep backend (bmasass) is unreachable, fall back ALL specialists to Qwen but log the fallback prominently:

```python
def check_backend_health(backend):
    try:
        r = requests.get(backend["url"].replace("/v1/chat/completions", "/health"), timeout=5)
        return r.status_code == 200
    except:
        return False

# Before vote
deepseek_healthy = check_backend_health(DEEPSEEK_BACKEND)
if not deepseek_healthy:
    print("[COUNCIL] [TWO WOLVES WARNING] Deep backend unreachable — all specialists falling back to fast path")
    # Override all backends to Qwen for this vote
    # Log the fallback in routing_manifest
```

### 7e. Never log credentials or PII in routing metadata

The routing manifest must NEVER include:
- Database passwords or API keys
- User PII from the question (the question itself is already in `council_votes.question`)
- Internal network topology beyond what is already in INFRASTRUCTURE_CONTEXT

## Testing

After making changes:
```bash
# Test normal vote (should show Raven→DeepSeek, Gecko→Qwen)
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Test: Should we add a new monitoring endpoint?", "max_tokens": 150}'

# Test high-stakes vote (should show ALL specialists→DeepSeek)
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Test: Should we delete thermal memory archive?", "max_tokens": 150, "high_stakes": true}'
```

Verify in logs:
- Normal vote: Raven and Turtle show `Deep path`, others show `Fast path`
- High-stakes vote: All 7 show `Deep path`
- No errors or timeouts from bmasass:8800

## Do NOT

- Do not remove the existing `VLLM_URL` / `VLLM_MODEL` constants (other code may reference them)
- Do not change the council vote API contract or response format
- Do not modify gateway.py — this is specialist_council.py only
- Do not hardcode any database passwords

## Success Criteria

1. Normal council votes complete with mixed backends, Raven and Turtle using DeepSeek-R1
2. High-stakes council votes route all specialists to DeepSeek-R1
3. Backend selection logged per specialist per vote
4. No regression in vote response format
5. Both backends health-checked before vote begins (fall back to Qwen if DeepSeek unreachable)
6. **Two Wolves**: Every council vote stores a `routing_manifest` in metacognition showing exactly which data crossed the wire to which node
7. **Two Wolves**: api_audit_log contains per-specialist backend entries for full forensic reconstruction
8. **Two Wolves**: Fallback events logged prominently when deep backend is unreachable
9. **Two Wolves**: No credentials or PII leak into routing metadata
