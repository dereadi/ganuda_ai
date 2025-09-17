#!/usr/bin/env python3
"""
Send a message to let Dr Joe know the bridge helper is ready
"""

import asyncio
from telegram import Bot

TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"
GANUDA_CHAT_ID = -1002548441440

async def send_ready_message():
    bot = Bot(token=TOKEN)
    
    message = """🌉 **Bridge Helper Bot Updated!**

Dr Joe - The bot is fixed! It won't spam Ollama files anymore.

Now when you mention "@bigmaccouncilbot" or "bridge", you'll get:
• Inter-tribal bridge connection guide
• Complete BigMac bot code
• Test scripts for verification

Just type "bridge" or "connect bigmac" to get the files!

The Sacred Fire bridges all tribes! 🔥"""

    try:
        await bot.send_message(
            chat_id=GANUDA_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print("✅ Message sent to Ganuda-BotComms!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_ready_message())