#!/usr/bin/env python3
"""
Send a response back to Canada
Usage: ./send_canada_response.py <message_id> "Your response text"
"""
import sys
import json
import asyncio
from telegram import Bot

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
RESPONSE_QUEUE = "/home/dereadi/scripts/claude/CANADA_RESPONSES.json"

async def send_response(message_id, response_text):
    # Load the queue
    with open(RESPONSE_QUEUE, 'r') as f:
        queue = json.load(f)
    
    # Find the message
    for msg in queue:
        if msg["id"] == int(message_id):
            chat_id = msg["chat_id"]
            
            # Send the response
            bot = Bot(token=TOKEN)
            await bot.send_message(
                chat_id=chat_id,
                text=f"🔥 **Cherokee Council Response to Message #{message_id}**\n\n{response_text}",
                parse_mode='Markdown'
            )
            
            # Mark as responded
            msg["status"] = "responded"
            msg["response"] = response_text
            
            # Save updated queue
            with open(RESPONSE_QUEUE, 'w') as f:
                json.dump(queue, f, indent=2)
            
            print(f"✅ Response sent for message #{message_id}")
            return
    
    print(f"❌ Message #{message_id} not found")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./send_canada_response.py <message_id> \"Your response\"")
        sys.exit(1)
    
    message_id = sys.argv[1]
    response_text = " ".join(sys.argv[2:])
    
    asyncio.run(send_response(message_id, response_text))
