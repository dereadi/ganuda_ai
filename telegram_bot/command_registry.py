# Command handler registration for main()
def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    print("=" * 50)
    print("Cherokee Chief Telegram Bot v3.0")
    print("Full Tribe Integration Edition")
    print("=" * 50)

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))

    # Council commands
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("veto", veto))
    app.add_handler(CommandHandler("ask", ask_command))

    # Monitoring commands
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("concerns", concerns_command))

    # Memory commands
    app.add_handler(CommandHandler("remember", remember_command))
    app.add_handler(CommandHandler("seed", seed_command))

    # Ticket/Jr commands
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("jrs", jrs_command))

    # FARA commands
    app.add_handler(CommandHandler("look", look_command))
    app.add_handler(CommandHandler("fara", fara_command))

    # Callbacks and messages
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Commands registered:")
    print("  /start, /help, /status")
    print("  /pending, /approve, /veto, /ask")
    print("  /health, /concerns")
    print("  /remember, /seed")
    print("  /ticket, /jrs")
    print("  /look, /fara")
    print()
    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)