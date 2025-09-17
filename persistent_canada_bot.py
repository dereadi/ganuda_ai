#!/usr/bin/env python3
"""
🔥 PERSISTENT CANADA BOT - Runs 24/7 in screen session
Watches for your Telegram messages and logs them for Claude to see
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
MESSAGE_LOG = Path("/home/dereadi/scripts/claude/CANADA_MESSAGES.log")
RESPONSE_QUEUE = Path("/home/dereadi/scripts/claude/CANADA_RESPONSES.json")

class CanadaBot:
    def __init__(self):
        self.message_count = 0
        
    async def handle_message(self, update, context):
        """Log messages for Claude and send acknowledgment"""
        if not update.message or not update.message.text:
            return
            
        user = update.message.from_user.first_name or "User"
        text = update.message.text
        chat_id = update.message.chat.id
        timestamp = datetime.now()
        
        # Log for Claude to see
        self.message_count += 1
        log_entry = f"""
{'='*60}
🔥 MESSAGE #{self.message_count} FROM CANADA
Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S CDT')}
User: {user}
Chat ID: {chat_id}
Message: {text}
{'='*60}
CLAUDE: Analyze this and respond with full tribal intelligence!
"""
        
        # Append to log file
        with open(MESSAGE_LOG, 'a') as f:
            f.write(log_entry + "\n")
        
        # Print to screen so Claude sees it
        print(log_entry)
        
        # Send immediate acknowledgment
        ack_message = f"""🔥 Cherokee Council received your message!

Message #{self.message_count}: "{text}"

Claude is analyzing with full tribal intelligence...
Response coming soon!

(You're connected from Canada! 🇨🇦)"""
        
        await update.message.reply_text(ack_message)
        
        # Save message for Claude to process
        message_data = {
            "id": self.message_count,
            "timestamp": timestamp.isoformat(),
            "user": user,
            "chat_id": chat_id,
            "text": text,
            "status": "pending"
        }
        
        # Append to response queue
        queue = []
        if RESPONSE_QUEUE.exists():
            with open(RESPONSE_QUEUE, 'r') as f:
                try:
                    queue = json.load(f)
                except:
                    queue = []
        
        queue.append(message_data)
        
        with open(RESPONSE_QUEUE, 'w') as f:
            json.dump(queue, f, indent=2)
        
        print(f"✅ Message #{self.message_count} logged and queued for response")

def main():
    print("🔥 PERSISTENT CANADA BOT STARTING...")
    print("="*60)
    print("This bot will run 24/7 in your screen session")
    print("It logs all messages for Claude to analyze")
    print("You can check messages at: CANADA_MESSAGES.log")
    print("="*60)
    print("")
    
    bot = CanadaBot()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("🔥 Ready to receive messages from Canada!")
    print("Send messages to @ganudabot")
    print("")
    
    app.run_polling()

if __name__ == "__main__":
    main()
