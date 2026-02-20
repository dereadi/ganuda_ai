# Jr Instruction: Derpatobot Resurrection — Research + Persona Switching

**Task ID:** DERPATOBOT-RESURRECT-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** #8486 (Duplo Phase 2 — Unified Channels & Tribal Research)
**Date:** February 9, 2026
**KB Reference:** KB-GATEWAY-LONGMAN-TWOWOLVES-DEPLOYMENT-FEB08-2026.md

## Background

The interactive Telegram bot (`@derpatobot`) died when `telegram_chief.py` was overwritten by the Governance Agent (drift detection daemon). The rebuilt `telegram_chief_v3.py` exists but is missing the `/research` command with persona switching, and has no systemd service running it.

This instruction resurrects the bot with research capabilities and deploys it as its own service alongside the governance agent.

## Edit 1: Add research imports to telegram_chief_v3.py

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

<<<<<<< SEARCH
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
=======
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

# Research infrastructure (Duplo persona switching)
sys.path.insert(0, '/ganuda/lib')
from research_dispatcher import ResearchDispatcher
from research_personas import build_research_query, PERSONAS
>>>>>>> REPLACE

## Edit 2: Add /research command handler with persona switching

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

<<<<<<< SEARCH
def main():
    """Start the bot"""
=======
async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research command — deep research with Duplo persona switching"""
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


def main():
    """Start the bot"""
>>>>>>> REPLACE

## Edit 3: Register /research and /results command handlers

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

<<<<<<< SEARCH
    app.add_handler(CommandHandler("tribal", tribal_command))

    print("Cherokee Chief Bot v3.0 starting...")
=======
    app.add_handler(CommandHandler("tribal", tribal_command))
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("results", results_command))

    print("Cherokee Chief Bot v3.1 starting — research personas active...")
>>>>>>> REPLACE

## Edit 4: Create systemd service for the interactive bot

Create `/ganuda/scripts/systemd/derpatobot.service`

```ini
[Unit]
Description=Cherokee AI Interactive Telegram Bot (@derpatobot)
After=network.target llm-gateway.service
Wants=llm-gateway.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/telegram_bot
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/home/dereadi/cherokee_venv/bin/python telegram_chief_v3.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Do NOT

- Do not modify `telegram_chief.py` — that is the governance agent, leave it alone
- Do not hardcode database passwords or API keys
- Do not hardcode the bot token — it comes from TELEGRAM_BOT_TOKEN env var in secrets.env
- Do not modify the governance agent systemd service (telegram-chief.service)
- Do not add executable bash blocks to this instruction

## Success Criteria

1. `telegram_chief_v3.py` passes Python syntax check
2. `/research` with no args shows usage with all persona names
3. `/research Does it make sense that jawas don't wear pants?` queues a job with `telegram` persona
4. `/research vetassist What is the nexus letter requirement?` queues with `vetassist` persona
5. `/research pharmassist Drug interaction check` queues with `pharmassist` persona
6. `/results` shows most recent research for the calling user
7. `derpatobot.service` file created at `/ganuda/scripts/systemd/derpatobot.service`
8. Service file uses `EnvironmentFile=/ganuda/config/secrets.env` for credentials

## Manual Steps After Jr Completes

TPM or Darrell must:

    sudo cp /ganuda/scripts/systemd/derpatobot.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now derpatobot.service
    sudo systemctl status derpatobot.service

Verify the bot responds in Telegram, then test:

    /research Does it make sense that jawas don't wear pants?
