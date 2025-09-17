#!/usr/bin/env python3
"""
🔥 WORKING TEMPORAL FLAT FILE BRIDGE
This one actually sends the responses back!
"""
import os
import json
import time
import asyncio
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

class WorkingTemporalBridge:
    def __init__(self):
        self.application = None
        self.monitoring = False
        self.last_outbox_check = 0
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initialize the temporal bridge"""
        epoch_now = time.time()
        human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        response = f"""🔥 **Working Temporal Bridge Active!**
        
⏰ **Epoch**: {epoch_now:.0f}
📅 **Time**: {human_time}

The Cherokee Tribe responds through flat files!
I will now properly send their responses back to you.
        
Send me any message and wait for the tribe's wisdom!"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def bridge_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bridge message to flat file and get response"""
        if not update.message or not update.message.text:
            return
        
        # Capture the EXACT moment
        epoch_now = time.time()
        human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Extract message details
        user = update.message.from_user.first_name or "User"
        chat_id = update.message.chat_id
        text = update.message.text
        
        print(f"📥 Received from {user}: {text}")
        
        # Create timestamped message
        message_data = {
            "epoch": epoch_now,
            "timestamp": human_time,
            "user": user,
            "chat_id": chat_id,
            "message": text
        }
        
        # Write to inbox (append mode)
        with open(INCOMING_FILE, 'a') as f:
            json.dump(message_data, f)
            f.write('\n')
        
        print(f"📝 Written to inbox at epoch {epoch_now}")
        
        # Quick acknowledgment
        await update.message.reply_text(
            f"🔥 Processing at epoch {epoch_now:.0f}...",
            parse_mode='Markdown'
        )
        
        # Now actively wait for the response
        response_text = await self.wait_for_tribe_response(chat_id, epoch_now)
        
        if response_text:
            # Send the actual tribe response!
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown'
            )
            print(f"✅ Response sent back to {user}")
        else:
            # Timeout
            await update.message.reply_text(
                "⏰ The tribe is processing deeply. Check back soon!",
                parse_mode='Markdown'
            )
    
    async def wait_for_tribe_response(self, chat_id, sent_epoch, timeout=8):
        """Actively wait for tribe response"""
        start_time = time.time()
        last_size = 0
        
        print(f"⏳ Waiting for response for chat {chat_id}...")
        
        while time.time() - start_time < timeout:
            try:
                # Check if outbox exists and has content
                if os.path.exists(OUTGOING_FILE):
                    current_stat = os.stat(OUTGOING_FILE)
                    
                    # If file has grown or been modified
                    if current_stat.st_size > 0 and current_stat.st_mtime > self.last_outbox_check:
                        # Read the entire file
                        with open(OUTGOING_FILE, 'r') as f:
                            content = f.read()
                        
                        if content.strip():
                            # Parse responses - could be multiple JSON objects
                            lines = content.strip().split('\n}')
                            
                            for line in lines:
                                if not line.strip():
                                    continue
                                    
                                # Re-add the closing brace if needed
                                if not line.endswith('}'):
                                    line += '}'
                                
                                try:
                                    response_data = json.loads(line)
                                    response_chat_id = str(response_data.get("chat_id", ""))
                                    
                                    # Check if this response is for our chat
                                    if response_chat_id == str(chat_id):
                                        response_text = response_data.get("response", "")
                                        response_epoch = float(response_data.get("epoch", time.time()))
                                        
                                        # Calculate response time
                                        response_time = response_epoch - sent_epoch
                                        
                                        # Add response time to message
                                        if response_text:
                                            response_text += f"\n\n⏱️ *Response time: {response_time:.2f} seconds*"
                                            
                                            print(f"🎯 Found response for chat {chat_id}!")
                                            
                                            # Clear this response from outbox
                                            self.clear_response_from_outbox(chat_id)
                                            
                                            return response_text
                                
                                except json.JSONDecodeError as e:
                                    print(f"JSON parse error: {e}")
                                    continue
                        
                        self.last_outbox_check = current_stat.st_mtime
                
            except Exception as e:
                print(f"Error checking outbox: {e}")
            
            # Small delay before next check
            await asyncio.sleep(0.2)
        
        print(f"⏰ Timeout waiting for response for chat {chat_id}")
        return None
    
    def clear_response_from_outbox(self, chat_id):
        """Remove processed response from outbox"""
        try:
            if os.path.exists(OUTGOING_FILE):
                with open(OUTGOING_FILE, 'r') as f:
                    content = f.read()
                
                # Parse all responses
                remaining = []
                lines = content.strip().split('\n}')
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    if not line.endswith('}'):
                        line += '}'
                    
                    try:
                        data = json.loads(line)
                        # Keep responses for other chats
                        if str(data.get("chat_id", "")) != str(chat_id):
                            remaining.append(json.dumps(data))
                    except:
                        pass
                
                # Write back remaining responses
                with open(OUTGOING_FILE, 'w') as f:
                    for resp in remaining:
                        f.write(resp + '\n')
                
                print(f"🧹 Cleared response for chat {chat_id} from outbox")
        
        except Exception as e:
            print(f"Error clearing outbox: {e}")

def main():
    """Run the working temporal bridge"""
    print("🔥 WORKING TEMPORAL FLAT FILE BRIDGE STARTING...")
    print(f"Epoch: {time.time()}")
    print(f"Time: {datetime.now()}")
    print("=" * 50)
    
    # Create bridge instance
    bridge = WorkingTemporalBridge()
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    bridge.application = application
    
    # Add handlers
    application.add_handler(CommandHandler("start", bridge.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bridge.bridge_message))
    
    # Run the bot
    print("🔥 Bridge ready to properly send responses!")
    print(f"Inbox: {INCOMING_FILE}")
    print(f"Outbox: {OUTGOING_FILE}")
    print("=" * 50)
    
    application.run_polling()

if __name__ == '__main__':
    main()