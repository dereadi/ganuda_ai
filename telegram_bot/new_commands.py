# New commands to add to telegram_chief.py
# Add these functions before main()

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
        await update.message.reply_text(f"Unknown specialist: {specialist_input}\nTry: crawdad, gecko, turtle, eagle, spider, raven, peace")
        return

    question = " ".join(args[1:])
    thinking_msg = await update.message.reply_text(f"Asking {specialist.replace(_,  ).title()}...")

    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/specialist/{specialist}/query",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"question": question, "max_tokens": 500},
            timeout=30
        )

        if response.ok:
            data = response.json()
            result = f"**{specialist.replace(_,  ).title()}**:\n\n{data.get(response, No response)}"
            await thinking_msg.edit_text(result[:2000], parse_mode="Markdown")
        else:
            await thinking_msg.edit_text(f"Error: {response.status_code}")
    except Exception as e:
        await thinking_msg.edit_text(f"Error: {e}")


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick cluster health: /health"""
    try:
        # Check gateway health
        gw_response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        gw_status = "healthy" if gw_response.ok else "ERROR"

        # Get service_health from database
        tribe = TribeInterface()
        with tribe.get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT node_name, service_name, status
                FROM service_health
                WHERE last_check > NOW() - INTERVAL 10 minutes
                ORDER BY node_name, service_name
            """)
            rows = cur.fetchall()

        lines = ["**Cluster Health**\n"]
        lines.append(f"Gateway: {OK if gw_status == healthy else ERROR}")

        if rows:
            current_node = None
            for node, service, status in rows:
                if node != current_node:
                    lines.append(f"\n**{node}**")
                    current_node = node
                emoji = "OK" if status == "healthy" else "ERR"
                lines.append(f"  [{emoji}] {service}")
        else:
            lines.append("\nNo recent health checks")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Health check error: {e}")


async def concerns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Today's Council concerns: /concerns"""
    try:
        tribe = TribeInterface()
        with tribe.get_db() as conn:
            cur = conn.cursor()
            # Get concerns from recent council votes
            cur.execute("""
                SELECT 
                    jsonb_array_elements_text(specialist_responses->concerns) as concern,
                    COUNT(*) as cnt
                FROM council_votes
                WHERE voted_at > NOW() - INTERVAL 24 hours
                  AND specialist_responses IS NOT NULL
                GROUP BY concern
                ORDER BY cnt DESC
                LIMIT 10
            """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No concerns raised in the last 24 hours")
            return

        lines = ["**Today's Council Concerns**\n"]
        for concern, count in rows:
            lines.append(f"- {concern} ({count}x)")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
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
            # Simple keyword search for now (semantic search requires embeddings)
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
            await thinking_msg.edit_text(f"No memories found for: _{query}_", parse_mode="Markdown")
            return

        lines = [f"**Memories matching** _{query}_:\n"]
        for i, (content, temp, created) in enumerate(rows, 1):
            temp_emoji = "HOT" if temp > 80 else "WARM" if temp > 50 else "COOL"
            date_str = created.strftime("%m/%d") if created else "?"
            lines.append(f"{i}. [{temp_emoji}] [{date_str}]")
            lines.append(f"   _{content[:150]}..._\n")

        await thinking_msg.edit_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await thinking_msg.edit_text(f"Memory search error: {e}")
