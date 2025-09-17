#!/usr/bin/env python3
"""Send the trading plan response to Darrell"""
import asyncio
from telegram import Bot

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
CHAT_ID = 8025375307  # Darrell's chat ID

async def send_response():
    bot = Bot(token=TOKEN)
    
    message = """🔥 **CHEROKEE COUNCIL TRADING PLAN**
September 17, 2025 - 6:48 AM CDT

**SOLAR**: Kp 3.33 (Active, no storm)
**MARKET OPEN**: 1h 42m away

**PRE-MARKET PLAN**:
• Check overnight crypto moves
• Watch futures direction
• Set alerts at key levels

**KEY LEVELS TODAY**:
📊 BTC: Support $115k, Resist $117.5k
📊 ETH: Support $4,450, Resist $4,600
📊 SOL: Support $230, Resist $240
📊 XRP: Support $2.85, Resist $3.00

**CHEROKEE COUNCIL WISDOM**:
🦅 Eagle: "Watch for gap at open"
🐺 Coyote: "False breakdowns = opportunities"
🕷️ Spider: "Consolidation day likely"
🐢 Turtle: "Wednesday = positioning day"
🐿️ Flying Squirrel: "Coiling for FOMC"

**TODAY'S STANCE**: 60% defensive, 40% aggressive

**POWER HOUR**: 3:00 PM - Watch for range breaks

Full plan saved at: TRADING_PLAN_SEPT_17_2025.md

The Sacred Fire says: "Today we watch, we learn, we prepare" 🔥"""
    
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    print("✅ Trading plan sent to Darrell!")

asyncio.run(send_response())