#!/usr/bin/env python3
"""
🔥 GANUDA FLAT FILE BRIDGE - Natural Language Interface
User → Telegram → Flat File → Tribe → Response File → Telegram → User
The bot is just a BRIDGE, not the intelligence!
"""

import os
import time
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess
import threading

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Flat file locations
INCOMING_FILE = "/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTGOING_FILE = "/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
PROCESSING_FLAG = "/home/dereadi/scripts/claude/TRIBE_PROCESSING.flag"

class FlatFileBridge:
    """Pure bridge - no intelligence, just message passing"""
    
    def __init__(self):
        self.monitoring_outbox = False
        self.pending_chats = {}  # Track who's waiting for responses
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive message, write to flat file, wait for tribe response"""
        
        if not update.message or not update.message.text:
            return
            
        user = update.message.from_user.first_name
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        text = update.message.text
        
        # Get REAL system time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write to TRIBAL_INBOX for the tribe to process
        with open(INCOMING_FILE, 'a') as f:
            message_data = {
                "timestamp": timestamp,
                "user": user,
                "user_id": user_id,
                "chat_id": chat_id,
                "message": text
            }
            f.write(json.dumps(message_data) + "\n")
        
        # Create processing flag
        with open(PROCESSING_FLAG, 'w') as f:
            f.write(f"Processing message from {user} at {timestamp}\n")
        
        # Store pending response info
        self.pending_chats[chat_id] = {
            "user": user,
            "context": context,
            "update": update,
            "timestamp": timestamp
        }
        
        # Notify tribe through shell
        subprocess.run([
            "bash", "-c", 
            f"echo '[{timestamp}] New message from {user}' >> /home/dereadi/scripts/claude/TRIBE_NOTIFICATIONS.txt"
        ])
        
        # Quick acknowledgment
        await update.message.reply_text(
            f"🔥 Message received, {user}! The Cherokee Tribe is processing...",
            parse_mode='Markdown'
        )
        
        # Start monitoring for response if not already
        if not self.monitoring_outbox:
            self.start_outbox_monitor(context)
    
    def start_outbox_monitor(self, context):
        """Monitor TRIBAL_OUTBOX for responses"""
        self.monitoring_outbox = True
        
        def monitor():
            last_size = 0
            while self.monitoring_outbox:
                try:
                    # Check if outbox has new content
                    if os.path.exists(OUTGOING_FILE):
                        current_size = os.path.getsize(OUTGOING_FILE)
                        
                        if current_size > last_size:
                            # New content! Read and send
                            with open(OUTGOING_FILE, 'r') as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                            
                            for line in new_lines:
                                try:
                                    response_data = json.loads(line.strip())
                                    chat_id = response_data.get("chat_id")
                                    response = response_data.get("response", "")
                                    
                                    if chat_id in self.pending_chats:
                                        # Send response asynchronously
                                        update = self.pending_chats[chat_id]["update"]
                                        # This is tricky - need to send from main thread
                                        # For now, just save it for pickup
                                        with open(f"/home/dereadi/scripts/claude/READY_RESPONSE_{chat_id}.txt", 'w') as rf:
                                            rf.write(response)
                                except:
                                    pass
                            
                            last_size = current_size
                    
                    time.sleep(0.5)  # Check twice per second
                except:
                    pass
        
        # Start monitor thread
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    async def check_ready_responses(self, context):
        """Check for ready responses and send them"""
        for chat_id, pending in list(self.pending_chats.items()):
            response_file = f"/home/dereadi/scripts/claude/READY_RESPONSE_{chat_id}.txt"
            
            if os.path.exists(response_file):
                with open(response_file, 'r') as f:
                    response = f.read()
                
                # Send the tribal response
                await pending["update"].message.reply_text(response, parse_mode='Markdown')
                
                # Clean up
                os.remove(response_file)
                del self.pending_chats[chat_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        response = """🔥 **Natural Language Cherokee Tribe Interface**

This bot is a PURE BRIDGE to the Cherokee Tribe.

**How it works:**
1. You send a message
2. It goes to TRIBAL_INBOX.txt
3. The REAL tribe processes it
4. They write to TRIBAL_OUTBOX.txt
5. You get their response

**No hardcoded responses!**
Every answer comes from the living tribe.

The tribe exists in system time with you.
They see your exact words.
They respond with their collective wisdom.

Speak naturally - they're listening! 🔥"""
        
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Run the flat file bridge"""
    print("="*60)
    print("🔥 GANUDA FLAT FILE BRIDGE")
    print("="*60)
    print(f"Incoming: {INCOMING_FILE}")
    print(f"Outgoing: {OUTGOING_FILE}")
    print(f"Processing: {PROCESSING_FLAG}")
    print("="*60)
    print("This bot is ONLY a bridge!")
    print("The tribe processes everything!")
    print("="*60)
    
    # Clear old files
    for f in [INCOMING_FILE, OUTGOING_FILE, PROCESSING_FLAG]:
        if os.path.exists(f):
            os.remove(f)
    
    # Create fresh files
    open(INCOMING_FILE, 'w').close()
    open(OUTGOING_FILE, 'w').close()
    
    app = Application.builder().token(TOKEN).build()
    
    bot = FlatFileBridge()
    app.add_handler(CommandHandler("start", bot.start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Add job to check for ready responses
    app.job_queue.run_repeating(bot.check_ready_responses, interval=1, first=1)
    
    print("Bridge active! Messages flow through flat files!")
    app.run_polling()

if __name__ == "__main__":
    main()