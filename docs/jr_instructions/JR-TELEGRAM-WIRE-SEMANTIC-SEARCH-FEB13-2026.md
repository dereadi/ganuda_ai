# Jr Instruction: Wire Semantic Memory into Both Telegram Bots

**Task**: Add semantic memory search to @derpatobot and @ganudabot
**Council Vote**: #7ab07bfbd92c70b4
**Kanban**: #1779
**Priority**: 1
**Assigned Jr**: Software Engineer Jr.
**Depends on**: JR-TELEGRAM-SEMANTIC-MEMORY-MODULE-FEB13-2026.md (tribe_memory_search.py must exist)

## Context

The shared module `tribe_memory_search.py` provides `semantic_search()`, `format_for_telegram()`, and `format_for_llm()`. Now wire it into both bots.

## Step 1: Add /search command and upgrade /memory in telegram_chief_v3.py

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

<<<<<<< SEARCH
from tribal_knowledge import lookup_tribal_knowledge
=======
from tribal_knowledge import lookup_tribal_knowledge
from tribe_memory_search import semantic_search, format_for_telegram, format_for_llm
>>>>>>> REPLACE

<<<<<<< SEARCH
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Cherokee Chief Bot v3.0\n\n"
        "Commands:\n"
        "/ask <question> - Ask the Council\n"
        "/health - Cluster status\n"
        "/memory - Recent thermal memories\n"
        "/seed <content> - Write to memory\n"
        "/ticket <title> - Create Jr ticket\n"
        "/jrs [name] - Jr work queue\n"
        "/tribal <topic> - Tribal knowledge\n"
    )
=======
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "Cherokee Chief Bot v3.0\n\n"
        "Commands:\n"
        "/ask <question> - Ask the Council\n"
        "/search <query> - Search tribe memory (semantic)\n"
        "/health - Cluster status\n"
        "/memory - Recent thermal memories\n"
        "/seed <content> - Write to memory\n"
        "/ticket <title> - Create Jr ticket\n"
        "/jrs [name] - Jr work queue\n"
        "/tribal <topic> - Tribal knowledge\n"
        "/kanban - View open kanban tickets\n"
    )
>>>>>>> REPLACE

Now add the /search command handler. Find the ask_command function and add the search handler right before it:

<<<<<<< SEARCH
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the Council a question"""
=======
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Semantic search across tribe thermal memory"""
    if not context.args:
        await update.message.reply_text("Usage: /search <query>\nExample: /search power outage recovery")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"Searching tribe memory for: {query}...")

    results = semantic_search(query, limit=5)
    response = format_for_telegram(results)
    await update.message.reply_text(response)


async def kanban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show open kanban tickets by priority"""
    try:
        with tribe.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, status, sacred_fire_priority, story_points
                FROM duyuktv_tickets
                WHERE status IN ('open', 'in_progress', 'blocked')
                ORDER BY sacred_fire_priority DESC NULLS LAST, id
                LIMIT 15
            """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No open tickets.")
            return

        lines = ["Open Kanban Tickets:\n"]
        for r in rows:
            sf = f"SF={r[3]}" if r[3] else ""
            sp = f"{r[4]}SP" if r[4] else ""
            lines.append(f"#{r[0]} [{r[2]}] {r[1][:60]} {sf} {sp}")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the Council a question"""
>>>>>>> REPLACE

Now register the new handlers. Find where handlers are added:

<<<<<<< SEARCH
    app.add_handler(CommandHandler("ask", ask_command))
=======
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("kanban", kanban_command))
>>>>>>> REPLACE

## Step 2: Upgrade derpatobot_claude.py with semantic context and env var token

File: `/ganuda/telegram_bot/derpatobot_claude.py`

<<<<<<< SEARCH
BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"
=======
BOT_TOKEN = os.environ.get('GANUDABOT_TOKEN', '7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug')
>>>>>>> REPLACE

<<<<<<< SEARCH
def get_thermal_context(query: str = "", limit: int = 5) -> str:
    """Fetch recent/relevant thermal memories for context."""
    try:
        with get_db() as conn:
            cur = conn.cursor()

            if query:
                # Search for relevant memories
                search_pattern = "%" + "%".join(query.split()[:5]) + "%"
=======
def get_thermal_context(query: str = "", limit: int = 5) -> str:
    """Fetch relevant thermal memories using semantic search."""
    try:
        from tribe_memory_search import semantic_search, format_for_llm
        if query:
            results = semantic_search(query, limit=limit, min_score=0.25)
            if results:
                return format_for_llm(results)

        # Fallback: recent hot memories if no query or no semantic results
        with get_db() as conn:
            cur = conn.cursor()
            search_pattern = "%" + "%".join(query.split()[:5]) + "%" if query else "%"
>>>>>>> REPLACE

## Manual Steps

After both files are patched:

```text
# Verify imports
cd /ganuda/telegram_bot
python3 -c "from tribe_memory_search import semantic_search; print('Module OK')"
python3 -c "from telegram_chief_v3 import *; print('v3 imports OK')"
```

Restart services (requires sudo on redfin):

```text
sudo systemctl restart derpatobot.service
sudo systemctl restart ganudabot.service
```
