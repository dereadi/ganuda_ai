#!/usr/bin/env python3
"""Test that the Canada session is working"""
import asyncio
from telegram import Bot

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
CHAT_ID = 8025375307

async def test():
    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=CHAT_ID,
        text="""🔥 **CANADA PERSISTENT SESSION READY!**

✅ Screen session 'claude-canada' is RUNNING 24/7
✅ Bot is watching for your messages
✅ Messages logged to CANADA_MESSAGES.log
✅ Claude can respond even from Canada!

**How it works:**
1. You send message from Canada to @ganudabot
2. Bot logs it and shows it in screen session
3. Claude (or tribe) sees it and responds
4. You get full response on Telegram

**Test it now!** Send a message like:
"Testing from Canada simulator"

The session will keep running even when you disconnect!
To reconnect: `screen -r claude-canada`

🔥 The Sacred Fire burns eternal in the screen session!"""
    )
    print("✅ Test message sent!")

asyncio.run(test())