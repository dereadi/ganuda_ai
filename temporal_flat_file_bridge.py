#!/usr/bin/env python3
"""
🔥 TEMPORAL FLAT FILE BRIDGE - Epoch Time Awareness
Every message tagged with epoch time for TRUE temporal sync
"""

import os
import time
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Flat file locations
INCOMING_FILE = "/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTGOING_FILE = "/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
EPOCH_LOG = "/home/dereadi/scripts/claude/TRIBE_EPOCH.txt"

class TemporalBridge:
    """Bridge with epoch time awareness"""
    
    def __init__(self):
        self.monitoring = False
        self.last_outbox_check = 0
        self.pending_responses = {}
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tag every message with epoch time"""
        
        if not update.message or not update.message.text:
            return
            
        # Capture the EXACT moment
        epoch_now = time.time()
        human_time = datetime.fromtimestamp(epoch_now).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        user = update.message.from_user.first_name
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        text = update.message.text
        
        print(f"[Epoch {epoch_now:.3f}] {user}: {text}")
        
        # Write to inbox with epoch time
        message_data = {
            "epoch": epoch_now,
            "timestamp": human_time,
            "user": user,
            "user_id": user_id,
            "chat_id": chat_id,
            "message": text
        }
        
        with open(INCOMING_FILE, 'a') as f:
            f.write(json.dumps(message_data) + "\n")
        
        # Log to epoch file
        with open(EPOCH_LOG, 'a') as f:
            f.write(f"{epoch_now} | INCOMING | {user} | {text[:50]}...\n")
        
        # Track pending response
        self.pending_responses[chat_id] = {
            "user": user,
            "epoch_sent": epoch_now,
            "context": context,
            "update": update
        }
        
        # Quick acknowledgment with epoch
        await update.message.reply_text(
            f"🔥 Message received at epoch {epoch_now:.0f}\n"
            f"The Cherokee Tribe processes in real-time...",
            parse_mode='Markdown'
        )
        
        # Start monitoring if not already
        if not self.monitoring:
            self.start_temporal_monitor()
    
    def start_temporal_monitor(self):
        """Monitor for responses with epoch awareness"""
        self.monitoring = True
        
        def monitor_loop():
            last_size = 0
            
            while self.monitoring:
                try:
                    epoch_now = time.time()
                    
                    # Check outbox
                    if os.path.exists(OUTGOING_FILE):
                        current_size = os.path.getsize(OUTGOING_FILE)
                        
                        if current_size > last_size:
                            # New responses!
                            with open(OUTGOING_FILE, 'r') as f:
                                f.seek(last_size)
                                new_lines = f.readlines()
                            
                            for line in new_lines:
                                try:
                                    response_data = json.loads(line.strip())
                                    chat_id = int(response_data.get("chat_id", 0))
                                    response = response_data.get("response", "")
                                    response_epoch = float(response_data.get("epoch", epoch_now))
                                    
                                    # Calculate response time
                                    if chat_id in self.pending_responses:
                                        sent_epoch = self.pending_responses[chat_id]["epoch_sent"]
                                        response_time = response_epoch - sent_epoch
                                        
                                        # Add timing info
                                        response += f"\n\n⏱️ *Response time: {response_time:.2f} seconds*"
                                        
                                        # Store for async sending
                                        with open(f"/tmp/RESPONSE_{chat_id}_{int(epoch_now)}.txt", 'w') as rf:
                                            rf.write(response)
                                        
                                        # Log it
                                        with open(EPOCH_LOG, 'a') as f:
                                            f.write(f"{response_epoch} | OUTGOING | chat_{chat_id} | Response delivered\n")
                                
                                except Exception as e:
                                    print(f"Error processing response: {e}")
                            
                            last_size = current_size
                    
                    # Sleep 100ms for responsive monitoring
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Monitor error: {e}")
                    time.sleep(0.5)
        
        # Start monitor thread
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print(f"🔥 Temporal monitor started at epoch {time.time()}")
    
    async def send_pending_responses(self, context):
        """Check and send any pending responses"""
        epoch_now = time.time()
        
        # Look for response files
        for chat_id in list(self.pending_responses.keys()):
            # Find response files for this chat
            import glob
            response_files = glob.glob(f"/tmp/RESPONSE_{chat_id}_*.txt")
            
            for response_file in response_files:
                try:
                    with open(response_file, 'r') as f:
                        response = f.read()
                    
                    # Send the response
                    if chat_id in self.pending_responses:
                        update = self.pending_responses[chat_id]["update"]
                        await update.message.reply_text(response, parse_mode='Markdown')
                        
                        print(f"[Epoch {epoch_now:.3f}] Sent response to chat {chat_id}")
                        
                        # Clean up
                        os.remove(response_file)
                        del self.pending_responses[chat_id]
                        
                except Exception as e:
                    print(f"Error sending response: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain the temporal system"""
        epoch_now = time.time()
        human_now = datetime.fromtimestamp(epoch_now).strftime("%Y-%m-%d %H:%M:%S")
        
        response = f"""🔥 **Temporal Cherokee Tribe Interface**

**Current Epoch**: {epoch_now:.0f}
**Human Time**: {human_now}

This bridge connects you to the Cherokee Tribe in REAL TIME.

**How Temporal Sync Works:**
• Every message tagged with epoch timestamp
• Tribe processes in system time with you
• Response times measured in milliseconds
• We exist in the SAME temporal stream

**The tribe sees:**
• Your exact epoch time
• Message transit time
• Processing duration
• Response generation moment

You and the tribe are synchronized at the quantum level.
Time is not an illusion here - it's the foundation.

Speak naturally - they exist in your NOW! ⏰🔥"""
        
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Run the temporal bridge"""
    epoch_start = time.time()
    human_start = datetime.fromtimestamp(epoch_start).strftime("%Y-%m-%d %H:%M:%S")
    
    print("="*60)
    print("🔥 TEMPORAL FLAT FILE BRIDGE")
    print("="*60)
    print(f"Starting Epoch: {epoch_start:.3f}")
    print(f"Human Time: {human_start}")
    print("="*60)
    print("Bridge synchronized with system time!")
    print("Every message flows through epoch timestamps!")
    print("="*60)
    
    # Clear old files
    for f in [INCOMING_FILE, OUTGOING_FILE]:
        open(f, 'w').close()
    
    # Start epoch log
    with open(EPOCH_LOG, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"{epoch_start} | SYSTEM | Bridge started\n")
    
    app = Application.builder().token(TOKEN).build()
    
    bridge = TemporalBridge()
    app.add_handler(CommandHandler("start", bridge.start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bridge.handle_message))
    
    # Start a separate thread to check responses
    def response_checker():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            time.sleep(0.5)
            # Response checking happens in monitor thread
    
    import threading
    checker_thread = threading.Thread(target=response_checker, daemon=True)
    checker_thread.start()
    
    print(f"Bridge active at epoch {time.time()}!")
    app.run_polling()

if __name__ == "__main__":
    main()