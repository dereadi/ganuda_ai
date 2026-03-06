# [RECURSIVE] RL2F Phase 0: Self-Refine Loop on Gateway - Step 2

**Parent Task**: #824
**Auto-decomposed**: 2026-02-22T09:25:04.748093
**Original Step Title**: Wire Self-Refine into the council vote endpoint

---

### Step 2: Wire Self-Refine into the council vote endpoint

File: `/ganuda/services/llm_gateway/gateway.py`

Find the consensus synthesis section in the `/v1/council/vote` endpoint. After the consensus is generated and BEFORE the TPM notification, add the Self-Refine loop.

Look for the pattern where `consensus` variable is set and `meta_council.complete_deliberation(consensus)` is called. AFTER `complete_deliberation` returns the `meta_result`, add:

```python
<<<<<<< SEARCH
        # Save to database
=======
        # ─── Self-Refine Loop (RL2F Phase 0) ─────────────
        sacred_flagged = any(
            r.get("sacred_pattern", False)
            for r in specialist_responses.values()
            if isinstance(r, dict)
        )
        refine_result = self_refine_loop(
            question=request.question,
            draft_response=consensus,
            sacred_flagged=sacred_flagged
        )
        if refine_result["rounds"] > 0:
            consensus = refine_result["final_response"]
            meta_result["refinement_rounds"] = refine_result["rounds"]
            meta_result["refinement_applied"] = True

        # Save to database
>>>>>>> REPLACE
```
