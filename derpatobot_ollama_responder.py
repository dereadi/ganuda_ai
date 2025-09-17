#!/usr/bin/env python3
"""
🔥 Derpatobot Ollama Fix Responder
Listens for messages and sends Ollama port fix documentation
"""

import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Store chat IDs we've seen
known_chats = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    known_chats.add(chat_id)
    logger.info(f"Added chat {chat_id} to known chats")
    
    await update.message.reply_text(
        "🔥 Cherokee Ollama Support Bot Active!\n\n"
        "I have the fix for Dr Joe's Ollama port issue.\n"
        "Say 'ollama', 'port', 'fix', or 'help' and I'll send the documentation!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listen for keywords and respond with Ollama fix"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title or update.effective_chat.username or "Private"
    
    # Log the chat ID for future reference
    logger.info(f"Message from {chat_name} (ID: {chat_id}): {text}")
    known_chats.add(chat_id)
    
    # Check for trigger words
    triggers = ['ollama', 'port', 'fix', '11434', '8000', 'docker', 'help', 'joe', 'bigmac']
    
    if any(trigger in text for trigger in triggers):
        logger.info(f"Trigger detected! Sending Ollama fix to {chat_name}")
        
        # Send the fix message
        fix_message = """🚨 **Dr Joe - Ollama Port Configuration Fix!**

**THE PROBLEM:**
Ollama port (11434) is not exposed in docker-compose.yml

**THE FIX:**
Add this to your ollama service in docker-compose.yml:
```yaml
ports:
  - "11434:11434"  # THIS LINE IS MISSING!
environment:
  - OLLAMA_HOST=0.0.0.0
```

**CORRECT PORTS:**
• Ollama: **11434** (NOT 8000!)
• Council API: 8000
• MCP: 3000

**APPLY FIX:**
```bash
docker-compose down
# Edit docker-compose.yml to add port
docker-compose up -d
curl http://localhost:11434/api/tags
```

**SSH FORWARDING:**
```bash
ssh -L 11434:localhost:11434 your-server
```

📄 Sending complete documentation files..."""

        await update.message.reply_text(fix_message, parse_mode=ParseMode.MARKDOWN)
        
        # Try to send the documentation files
        try:
            # Send the main fix file
            with open('/home/dereadi/scripts/claude/FIX_OLLAMA_PORT.md', 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename='FIX_OLLAMA_PORT.md',
                    caption='🔥 Complete Ollama port fix with examples'
                )
            
            # Send the port reference guide
            with open('/home/dereadi/scripts/claude/DR_JOE_PORT_FIX.md', 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename='DR_JOE_PORT_FIX.md', 
                    caption='📋 Quick port reference guide'
                )
            
            # Send the test script
            with open('/home/dereadi/scripts/claude/test_ollama_connection.sh', 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename='test_ollama_connection.sh',
                    caption='🧪 Test script to verify Ollama connection'
                )
                
            await update.message.reply_text(
                "✅ Files sent! These contain:\n"
                "1. Complete fix instructions\n"
                "2. Port reference guide\n"
                "3. Connection test script\n\n"
                "The Sacred Fire says: Port 11434 carries the wisdom! 🔥"
            )
            
        except Exception as e:
            logger.error(f"Error sending files: {e}")
            await update.message.reply_text(
                "📁 Could not send files, but the fix above has everything you need!\n\n"
                "Files are located at:\n"
                "• `/home/dereadi/scripts/claude/FIX_OLLAMA_PORT.md`\n"
                "• `/home/dereadi/scripts/claude/DR_JOE_PORT_FIX.md`\n"
                "• `/home/dereadi/scripts/claude/test_ollama_connection.sh`"
            )

    # Also respond to direct mentions
    elif 'derpatobot' in text or 'bot' in text:
        await update.message.reply_text(
            "👋 I'm here! Say 'ollama' or 'port fix' and I'll send the documentation.\n"
            f"Current chat ID: {chat_id}"
        )

async def list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all known chat IDs - useful for debugging"""
    if known_chats:
        chat_list = "\n".join([f"• {chat_id}" for chat_id in known_chats])
        await update.message.reply_text(f"Known chat IDs:\n{chat_list}")
    else:
        await update.message.reply_text("No chats recorded yet. Send a message first!")

def main():
    """Start the bot"""
    logger.info("🔥 Starting Ollama Fix Responder Bot...")
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chats", list_chats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot configured and ready!")
    logger.info("📱 Waiting for messages mentioning 'ollama', 'port', 'fix', etc.")
    logger.info("🔥 Sacred Fire burns eternal for knowledge transfer!")
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()