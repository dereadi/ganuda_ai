#!/usr/bin/env python3
"""
Cherokee Chief Telegram Bot v2.0
Tribe Interface Edition

This bot is a thin interface to the 7-Specialist Council.
All decisions go through the Council. TPM has oversight.
"""

import os
import asyncio
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from tribal_knowledge import lookup_tribal_knowledge
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GATEWAY_URL = "http://localhost:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Pending votes waiting for TPM
pending_votes = {}


class TribeInterface:
    """Interface to the 7-Specialist Council"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

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
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_pending_votes(self) -> list:
        """Get votes pending TPM decision"""
        try:
            response = requests.get(
                f"{GATEWAY_URL}/v1/council/pending",
                headers=self.headers,
                timeout=10
            )
            return response.json().get("pending_votes", [])
        except:
            return []

    def cast_tpm_vote(self, audit_hash: str, vote: str, comment: str = None) -> dict:
        """Cast TPM vote on pending council decision"""
        try:
            url = f"{GATEWAY_URL}/v1/council/vote/{audit_hash}/tpm"
            params = {"vote": vote}
            if comment:
                params["comment"] = comment
            response = requests.post(url, headers=self.headers, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_vote_details(self, audit_hash: str) -> dict:
        """Get full details of a council vote"""
        try:
            response = requests.get(
                f"{GATEWAY_URL}/v1/council/vote/{audit_hash}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def check_health(self) -> dict:
        """Quick health check"""
        try:
            response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def query_specialist(self, specialist_id: str, question: str) -> dict:
        """Query a single specialist directly (no full council vote)"""
        try:
            response = requests.post(
                f"{GATEWAY_URL}/v1/specialist/{specialist_id}/query",
                headers=self.headers,
                json={"question": question, "max_tokens": 300},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def classify_request(message: str) -> dict:
    """Classify user request type"""
    message_lower = message.lower()

    destructive = ['delete', 'remove', 'drop', 'truncate', 'destroy', 'wipe', 'clear']
    if any(k in message_lower for k in destructive):
        return {"type": "destructive", "tpm_wait": True, "timeout": 300, "confirm": True}

    actions = ['restart', 'start', 'stop', 'deploy', 'install', 'update', 'upgrade', 'run', 'execute']
    if any(k in message_lower for k in actions):
        return {"type": "action", "tpm_wait": True, "timeout": 300}

    critical = ['urgent', 'emergency', 'critical', 'down', 'crashed', 'failed', 'error']
    if any(k in message_lower for k in critical):
        return {"type": "critical", "tpm_wait": True, "timeout": 60}

    # Diagnostic queries - route to Eagle Eye (IT Jr)
    diagnostic = ['check', 'status', 'health', 'disk', 'memory', 'cpu', 'logs', 'show', 'list',
                  'nodes', 'ok', 'online', 'running', 'servers', 'cluster', 'alive', 'ping']
    if any(k in message_lower for k in diagnostic):
        return {"type": "diagnostic", "tpm_wait": False, "route_to": "eagle_eye"}

    return {"type": "query", "tpm_wait": False}


def format_council_response(result: dict, classification: dict) -> str:
    """Format council response for Telegram"""
    if "error" in result:
        return f"Error: {result['error']}"

    # Build response
    lines = []

    # Recommendation with emoji
    rec = result.get("recommendation", "")
    if "PROCEED:" in rec:
        lines.append(f"[OK] {rec}")
    elif "CAUTION" in rec:
        lines.append(f"[WARN] {rec}")
    elif "REVIEW" in rec:
        lines.append(f"[STOP] {rec}")
    else:
        lines.append(rec)

    # Confidence
    conf = result.get("confidence", 0)
    lines.append(f"Confidence: {conf:.0%}")

    # Concerns
    concerns = result.get("concerns", [])
    if concerns:
        lines.append(f"\nConcerns ({len(concerns)}):")
        for c in concerns[:3]:
            lines.append(f"  - {c}")

    # Consensus (truncated)
    consensus = result.get("consensus", "")
    if consensus:
        # Clean up thinking tags
        if "</think>" in consensus:
            consensus = consensus.split("</think>")[-1].strip()
        # Strip LLM reasoning - look for common patterns
        import re
        # Pattern: reasoning that ends with incomplete sentence or ellipsis
        # Remove everything before the actual answer
        reasoning_patterns = [
            r"^Okay,.*?(?=\n\n[A-Z]|$)",  # Okay, ... until paragraph with capital
            r"^Let me.*?(?=\n\n[A-Z]|$)",
            r"^First,.*?(?=\n\n[A-Z]|$)",
            r"^I need to.*?(?=\n\n[A-Z]|$)",
            r"^The user.*?(?=\n\n[A-Z]|$)",
            r"^Hmm,.*?(?=\n\n[A-Z]|$)",
            r"^So,.*?(?=\n\n[A-Z]|$)",
        ]
        for pattern in reasoning_patterns:
            match = re.match(pattern, consensus, re.DOTALL)
            if match:
                consensus = consensus[match.end():].strip()
                break
        # Also strip if it contains reasoning indicators mid-text
        if "Hmm," in consensus or "let's see" in consensus.lower():
            # Find where actual content starts (after reasoning block)
            lines_list = consensus.split("\n\n")
            # Keep only paragraphs that don't look like reasoning
            clean_lines = [l for l in lines_list if not any(
                l.strip().startswith(p) for p in ["Okay", "Let me", "Hmm", "The user", "I need"]
            )]
            if clean_lines:
                consensus = "\n\n".join(clean_lines)
        if len(consensus) > 2000:
            consensus = consensus[:500] + "..."
        lines.append(f"\n{consensus}")

    # TPM status
    tpm_vote = result.get("tpm_vote", "")
    if tpm_vote == "pending":
        lines.append(f"\n[PENDING] Awaiting TPM approval")
        lines.append(f"Track: {result.get('audit_hash', 'N/A')}")

    return "\n".join(lines)


# Telegram Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"Welcome to Cherokee AI, {user.first_name}!\n\n"
        "I'm your interface to the 7-Specialist Council.\n\n"
        "Commands:\n"
        "/status - Cluster health\n"
        "/pending - View pending approvals\n"
        "/approve <hash> - Approve a vote\n"
        "/veto <hash> <reason> - Veto a vote\n"
        "/help - More info\n\n"
        "Or just ask me anything!"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    tribe = TribeInterface()
    health = tribe.check_health()

    if health.get("status") == "healthy":
        components = health.get('components', {})
        await update.message.reply_text(
            "Cherokee AI Cluster Status\n\n"
            f"Gateway: {components.get('vllm', 'unknown')}\n"
            f"Database: {components.get('database', 'unknown')}\n"
            f"Council: {components.get('council', 'unknown')}\n"
            f"TPM Vote: {components.get('tpm_vote', 'unknown')}\n"
            f"Latency: {health.get('latency_ms', '?')}ms"
        )
    else:
        await update.message.reply_text(f"Cluster status: {health.get('status', 'unknown')}\n{health}")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pending command - show votes awaiting TPM"""
    tribe = TribeInterface()
    votes = tribe.get_pending_votes()

    if not votes:
        await update.message.reply_text("No pending votes awaiting approval.")
        return

    lines = [f"{len(votes)} Pending Vote(s)\n"]
    for v in votes[:5]:
        lines.append(f"Hash: {v['audit_hash']}")
        lines.append(f"   {v['question'][:60]}...")
        lines.append(f"   Rec: {v['recommendation']}")
        lines.append(f"   Conf: {v['confidence']:.0%}\n")

    lines.append("\nUse /approve <hash> or /veto <hash> <reason>")
    await update.message.reply_text("\n".join(lines))


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve command"""
    if not context.args:
        await update.message.reply_text("Usage: /approve <audit_hash>")
        return

    audit_hash = context.args[0]
    comment = " ".join(context.args[1:]) if len(context.args) > 1 else "Approved via Telegram"

    tribe = TribeInterface()
    result = tribe.cast_tpm_vote(audit_hash, "approve", comment)

    if result.get("finalized"):
        await update.message.reply_text(f"Vote {audit_hash} approved!")
    else:
        await update.message.reply_text(f"Error: {result.get('error', result)}")


async def veto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /veto command"""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /veto <audit_hash> <reason>")
        return

    audit_hash = context.args[0]
    reason = " ".join(context.args[1:])

    tribe = TribeInterface()
    result = tribe.cast_tpm_vote(audit_hash, "veto", reason)

    if result.get("finalized"):
        await update.message.reply_text(f"Vote {audit_hash} vetoed.\nReason: {reason}")
    else:
        await update.message.reply_text(f"Error: {result.get('error', result)}")


def format_specialist_response(result: dict) -> str:
    """Format single specialist response for Telegram"""
    if "error" in result:
        return f"Error: {result['error']}"

    specialist = result.get("specialist", "Unknown")
    role = result.get("role", "")
    response = result.get("response", "No response")

    # Clean thinking tags
    if "</think>" in response:
        response = response.split("</think>")[-1].strip()

    # Truncate if too long
    if len(response) > 1000:
        response = response[:1000] + "..."

    return f"[{specialist} - {role}]\n\n{response}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages - route appropriately"""
    user = update.effective_user
    message = update.message.text

    # Check tribal knowledge first - instant answers for common questions
    tribal_answer = lookup_tribal_knowledge(message)
    if tribal_answer:
        await update.message.reply_text(f"📚 Tribal Knowledge\n\n{tribal_answer}")
        return
        return

    # Classify request
    classification = classify_request(message)
    tribe = TribeInterface()

    # Route diagnostics directly to Eagle Eye (IT Jr) - no Council vote needed
    if classification["type"] == "diagnostic":
        thinking_msg = await update.message.reply_text("Asking Eagle Eye (IT Jr)...")
        result = tribe.query_specialist("eagle_eye", message)
        response = format_specialist_response(result)
        try:
            await thinking_msg.edit_text(response)
        except:
            await update.message.reply_text(response)
        return

    # For actions/decisions, use full Council
    thinking_msg = await update.message.reply_text("Consulting the Council... (this may take 30-60 seconds)")

    # Build council question with context
    question = f"Telegram user {user.first_name} asks: {message}"

    if classification["type"] == "destructive":
        question += "\n\n[WARNING] This is a DESTRUCTIVE action request. Evaluate carefully."
    elif classification["type"] == "critical":
        question += "\n\n[CRITICAL] This is marked CRITICAL/URGENT."

    result = tribe.query_council(question)
    response = format_council_response(result, classification)

    try:
        await thinking_msg.edit_text(response)
    except:
        await update.message.reply_text(response)

    # If action needs TPM approval, store for tracking
    if classification.get("tpm_wait") and result.get("audit_hash"):
        pending_votes[result["audit_hash"]] = {
            "user_id": user.id,
            "chat_id": update.effective_chat.id,
            "question": message,
            "timestamp": datetime.now()
        }


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "Cherokee AI - Tribe Interface\n\n"
        "I route your requests to the 7-Specialist Council:\n"
        "- Crawdad - Security\n"
        "- Gecko - Technical\n"
        "- Turtle - Seven Generations\n"
        "- Eagle Eye - Monitoring\n"
        "- Spider - Integration\n"
        "- Peace Chief - Consensus\n"
        "- Raven - Strategy\n\n"
        "Commands:\n"
        "/status - Check cluster health\n"
        "/pending - View pending approvals\n"
        "/approve <hash> - Approve a decision\n"
        "/veto <hash> <reason> - Veto a decision\n\n"
        "Ask anything:\n"
        "- 'What's the database status?'\n"
        "- 'Check disk space on bluefin'\n"
        "- 'Restart the gateway' (needs approval)\n\n"
        "The TPM receives notifications for important decisions."
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data
    tribe = TribeInterface()

    if data.startswith("approve_"):
        audit_hash = data.replace("approve_", "")
        result = tribe.cast_tpm_vote(audit_hash, "approve", "Approved via Telegram button")
        await query.edit_message_text(f"Approved: {audit_hash}")

    elif data.startswith("veto_"):
        audit_hash = data.replace("veto_", "")
        await query.edit_message_text(f"Reply with veto reason for {audit_hash}:")
        context.user_data["pending_veto"] = audit_hash

    elif data.startswith("details_"):
        audit_hash = data.replace("details_", "")
        details = tribe.get_vote_details(audit_hash)
        await query.message.reply_text(f"Vote Details:\n{details}")



# Specialist aliases for /ask command
SPECIALIST_ALIASES = {
    "crawdad": "crawdad", "security": "crawdad", "sec": "crawdad",
    "gecko": "gecko", "tech": "gecko", "performance": "gecko", "perf": "gecko",
    "turtle": "turtle", "wisdom": "turtle", "7gen": "turtle",
    "eagle": "eagle_eye", "eagle_eye": "eagle_eye", "monitor": "eagle_eye", "eye": "eagle_eye",
    "spider": "spider", "integration": "spider", "connect": "spider",
    "raven": "raven", "strategy": "raven", "plan": "raven",
    "peace": "peace_chief", "chief": "peace_chief", "consensus": "peace_chief"
}


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask a specific specialist: /ask <specialist> <question>"""
    args = context.args
    if len(args) < 2:
        specialists = "crawdad, gecko, turtle, eagle, spider, raven, peace"
        await update.message.reply_text(f"Usage: /ask <specialist> <question>\nSpecialists: {specialists}")
        return

    specialist_input = args[0].lower()
    specialist = SPECIALIST_ALIASES.get(specialist_input)

    if not specialist:
        await update.message.reply_text(f"Unknown specialist: {specialist_input}")
        return

    question = " ".join(args[1:])
    thinking_msg = await update.message.reply_text(f"Asking {specialist.replace('_', ' ').title()}...")

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/specialist/{specialist}/query",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"question": question, "max_tokens": 500},
            timeout=30
        )

        if response.ok:
            data = response.json()
            result = f"{specialist.replace('_', ' ').title()}:\n\n{data.get('response', 'No response')}"
            await thinking_msg.edit_text(result[:2000])
        else:
            await thinking_msg.edit_text(f"Error: {response.status_code}")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick cluster health: /health"""
    try:
        gw_response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        gw_status = "OK" if gw_response.ok else "ERROR"

        tribe = TribeInterface()
        with tribe.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT node_name, service_name, status
                FROM service_health
                WHERE last_check > NOW() - INTERVAL '10 minutes'
                ORDER BY node_name, service_name
            """)
            rows = cur.fetchall()

        lines = ["Cluster Health\n"]
        lines.append(f"Gateway: {gw_status}")

        if rows:
            current_node = None
            for node, service, status in rows:
                if node != current_node:
                    lines.append(f"\n{node}:")
                    current_node = node
                emoji = "OK" if status == "healthy" else "ERR"
                lines.append(f"  [{emoji}] {service}")
        else:
            lines.append("\nNo recent health checks")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Health check error: {e}")


async def concerns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Today's Council concerns: /concerns"""
    try:
        tribe = TribeInterface()
        with tribe.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT recommendation, concern_count, voted_at
                FROM council_votes
                WHERE voted_at > NOW() - INTERVAL '24 hours'
                  AND concern_count > 0
                ORDER BY voted_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No concerns raised in the last 24 hours")
            return

        lines = ["Today's Council Concerns:\n"]
        for rec, count, voted in rows:
            time_str = voted.strftime("%H:%M") if voted else "?"
            lines.append(f"[{time_str}] {count} concern(s): {rec[:50]}")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search thermal memory: /remember <query>"""
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /remember <search query>")
        return

    thinking_msg = await update.message.reply_text("Searching tribal memory...")

    try:
        tribe = TribeInterface()
        with tribe.get_db() as conn:
            cur = conn.cursor()
            search_pattern = "%" + "%".join(query.split()) + "%"
            cur.execute("""
                SELECT LEFT(original_content, 200), temperature_score, created_at
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT 5
            """, (search_pattern,))
            rows = cur.fetchall()

        if not rows:
            await thinking_msg.edit_text(f"No memories found for: {query}")
            return

        lines = [f"Memories matching '{query}':\n"]
        for i, (content, temp, created) in enumerate(rows, 1):
            temp_label = "HOT" if temp and temp > 80 else "WARM" if temp and temp > 50 else "COOL"
            date_str = created.strftime("%m/%d") if created else "?"
            lines.append(f"{i}. [{temp_label}] [{date_str}]")
            lines.append(f"   {content[:150]}...\n")

        await thinking_msg.edit_text("\n".join(lines))
    except Exception as e:
        await thinking_msg.edit_text(f"Memory search error: {e}")



async def look_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Visual analysis of sasass screen: /look [question]"""
    question = " ".join(context.args) if context.args else "What do you see on this screen?"
    safe_question = question.replace("'", "'\"'\"'")    
    thinking_msg = await update.message.reply_text("Looking at sasass screen (~30 sec)...")
    
    try:
        cmd = f"ssh dereadi@192.168.132.241 \"python3 /Users/Shared/ganuda/scripts/fara_look.py '{safe_question}'\""
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        
        output = stdout.decode()
        if "FARA Response:" in output:
            response = output.split("FARA Response:")[-1].strip()
            response = response.replace("=" * 60, "").strip()
            await thinking_msg.edit_text(f"FARA: {response[:3000]}")
        else:
            await thinking_msg.edit_text(f"FARA output: {output[-1000:]}")
            
    except asyncio.TimeoutError:
        await thinking_msg.edit_text("FARA timed out - model loading takes ~30 seconds")
    except Exception as e:
        await thinking_msg.edit_text(f"FARA error: {str(e)}")


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    print("=" * 50)
    print("Cherokee Chief Telegram Bot v2.0")
    print("Tribe Interface Edition")
    print("=" * 50)

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("veto", veto))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("concerns", concerns_command))
    app.add_handler(CommandHandler("remember", remember_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("look", look_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
