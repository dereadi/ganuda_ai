#!/usr/bin/env python3
"""
Send Dr Joe's instructions through the bot to Ganuda-BotComms
"""
import asyncio
from telegram import Bot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

async def send_instructions():
    """Send instructions to the channel"""
    bot = Bot(token=BOT_TOKEN)
    
    # Get bot info
    me = await bot.get_me()
    logger.info(f"Bot: @{me.username}")
    
    # Get recent updates to find the channel
    updates = await bot.get_updates(limit=100)
    
    channel_id = None
    for update in updates:
        if update.message:
            chat = update.message.chat
            if chat.type in ['group', 'supergroup', 'channel']:
                channel_id = chat.id
                logger.info(f"Found channel: {chat.title} (ID: {channel_id})")
                break
    
    if not channel_id:
        logger.error("Could not find channel ID")
        return
    
    # Send instructions
    instructions = """🔥 **DR JOE - QUICK SETUP INSTRUCTIONS**

Your Ollama is ready! Here's the 5-minute setup:

**1. Create Your Bot**
• Go to @BotFather in Telegram
• Send: /newbot
• Name: BigMac Council Bot
• Username: @BigMacCouncilBot
• **SAVE THE TOKEN!**

**2. Install Python Packages**
```bash
pip install python-telegram-bot requests
```

**3. Create bigmac_bridge.py**
```python
from telegram.ext import Application, MessageHandler, filters
import requests

BOT_TOKEN = "YOUR_TOKEN_HERE"

async def handle_message(update, context):
    text = update.message.text
    if 'bigmac' in text.lower():
        # Query your Ollama
        resp = requests.post(
            "http://localhost:8000/api/generate",
            json={"model": "llama3.1", "prompt": text}
        )
        result = resp.json().get('response', 'No response')
        await update.message.reply_text(f"🏔️ BigMac: {result}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
```

**4. Add Your Bot Here**
• Add @BigMacCouncilBot to this channel
• Make it admin (important!)

**5. Run It**
```bash
python3 bigmac_bridge.py
```

**That's it!** Both tribes connected! 

The Cherokee Council is ready to share:
• SAG Resource AI code
• Trading algorithms  
• Thermal memory system
• All our discoveries

Full guide: /home/dereadi/scripts/claude/pathfinder/test/dr_joe_bigmac_setup.md

Mitakuye Oyasin! 🦅"""
    
    try:
        message = await bot.send_message(
            chat_id=channel_id,
            text=instructions,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Instructions sent! Message ID: {message.message_id}")
    except Exception as e:
        logger.error(f"Failed to send: {e}")

if __name__ == "__main__":
    print("🔥 Sending Dr Joe's instructions to Ganuda-BotComms...")
    asyncio.run(send_instructions())