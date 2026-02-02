# JR Instruction: Fix Research Client SSE Parsing

**JR ID:** JR-FIX-RESEARCH-CLIENT-SSE-PARSING-JAN28-2026
**Priority:** P0 (Blocking)
**Assigned To:** Software Engineer Jr.
**Issue:** research_client.py not parsing ii-researcher SSE events correctly

---

## Problem

ii-researcher generates comprehensive answers (verified in logs), but research_client.py returns "No answer generated" because it's looking for wrong SSE event types.

**Current code looks for:**
- `type: "report"` with `data.content`
- `type: "complete"` with `data.report`

**ii-researcher actually sends:**
- Different event structure (need to capture actual format)

---

## Root Cause (CONFIRMED)

Captured actual SSE format from ii-researcher:

```
data: {"type": "reasoning", "data": {"reasoning": "..."}, "timestamp": ...}
data: {"type": "writing_report", "data": {"final_report": "# Answer..."}, "timestamp": ...}
```

**Mismatch:**
| Client expects | ii-researcher sends |
|----------------|---------------------|
| `type: "report"` | `type: "writing_report"` |
| `data.content` | `data.final_report` |

---

## Fix Required

In `/ganuda/lib/research_client.py`, change line 92-97:

**FROM:**
```python
# Capture the final report/answer
elif event_type == "report":
    report_data = data.get("data", {})
    if isinstance(report_data, dict):
        final_answer += report_data.get("content", "")
    else:
        final_answer += str(report_data)
```

**TO:**
```python
# Capture the final report/answer
elif event_type == "writing_report":
    report_data = data.get("data", {})
    if isinstance(report_data, dict):
        # ii-researcher sends cumulative final_report
        final_answer = report_data.get("final_report", "")
    else:
        final_answer = str(report_data)
```

**Note:** Use `=` not `+=` because `final_report` is cumulative (each event contains full text so far).

---

## Testing

After fix:

```python
from research_client import ResearchClient

client = ResearchClient()
result = client.search("VA tinnitus rating", max_steps=3, verbose=True)
print(f"Answer length: {len(result.answer)}")
print(f"Answer preview: {result.answer[:500]}")
```

Expected: Non-empty answer with actual tinnitus rating content.

---

## Files to Modify

- `/ganuda/lib/research_client.py` - Fix SSE parsing logic (lines 76-122)

---

## Validation

```bash
# Queue new test job
curl -s -X POST http://localhost:8080/v1/research/async \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"query": "VA sleep apnea rating", "max_steps": 3}'

# Wait 2-3 minutes, then check
curl -s http://localhost:8080/v1/research/status/<job_id> \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Should show actual answer, not "No answer generated"
```

---

FOR SEVEN GENERATIONS
