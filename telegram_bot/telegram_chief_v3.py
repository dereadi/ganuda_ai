#!/usr/bin/env python3
"""
Cherokee Chief Telegram Bot v3.0
Fully Integrated Tribe Interface Edition

This bot interfaces with the 7-Specialist Council.
All decisions go through the Council. TPM has oversight.

Capabilities:
- Council queries and voting
- Thermal memory read/write
- Jr work queue management
- FARA vision integration
- Proactive notifications
"""

import os
import sys
import asyncio
import logging
import requests
import psycopg2
from datetime import datetime
from contextlib import contextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from tribal_knowledge import lookup_tribal_knowledge
from tribe_memory_search import semantic_search, format_for_telegram, format_for_llm

# Deep query infrastructure (Duplo persona switching)
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')
from research_dispatcher import ResearchDispatcher
from research_personas import build_research_query, PERSONAS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GATEWAY_URL = os.environ.get('GATEWAY_URL', 'http://localhost:8080')
API_KEY = os.environ.get('CHEROKEE_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')
GROUP_CHAT_ID = os.environ.get('TELEGRAM_GROUP_CHAT_ID')

# Database config
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Pending votes waiting for TPM
pending_votes = {}


class TribeInterface:
    """Interface to the 7-Specialist Council with full database access"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.db_config = DB_CONFIG

    @contextmanager
    def get_db(self):
        """Get database connection as context manager"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
        finally:
            if conn:
                conn.close()

    def query_council(self, question: str, include_responses: bool = False) -> dict:
        """Submit question to Council for vote"""
        try:
            response = requests.post(
                f"{GATEWAY_URL}/v1/council/vote",
                headers=self.headers,
                json={
                    "question": question,
                    "max_tokens": 200,
                    "include_responses": include_responses
                },
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_thermal_memories(self, limit: int = 5, min_temp: int = 50) -> list:
        """Read recent thermal memories"""
        try:
            with self.get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT LEFT(original_content, 200), temperature_score, created_at
                    FROM thermal_memory_archive
                    WHERE temperature_score >= %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (min_temp, limit))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Failed to read thermal memory: {e}")
            return []

    def seed_memory(self, content: str, temperature: int = 70) -> bool:
        """Write to thermal memory archive"""
        try:
            with self.get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO thermal_memory_archive (
                        memory_hash, original_content, current_stage, temperature_score
                    ) VALUES (
                        md5(%s || NOW()::text), %s,
                        CASE WHEN %s > 80 THEN 'HOT' WHEN %s > 50 THEN 'WARM' ELSE 'COOL' END,
                        %s
                    )
                """, (content, content, temperature, temperature, temperature))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to seed memory: {e}")
            return False

    def create_ticket(self, title: str, description: str, priority: int = 2, assigned_jr: str = None) -> dict:
        """Create a ticket in Jr work queue"""
        try:
            with self.get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO jr_work_queue (title, description, priority, assigned_jr, source)
                    VALUES (%s, %s, %s, %s, 'telegram')
                    RETURNING task_id, title
                """, (title, description, priority, assigned_jr))
                result = cur.fetchone()
                conn.commit()
                return {"task_id": result[0], "title": result[1]}
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            return {"error": str(e)}

    def get_jr_queue(self, jr_name: str = None) -> list:
        """Get Jr work queue status"""
        try:
            with self.get_db() as conn:
                cur = conn.cursor()
                if jr_name:
                    cur.execute("""
                        SELECT title, status, priority, assigned_jr
                        FROM jr_work_queue
                        WHERE assigned_jr ILIKE %s AND status IN ('pending', 'in_progress')
                        ORDER BY priority ASC LIMIT 10
                    """, (f'%{jr_name}%',))
                else:
                    cur.execute("""
                        SELECT title, status, priority, assigned_jr
                        FROM jr_work_queue
                        WHERE status IN ('pending', 'in_progress')
                        ORDER BY priority ASC LIMIT 10
                    """)
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Failed to get queue: {e}")
            return []

    def get_cluster_health(self) -> dict:
        """Get federation cluster health"""
        try:
            with self.get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT hostname, ip_address, online_status, last_seen
                    FROM hardware_inventory
                    WHERE hostname IN ('redfin', 'bluefin', 'greenfin', 'sasass', 'sasass2')
                """)
                nodes = cur.fetchall()
                return {
                    "nodes": [{"name": n[0], "ip": n[1], "online": n[2], "last_seen": str(n[3])} for n in nodes],
                    "total": len(nodes)
                }
        except Exception as e:
            return {"error": str(e)}


# Initialize tribe interface
tribe = TribeInterface()


# Command handlers
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
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, sacred_fire_priority, story_points
            FROM duyuktv_tickets
            WHERE status IN ('open', 'in_progress', 'blocked')
            ORDER BY sacred_fire_priority DESC NULLS LAST, id
            LIMIT 15
        """)
        rows = cur.fetchall()
        conn.close()

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
    if not context.args:
        await update.message.reply_text("Usage: /ask <your question>")
        return

    question = " ".join(context.args)
    await update.message.reply_text(f"Consulting the Council...")

    result = tribe.query_council(question, include_responses=True)

    if "error" in result:
        await update.message.reply_text(f"Error: {result['error']}")
        return

    response = f"Council Decision: {result.get('decision', 'No decision')}\n"
    response += f"Confidence: {result.get('confidence', 'N/A')}%\n"
    if result.get('concerns'):
        response += f"Concerns: {', '.join(result['concerns'])}"

    await update.message.reply_text(response)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show cluster health"""
    health = tribe.get_cluster_health()

    if "error" in health:
        await update.message.reply_text(f"Error: {health['error']}")
        return

    response = "Federation Cluster Status:\n\n"
    for node in health.get("nodes", []):
        status = "ONLINE" if node["online"] else "OFFLINE"
        response += f"{node['name']}: {status}\n"

    await update.message.reply_text(response)


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent thermal memories"""
    memories = tribe.get_thermal_memories(limit=5)

    if not memories:
        await update.message.reply_text("No recent memories found.")
        return

    response = "Recent Thermal Memories:\n\n"
    for mem in memories:
        content, temp, created = mem
        response += f"[{temp}°] {content[:100]}...\n\n"

    await update.message.reply_text(response)


async def seed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seed content to thermal memory"""
    if not context.args:
        await update.message.reply_text("Usage: /seed <content to remember>")
        return

    content = " ".join(context.args)
    success = tribe.seed_memory(content, temperature=75)

    if success:
        await update.message.reply_text(f"Memory seeded at 75°")
    else:
        await update.message.reply_text("Failed to seed memory.")


async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a Jr ticket"""
    if not context.args:
        await update.message.reply_text("Usage: /ticket <title> | <description>")
        return

    text = " ".join(context.args)
    parts = text.split("|")
    title = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else title

    result = tribe.create_ticket(title, description)

    if "error" in result:
        await update.message.reply_text(f"Error: {result['error']}")
    else:
        await update.message.reply_text(f"Ticket created: {result['task_id'][:8]}...")


async def jrs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Jr work queue"""
    jr_name = context.args[0] if context.args else None
    queue = tribe.get_jr_queue(jr_name)

    if not queue:
        await update.message.reply_text("No pending tasks in queue.")
        return

    response = "Jr Work Queue:\n\n"
    for task in queue:
        title, status, priority, assigned = task
        response += f"P{priority} [{status}] {title[:30]}... -> {assigned}\n"

    await update.message.reply_text(response)


async def tribal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Look up tribal knowledge"""
    if not context.args:
        await update.message.reply_text("Usage: /tribal <topic>")
        return

    topic = context.args[0].lower()
    knowledge = lookup_tribal_knowledge(topic)
    await update.message.reply_text(knowledge or f"No knowledge found for '{topic}'")


async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research command — deep query with Duplo persona switching"""
    if not context.args:
        persona_list = "\n".join(f"  `{k}` — {v.split(chr(10))[0][:60]}" for k, v in PERSONAS.items() if k != "default")
        await update.message.reply_text(
            "Usage: /research [persona] <question>\n\n"
            "Personas (Duplo blocks):\n"
            f"{persona_list}\n\n"
            "Examples:\n"
            "  /research How do I debug PostgreSQL timeouts?\n"
            "  /research vetassist What is the nexus letter requirement?\n"
            "  /research pharmassist Interaction between metformin and lisinopril?\n"
            "  /research legal Can an LLC be pierced for AI liability?\n\n"
            "Default persona: `telegram` (technical generalist)"
        )
        return

    # Check if first arg is a persona name
    first_arg = context.args[0].lower()
    if first_arg in PERSONAS:
        persona = first_arg
        question = " ".join(context.args[1:])
        if not question:
            await update.message.reply_text(f"Usage: /research {persona} <your question>")
            return
    else:
        persona = "telegram"
        question = " ".join(context.args)

    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    await update.message.reply_text(
        f"🔍 Starting deep research...\n\n"
        f"Q: {question[:100]}{'...' if len(question) > 100 else ''}\n"
        f"Persona: {persona}\n\n"
        f"Results in 3-5 minutes."
    )

    try:
        dispatcher = ResearchDispatcher()
        full_query = build_research_query(question, persona)

        job_id = dispatcher.queue_research(
            query=full_query,
            requester_type="telegram",
            requester_id=str(user.id),
            callback_type="telegram",
            callback_target=chat_id,
            max_steps=5
        )

        await update.message.reply_text(
            f"✅ Research queued: {job_id}\n\n"
            f"I'll notify you when complete."
        )

    except Exception as e:
        logger.error(f"Research error: {e}")
        await update.message.reply_text(f"❌ Research error: {str(e)}")


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /results command — check latest research results"""
    user = update.effective_user

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT job_id, LEFT(query, 80), status, result_summary, created_at
            FROM research_jobs
            WHERE requester_type = 'telegram' AND requester_id = %s
            ORDER BY created_at DESC LIMIT 3
        """, (str(user.id),))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("No research results found. Try /research <question>")
            return

        for job_id, query_preview, status, summary, created in rows:
            status_icon = "✅" if status == "completed" else "⏳" if status == "processing" else "📋"
            text = f"{status_icon} {job_id[:12]}\n{query_preview}\n"
            if summary:
                text += f"\n{summary[:500]}"
            await update.message.reply_text(text)

    except Exception as e:
        logger.error(f"Results error: {e}")
        await update.message.reply_text(f"❌ Error fetching results: {str(e)}")


async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remember command — capture a thought to thermal memory from anywhere.
    If the thought is unclear, asks a follow-up question before persisting."""
    user = update.effective_user
    if not context.args:
        await update.message.reply_text(
            "Usage: /remember <your thought>\n\n"
            "Example: /remember we should try Redis for the Layer2 hot cache before the LoRA work\n\n"
            "I'll save it to thermal memory. If anything's unclear, I'll ask before saving."
        )
        return

    thought = " ".join(context.args)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Ask the LLM if the thought is clear enough to be useful later
    try:
        clarify_response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq'),
                "messages": [
                    {"role": "system", "content": (
                        "You are a thought-capture assistant for the Cherokee AI Federation. "
                        "The user is capturing a thought on the go (walking, driving, away from computer). "
                        "Your job: determine if this thought has enough context to be useful when revisited later. "
                        "If it IS clear enough, respond with exactly: CLEAR\n"
                        "If it is NOT clear enough, respond with exactly: CLARIFY: <one short follow-up question>\n"
                        "Examples of unclear thoughts that need clarification:\n"
                        "- 'try the other approach' → CLARIFY: Which approach, and for which project?\n"
                        "- 'fix the thing on bluefin' → CLARIFY: Which service or config on bluefin?\n"
                        "Examples of clear thoughts:\n"
                        "- 'use Redis for Layer2 hot cache before starting LoRA work' → CLEAR\n"
                        "- 'speed detection should use optical flow instead of frame diff for the garage cam' → CLEAR\n"
                        "Be generous — if it's mostly clear, say CLEAR. Only ask if truly ambiguous."
                    )},
                    {"role": "user", "content": thought}
                ],
                "max_tokens": 100,
                "temperature": 0.3
            },
            timeout=30
        )
        llm_reply = clarify_response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Clarity check failed, saving anyway: {e}")
        llm_reply = "CLEAR"

    if llm_reply.startswith("CLARIFY:"):
        # Store the pending thought in context for follow-up
        context.user_data['pending_remember'] = thought
        follow_up = llm_reply.replace("CLARIFY:", "").strip()
        await update.message.reply_text(
            f"Before I save that — {follow_up}\n\n"
            f"Reply with the clarification and I'll save the full thought. "
            f"Or say /save to save it as-is."
        )
        return

    # CLEAR — persist to thermal memory
    await _persist_thought(update, user, thought, timestamp)


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /save — force-save a pending thought without clarification"""
    user = update.effective_user
    thought = context.user_data.get('pending_remember')
    if not thought:
        await update.message.reply_text("No pending thought to save. Use /remember <thought> first.")
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    del context.user_data['pending_remember']
    await _persist_thought(update, user, thought, timestamp)


async def _handle_remember_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text replies that clarify a pending /remember thought"""
    if 'pending_remember' not in context.user_data:
        return False  # Not a remember follow-up

    original = context.user_data.pop('pending_remember')
    clarification = update.message.text
    combined = f"{original} — CLARIFICATION: {clarification}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    await _persist_thought(update, update.effective_user, combined, timestamp)
    return True


async def _persist_thought(update, user, thought, timestamp):
    """Save a thought to thermal memory at 90 degrees"""
    import hashlib
    memory_content = (
        f"FLYING SQUIRREL THOUGHT CAPTURE ({timestamp})\n"
        f"Source: Telegram /remember (mobile)\n"
        f"User: {user.first_name} ({user.id})\n\n"
        f"{thought}"
    )
    memory_hash = hashlib.md5(f"remember-{user.id}-{timestamp}".encode()).hexdigest()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, memory_type, original_content, temperature_score, tags)
            VALUES (%s, 'thought_capture', %s, 90, ARRAY['mobile','thought-capture','flying-squirrel'])
            RETURNING id
        """, (memory_hash, memory_content))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(
            f"Saved to thermal memory (#{row[0]}, 90 deg).\n"
            f"It'll be there when you get back to the terminal."
        )
    except Exception as e:
        logger.error(f"Remember persist error: {e}")
        await update.message.reply_text(f"Failed to save: {e}")


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("kanban", kanban_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("seed", seed_command))
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("jrs", jrs_command))
    app.add_handler(CommandHandler("tribal", tribal_command))
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("results", results_command))
    app.add_handler(CommandHandler("remember", remember_command))
    app.add_handler(CommandHandler("save", save_command))

    # Message handler for /remember follow-up clarifications (must be after command handlers)
    async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route text messages — check for pending /remember follow-up first"""
        if await _handle_remember_followup(update, context):
            return
        # Fall through to existing message handling if any

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    print("Cherokee Chief Bot v3.1 starting — deep query personas + /remember active...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()