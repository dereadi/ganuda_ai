# JR Instruction: Fix Research API Field Names

**JR ID:** JR-FIX-RESEARCH-API-FIELD-NAMES-JAN28-2026
**Priority:** P0 (Blocking UI)
**Assigned To:** Backend Jr.

---

## Problem

Research results don't display on frontend because API returns different field names than frontend expects.

| API returns | Frontend expects |
|-------------|------------------|
| `job_id` | `research_id` |
| `answer` | `summary` |
| (missing) | `full_result` |
| (missing) | `condition` |

---

## Fix

Edit `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py` lines 118-128:

**BEFORE:**
```python
"results": [
    {
        "job_id": r['job_id'],
        "question": r['question'],
        "answer": r['answer'],
        "sources": r['sources'] if r['sources'] else [],
        "status": "completed",
        "created_at": r['created_at'].isoformat() if r['created_at'] else None,
        "completed_at": r['completed_at'].isoformat() if r['completed_at'] else None
    }
    for r in results
]
```

**AFTER:**
```python
"results": [
    {
        "research_id": r['job_id'],
        "question": r['question'],
        "condition": None,
        "status": "completed",
        "summary": r['answer'],
        "full_result": {"answer": r['answer'], "sources": r['sources'] if r['sources'] else []},
        "created_at": r['created_at'].isoformat() if r['created_at'] else None,
        "completed_at": r['completed_at'].isoformat() if r['completed_at'] else None
    }
    for r in results
]
```

---

## Validation

```bash
curl -s "http://localhost:8001/api/v1/research/results/aa549d11-e4f5-4022-9b62-8c127b6a6213" | python3 -m json.tool
```

Should return `research_id` and `summary` fields.

---

FOR SEVEN GENERATIONS
