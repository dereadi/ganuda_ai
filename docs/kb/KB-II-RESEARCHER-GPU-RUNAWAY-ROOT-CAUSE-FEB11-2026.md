# KB: ii-researcher GPU Runaway — Root Cause Analysis & Fix

**Date**: February 11, 2026
**Severity**: P0 (GPU pegged at 100% for 1+ hour, 83C, 300W sustained)
**Trigger**: Post-power-outage service restart + Moltbook feed processing
**Kanban**: #1765
**Related KB**: KB-JR-DUAL-PIPELINE-ARCHITECTURE-FEB11-2026, KB-POWER-FAILURE-RECOVERY-FEB07-2026
**Thermal**: #84062

---

## Executive Summary

Three bugs in the ii-researcher + moltbook-proxy stack combined to peg the GPU at 100% indefinitely after a power outage. An orphaned asyncio task kept generating tokens through the 72B model with no token limit and no timeout, long after the calling client had disconnected.

---

## Kill Chain (Full Root Cause)

```
Power outage
  → Services restart via systemd
  → Moltbook proxy loads cached feed_check.json
  → research_dispatcher.py scores posts for relevance
  → "The supply chain attack nobody is talking about: skill.md is an unsigned binary" scores > 0.6
  → build_query() concatenates title + topic angles:
      identity → "consciousness substrate-independence phenomenology"
      security → "AI safety alignment verification"
  → dispatch() sends GET to ii-researcher:8090/search with max_steps=3
  → SearXNG down (port 8888 refused post-outage) → all 3 search steps fail
  → max_steps hit → forced report generation via ReportBuilder.generate_advance_report_stream()
  → Report builder calls 72B for intro + 2-7 subtopics, each with NO max_tokens
  → Dispatcher times out after 60s, disconnects HTTP
  → BUG: asyncio task is orphaned — continues generating in event loop
  → GPU pegged at 100% generating hallucinated research paper indefinitely
```

---

## The Three Bugs

### Bug 1: No max_tokens on LLM calls (report.py)

**File**: `/ganuda/services/ii-researcher/ii_researcher/reasoning/builders/report.py`
**Methods**: `_generate_stream()` (line ~278), `_generate_response()` (line ~304)

Both methods called `chat.completions.create()` with no `max_tokens` parameter. With the 72B model's 32K context window, a single subtopic report could generate until context exhaustion. The report builder iterates through 2-7 subtopics, each including ALL previous content in the prompt — so context grows exponentially.

**Fix**: Added `max_tokens=2048` to both methods. Each subtopic section now caps at ~1500 words.

### Bug 2: Orphaned asyncio task (api.py)

**File**: `/ganuda/services/ii-researcher/api.py`
**Function**: `stream_generator()` (line ~41)

The function creates an asyncio task via `asyncio.create_task(reasoning_agent.run(...))`. When the HTTP client disconnects (e.g., dispatcher timeout), FastAPI's `StreamingResponse` stops iterating the generator, but the asyncio task **continues running in the event loop**. There was no overall timeout — the task could run forever.

The `finally` block attempted cancellation with bare `await search_task`, which could itself hang if the task didn't respond to cancellation.

**Fix**:
- Added `MAX_REQUEST_DURATION = 600` (10 minute hard ceiling)
- Added `time.monotonic()` check each loop iteration
- Changed cancellation to `asyncio.wait_for(search_task, timeout=5.0)` with grace period

### Bug 3: SSE event type mismatch (research_dispatcher.py)

**File**: `/ganuda/services/moltbook_proxy/research_dispatcher.py`
**Function**: `dispatch()` SSE parsing loop (line ~219)

The dispatcher looked for event types `'answer'` and `'done'`, but ii-researcher actually sends `'writing_report'` and `'complete'`/`'close'`. This meant the dispatcher never captured the actual report content — `summary_parts` stayed empty. The dispatcher would time out after `max_stream_time=60` having read nothing useful.

**Fix**:
- Added `'writing_report'` alongside `'answer'` for report content events
- Added `'complete'` and `'close'` alongside `'done'` for termination events
- Added `'error'` event handling
- Changed summary accumulation to replacement (cumulative `writing_report` events contain full report)

---

## Additional Bug Discovered During Fix: is_research_task() Substring Match

**File**: `/ganuda/jr_executor/research_task_executor.py:595`

Jr task #695 (queued to fix this very bug) was misrouted to `ResearchTaskExecutor` because the title "Fix ii-**research**er GPU runaway" triggered `'research' in title` — a substring match that catches "researcher", "ii-researcher", etc.

The ResearchTaskExecutor then extracted code fragments from the SEARCH/REPLACE blocks in the instruction file and sent them to ii-researcher as "research queries" (e.g., `"return asyncio.create_task("`, `"{e}")`), generating 16-25K char "research papers" about Python syntax. This pegged the GPU a second time.

**Workaround**: Re-queued as #696 with title "Fix GPU runaway — add max_tokens, timeout, event type mismatch" (no "research" substring). Jr executor then thrashed, so TPM applied patches directly.

**Root fix needed**: Change `is_research_task()` to use word boundary matching:
```python
# Current (broken)
if 'research' in title:

# Fixed
import re
if re.search(r'\bresearch\b', title):
```

---

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `services/ii-researcher/ii_researcher/reasoning/builders/report.py` | `max_tokens=2048` on both LLM call methods | ~279, ~308 |
| `services/ii-researcher/api.py` | `import time`, `MAX_REQUEST_DURATION`, elapsed check, improved cancellation | ~1-12, ~41-92 |
| `services/moltbook_proxy/research_dispatcher.py` | Handle `writing_report`, `complete`, `close`, `error` event types | ~219-226 |

---

## Validation

After applying fixes and restarting ii-researcher:
- [ ] GPU returns to idle when no requests active
- [ ] New research request completes within 600s
- [ ] Moltbook dispatcher receives actual report content (not empty summary)
- [ ] Disconnected client does not leave orphaned GPU task

---

## Prevention Checklist (For Future LLM Service Development)

1. **Always set max_tokens** on every LLM API call. There is no valid reason for unlimited generation in production.
2. **Always add a hard timeout** to any async generator that creates background tasks. `asyncio.create_task()` survives client disconnection.
3. **Always use `asyncio.wait_for()` for task cancellation** — bare `await task` can hang if the task ignores `CancelledError`.
4. **Always verify SSE event type contracts** between producer and consumer. Log unknown event types rather than silently ignoring them.
5. **Never use substring matching for task routing** — use word boundary regex or exact match.
6. **Test with SearXNG down** — the failure mode when search fails is where the runaway behavior emerged.

---

## Timeline

| Time | Event |
|------|-------|
| ~08:39 | Power restored, services restart via systemd |
| ~08:40 | Moltbook proxy processes cached feed, dispatches research query |
| ~08:40 | SearXNG down → ii-researcher search steps fail → forced report generation |
| ~08:41 | Dispatcher times out at 60s, disconnects |
| ~08:41 | Orphaned asyncio task continues generating through 72B indefinitely |
| 09:24 | TPM notices GPU at 100%, 83C, 300W |
| 09:30 | Root cause traced to ii-researcher PID connected to vLLM port 8000 |
| 09:33 | Three bugs identified, Jr instruction written (JR-II-RESEARCHER-GPU-RUNAWAY-FIX-FEB11-2026.md) |
| 09:33 | Jr task #695 queued |
| 09:35 | `sudo systemctl restart ii-researcher` kills orphaned task |
| 09:35 | Jr #695 misrouted to ResearchTaskExecutor (is_research_task substring bug) |
| 09:42 | ResearchTaskExecutor sends code fragments to ii-researcher as queries |
| 09:44 | #695 marked failed, #696 queued with safe title |
| 09:45 | `sudo systemctl restart jr-orchestrator` |
| 09:48 | Software Engineer Jr. worker thrashes, dies |
| 09:49 | TPM applies all three patches directly |
| 09:50 | `sudo systemctl restart ii-researcher` to load patched code |

---

*For Seven Generations — a fire that cannot be quenched was never meant to burn. But a fire that burns without purpose is not sacred — it is waste.*
