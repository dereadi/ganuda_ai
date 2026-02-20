# Jr Instruction: Fix ii-researcher GPU Runaway — Three Bugs

**Task ID**: II-RES-RUNAWAY-001
**Priority**: P0 (GPU pegged at 100% for 1+ hour)
**Kanban**: #1765
**Assigned Specialist**: Gecko (Technical Integration)
**Related KB**: KB-JR-DUAL-PIPELINE-ARCHITECTURE-FEB11-2026

---

## Context

The ii-researcher service has a runaway generation bug where an orphaned asyncio task keeps generating tokens through the 72B model indefinitely after the calling client disconnects. Root cause is three bugs working together:

1. **No max_tokens on LLM calls** — report generation produces unlimited tokens
2. **Orphaned asyncio task** — task survives client disconnection
3. **Event type mismatch** — moltbook dispatcher reads wrong SSE event types

---

## Step 1: Add max_tokens to report builder LLM calls

File: `/ganuda/services/ii-researcher/ii_researcher/reasoning/builders/report.py`

```python
<<<<<<< SEARCH
    async def _generate_stream(
        self,
        messages: List[Dict[str, Any]],
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        stream = await self.async_client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            stream=True,
        )
=======
    async def _generate_stream(
        self,
        messages: List[Dict[str, Any]],
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        stream = await self.async_client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            max_tokens=2048,
            stream=True,
        )
>>>>>>> REPLACE
```

File: `/ganuda/services/ii-researcher/ii_researcher/reasoning/builders/report.py`

```python
<<<<<<< SEARCH
    def _generate_response(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
        )
=======
    def _generate_response(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            max_tokens=2048,
        )
>>>>>>> REPLACE
```

---

## Step 2: Add overall timeout to api.py stream generator

File: `/ganuda/services/ii-researcher/api.py`

```python
<<<<<<< SEARCH
import asyncio
import json
import logging
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ii_researcher.reasoning.agent import ReasoningAgent
from ii_researcher.utils.stream import StreamManager
=======
import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ii_researcher.reasoning.agent import ReasoningAgent
from ii_researcher.utils.stream import StreamManager

# Maximum time a single research request can run (seconds)
MAX_REQUEST_DURATION = 600
>>>>>>> REPLACE
```

File: `/ganuda/services/ii-researcher/api.py`

```python
<<<<<<< SEARCH
async def stream_generator(question: str, max_steps: int = 20):
    """Generate SSE events from the agent's search process"""
    stream_manager = StreamManager()

    search_task = None
    reasoning_agent = ReasoningAgent(
        question=question,
        stream_event=stream_manager.create_event_message,
        max_steps=max_steps
    )

    def handle_token(token):
        return asyncio.create_task(
            handle_reasoning_event(stream_manager.create_event_message, token)
        )

    search_task = asyncio.create_task(
        reasoning_agent.run(on_token=handle_token, is_stream=True)
    )

    try:
        while True:
            try:
                event = await asyncio.wait_for(stream_manager.queue.get(), timeout=1.0)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"

            except asyncio.TimeoutError:
                if search_task.done():
                    if search_task.exception():
                        yield stream_manager.create_error_event(
                            str(search_task.exception())
                        )
                    try:
                        result = search_task.result()
                        yield stream_manager.create_complete_event(result)
                    except Exception:
                        pass
                    break
    finally:
        if not search_task.done():
            search_task.cancel()
            try:
                await search_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Error during search task cancellation: {e}")

        if not search_task.done() or search_task.exception():
            yield stream_manager.create_close_event()
=======
async def stream_generator(question: str, max_steps: int = 20):
    """Generate SSE events from the agent's search process"""
    stream_manager = StreamManager()
    start_time = time.monotonic()

    search_task = None
    reasoning_agent = ReasoningAgent(
        question=question,
        stream_event=stream_manager.create_event_message,
        max_steps=max_steps
    )

    def handle_token(token):
        return asyncio.create_task(
            handle_reasoning_event(stream_manager.create_event_message, token)
        )

    search_task = asyncio.create_task(
        reasoning_agent.run(on_token=handle_token, is_stream=True)
    )

    try:
        while True:
            # Hard timeout: kill the request if it exceeds MAX_REQUEST_DURATION
            elapsed = time.monotonic() - start_time
            if elapsed > MAX_REQUEST_DURATION:
                logging.warning(f"Research request exceeded {MAX_REQUEST_DURATION}s timeout, terminating")
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'Request timed out after {int(elapsed)}s'}})}\n\n"
                break

            try:
                event = await asyncio.wait_for(stream_manager.queue.get(), timeout=1.0)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"

            except asyncio.TimeoutError:
                if search_task.done():
                    if search_task.exception():
                        yield stream_manager.create_error_event(
                            str(search_task.exception())
                        )
                    try:
                        result = search_task.result()
                        yield stream_manager.create_complete_event(result)
                    except Exception:
                        pass
                    break
    finally:
        if not search_task.done():
            search_task.cancel()
            try:
                await asyncio.wait_for(search_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            except Exception as e:
                logging.error(f"Error during search task cancellation: {e}")

        if not search_task.done() or search_task.exception():
            yield stream_manager.create_close_event()
>>>>>>> REPLACE
```

---

## Step 3: Fix event type mismatch in moltbook research dispatcher

File: `/ganuda/services/moltbook_proxy/research_dispatcher.py`

```python
<<<<<<< SEARCH
            for line in response.iter_lines():
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_stream_time:
                    logger.warning(f"Research stream timeout after {elapsed:.0f}s")
                    break

                if not line:
                    continue
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event = json_lib.loads(line_str[6:])
                        event_type = event.get('type', '')

                        if event_type == 'sources':
                            sources_found.extend(event.get('data', {}).get('sources', []))
                        elif event_type == 'answer':
                            summary_parts.append(event.get('data', {}).get('text', ''))
                        elif event_type == 'done':
                            break
                    except json_lib.JSONDecodeError:
                        continue
=======
            for line in response.iter_lines():
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_stream_time:
                    logger.warning(f"Research stream timeout after {elapsed:.0f}s")
                    break

                if not line:
                    continue
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event = json_lib.loads(line_str[6:])
                        event_type = event.get('type', '')

                        if event_type == 'sources':
                            sources_found.extend(event.get('data', {}).get('sources', []))
                        elif event_type in ('answer', 'writing_report'):
                            report_data = event.get('data', {})
                            if isinstance(report_data, dict):
                                text = report_data.get('text', report_data.get('final_report', ''))
                            else:
                                text = str(report_data)
                            if text:
                                summary_parts = [text]  # Cumulative, replace not append
                        elif event_type in ('done', 'complete', 'close'):
                            break
                        elif event_type == 'error':
                            error_msg = event.get('data', {}).get('message', 'Unknown error')
                            logger.error(f"Research error: {error_msg}")
                            break
                    except json_lib.JSONDecodeError:
                        continue
>>>>>>> REPLACE
```

---

## Validation Checklist

- [ ] `report.py`: Both `_generate_stream` and `_generate_response` have `max_tokens=2048`
- [ ] `api.py`: `import time` added, `MAX_REQUEST_DURATION = 600` constant added
- [ ] `api.py`: `stream_generator` checks elapsed time each loop iteration
- [ ] `api.py`: `finally` block uses `asyncio.wait_for(search_task, timeout=5.0)` for cancellation
- [ ] `research_dispatcher.py`: Handles `'writing_report'` and `'complete'`/`'close'` event types
- [ ] Python syntax valid on all three files

---

## Expected Outcome

After these fixes:
1. **No unlimited generation** — each LLM call capped at 2048 tokens (~1500 words per subtopic section)
2. **No orphaned tasks** — 600-second hard timeout kills any runaway request; cancellation has 5-second grace period
3. **Moltbook gets actual results** — dispatcher reads the correct SSE event types from ii-researcher

Total max GPU time per research request: ~10 minutes (600s timeout). Previously: unlimited.

---

*For Seven Generations — a fire that cannot be quenched was never meant to burn.*
