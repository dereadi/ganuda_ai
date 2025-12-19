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
import asyncio
import logging
import requests
import psycopg2
from datetime import datetime
from contextlib import contextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from tribal_knowledge import lookup_tribal_knowledge

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
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
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
        "/health - Cluster status\n"
        "/memory - Recent thermal memories\n"
        "/seed <content> - Write to memory\n"
        "/ticket <title> - Create Jr ticket\n"
        "/jrs [name] - Jr work queue\n"
        "/tribal <topic> - Tribal knowledge\n"
    )


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
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("seed", seed_command))
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("jrs", jrs_command))
    app.add_handler(CommandHandler("tribal", tribal_command))

    print("Cherokee Chief Bot v3.0 starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()