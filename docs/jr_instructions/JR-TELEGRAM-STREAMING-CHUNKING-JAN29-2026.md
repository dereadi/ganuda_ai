# JR Instruction: Telegram Streaming and Chunking

**JR ID:** JR-TELEGRAM-STREAMING-CHUNKING-JAN29-2026
**Priority:** P0 - IMMEDIATE
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-TELEGRAM-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE

---

## Objective

Add streaming-style responses and intelligent message chunking to telegram_chief.py for better UX.

---

## Background

Council unanimously approved this enhancement. Current behavior sends one large message after full LLM completion. Target behavior:
1. Show typing indicator immediately
2. Send response in digestible chunks
3. Handle Telegram's 4096 char limit gracefully

---

## Implementation

### Step 1: Create Message Chunker Module

Create `/ganuda/telegram_bot/message_chunker.py`:

```python
"""
Message Chunker - Telegram-aware text splitting.
Cherokee AI Federation - For Seven Generations
"""

import re
from typing import List

TELEGRAM_MAX_LENGTH = 4096
PREFERRED_CHUNK_SIZE = 3500  # Leave room for formatting
MIN_CHUNK_SIZE = 200

def chunk_message(text: str, max_length: int = PREFERRED_CHUNK_SIZE) -> List[str]:
    """
    Split text into Telegram-safe chunks at paragraph boundaries.

    Args:
        text: The full message text
        max_length: Maximum chunk size (default 3500)

    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to break at paragraph (double newline)
        chunk = remaining[:max_length]

        # Find last paragraph break
        para_break = chunk.rfind('\n\n')
        if para_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:para_break].strip())
            remaining = remaining[para_break:].strip()
            continue

        # Fall back to single newline
        line_break = chunk.rfind('\n')
        if line_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:line_break].strip())
            remaining = remaining[line_break:].strip()
            continue

        # Fall back to sentence break
        sentence_break = max(
            chunk.rfind('. '),
            chunk.rfind('? '),
            chunk.rfind('! ')
        )
        if sentence_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:sentence_break + 1].strip())
            remaining = remaining[sentence_break + 1:].strip()
            continue

        # Hard break at max_length
        chunks.append(remaining[:max_length].strip())
        remaining = remaining[max_length:].strip()

    return chunks


def escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_chunk_header(current: int, total: int) -> str:
    """Generate chunk header for multi-part messages."""
    if total <= 1:
        return ""
    return f"_({current}/{total})_\n\n"
```

### Step 2: Add Typing Indicator Helper

Add to `/ganuda/telegram_bot/telegram_chief.py` (after imports):

```python
import asyncio
from message_chunker import chunk_message, format_chunk_header

async def send_with_typing(update, context, text: str, parse_mode: str = None):
    """Send message with typing indicator and chunking."""
    chat_id = update.effective_chat.id

    # Show typing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Chunk the message
    chunks = chunk_message(text)
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        # Add header for multi-part
        if total > 1:
            header = format_chunk_header(i + 1, total)
            chunk = header + chunk

        await update.message.reply_text(chunk, parse_mode=parse_mode)

        # Brief delay between chunks to avoid rate limiting
        if i < total - 1:
            await asyncio.sleep(0.3)
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
```

### Step 3: Update handle_message to Use Chunking

Find the main message handler in telegram_chief.py and update the response sending:

**Before:**
```python
await update.message.reply_text(response_text)
```

**After:**
```python
await send_with_typing(update, context, response_text)
```

### Step 4: Add Streaming for Long Operations

For Council queries and research, add progressive updates:

```python
async def handle_message_with_progress(update, context, query: str):
    """Handle message with progress updates for long operations."""
    chat_id = update.effective_chat.id

    # Initial acknowledgment
    progress_msg = await update.message.reply_text("🤔 Thinking...")

    try:
        # Show we're working
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # For Council queries, show specialist engagement
        if is_council_query(query):
            await progress_msg.edit_text("🦅 Consulting the Council...\n\n_7 specialists deliberating..._", parse_mode="Markdown")

        # Get response
        response = await get_llm_response(query)

        # Delete progress message
        await progress_msg.delete()

        # Send chunked response
        await send_with_typing(update, context, response)

    except Exception as e:
        await progress_msg.edit_text(f"❌ Error: {str(e)}")
```

---

## Testing

1. Send a message that generates a long response (>4000 chars)
2. Verify typing indicator appears immediately
3. Verify response arrives in multiple chunks
4. Verify chunks break at paragraph/sentence boundaries
5. Verify no truncation occurs

Test command:
```
/research Explain the complete history of PostgreSQL database
```

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/telegram_bot/message_chunker.py` | CREATE |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY - add send_with_typing, update handlers |

---

## Service Restart

```bash
sudo systemctl restart telegram-chief
```

---

FOR SEVEN GENERATIONS
