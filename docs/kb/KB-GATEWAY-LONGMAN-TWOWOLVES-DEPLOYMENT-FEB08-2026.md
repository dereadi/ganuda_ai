# KB: Gateway Long Man Routing + Two Wolves Audit Trail Deployment

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Category:** Gateway / Council Routing / Audit Trail
**Council Vote:** #8486 (Phase 1: Long Man routing, Phase 2: Two Wolves audit)
**Jr Task:** #659 (GATEWAY-LONGMAN-TWO-WOLVES-001)

## The Problem

The gateway (`/ganuda/services/llm_gateway/gateway.py`) has its own specialist query pipeline that does NOT call `specialist_council.py`'s `vote()` method. This means:

- Long Man routing deployed to specialist_council.py was **not active** for production API calls
- Two Wolves audit trail was **not triggered** by gateway votes
- Gateway routed ALL 7 specialists to Qwen on redfin via hardcoded `VLLM_BACKEND`
- `api_audit_log` had **zero** `council-internal` entries

This duplication was discovered by testing a vote through the gateway API and checking the audit log.

## The Fix

4 SEARCH/REPLACE edits to gateway.py:

| Edit | What | Lines (approx) |
|------|------|----------------|
| 1 | Add `SPECIALIST_ROUTING` map, `DEEPSEEK_MODEL`, `QWEN_MODEL`, `check_council_backend_health()` | After line 227 |
| 2 | Modify `query_vllm_sync()` to accept `backend_url`, `model`, `timeout` params (defaults preserve old behavior) | Line 604 |
| 3 | Add Long Man routing + timing to `query_specialist()` inner function + ThreadPoolExecutor | Line 978-1019 |
| 4 | Build `routing_manifest`, merge into metacognition, add per-specialist `api_audit_log` entries | Line 1046-1062 |

## Key Design Decisions

1. **Modified gateway.py directly** (Option A) rather than refactoring to call specialist_council.py (Option B). The gateway has extra features (memory context, YAML constraints, metacognition) worth keeping.

2. **Used simple string labels** (`"deepseek"`, `"qwen"`) in `routing_map` rather than dict structures like specialist_council.py. Simpler for the gateway's flatter architecture.

3. **Health check runs once** before the ThreadPoolExecutor, not per-specialist. Avoids 2 extra HTTP round-trips per vote.

4. **Consensus synthesis stays on Qwen** — Peace Chief always synthesizes on the fast path regardless of routing.

5. **`query_vllm_sync()` defaults unchanged** — existing callers (consensus, other endpoints) are not affected.

## Performance Impact

| Metric | Before (all Qwen) | After (Long Man) |
|--------|-------------------|-------------------|
| Normal vote total | ~3.5s | ~35s |
| Qwen specialists | ~2.5s each | ~2.5s each (unchanged) |
| DeepSeek specialists | N/A | ~35s each (bmasass M4 Max) |
| Bottleneck | N/A | Raven + Turtle on DeepSeek |

The 10x latency increase for normal votes is expected — DeepSeek-R1 on bmasass runs at ~23 tok/s via MLX. This is the cost of reasoning depth. When DeepSeek is down, all specialists fall back to Qwen and latency returns to ~3.5s.

## Verification Queries

```sql
-- Check routing_manifest for latest vote
SELECT audit_hash, metacognition->'routing_manifest' as manifest
FROM council_votes ORDER BY voted_at DESC LIMIT 1;

-- Check per-specialist audit entries
SELECT endpoint, client_ip, response_time_ms
FROM api_audit_log
WHERE key_id = 'council-internal'
ORDER BY created_at DESC LIMIT 7;

-- Count total council-internal entries
SELECT COUNT(*) FROM api_audit_log WHERE key_id = 'council-internal';
```

## Architectural Note: Gateway vs specialist_council.py

These two files maintain **parallel** specialist query pipelines:

| Feature | specialist_council.py | gateway.py |
|---------|----------------------|------------|
| Memory context | No | Yes |
| YAML constraints | No | Yes |
| Temporal context | No | Yes |
| Metacognitive council | No | Yes |
| Long Man routing | Yes (v1.4) | Yes (now) |
| Two Wolves audit | Yes | Yes (now) |
| Called by gateway API | **No** | **Yes** |

`specialist_council.py` is used by `cascaded_council.py` and direct imports. The gateway API uses its own pipeline. Both now have routing parity.

**Future consideration:** Unify into a single pipeline. But that's a larger refactor — Option B from the original analysis.

## Related

- KB-TWO-WOLVES-DATA-SOVEREIGNTY-COUNCIL-ROUTING-FEB08-2026.md
- KB-JR-INSTRUCTION-FORMAT-REGEX-COMPATIBILITY-FEB08-2026.md
- Council Vote #8486 (Long Man routing + Two Wolves audit)
- Jr instruction: JR-GATEWAY-LONGMAN-TWOWOLVES-FEB08-2026.md
