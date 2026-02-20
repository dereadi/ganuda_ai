#!/usr/bin/env python3
"""
Derpatobot - Claude-Connected Cherokee AI Bot
Persistent context, thermal memory access, full reasoning capability.

For Seven Generations - Cherokee AI Federation
"""
import os
import logging
import asyncio
import anthropic
import psycopg2
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('GANUDABOT_TOKEN', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production', 
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Conversation history per user (in-memory for now)
conversations = {}

SYSTEM_PROMPT = """You are the Cherokee AI Federation's intelligent assistant, connected via Telegram.

ABOUT YOU:
- You have direct access to thermal memory (the federation's knowledge base)
- You know about the 6-node infrastructure: redfin (GPU), bluefin (DB), greenfin (daemons), sasass, sasass2, bmasass
- You can see recent thermal memories that will be injected into this conversation
- You remember the conversation history with this user

THERMAL MEMORY SYSTEM:
- thermal_memory_archive: PostgreSQL table storing all knowledge, events, decisions
- temperature_score: 0-100 (higher = hotter/more important)
- Recent memories are injected below for context

Be helpful, concise, and remember you're talking to a member of the Cherokee AI tribe.
When asked about thermal memory, system status, or recent work - refer to the injected context below.
"""


def get_db():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


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
            if query:
                search_pattern = "%" + "%".join(query.split()[:5]) + "%"
                cur.execute("""
                    SELECT LEFT(original_content, 400), temperature_score, created_at
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
            else:
                cur.execute("""
                    SELECT LEFT(original_content, 400), temperature_score, created_at
                    FROM thermal_memory_archive
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cur.fetchall()
            
            if not rows:
                return "\n[No relevant thermal memories found]\n"
            
            context = "\n--- THERMAL MEMORY CONTEXT ---\n"
            for content, temp, created in rows:
                date_str = created.strftime("%m/%d %H:%M") if created else "?"
                temp_label = "HOT" if temp and temp > 80 else "WARM" if temp and temp > 50 else "COOL"
                context += f"[{temp_label} {temp:.0f}C | {date_str}] {content}\n\n"
            context += "--- END THERMAL CONTEXT ---\n"
            
            return context
    except Exception as e:
        logger.error(f"Thermal context error: {e}")
        return f"\n[Thermal memory error: {e}]\n"


def get_system_status() -> str:
    """Get current federation status."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Get Jr agent status
            cur.execute("""
                SELECT agent_id, node_name, last_active
                FROM jr_agent_state
                ORDER BY last_active DESC
                LIMIT 5
            """)
            agents = cur.fetchall()
            
            # Get recent tasks
            cur.execute("""
                SELECT task_id, status, task_type
                FROM jr_task_announcements
                ORDER BY announced_at DESC
                LIMIT 3
            """)
            tasks = cur.fetchall()
            
            status = "\n--- FEDERATION STATUS ---\n"
            status += "Jr Agents:\n"
            for aid, node, active in agents:
                status += f"  - {aid} @ {node}\n"
            status += "\nRecent Tasks:\n"
            for tid, st, tt in tasks:
                status += f"  - {tid}: {st} ({tt})\n"
            status += "--- END STATUS ---\n"
            
            return status
    except Exception as e:
        return f"\n[Status error: {e}]\n"


async def query_claude(user_id: int, message: str) -> str:
    """Query Claude with conversation history and thermal context."""
    
    if not ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY not configured. Set it in environment."
    
    # Get or create conversation history
    if user_id not in conversations:
        conversations[user_id] = []
    
    history = conversations[user_id]
    
    # Get thermal context based on the query
    thermal_context = get_thermal_context(message, limit=5)
    
    # Check if asking about status
    if any(kw in message.lower() for kw in ['status', 'agents', 'nodes', 'jr']):
        thermal_context += get_system_status()
    
    # Build the full system prompt with context
    full_system = SYSTEM_PROMPT + thermal_context
    
    # Add user message to history
    history.append({"role": "user", "content": message})
    
    # Keep history manageable (last 20 messages)
    if len(history) > 20:
        history = history[-20:]
        conversations[user_id] = history
    
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=full_system,
            messages=history
        )
        
        assistant_message = response.content[0].text
        
        # Add assistant response to history
        history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return f"Error querying Claude: {e}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user.first_name or "Friend"
    await update.message.reply_text(
        f"Osiyo {user}! I'm the Cherokee AI Federation assistant.\n\n"
        "I have access to thermal memory and can help with:\n"
        "- Questions about our infrastructure\n"
        "- Recent work and decisions\n"
        "- Jr agent status\n"
        "- Anything in tribal knowledge\n\n"
        "Just ask me anything!"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history."""
    user_id = update.effective_user.id
    if user_id in conversations:
        conversations[user_id] = []
    await update.message.reply_text("Conversation history cleared. Fresh start!")


async def thermal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent thermal memories."""
    thermal_ctx = get_thermal_context("", limit=5)
    await update.message.reply_text(f"Recent Thermal Memories:\n{thermal_ctx}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages."""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    message = update.message.text
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Query Claude
    response = await query_claude(user_id, message)
    
    # Send response (split if too long)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)


def main():
    """Start the bot."""
    print("=" * 50)
    print("Derpatobot - Claude-Connected Cherokee AI")
    print("=" * 50)
    
    if not ANTHROPIC_API_KEY:
        print("WARNING: ANTHROPIC_API_KEY not set!")
        print("Set it with: export ANTHROPIC_API_KEY='your-key'")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("thermal", thermal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
