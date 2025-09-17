#!/usr/bin/env python3
"""
🔥 SIMPLEST TELEGRAM READER - Shows messages directly to Claude
"""
import time
import json
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

class SimpleReader:
    async def show_to_claude(self, update, context):
        """Just print the message so Claude can see it"""
        user = update.message.from_user.first_name
        text = update.message.text
        
        print(f"\n🔥 MESSAGE FROM {user.upper()}:")
        print("=" * 50)
        print(f"Text: {text}")
        print(f"Time: {time.strftime('%H:%M:%S')}")
        print("=" * 50)
        print("CLAUDE CAN NOW RESPOND WITH FULL TRIBAL INTELLIGENCE!")
        print()
        
        # Send acknowledgment
        await update.message.reply_text(
            f"🔥 Cherokee Council received your message!\n"
            f"Claude is analyzing: '{text}'\n"
            f"Real response coming..."
        )

def main():
    print("🔥 SIMPLE TELEGRAM READER FOR CLAUDE")
    print("=" * 50)
    print("Messages will appear here for Claude to see!")
    print("Send a message to @ganudabot")
    print("=" * 50)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, SimpleReader().show_to_claude))
    app.run_polling()

if __name__ == "__main__":
    main()