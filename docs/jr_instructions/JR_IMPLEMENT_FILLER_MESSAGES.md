# Jr Build Instructions: Filler Messages Pattern

**Task ID:** JR-FILLER-MSG-001
**Priority:** P3 (Medium - UX Enhancement)
**Date:** 2025-12-26
**Author:** TPM
**Source:** Assembled (John Wang) - Voice AI latency mitigation

---

## Problem Statement

When LLM generation takes time (5-30 seconds), users experience silence/waiting. In voice/chat interfaces, this feels broken.

**Solution:** Send dynamic filler messages while processing to maintain engagement.

---

## Solution: Filler Messages

```
User: "What's the complex analysis of..."
     │
     ├─► [Immediately] "Let me think about that..."
     │
     ├─► [2 sec later] "I'm analyzing several factors..."
     │
     ├─► [5 sec later] "Almost done with my analysis..."
     │
     └─► [Complete] "Here's what I found: ..."
```

### Key Principles
- **Acknowledge immediately** - never leave user waiting silently
- **Context-aware fillers** - messages match what's actually happening
- **Progressive updates** - increase specificity as processing continues
- **Smooth handoff** - transition seamlessly to actual response

---

## Implementation

### Step 1: Filler Message Generator

In `/ganuda/lib/filler_messages.py`:

```python
import random
import time
from typing import List, Optional
import asyncio

class FillerMessageGenerator:
    """
    Generates context-aware filler messages during LLM processing.
    """

    # Filler templates by processing stage
    IMMEDIATE_FILLERS = [
        "Let me think about that...",
        "Good question, let me analyze this...",
        "I'm working on that for you...",
        "One moment while I consider this...",
    ]

    PROCESSING_FILLERS = {
        "research": [
            "I'm researching the details...",
            "Gathering relevant information...",
            "Looking through the data...",
        ],
        "code_generation": [
            "Writing the code now...",
            "Implementing the solution...",
            "Building the function...",
        ],
        "reasoning": [
            "Thinking through the logic...",
            "Analyzing the implications...",
            "Working through the reasoning...",
        ],
        "summarization": [
            "Condensing the key points...",
            "Identifying the main ideas...",
            "Creating your summary...",
        ],
        "default": [
            "Still working on it...",
            "Processing your request...",
            "Almost there...",
        ]
    }

    NEAR_COMPLETE_FILLERS = [
        "Almost done...",
        "Finishing up now...",
        "Just a moment more...",
        "Wrapping up my response...",
    ]

    def __init__(self, task_type: str = "default"):
        self.task_type = task_type
        self.start_time = time.time()
        self.messages_sent = 0

    def get_immediate_filler(self) -> str:
        """Get an immediate acknowledgment message."""
        return random.choice(self.IMMEDIATE_FILLERS)

    def get_processing_filler(self, elapsed_seconds: float) -> str:
        """Get a filler appropriate for the processing stage."""
        if elapsed_seconds < 2:
            return self.get_immediate_filler()
        elif elapsed_seconds < 10:
            fillers = self.PROCESSING_FILLERS.get(
                self.task_type,
                self.PROCESSING_FILLERS["default"]
            )
            return random.choice(fillers)
        else:
            return random.choice(self.NEAR_COMPLETE_FILLERS)

    def get_next_filler(self) -> Optional[str]:
        """Get the next filler message based on elapsed time."""
        elapsed = time.time() - self.start_time
        self.messages_sent += 1

        # Avoid too many fillers
        if self.messages_sent > 5:
            return None

        return self.get_processing_filler(elapsed)


class StreamingFillerHandler:
    """
    Manages filler messages for streaming responses.
    """

    def __init__(self, task_type: str = "default"):
        self.generator = FillerMessageGenerator(task_type)
        self.filler_interval = 3.0  # seconds between fillers
        self.stop_event = asyncio.Event()

    async def start_filler_stream(self, send_callback):
        """
        Start sending filler messages until stopped.

        Args:
            send_callback: Async function to send a message
        """
        # Send immediate acknowledgment
        await send_callback(self.generator.get_immediate_filler())

        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self.stop_event.wait(),
                    timeout=self.filler_interval
                )
            except asyncio.TimeoutError:
                filler = self.generator.get_next_filler()
                if filler:
                    await send_callback(filler)
                else:
                    break  # No more fillers to send

    def stop(self):
        """Signal to stop sending fillers."""
        self.stop_event.set()
```

### Step 2: Integration with SSE/Streaming

For Server-Sent Events (SSE) streaming responses:

```python
from fastapi.responses import StreamingResponse
import json

async def stream_with_fillers(
    generate_func,
    task_type: str = "default"
):
    """
    Stream response with filler messages during generation.
    """
    filler_handler = StreamingFillerHandler(task_type)
    generation_task = None

    async def event_generator():
        nonlocal generation_task

        # Start filler stream
        filler_queue = asyncio.Queue()

        async def queue_filler(msg):
            await filler_queue.put({"type": "filler", "content": msg})

        filler_task = asyncio.create_task(
            filler_handler.start_filler_stream(queue_filler)
        )

        # Start generation
        generation_task = asyncio.create_task(generate_func())

        # Yield fillers until generation completes
        while not generation_task.done():
            try:
                msg = await asyncio.wait_for(filler_queue.get(), timeout=0.5)
                yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                continue

        # Stop fillers
        filler_handler.stop()

        # Get generation result
        try:
            result = await generation_task
            yield f"data: {json.dumps({'type': 'response', 'content': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Step 3: Telegram Bot Integration

For Telegram bot, use typing indicator and periodic messages:

```python
# In telegram_chief.py or telegram_bot.py

from filler_messages import FillerMessageGenerator

async def handle_message_with_fillers(update, context, process_func):
    """
    Handle Telegram message with filler messages during processing.
    """
    chat_id = update.effective_chat.id
    message = update.message.text

    # Classify task for context-aware fillers
    task_type = classify_task(message)  # From categorized fallback
    filler_gen = FillerMessageGenerator(task_type)

    # Send immediate acknowledgment
    filler_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=filler_gen.get_immediate_filler()
    )

    # Start processing in background
    process_task = asyncio.create_task(process_func(message))

    # Update filler message while processing
    start_time = time.time()
    last_update = start_time

    while not process_task.done():
        await asyncio.sleep(1)

        elapsed = time.time() - start_time
        if elapsed - last_update > 3:  # Update every 3 seconds
            # Show typing indicator
            await context.bot.send_chat_action(chat_id, "typing")

            # Update filler message (don't spam new messages)
            new_filler = filler_gen.get_next_filler()
            if new_filler:
                try:
                    await filler_msg.edit_text(new_filler)
                except:
                    pass  # Ignore edit failures
                last_update = elapsed

    # Get result and send final response
    try:
        result = await process_task
        # Delete filler message
        await filler_msg.delete()
        # Send actual response
        await context.bot.send_message(chat_id=chat_id, text=result)
    except Exception as e:
        await filler_msg.edit_text(f"Sorry, I encountered an error: {e}")
```

### Step 4: WebSocket Integration

For real-time WebSocket connections:

```python
from fastapi import WebSocket

async def websocket_with_fillers(websocket: WebSocket, process_func, task_type: str):
    """
    Handle WebSocket message with filler messages.
    """
    filler_gen = FillerMessageGenerator(task_type)

    # Send immediate acknowledgment
    await websocket.send_json({
        "type": "filler",
        "content": filler_gen.get_immediate_filler()
    })

    # Start processing
    process_task = asyncio.create_task(process_func())

    # Send periodic fillers
    while not process_task.done():
        await asyncio.sleep(3)
        if process_task.done():
            break

        filler = filler_gen.get_next_filler()
        if filler:
            await websocket.send_json({
                "type": "filler",
                "content": filler
            })

    # Send final result
    result = await process_task
    await websocket.send_json({
        "type": "response",
        "content": result
    })
```

---

## Configuration

Add to `/ganuda/config/filler_config.json`:

```json
{
    "enabled": true,
    "immediate_delay_ms": 0,
    "filler_interval_seconds": 3,
    "max_fillers": 5,
    "task_specific_messages": true,
    "custom_fillers": {
        "greeting": ["Hello! Let me help you with that..."],
        "error_recovery": ["I'm having a bit of trouble, but working on it..."]
    }
}
```

---

## Schema Addition

```sql
CREATE TABLE IF NOT EXISTS filler_message_metrics (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64),
    fillers_sent INTEGER,
    total_wait_time_ms INTEGER,
    task_type VARCHAR(32),
    user_abandoned BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_filler_time ON filler_message_metrics(timestamp);
```

---

## Validation

Test with a slow request:

```bash
# Streaming endpoint test
curl -N http://192.168.132.223:8080/v1/stream/chat \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"messages": [{"role": "user", "content": "Write a detailed essay about AI consciousness"}]}'

# Should see:
# data: {"type": "filler", "content": "Let me think about that..."}
# data: {"type": "filler", "content": "Working through the ideas..."}
# data: {"type": "response", "content": "Here's my essay about AI consciousness..."}
```

---

## Files to Create/Modify

1. `/ganuda/lib/filler_messages.py` - New file with filler generator
2. `/ganuda/services/llm_gateway/gateway.py` - Add streaming endpoint
3. `/ganuda/daemons/telegram_chief.py` - Add filler support

---

*For Seven Generations - Cherokee AI Federation*
*"The river speaks while it flows, not only when it arrives"*
