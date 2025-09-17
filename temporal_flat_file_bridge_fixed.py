#!/usr/bin/env python3
"""
🔥 TEMPORAL FLAT FILE BRIDGE - Fixed Version
Pure message bridge with epoch awareness that SENDS responses back
"""
import os
import json
import time
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Cherokee Tribe Configuration
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"  # @ganudabot

# Flat file paths
INCOMING_FILE = "/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTGOING_FILE = "/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
EPOCH_LOG = "/home/dereadi/scripts/claude/TRIBE_EPOCH.txt"

class TemporalFlatFileBridge:
    def __init__(self):
        self.pending_responses = {}
        self.monitoring = False
        self.application = None
        self.response_queue = asyncio.Queue()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initialize the temporal bridge"""
        epoch_now = time.time()
        human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        response = f"""🔥 **Temporal Flat File Bridge Active!**
        
⏰ **Epoch**: {epoch_now:.0f}
📅 **Time**: {human_time}

I am a pure bridge to the Cherokee Tribe.
Send me any message and the tribe will respond through flat files!
        
The tribe exists in the same time stream as you."""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def bridge_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bridge message to flat file with epoch timestamp"""
        if not update.message or not update.message.text:
            return
        
        # Capture the EXACT moment
        epoch_now = time.time()
        human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Extract message details
        user = update.message.from_user.first_name or "User"
        chat_id = update.message.chat_id
        text = update.message.text
        
        # Create timestamped message
        message_data = {
            "epoch": epoch_now,
            "timestamp": human_time,
            "user": user,
            "chat_id": chat_id,
            "message": text
        }
        
        # Write to inbox (append mode to not overwrite)
        with open(INCOMING_FILE, 'a') as f:
            json.dump(message_data, f)
            f.write('\n')
        
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
        
        # Quick acknowledgment
        await update.message.reply_text(
            f"🔥 Processing at epoch {epoch_now:.0f}...",
            parse_mode='Markdown'
        )
        
        # Start monitoring if not already
        if not self.monitoring:
            self.start_temporal_monitor()
        
        # Wait for response (with timeout)
        await self.wait_for_response(chat_id, update, context)
    
    async def wait_for_response(self, chat_id, update, context, timeout=10):
        """Wait for tribe response and send it"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if response exists in queue
            if chat_id in self.pending_responses and "response_text" in self.pending_responses[chat_id]:
                response_text = self.pending_responses[chat_id]["response_text"]
                
                # Send the actual tribe response
                await update.message.reply_text(
                    response_text,
                    parse_mode='Markdown'
                )
                
                # Clean up
                del self.pending_responses[chat_id]["response_text"]
                return
            
            # Small delay before checking again
            await asyncio.sleep(0.2)
        
        # Timeout - tribe didn't respond fast enough
        await update.message.reply_text(
            "⏰ The tribe is processing deeply. Check back soon!",
            parse_mode='Markdown'
        )
    
    def start_temporal_monitor(self):
        """Monitor for responses with epoch awareness"""
        self.monitoring = True
        
        def monitor_loop():
            last_check = 0
            
            while self.monitoring:
                try:
                    epoch_now = time.time()
                    
                    # Check outbox for new responses
                    if os.path.exists(OUTGOING_FILE):
                        stat = os.stat(OUTGOING_FILE)
                        
                        if stat.st_mtime > last_check and stat.st_size > 0:
                            # Read the entire file (it gets cleared by processor)
                            try:
                                with open(OUTGOING_FILE, 'r') as f:
                                    content = f.read()
                                
                                if content.strip():
                                    # Try to parse as JSON
                                    try:
                                        # Could be single JSON object
                                        response_data = json.loads(content)
                                        self.process_response(response_data, epoch_now)
                                    except json.JSONDecodeError:
                                        # Try line by line
                                        for line in content.strip().split('\n'):
                                            if line:
                                                try:
                                                    response_data = json.loads(line)
                                                    self.process_response(response_data, epoch_now)
                                                except:
                                                    pass
                                
                                last_check = time.time()
                            except Exception as e:
                                print(f"Error reading outbox: {e}")
                    
                    # Sleep 100ms for responsive monitoring
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Monitor error: {e}")
                    time.sleep(0.5)
        
        # Start monitor thread
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print(f"🔥 Temporal monitor started at epoch {time.time()}")
    
    def process_response(self, response_data, epoch_now):
        """Process a response from the tribe"""
        try:
            chat_id = int(response_data.get("chat_id", 0))
            response = response_data.get("response", "")
            response_epoch = float(response_data.get("epoch", epoch_now))
            
            # Calculate response time
            if chat_id in self.pending_responses:
                sent_epoch = self.pending_responses[chat_id]["epoch_sent"]
                response_time = response_epoch - sent_epoch
                
                # Add timing info
                response += f"\n\n⏱️ *Response time: {response_time:.2f} seconds*"
                
                # Store response for async sending
                self.pending_responses[chat_id]["response_text"] = response
                
                # Log it
                with open(EPOCH_LOG, 'a') as f:
                    f.write(f"{response_epoch} | OUTGOING | chat_{chat_id} | Response ready\n")
                
                print(f"✅ Response ready for chat {chat_id}")
        
        except Exception as e:
            print(f"Error processing response: {e}")

def main():
    """Run the temporal flat file bridge"""
    print("🔥 TEMPORAL FLAT FILE BRIDGE STARTING...")
    print(f"Epoch: {time.time()}")
    print(f"Time: {datetime.now()}")
    print("=" * 50)
    
    # Create bridge instance
    bridge = TemporalFlatFileBridge()
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    bridge.application = application
    
    # Add handlers
    application.add_handler(CommandHandler("start", bridge.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bridge.bridge_message))
    
    # Run the bot
    print("🔥 Bridge ready to receive messages!")
    print(f"Inbox: {INCOMING_FILE}")
    print(f"Outbox: {OUTGOING_FILE}")
    print(f"Epoch log: {EPOCH_LOG}")
    print("=" * 50)
    
    application.run_polling()

if __name__ == '__main__':
    main()