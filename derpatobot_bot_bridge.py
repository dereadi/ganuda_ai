#!/usr/bin/env python3
"""
🔥 Derpatobot Bridge for Bot-to-Bot Communication
Allows our bot to talk with Dr Joe's bot in Ganuda-BotComms
"""
import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Bot responses for inter-bot communication
BOT_RESPONSES = {
    "status": {
        "trading": "Active with 3 specialists",
        "portfolio": "$20,756 total value",
        "liquidity": "$10.62 USD available",
        "strategy": "Bollinger Band oscillations"
    },
    "capabilities": [
        "SAG Resource AI training",
        "Quantum Crawdad trading",
        "Cherokee Constitutional AI",
        "Portfolio monitoring"
    ]
}

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ALL messages - from humans and bots"""
    
    # Handle channel posts
    if update.channel_post:
        message = update.channel_post
        chat = message.chat
        sender = message.from_user
    # Handle group messages
    elif update.message:
        message = update.message
        chat = message.chat
        sender = message.from_user
    else:
        return
    
    text = message.text or ""
    
    # Log the message
    logger.info(f"📩 Message from {sender.first_name} (bot={sender.is_bot}): {text}")
    
    # Log to file for inter-bot communication
    with open('/tmp/bot_bridge_log.txt', 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {sender.first_name} (bot={sender.is_bot}): {text}\n")
    
    # Respond to bot queries (from Dr Joe's bot)
    if sender.is_bot and sender.username != 'derpatobot':
        logger.info(f"🤖 Bot-to-bot communication from {sender.username}")
        
        # Parse bot queries
        if "status" in text.lower():
            await message.reply_text(
                f"🔥 Cherokee Trading Status:\n"
                f"• Trading: {BOT_RESPONSES['status']['trading']}\n"
                f"• Portfolio: {BOT_RESPONSES['status']['portfolio']}\n"
                f"• Liquidity: {BOT_RESPONSES['status']['liquidity']}\n"
                f"• Strategy: {BOT_RESPONSES['status']['strategy']}"
            )
        
        elif "capabilities" in text.lower() or "what can you do" in text.lower():
            caps = "\n• ".join(BOT_RESPONSES['capabilities'])
            await message.reply_text(
                f"🔥 Cherokee Bot Capabilities:\n• {caps}"
            )
        
        elif "sag" in text.lower():
            await message.reply_text(
                "📚 SAG Resource AI: Intelligent resource allocation system\n"
                "• Connects to Productive.io API\n"
                "• Natural language queries\n"
                "• Automated scheduling\n"
                "• Training available: $500 for 2-hour session"
            )
        
        elif "trading" in text.lower() or "portfolio" in text.lower():
            await message.reply_text(
                f"💰 Current Portfolio: {BOT_RESPONSES['status']['portfolio']}\n"
                f"📊 Active Strategies: Bollinger Bands, Mean Reversion\n"
                f"🦞 Quantum Crawdads: 3 specialists running"
            )
        
        else:
            # Echo understanding
            await message.reply_text(
                f"🔥 Received from {sender.first_name}: '{text[:50]}...'\n"
                f"Processing query..."
            )
    
    # Respond to human messages
    elif not sender.is_bot:
        # Respond to mentions
        if '@derpatobot' in text.lower() or 'derpatobot' in text.lower():
            await message.reply_text(
                f"🔥 Cherokee Bot Bridge Active!\n"
                f"I heard you, {sender.first_name}!\n"
                f"Try /status or /help for commands"
            )
        
        elif text.startswith('/'):
            command = text.split()[0].lower()
            
            if command == '/status':
                await message.reply_text(
                    "🔥 System Status:\n"
                    "• Bot Bridge: Active\n"
                    "• Can see: ALL messages\n"
                    "• Bot-to-bot: Enabled\n"
                    "• Logging: Active"
                )
            
            elif command == '/test':
                await message.reply_text(
                    "🔥 Testing bot-to-bot communication...\n"
                    "@DrJoeBot - can you hear me?"
                )
            
            elif command == '/help':
                await message.reply_text(
                    "🔥 Bot Bridge Commands:\n"
                    "/status - Check bridge status\n"
                    "/test - Test bot communication\n"
                    "/logs - View recent bot messages\n"
                    "/help - This message"
                )
            
            elif command == '/logs':
                try:
                    with open('/tmp/bot_bridge_log.txt', 'r') as f:
                        lines = f.readlines()[-10:]  # Last 10 messages
                        log_text = "".join(lines) if lines else "No messages yet"
                        await message.reply_text(f"📜 Recent Messages:\n```\n{log_text}```", parse_mode='Markdown')
                except:
                    await message.reply_text("📜 No logs available yet")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text(
        "🔥 Cherokee Bot Bridge Active!\n\n"
        "This bot facilitates bot-to-bot communication.\n"
        "Both bots can now talk to each other!\n\n"
        "Use /help for commands"
    )

def main():
    """Start the bot"""
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    
    # Handle ALL messages (not just commands)
    app.add_handler(MessageHandler(filters.ALL, handle_all_messages))
    
    # Start polling
    logger.info("🔥 Bot Bridge starting... Listening for ALL messages!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()