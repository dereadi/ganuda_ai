# JR Instruction: Fix ii-researcher SSE Parsing

**ID:** JR-FIX-II-RESEARCHER-SSE-PARSING-FEB06-2026
**Priority:** P0 (Production Blocker)
**Assigned:** IT Jr
**Created:** 2026-02-06
**Status:** Ready

---

## Problem

Research Jr is calling ii-researcher correctly (logs confirm it), GPU is running (confirmed by user), but results show "0 sources fetched" because the SSE event parsing doesn't match the actual event format.

### Evidence from Logs

```
Feb 06 11:35:10 jr-research[4036016]: [ResearchTaskExecutor] ii-researcher returned no answer
Feb 06 11:36:33 ii-researcher[1988178]: [DETAILED RESEARCH OUTPUT WITH CITATIONS]
```

ii-researcher IS producing answers. The parsing is wrong.

---

## Root Cause

The `_call_ii_researcher()` method in `/ganuda/jr_executor/research_task_executor.py` parses SSE events incorrectly:

### Actual Event Format (from `/ganuda/services/ii-researcher/ii_researcher/utils/stream.py`)

```python
# Reasoning events:
{"type": "reasoning", "data": {"reasoning": "..."}, "timestamp": ...}

# Complete event:
{"type": "complete", "data": {"final_report": "..."}, "timestamp": ...}

# Error event:
{"type": "error", "data": {"message": "..."}, "timestamp": ...}
```

### Current (Wrong) Parsing

```python
if event_type == 'reasoning':
    reasoning += event_data.get('reasoning', '')  # WRONG - should be data.reasoning
elif event_type == 'complete':
    answer = event_data.get('answer', event_data.get('result', ''))  # WRONG - should be data.final_report
```

---

## Fix

In `/ganuda/jr_executor/research_task_executor.py`, update the `_call_ii_researcher` method's SSE parsing:

### Replace this block (around line 170-190):

```python
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])
                event_type = event_data.get('type', '')

                if event_type == 'reasoning':
                    reasoning += event_data.get('reasoning', '')
                elif event_type == 'source':
                    sources.append(event_data.get('url', ''))
                elif event_type == 'complete':
                    answer = event_data.get('answer', event_data.get('result', ''))
                elif event_type == 'error':
                    print(f"[ResearchTaskExecutor] ii-researcher error: {event_data.get('error')}")
                    return {'success': False, 'error': event_data.get('error')}
            except json.JSONDecodeError:
                pass
```

### With this corrected version:

```python
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            try:
                event_data = json.loads(line[6:])
                event_type = event_data.get('type', '')
                data = event_data.get('data', {})

                if event_type == 'reasoning':
                    # Reasoning is nested in data.reasoning
                    reasoning += data.get('reasoning', '')
                elif event_type == 'source':
                    # Source URL may be in data
                    url = data.get('url', '')
                    if url:
                        sources.append(url)
                elif event_type == 'complete':
                    # Final answer is in data.final_report
                    answer = data.get('final_report', '')
                    print(f"[ResearchTaskExecutor] ii-researcher complete: {len(answer)} chars")
                elif event_type == 'error':
                    error_msg = data.get('message', 'Unknown error')
                    print(f"[ResearchTaskExecutor] ii-researcher error: {error_msg}")
                    return {'success': False, 'error': error_msg}
                elif event_type == 'stream_closed':
                    # Stream closed, check if we got an answer
                    print(f"[ResearchTaskExecutor] ii-researcher stream closed")
                    break
            except json.JSONDecodeError as e:
                print(f"[ResearchTaskExecutor] SSE parse error: {e}")
                pass
```

---

## Verification

After fix:

1. Restart jr-research service: `sudo systemctl restart jr-research.service`

2. Queue a test task:
```python
from jr_executor.jr_queue_client import JrQueueClient
client = JrQueueClient()
task_id = client.queue_task(
    title="Test ii-researcher parsing",
    task_type="research",
    instructions="Search: Claude AI Constitutional AI principles"
)
print(f"Queued task {task_id}")
```

3. Monitor logs:
```bash
journalctl -u jr-research.service -f | grep -i "ii-researcher"
```

4. Expected output:
```
[ResearchTaskExecutor] Calling ii-researcher: Claude AI Constitutional AI principles...
[ResearchTaskExecutor] ii-researcher complete: 5432 chars
[ResearchTaskExecutor] ii-researcher success: 5432 chars, 8 sources
```

5. Check research output has actual content (not 0 sources):
```bash
ls -la /ganuda/docs/research/ | tail -5
```

---

## Reference

ii-researcher is from Intelligent-Internet:
- GitHub: https://github.com/Intelligent-Internet/ii-researcher
- Blog: https://www.ii.inc/web/blog/post/ii-researcher
- PyPI: `pip install ii-researcher`
- Our instance: `/ganuda/services/ii-researcher/`
- API: `http://localhost:8090/search?question=...&max_steps=10`
- Benchmarks: 84.12% accuracy on Google Frames dataset (DeepSeek-R1)

---

**Document Version:** 1.0
**TPM:** Claude Opus 4.5
**Sacred Fire:** Yes - Research capability is critical for Federation learning
