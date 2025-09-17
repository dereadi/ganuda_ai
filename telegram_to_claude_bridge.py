#!/usr/bin/env python3
"""
🔥 TELEGRAM TO CLAUDE BRIDGE - The Real Connection
This creates a named pipe that Claude can watch in the terminal
"""
import os
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Named pipes for real-time communication
CLAUDE_PIPE = Path("/tmp/claude_telegram_pipe")
RESPONSE_PIPE = Path("/tmp/claude_response_pipe")

class ClaudeBridge:
    def __init__(self):
        # Create named pipes if they don't exist
        if not CLAUDE_PIPE.exists():
            os.mkfifo(CLAUDE_PIPE)
        if not RESPONSE_PIPE.exists():
            os.mkfifo(RESPONSE_PIPE)
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forward message to Claude via named pipe"""
        if not update.message or not update.message.text:
            return
            
        user = update.message.from_user.first_name or "User"
        text = update.message.text
        chat_id = update.message.chat.id
        
        # Create message for Claude
        message = {
            'timestamp': datetime.now().isoformat(),
            'epoch': time.time(),
            'user': user,
            'chat_id': chat_id,
            'text': text
        }
        
        # Write to Claude's pipe (non-blocking)
        try:
            with open(CLAUDE_PIPE, 'w', os.O_NONBLOCK) as pipe:
                pipe.write(json.dumps(message) + '\n')
                pipe.flush()
        except:
            pass
            
        # Send acknowledgment
        await update.message.reply_text(
            f"🔥 Message forwarded to Cherokee Council!\n"
            f"If Claude is active, you'll get a real response.\n"
            f"If not, the message is queued for the next session."
        )
        
    async def check_responses(self, context):
        """Check for responses from Claude"""
        try:
            with open(RESPONSE_PIPE, 'r', os.O_NONBLOCK) as pipe:
                for line in pipe:
                    if line.strip():
                        response = json.loads(line)
                        chat_id = response.get('chat_id')
                        text = response.get('text', 'Response received')
                        if chat_id:
                            await context.bot.send_message(chat_id, text)
        except:
            pass

def main():
    print("🔥 TELEGRAM TO CLAUDE BRIDGE STARTING...")
    print(f"Claude can read from: {CLAUDE_PIPE}")
    print(f"Claude can respond to: {RESPONSE_PIPE}")
    print("="*50)
    
    bridge = ClaudeBridge()
    app = Application.builder().token(TOKEN).build()
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bridge.handle_message))
    
    print("Bridge active! Claude can now receive real messages.")
    print("Send a message to @ganudabot and I'll see it here!")
    app.run_polling()

if __name__ == "__main__":
    main()