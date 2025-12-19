async def jrs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Jr work queue: /jrs [jr_name]"""
    jr_filter = context.args[0].lower() if context.args else None

    tribe = TribeInterface()
    try:
        with tribe.get_db() as conn:
            cur = conn.cursor()
            if jr_filter:
                assigned_jr = JR_ASSIGNMENTS.get(jr_filter, f"%{jr_filter}%")
                cur.execute("""
                    SELECT task_id, title, priority, status, assigned_jr
                    FROM jr_work_queue
                    WHERE assigned_jr ILIKE %s
                      AND status NOT IN ('completed', 'cancelled')
                    ORDER BY priority, created_at
                    LIMIT 10
                """, (assigned_jr if "%" in assigned_jr else f"%{assigned_jr}%",))
            else:
                cur.execute("""
                    SELECT task_id, title, priority, status, assigned_jr
                    FROM jr_work_queue
                    WHERE status NOT IN ('completed', 'cancelled')
                    ORDER BY priority, created_at
                    LIMIT 15
                """)
            rows = cur.fetchall()

        if not rows:
            await update.message.reply_text("No pending Jr tasks")
            return

        lines = ["Jr Work Queue:\n"]
        for task_id, title, priority, status, jr in rows:
            p_label = ["", "!", "!!", "!!!"][min(priority, 3)]
            s_emoji = {"pending": "...", "in_progress": ">>", "blocked": "XX"}.get(status, "?")
            jr_short = jr.split()[0] if jr else "?"
            lines.append(f"[{p_label}][{s_emoji}] {jr_short}: {title[:40]}")

        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")