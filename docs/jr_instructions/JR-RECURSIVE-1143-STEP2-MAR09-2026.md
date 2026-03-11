# [RECURSIVE] Thermal Memory Canonical Flag DC-14 Phase 1 - Step 2

**Parent Task**: #1143
**Auto-decomposed**: 2026-03-09T14:30:13.407968
**Original Step Title**: Update retrieval to prefer canonical memories

---

### Step 2: Update retrieval to prefer canonical memories

In `/ganuda/lib/specialist_council.py`, find the thermal memory retrieval query in the RAG pipeline. After the existing ORDER BY clause, add canonical preference:

```
<<<<<<< SEARCH
            ORDER BY similarity DESC
            LIMIT %s
=======
            ORDER BY canonical DESC, similarity DESC
            LIMIT %s
>>>>>>> REPLACE
```
