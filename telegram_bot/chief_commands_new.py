# New commands for Chief - December 21, 2025
# Add these to telegram_chief.py

async def hot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hottest memories: /hot"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT memory_hash, LEFT(original_content, 150) as content, 
                       temperature_score, created_at
                FROM thermal_memory_archive
                ORDER BY temperature_score DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
        
        if not rows:
            await update.message.reply_text("No memories found.")
            return
        
        msg = "🔥 **Hottest Tribal Memories**\n\n"
        for hash, content, temp, created in rows:
            date_str = created.strftime("%m/%d") if created else "?"
            temp_emoji = "🔥" if temp >= 90 else "🌡️" if temp >= 50 else "❄️"
            msg += f"{temp_emoji} [{temp:.0f}°] {content[:100]}...\n"
            msg += f"   _({date_str})_\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def thermal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain thermal memory: /thermal"""
    explanation = """🌡️ **What is Thermal Memory?**

Thermal memory is our tribe's collective long-term memory.

**Temperature = Importance:**
🔥 Hot (90-100): Critical knowledge, used often
🌡️ Warm (50-89): Important, referenced regularly  
❄️ Cool (10-49): Background knowledge
🧊 Cold (<10): Fading, rarely accessed

**How it works:**
• When we use a memory → it heats up
• Unused memories slowly cool down
• Hottest memories guide our decisions

**Like oral tradition:**
Important stories stay alive when told often.
Forgotten tales fade over generations.

Use /hot to see our hottest memories
Use /remember <topic> to search"""
    
    await update.message.reply_text(explanation, parse_mode="Markdown")


async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create ticket: /ticket <title> | <description>"""
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /ticket Bug in gateway | The API returns 500 errors")
        return
    
    parts = text.split("|", 1)
    title = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else "Created via Telegram by Chief"
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO duyuktv_tickets (title, description, tribal_agent, status, priority, created_at)
                VALUES (%s, %s, 'chief', 'open', 'normal', NOW())
                RETURNING id
            """, (title, description))
            ticket_id = cur.fetchone()[0]
            conn.commit()
        
        await update.message.reply_text(f"✅ Ticket #{ticket_id} created: {title}")
    except Exception as e:
        await update.message.reply_text(f"Error creating ticket: {e}")


async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Chief's tickets: /mytickets"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, status, priority, created_at
                FROM duyuktv_tickets
                WHERE tribal_agent = 'chief' OR assigned_to = 'chief'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
        
        if not rows:
            await update.message.reply_text("No tickets found.")
            return
        
        msg = "📋 **Your Tickets**\n\n"
        for id, title, status, priority, created in rows:
            status_emoji = "✅" if status == "closed" else "🔄" if status == "in_progress" else "📝"
            msg += f"{status_emoji} #{id}: {title}\n"
            msg += f"   Status: {status} | Priority: {priority}\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def tribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tribe status: /tribe"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Get Jr agents
            cur.execute("""
                SELECT agent_id, node_name, specialization, tasks_completed, 
                       last_active, success_rate
                FROM jr_agent_state
                ORDER BY last_active DESC
                LIMIT 10
            """)
            jrs = cur.fetchall()
        
        msg = "👥 **Tribe Status**\n\n"
        msg += "**7 Specialists (Always Active):**\n"
        msg += "🦎 Gecko - Technical\n"
        msg += "🦀 Crawdad - Security\n" 
        msg += "🐢 Turtle - Seven Generations\n"
        msg += "🦅 Eagle Eye - Monitoring\n"
        msg += "🕷️ Spider - Integration\n"
        msg += "☮️ Peace Chief - Consensus\n"
        msg += "🐦‍⬛ Raven - Strategy\n\n"
        
        msg += "**Jr Agents:**\n"
        for agent_id, node, spec, tasks, last_active, rate in jrs:
            active = "🟢" if last_active and (datetime.now() - last_active).days < 1 else "🟡"
            msg += f"{active} {agent_id} @ {node}\n"
            msg += f"   Tasks: {tasks} | Success: {rate*100:.0f}%\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Add to main():
#     app.add_handler(CommandHandler("hot", hot_command))
#     app.add_handler(CommandHandler("thermal", thermal_command))  
#     app.add_handler(CommandHandler("ticket", ticket_command))
#     app.add_handler(CommandHandler("mytickets", mytickets_command))
#     app.add_handler(CommandHandler("tribe", tribe_command))
