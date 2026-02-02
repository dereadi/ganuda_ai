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


async def show_council_progress(update, context):
    """Show Council consultation progress."""
    msg = await update.message.reply_text("🦅 Consulting the Council...")
    progress = ToolProgress(msg)
    await asyncio.sleep(0.3)
    await progress.add_step('council', "7 specialists deliberating...")
    return progress


async def show_research_progress(update, context, query: str):
    """Show research progress."""
    short_query = query[:50] + "..." if len(query) > 50 else query
    msg = await update.message.reply_text(f"🔍 Starting research: {short_query}")
    progress = ToolProgress(msg)
    return progress


async def show_tool_call(update, context, tool_name: str, description: str):
    """Show generic tool call progress."""
    msg = await update.message.reply_text(f"🔧 {tool_name}: {description}")
    progress = ToolProgress(msg)
    return progress
