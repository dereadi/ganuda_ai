# JR Instruction: Telegram Tool Transparency

**JR ID:** JR-TELEGRAM-TOOL-TRANSPARENCY-JAN29-2026
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-TELEGRAM-ENHANCEMENT-JAN29-2026
**Council Vote:** 7-0 APPROVE (Peace Chief specifically recommended)
**Depends On:** JR-TELEGRAM-STREAMING-CHUNKING-JAN29-2026

---

## Objective

Show tool invocations inline before final responses. Users see what the bot is doing - builds trust and transparency.

---

## Target UX

```
User: What's the latest on ii-researcher?
Bot: 🔧 Querying Council...
Bot: 📊 7 specialists responding...
Bot: ✅ Council reached consensus

[Final response with Council synthesis]
```

```
User: /research PostgreSQL tuning
Bot: 🔍 Starting deep research...
Bot: 📚 Searching knowledge base...
Bot: 🌐 Querying web sources...
Bot: ✅ Research complete

[Research results]
```

---

## Implementation

### Step 1: Create Tool Display Module

Create `/ganuda/telegram_bot/tool_display.py`:

```python
"""
Tool Display - Show tool invocations inline.
Cherokee AI Federation - For Seven Generations
"""

from typing import Optional
from telegram import Message
import asyncio

# Tool status emojis
TOOL_ICONS = {
    'thinking': '🤔',
    'council': '🦅',
    'research': '🔍',
    'search': '🔎',
    'database': '🗄️',
    'api': '🔌',
    'processing': '⚙️',
    'success': '✅',
    'error': '❌',
    'waiting': '⏳',
}

class ToolProgress:
    """Manage tool progress display in Telegram."""

    def __init__(self, message: Message):
        self.message = message
        self.steps = []

    async def add_step(self, icon_key: str, text: str):
        """Add a step to the progress display."""
        icon = TOOL_ICONS.get(icon_key, '🔧')
        self.steps.append(f"{icon} {text}")
        await self._update_display()

    async def complete(self, success: bool = True):
        """Mark progress as complete."""
        icon = TOOL_ICONS['success'] if success else TOOL_ICONS['error']
        status = "Complete" if success else "Failed"
        self.steps.append(f"{icon} {status}")
        await self._update_display()

    async def _update_display(self):
        """Update the message with current steps."""
        text = "\n".join(self.steps)
        try:
            await self.message.edit_text(text)
        except Exception:
            pass  # Message may have been deleted

    async def delete(self):
        """Delete the progress message."""
        try:
            await self.message.delete()
        except Exception:
            pass


async def show_council_progress(update, context) -> ToolProgress:
    """Show Council consultation progress."""
    msg = await update.message.reply_text("🦅 Consulting the Council...")
    progress = ToolProgress(msg)
    await asyncio.sleep(0.3)
    await progress.add_step('council', "7 specialists deliberating...")
    return progress


async def show_research_progress(update, context, query: str) -> ToolProgress:
    """Show research progress."""
    short_query = query[:50] + "..." if len(query) > 50 else query
    msg = await update.message.reply_text(f"🔍 Starting research: {short_query}")
    progress = ToolProgress(msg)
    return progress


async def show_tool_call(update, context, tool_name: str, description: str) -> ToolProgress:
    """Show generic tool call progress."""
    msg = await update.message.reply_text(f"🔧 {tool_name}: {description}")
    progress = ToolProgress(msg)
    return progress
```

### Step 2: Update Council Query Handler

In `/ganuda/telegram_bot/telegram_chief.py`, find where Council is queried and add progress:

```python
from tool_display import show_council_progress, show_research_progress

async def handle_council_query(update, context, query: str):
    """Handle query that goes to Council with progress display."""

    # Show progress
    progress = await show_council_progress(update, context)

    try:
        # Import and call Council
        from specialist_council import council_vote_first
        result = council_vote_first(query)

        # Update progress with vote info
        vote_counts = result.get('vote_counts', {})
        approve = vote_counts.get('APPROVE', 0)
        reject = vote_counts.get('REJECT', 0)

        await progress.add_step('processing', f"Vote: {approve} approve, {reject} reject")
        await progress.complete(success=result.get('decision') == 'APPROVED')

        # Brief pause for user to see result
        await asyncio.sleep(0.5)
        await progress.delete()

        # Send actual response
        response = format_council_response(result)
        await send_with_typing(update, context, response)

    except Exception as e:
        await progress.add_step('error', str(e))
        await progress.complete(success=False)
```

### Step 3: Update Research Command

In the `research_command` handler:

```python
async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research with progress display."""
    if not context.args:
        await update.message.reply_text("Usage: /research <question>")
        return

    query = " ".join(context.args)

    # Show progress
    progress = await show_research_progress(update, context, query)

    try:
        await progress.add_step('search', "Querying knowledge base...")
        await asyncio.sleep(0.5)

        await progress.add_step('api', "Dispatching to ii-researcher...")

        # Queue research
        from research_dispatcher import ResearchDispatcher
        dispatcher = ResearchDispatcher()
        job_id = dispatcher.queue_research(
            query=query,
            requester_type="telegram",
            requester_id=str(update.effective_user.id),
            callback_type="telegram",
            callback_target=str(update.effective_chat.id)
        )

        await progress.add_step('success', f"Queued: {job_id[:8]}")
        await progress.complete(success=True)

        # Keep progress visible briefly
        await asyncio.sleep(1)
        await progress.delete()

        await update.message.reply_text(
            f"✅ Research queued!\n\n"
            f"Job: `{job_id[:8]}`\n"
            f"Results in 3-5 minutes.",
            parse_mode="Markdown"
        )

    except Exception as e:
        await progress.add_step('error', str(e)[:50])
        await progress.complete(success=False)
```

---

## Testing

1. Ask a question that triggers Council:
   ```
   Should we use Redis or PostgreSQL for caching?
   ```
   - Verify progress shows: "Consulting Council" → "7 specialists" → "Vote: X approve" → "Complete"

2. Run /research:
   ```
   /research How does PostgreSQL handle vacuum?
   ```
   - Verify progress shows: "Starting research" → "Querying knowledge base" → "Dispatching" → "Queued"

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/telegram_bot/tool_display.py` | CREATE |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY - integrate tool progress |

---

## Service Restart

```bash
sudo systemctl restart telegram-chief
```

---

FOR SEVEN GENERATIONS
