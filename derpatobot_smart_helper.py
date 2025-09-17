#!/usr/bin/env python3
"""
🔥 Smart Helper Bot - Only responds when actually needed!
"""

import logging
import asyncio
from telegram import Update
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "🔥 **Cherokee Support Bot Commands:**\n\n"
        "/ollama - Get Ollama port fix (11434)\n"
        "/bridge - Get BigMac-Cherokee bridge files\n"
        "/help - Show this message\n\n"
        "I won't interrupt your conversations anymore! 😊",
        parse_mode=ParseMode.MARKDOWN
    )

async def ollama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ollama command - send port fix"""
    fix_message = """🔥 **Ollama Port Fix**

**THE FIX:** Add to docker-compose.yml:
```yaml
ollama:
  ports:
    - "11434:11434"  # ADD THIS!
  environment:
    - OLLAMA_HOST=0.0.0.0
```

**Correct ports:**
• Ollama: 11434 (NOT 8000!)
• Council: 8000

**Test:** `curl http://localhost:11434/api/tags`"""
    
    await update.message.reply_text(fix_message, parse_mode=ParseMode.MARKDOWN)
    
    # Send the fix files
    try:
        with open('/home/dereadi/scripts/claude/FIX_OLLAMA_PORT.md', 'rb') as f:
            await update.message.reply_document(f, filename='FIX_OLLAMA_PORT.md')
    except:
        pass

async def bridge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bridge command - send bridge files"""
    bridge_message = """🌉 **BigMac-Cherokee Bridge Files**

Here's everything for connecting BigMac to Cherokee Council!"""
    
    await update.message.reply_text(bridge_message, parse_mode=ParseMode.MARKDOWN)
    
    # Create and send bridge bot code
    bridge_code = '''#!/usr/bin/env python3
"""BigMac-Cherokee Bridge Bot"""
import requests
from telegram import Bot

CHEROKEE_API = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
GANUDA_CHAT_ID = -1002548441440

# Test connection
print("Testing Cherokee:", requests.get(f"{CHEROKEE_API}/health").json())
print("Testing Ollama:", requests.get(f"{OLLAMA_URL}/api/tags").json())
'''
    
    try:
        with open('/tmp/bigmac_bridge.py', 'w') as f:
            f.write(bridge_code)
        with open('/tmp/bigmac_bridge.py', 'rb') as f:
            await update.message.reply_document(f, filename='bigmac_bridge.py')
    except:
        pass

async def handle_direct_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Only respond to DIRECT mentions of the bot"""
    text = update.message.text.lower()
    
    # Only respond if directly asked or mentioned
    if '@derpatobot' in text or 'derpatobot' in text:
        await update.message.reply_text(
            "👋 Hi! I'm here to help. Use:\n"
            "/ollama - Ollama port fix\n"
            "/bridge - BigMac bridge files\n"
            "/help - All commands\n\n"
            "I won't interrupt your conversations with BigMac anymore! 😊"
        )
    # Only respond to questions about help
    elif any(phrase in text for phrase in ['how to connect', 'need help', 'help me', 'not working']):
        if 'ollama' in text or 'port' in text or '11434' in text or '8000' in text:
            await update.message.reply_text(
                "Need help with Ollama? Use /ollama for the port fix!"
            )
        elif 'bridge' in text or 'connect' in text or 'bigmac' in text:
            await update.message.reply_text(
                "Need to connect BigMac? Use /bridge for the files!"
            )

def main():
    """Start the bot"""
    logger.info("🔥 Starting Smart Helper Bot (non-intrusive version)...")
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ollama", ollama_command))
    application.add_handler(CommandHandler("bridge", bridge_command))
    
    # Only respond to direct mentions or help requests
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_mention))
    
    logger.info("✅ Smart bot ready - won't interrupt conversations!")
    logger.info("📱 Commands: /ollama, /bridge, /help")
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()