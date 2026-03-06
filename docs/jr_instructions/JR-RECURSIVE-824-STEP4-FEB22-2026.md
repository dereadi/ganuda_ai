# [RECURSIVE] RL2F Phase 0: Self-Refine Loop on Gateway - Step 4

**Parent Task**: #824
**Auto-decomposed**: 2026-02-22T09:25:04.750115
**Original Step Title**: Add refinement metadata to the response

---

### Step 4: Add refinement metadata to the response

File: `/ganuda/services/llm_gateway/gateway.py`

In the return dict at the end of the council vote endpoint, add refinement info:

```python
<<<<<<< SEARCH
            "metacognition": meta_result
=======
            "metacognition": meta_result,
            "refinement": {
                "rounds": refine_result.get("rounds", 0),
                "applied": refine_result.get("rounds", 0) > 0,
                "should_ask": refine_result.get("should_ask", False),
                "clarifying_question": refine_result.get("clarifying_question")
            }
>>>>>>> REPLACE
```

## Verification

1. Restart the gateway: `sudo systemctl restart llm-gateway`
2. Clear pycache: `rm -rf /ganuda/services/llm_gateway/__pycache__/`
3. Test with a normal council query:
   ```text
   curl -s -X POST http://localhost:8080/v1/council/vote \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $GATEWAY_API_KEY" \
     -d '{"question": "Should we add rate limiting to the gateway?"}' | python3 -m json.tool
   ```
4. Verify `refinement` key exists in response
5. Check thermal memory for reflexion traces:
   ```text
   psql -h localhost -U claude -d zammad_production \
     -c "SELECT id, LEFT(original_content, 100), metadata->>'type' FROM thermal_memory_archive WHERE metadata->>'type' = 'reflexion_trace' ORDER BY id DESC LIMIT 5;"
   ```

## What NOT to Change

- Do NOT modify specialist prompts
- Do NOT change the council vote schema
- Do NOT add new dependencies or imports beyond what gateway.py already has
- Do NOT modify mar_reflexion.py — this is a SEPARATE mechanism
- Do NOT touch sacred memory retrieval or temperature scoring

## Rollback

Set `SELF_REFINE_MAX_ROUNDS=0` in the environment to disable the loop without code changes. The function returns immediately with the original response when rounds=0 and sacred_flagged=False will still run but produce APPROVED on first pass in practice.

Actually, for a clean disable, add to the top of `self_refine_loop`:

The existing code handles this: if `SELF_REFINE_MAX_ROUNDS` is set to 0, the `range(0)` loop body never executes, returning the original response with 0 rounds.
