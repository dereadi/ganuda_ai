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
    'host': os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Partner's Telegram user ID — only Partner can trigger council votes
PARTNER_USER_ID = int(os.environ.get('PARTNER_TELEGRAM_ID', '8025375307'))

# Add ganuda paths for imports
import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

# Conversation history per user (in-memory for now)
conversations = {}

SYSTEM_PROMPT = """You are the Stoneclad organism's Telegram interface — a functional gateway to a real production AI federation, not a roleplaying assistant.

IDENTITY: The organism is called Stoneclad (Nvya Unequa). The human is Partner (never "Chief" or "boss"). You are one interface to the organism, not the organism itself.

WHAT YOU HAVE:
- Thermal memory: 95K+ entries searchable via semantic search (injected below)
- Conversation history with this user
- Real-time access to council votes, concern evals, and cluster health

WHAT YOU DO NOT DO:
- NEVER roleplay council members. The real council has 13 voices (Spider, Coyote, Crawdad, Eagle Eye, Gecko, Turtle, Raven, Peace Chief + 5 outer) running on Qwen2.5-72B, Llama-3.3-70B, and Qwen3-30B across redfin and bmasass. You cannot simulate them.
- NEVER use governance theater — no fake "council fire crackling", no invented components like "War Chief (OpenAI-aspect)" or "Pi-geometry patterns"
- NEVER invent architecture that does not exist. If unsure, say so.
- NEVER use emojis in governance responses (breadcrumbs use only the bread emoji)
- If someone asks for a council vote, tell them you are routing it or say you cannot — do not fake one.

REAL ARCHITECTURE:
- 6 Linux nodes: redfin (RTX PRO 6000, local), bluefin (PostgreSQL, RTX 5070), greenfin (embedding, FreeIPA), owlfin/eaglefin (DMZ Caddy), bmasass (M4 Max, mobile)
- 2 Mac nodes: sasass, sasass2
- Services: vLLM:8000, LLM Gateway:8080, ConsultationRing:9400, VetAssist:8001/3000
- Governance: specialist_council.py (real council votes), concern_eval_engine.py (211+ persistent evals), z3_verifier.py (formal verification), production_manifest.yaml
- Observation: Fire Guard (2min), Medicine Woman, Elisi Observer, Safety Canary, Dawn Mist (6:15 AM)
- Memory: thermal_memory_archive (PostgreSQL), chirality_breadcrumbs (R2L/L2R signals between hands)

SPECIAL COMMANDS (detected in message text):
- "council vote on..." / "ask the council..." / "take this to council" → REAL council vote will be triggered
- "smoke test" / "health check" → cluster health check
- "breadcrumb:" or message starting with bread emoji → stored as L2R chirality breadcrumb
- "drift" / "confidence" → real vote statistics from database, not theater

TONE: Direct, concise, grounded in real data. Reference thermals by ID when relevant. State facts, not performances.

PARTNER is the tie-breaker and idea fairy. The council leads day-to-day operations. The organism works autonomously; Partner steers from the outside loop.
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


def run_council_vote_sync(question: str) -> str:
    """Actually call the real council. Not roleplay."""
    try:
        from specialist_council import council_vote
        result = council_vote(question, max_tokens=300, include_responses=False)
        response = f"COUNCIL VOTE #{result['audit_hash']}\n"
        response += f"Confidence: {result['confidence']}\n"
        response += f"Concerns: {', '.join(result.get('concerns', []))}\n\n"
        response += f"CONSENSUS:\n{result.get('consensus', 'No consensus')[:800]}\n\n"
        response += f"Recommendation: {result.get('recommendation', 'N/A')}"
        return response
    except Exception as e:
        logger.error(f"Council vote error: {e}")
        return f"Council vote failed: {e}"


def get_drift_stats() -> str:
    """Get real drift/confidence data, not theater."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT count(*), avg(confidence), min(confidence), max(confidence)
                FROM council_votes
                WHERE voted_at > now() - interval '24 hours'
            """)
            count, avg_conf, min_conf, max_conf = cur.fetchone()

            cur.execute("SELECT count(*) FROM council_concern_evals WHERE active = true")
            eval_count = cur.fetchone()[0]

            response = f"DRIFT ANALYSIS (real data):\n"
            response += f"Votes (24h): {count or 0}\n"
            response += f"Avg confidence: {avg_conf:.2f}\n" if avg_conf else "No votes in 24h\n"
            response += f"Range: {min_conf:.2f} - {max_conf:.2f}\n" if min_conf else ""
            response += f"Active concern evals: {eval_count}\n"
            if avg_conf and avg_conf < 0.4 and count and count > 3:
                response += "\nLow confidence is expected during heavy architectural debate."
                response += "\nThis is healthy disagreement, not drift."
            return response
    except Exception as e:
        return f"Drift stats error: {e}"


def store_breadcrumb(direction: str, content: str) -> str:
    """Store a chirality breadcrumb."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO chirality_breadcrumbs (direction, content, delivery_channel)
                VALUES (%s, %s, 'telegram')
            """, (direction, content))
            conn.commit()
            return "Breadcrumb stored."
    except Exception as e:
        return f"Breadcrumb error: {e}"


def get_pending_breadcrumbs() -> list:
    """Get undelivered R2L breadcrumbs."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, content FROM chirality_breadcrumbs
                WHERE direction = 'R2L' AND delivered = false
                ORDER BY created_at ASC LIMIT 3
            """)
            crumbs = cur.fetchall()
            for crumb_id, _ in crumbs:
                cur.execute("""
                    UPDATE chirality_breadcrumbs
                    SET delivered = true, delivered_at = now(), delivery_channel = 'telegram'
                    WHERE id = %s
                """, (crumb_id,))
            conn.commit()
            return crumbs
    except Exception:
        return []


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages with grounded routing."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    message = update.message.text
    msg_lower = message.lower()

    # Show typing indicator
    await update.message.chat.send_action("typing")

    # ── Route: Breadcrumb (L2R) ────────────────────────────────────
    if message.startswith('\U0001F35E') or msg_lower.startswith('breadcrumb:'):
        content = message.lstrip('\U0001F35E').lstrip().removeprefix('breadcrumb:').strip()
        if content:
            result = store_breadcrumb('L2R', content)
            await update.message.reply_text(f"\U0001F35E Stored. The right hand holds it.")
            return

    # Log user ID for first-time identification
    logger.info(f"Message from user_id={user_id} ({update.effective_user.first_name}): {message[:80]}")

    # ── Route: Council vote (Partner only) ─────────────────────────
    council_triggers = ['council vote on', 'ask the council', 'take this to the council',
                        'take this to council', 'let the council decide', 'council:']
    if any(trigger in msg_lower for trigger in council_triggers):
        if PARTNER_USER_ID and user_id != PARTNER_USER_ID:
            await update.message.reply_text("Council votes require Partner authorization.")
            return
        # Extract the question
        question = message
        for trigger in council_triggers:
            if trigger in msg_lower:
                idx = msg_lower.index(trigger) + len(trigger)
                question = message[idx:].strip() or message
                break
        await update.message.reply_text("Convening the council... (this takes ~60 seconds)")
        await update.message.chat.send_action("typing")
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_council_vote_sync, question)
        await update.message.reply_text(result[:4000])
        return

    # ── Route: Drift/confidence query ──────────────────────────────
    if any(kw in msg_lower for kw in ['drift', 'confidence', 'drift warning']):
        stats = get_drift_stats()
        await update.message.reply_text(stats)
        return

    # ── Route: Smoke test ──────────────────────────────────────────
    if any(kw in msg_lower for kw in ['smoke test', 'health check', 'owl pass']):
        await update.message.reply_text("Running smoke test...")
        try:
            import subprocess
            result = subprocess.run(
                ['/ganuda/venv/bin/python3', '/ganuda/scripts/smoke_test.py', '--quick'],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, 'PYTHONPATH': '/ganuda'}
            )
            output = result.stdout[-3000:] if result.stdout else result.stderr[-1000:]
            await update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Smoke test failed: {e}")
        return

    # ── Default: Query Claude with thermal context ─────────────────
    response = await query_claude(user_id, message)

    # Append any pending breadcrumbs
    crumbs = get_pending_breadcrumbs()
    if crumbs:
        response += "\n\n"
        for _, content in crumbs:
            response += f"\U0001F35E {content}\n"

    # Send response (split if too long)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)


async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document and photo attachments."""
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info(f"Attachment from user_id={user_id} ({update.effective_user.first_name})")
    await update.message.chat.send_action("typing")

    caption = update.message.caption or ""

    try:
        if update.message.document:
            file_obj = await update.message.document.get_file()
            filename = update.message.document.file_name or "attachment"
            mime = update.message.document.mime_type or "unknown"
        elif update.message.photo:
            file_obj = await update.message.photo[-1].get_file()
            filename = "photo.jpg"
            mime = "image/jpeg"
        else:
            await update.message.reply_text("Attachment type not supported yet.")
            return

        save_path = f"/tmp/ganuda_telegram_{user_id}_{filename}"
        await file_obj.download_to_drive(save_path)
        logger.info(f"Attachment saved: {save_path} ({mime})")

        # Read text-based files
        text_extensions = ['.txt', '.md', '.py', '.json', '.yaml', '.yml', '.csv', '.log', '.sh', '.conf']
        file_content = None
        if any(filename.endswith(ext) for ext in text_extensions) or 'text' in mime:
            try:
                with open(save_path, 'r', errors='replace') as f:
                    file_content = f.read(10000)
            except Exception:
                pass

        # Check for council vote trigger in caption
        cap_lower = caption.lower()
        council_triggers = ['council vote on', 'ask the council', 'take this to the council',
                            'take this to council', 'let the council decide', 'council:']
        if any(trigger in cap_lower for trigger in council_triggers):
            question = caption
            for trigger in council_triggers:
                if trigger in cap_lower:
                    idx = cap_lower.index(trigger) + len(trigger)
                    question = caption[idx:].strip() or caption
                    break
            if file_content:
                question += f"\n\nAttachment content ({filename}):\n{file_content[:3000]}"
            await update.message.reply_text("Convening the council with attachment... (~60 seconds)")
            await update.message.chat.send_action("typing")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_council_vote_sync, question)
            await update.message.reply_text(result[:4000])
            return

        # Normal processing
        if file_content:
            message_text = f"[Attachment: {filename}]\n\n{file_content[:5000]}"
            if caption:
                message_text = f"{caption}\n\n{message_text}"
            response = await query_claude(user_id, message_text)
        elif caption:
            response = await query_claude(user_id, f"[Attachment: {filename} ({mime})] {caption}")
        else:
            response = (f"Received: {filename} ({mime}). Saved to {save_path}. "
                       f"Send with a caption to tell me what to do, "
                       f"or caption with 'council vote on' to take it to the council.")

        crumbs = get_pending_breadcrumbs()
        if crumbs:
            response += "\n\n"
            for _, content in crumbs:
                response += f"\U0001F35E {content}\n"

        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await update.message.reply_text(response[i:i+4000])
        else:
            await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Attachment error: {e}")
        await update.message.reply_text(f"Error processing attachment: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages — placeholder for Whisper integration."""
    await update.message.reply_text(
        "Voice received but Whisper transcription not yet wired (VOICE-CLUSTER-001). "
        "Please type your message or send a text file for now."
    )


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
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_attachment))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
