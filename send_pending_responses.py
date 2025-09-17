#!/usr/bin/env python3
"""
Send pending responses from OUTBOX to Telegram
"""
import json
import asyncio
from telegram import Bot

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
OUTBOX = "/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"

async def send_pending():
    bot = Bot(TOKEN)
    
    # Read outbox
    with open(OUTBOX, 'r') as f:
        content = f.read()
    
    if not content.strip():
        print("No pending responses")
        return
    
    # Parse responses
    sent_count = 0
    lines = content.strip().split('\n}')
    
    for line in lines:
        if not line.strip():
            continue
            
        if not line.endswith('}'):
            line += '}'
        
        try:
            data = json.loads(line)
            chat_id = data.get("chat_id")
            response = data.get("response", "")
            user = data.get("user", "")
            
            if chat_id and response:
                print(f"Sending response to {user} (chat {chat_id})...")
                await bot.send_message(
                    chat_id=int(chat_id),
                    text=response,
                    parse_mode='Markdown'
                )
                sent_count += 1
                print(f"✅ Sent!")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\nSent {sent_count} responses")
    
    # Clear outbox after sending
    if sent_count > 0:
        open(OUTBOX, 'w').close()
        print("Outbox cleared")

if __name__ == "__main__":
    asyncio.run(send_pending())