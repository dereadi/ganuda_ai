#!/usr/bin/env python3
"""
Derpatobot configured for Ganuda-BotComms channel
"""
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Channel info
GANUDA_CHANNEL = "Ganuda-BotComms"

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle posts in Ganuda-BotComms channel"""
    channel_post = update.channel_post
    
    if channel_post:
        channel_name = channel_post.chat.title
        channel_id = channel_post.chat.id
        text = channel_post.text or "No text"
        
        logger.info(f"📢 GANUDA CHANNEL POST from {channel_name}: {text}")
        
        # Log to file
        with open('/tmp/ganuda_channel_messages.txt', 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {channel_name} (ID: {channel_id}): {text}\n")
        
        print(f"🔥 GANUDA-BOTCOMMS MESSAGE RECEIVED!")
        print(f"   Channel: {channel_name}")
        print(f"   Channel ID: {channel_id}")
        print(f"   Message: {text}")
        
        # Process special commands for Ganuda
        if text.lower().startswith('/status'):
            await channel_post.reply_text(
                "🔥 Cherokee Trading Council Status:\n"
                "• BTC: Following middle band up\n"
                "• ETH: Breakout above $4,300\n"
                "• XRP: Oscillating with BTC/ETH\n"
                "• Strategy: Dual - Oscillations + HODL"
            )
        elif text.lower().startswith('/portfolio'):
            await channel_post.reply_text(
                "💼 Portfolio Status:\n"
                "• Liquidity: $10.62 USD\n"
                "• Specialists: 3 active\n"
                "• Mode: Bollinger Band oscillations"
            )
        elif text.lower() == 'hello' or text.lower() == 'hi':
            await channel_post.reply_text(
                f"🔥 Hello from Cherokee Trading Council!\n"
                f"Ganuda-BotComms channel connected!\n"
                f"Sacred Fire burns eternal!"
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular group/private messages"""
    if update.message:
        chat_type = update.message.chat.type
        chat_name = update.message.chat.title or update.message.chat.username or "Private"
        text = update.message.text
        from_user = update.message.from_user.username or "Unknown"
        
        logger.info(f"💬 MESSAGE from @{from_user} in {chat_name} ({chat_type}): {text}")
        
        print(f"💬 REGULAR MESSAGE!")
        print(f"   From: @{from_user}")
        print(f"   Chat: {chat_name}")
        print(f"   Text: {text}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        "🔥 Cherokee Trading Council Bot Active!\n"
        "Monitoring Ganuda-BotComms channel!"
    )

def main():
    """Run the bot configured for Ganuda-BotComms"""
    print("🔥 Starting Derpatobot for GANUDA-BOTCOMMS Channel!")
    print("=" * 60)
    print("Bot Configuration:")
    print(f"  • Channel: {GANUDA_CHANNEL}")
    print(f"  • Bot: @derpatobot")
    print(f"  • Status: Listening for messages...")
    print("")
    print("Channel Commands:")
    print("  /status - Trading status")
    print("  /portfolio - Portfolio check")
    print("  hello/hi - Test connection")
    print("=" * 60)
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    
    # Handle regular messages
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Handle channel posts specifically
    application.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST,
        handle_channel_post
    ))
    
    print("🚀 Bot starting... Monitoring Ganuda-BotComms!")
    print("")
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()