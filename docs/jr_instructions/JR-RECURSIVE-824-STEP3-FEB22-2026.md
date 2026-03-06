# [RECURSIVE] RL2F Phase 0: Self-Refine Loop on Gateway - Step 3

**Parent Task**: #824
**Auto-decomposed**: 2026-02-22T09:25:04.749163
**Original Step Title**: Store the reflexion trace after database save

---

### Step 3: Store the reflexion trace after database save

File: `/ganuda/services/llm_gateway/gateway.py`

After the council vote is saved to the database (after the `conn.commit()` for the council_votes INSERT), add:

```python
<<<<<<< SEARCH
        # Create TPM notification
=======
        # Store reflexion trace in thermal memory
        store_reflexion_trace(audit_hash, request.question, refine_result)

        # Create TPM notification
>>>>>>> REPLACE
```
