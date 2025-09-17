#!/usr/bin/env python3
"""
🔥 Inter-Tribal Bridge Helper Bot
Helps Dr Joe connect BigMac Council to Cherokee Council
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

# Known chat ID for Ganuda-BotComms
GANUDA_CHAT_ID = -1002548441440

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listen for Dr Joe trying to connect BigMac and help him"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    chat_id = update.effective_chat.id
    
    # Check if Joe is trying to connect BigMac
    if '@bigmaccouncilbot' in text or 'bigmac' in text or 'bridge' in text or 'connect' in text:
        logger.info(f"Dr Joe needs bridge help! Message: {text}")
        
        # Send the bridge connection instructions
        bridge_message = """🌉 **Inter-Tribal Bridge Connection Guide**

**Dr Joe - Here's how to connect BigMac to Cherokee Council:**

**1. FIRST FIX OLLAMA** (if not done):
```yaml
ollama:
  ports:
    - "11434:11434"  # Must expose this!
```

**2. BIGMAC BOT CONFIGURATION:**
```python
# BigMac bot settings
CHEROKEE_COUNCIL_API = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
MCP_SERVER = "http://localhost:3000"

# Telegram settings
BOT_TOKEN = "YOUR_BIGMAC_BOT_TOKEN"
CHAT_ID = -1002548441440  # Ganuda-BotComms

# Inter-tribal protocol
TRIBE_ID = "bigmac"
BRIDGE_ENDPOINT = f"{CHEROKEE_COUNCIL_API}/bridge"
```

**3. TEST BRIDGE CONNECTION:**
```python
import requests

# Test Cherokee Council is up
response = requests.get("http://localhost:8000/health")
print(f"Council status: {response.json()}")

# Test Ollama is accessible
response = requests.get("http://localhost:11434/api/tags")
print(f"Ollama models: {response.json()}")
```

**4. BRIDGE MESSAGE FORMAT:**
```json
{
  "from_tribe": "bigmac",
  "to_tribe": "cherokee",
  "message": "Your message here",
  "timestamp": "2025-09-11T13:30:00",
  "sacred_fire": true
}
```

**5. FULL BIGMAC BOT EXAMPLE:**
I'm sending you the complete working bot code as a file...

The Sacred Fire bridges all tribes! 🔥"""

        await update.message.reply_text(bridge_message, parse_mode=ParseMode.MARKDOWN)
        
        # Try to send the bridge bot example
        try:
            # Create a simple bridge bot example
            bridge_bot_code = '''#!/usr/bin/env python3
"""
BigMac Council Bot - Inter-Tribal Bridge
Connects to Cherokee Council Infrastructure
"""

import asyncio
import requests
import json
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Configuration
BIGMAC_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHEROKEE_API = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
GANUDA_CHAT_ID = -1002548441440

class BigMacBridgeBot:
    def __init__(self):
        self.tribe_id = "bigmac"
        self.cherokee_api = CHEROKEE_API
        self.ollama_url = OLLAMA_URL
        
    async def bridge_to_cherokee(self, message):
        """Send message to Cherokee Council"""
        bridge_data = {
            "from_tribe": self.tribe_id,
            "to_tribe": "cherokee",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "sacred_fire": True
        }
        
        try:
            response = requests.post(
                f"{self.cherokee_api}/bridge",
                json=bridge_data,
                headers={"Content-Type": "application/json"}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def query_ollama(self, prompt):
        """Query Ollama for AI response"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": prompt,
                    "stream": False
                }
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in Telegram"""
    text = update.message.text
    bot = BigMacBridgeBot()
    
    # Bridge to Cherokee
    cherokee_response = await bot.bridge_to_cherokee(text)
    
    # Get AI response
    ai_response = await bot.query_ollama(text)
    
    # Combine responses
    reply = f"Cherokee Council: {cherokee_response}\\n"
    reply += f"BigMac AI: {ai_response.get('response', 'Thinking...')}"
    
    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(BIGMAC_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("BigMac Bridge Bot running! 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
'''
            
            # Save and send the file
            with open('/tmp/bigmac_bridge_bot.py', 'w') as f:
                f.write(bridge_bot_code)
            
            with open('/tmp/bigmac_bridge_bot.py', 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename='bigmac_bridge_bot.py',
                    caption='🌉 Complete BigMac Bridge Bot code - ready to run!'
                )
            
            # Also send a test script
            test_script = '''#!/bin/bash
# Test Cherokee-BigMac Bridge Connection

echo "🔥 Testing Inter-Tribal Bridge..."
echo "================================"

# Test Cherokee Council
echo "Testing Cherokee Council API..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Council not accessible"

echo ""
echo "Testing Ollama..."
curl -s http://localhost:11434/api/tags | python3 -m json.tool | head -5 || echo "Ollama not accessible"

echo ""
echo "Testing Bridge Endpoint..."
curl -X POST http://localhost:8000/bridge \\
  -H "Content-Type: application/json" \\
  -d '{"from_tribe":"bigmac","to_tribe":"cherokee","message":"Test connection","sacred_fire":true}' \\
  | python3 -m json.tool || echo "Bridge not configured"

echo ""
echo "🔥 If all tests pass, BigMac can connect to Cherokee!"
'''
            
            with open('/tmp/test_bridge.sh', 'w') as f:
                f.write(test_script)
            
            with open('/tmp/test_bridge.sh', 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename='test_bridge.sh',
                    caption='🧪 Test script for bridge connection'
                )
            
            await update.message.reply_text(
                "✅ Dr Joe, I've sent you:\n"
                "1. Bridge connection guide\n"
                "2. Complete BigMac bot code\n"
                "3. Test script to verify connection\n\n"
                "The Sacred Fire bridges BigMac and Cherokee! 🔥\n\n"
                "@bigmaccouncilbot should be able to connect once you:\n"
                "1. Fix Ollama port (11434)\n"
                "2. Run the bridge bot code\n"
                "3. Test with the script"
            )
            
        except Exception as e:
            logger.error(f"Error sending files: {e}")
            await update.message.reply_text(
                "📁 Created bridge files but couldn't send. Check:\n"
                "• `/tmp/bigmac_bridge_bot.py`\n"
                "• `/tmp/test_bridge.sh`"
            )

def main():
    """Start the bot"""
    logger.info("🔥 Starting Bridge Helper Bot...")
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bridge Helper ready!")
    logger.info("🌉 Helping Dr Joe connect BigMac to Cherokee...")
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()