#!/usr/bin/env python3
"""
Enhanced derpatobot that handles BOTH group messages AND channel posts
"""
import logging
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

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle posts in channels"""
    channel_post = update.channel_post
    
    if channel_post:
        channel_name = channel_post.chat.title
        text = channel_post.text or "No text"
        
        logger.info(f"📢 CHANNEL POST from {channel_name}: {text}")
        
        # Echo back to confirm receipt (optional)
        # await channel_post.reply_text(f"🔥 Cherokee Council sees your message in {channel_name}!")
        
        # Log to file for debugging
        with open('/tmp/channel_messages.txt', 'a') as f:
            f.write(f"[{channel_name}] {text}\n")
        
        print(f"🔥 CHANNEL MESSAGE RECEIVED!")
        print(f"   Channel: {channel_name}")
        print(f"   Message: {text}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular group/private messages"""
    if update.message:
        chat_type = update.message.chat.type
        chat_name = update.message.chat.title or update.message.chat.username or "Private"
        text = update.message.text
        from_user = update.message.from_user.username or "Unknown"
        
        logger.info(f"💬 MESSAGE from @{from_user} in {chat_name} ({chat_type}): {text}")
        
        print(f"💬 MESSAGE RECEIVED!")
        print(f"   From: @{from_user}")
        print(f"   Chat: {chat_name} ({chat_type})")
        print(f"   Text: {text}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        "🔥 Cherokee Trading Council Bot Active!\n"
        "I can now see messages in channels AND groups!"
    )

def main():
    """Run the bot with channel support"""
    print("🔥 Starting Enhanced Derpatobot with CHANNEL support!")
    print("Bot will now see:")
    print("  ✅ Group messages")
    print("  ✅ Channel posts")
    print("  ✅ Private messages")
    print("")
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers for different message types
    application.add_handler(CommandHandler("start", start))
    
    # Handle regular messages (groups and private)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # IMPORTANT: Handle channel posts!
    application.add_handler(MessageHandler(
        filters.TEXT & filters.UpdateType.CHANNEL_POST,
        handle_channel_post
    ))
    
    print("🚀 Bot starting... Check for messages!")
    print("=" * 50)
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()