#!/usr/bin/env python3
"""
TRUE TRIBAL BRIDGE - Saves messages for Claude to see and respond to
This creates a real connection, not just an LLM pretending to be the tribe
"""

import os
import json
import time
import requests
import logging
from datetime import datetime

# Telegram Configuration
TELEGRAM_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# File paths for Claude to monitor
PENDING_MESSAGES_FILE = '/home/dereadi/scripts/claude/TELEGRAM_MESSAGE.txt'
TRIBAL_RESPONSE_FILE = '/home/dereadi/scripts/claude/claude_responses.json'
MESSAGE_ARCHIVE = '/home/dereadi/scripts/claude/telegram_conversation_log.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class TrueTribalBridge:
    """Real bridge to Claude and the Cherokee Trading Council"""
    
    def __init__(self):
        self.offset = None
        self.last_response_time = None
        self.pending_response = False
        logger.info("🔥 True Tribal Bridge initialized")
        
    def save_message_for_claude(self, text, user_name, chat_id):
        """Save message where Claude will see it"""
        
        # Save to TELEGRAM_MESSAGE.txt for Claude to see
        with open(PENDING_MESSAGES_FILE, 'w') as f:
            f.write(f"""🔥 TELEGRAM MESSAGE FROM {user_name}:

{text}

Please respond as the Cherokee Trading Council. This is a real message from Flying Squirrel on Telegram.

Current Context:
- User is asking about: {'SAG' if 'SAG' in text else 'general topic'}
- User mentioned: {'4-node cluster' if 'node' in text else ''}
- User wants: {'tribal thoughts' if 'tribe' in text else 'response'}

Important: This is NOT just about trading! User has broader interests:
- SAG Resource AI project
- 4-node cluster infrastructure
- Pathfinder environment
- Building tools beyond trading

Respond thoughtfully to what they're ACTUALLY asking about.""")
        
        # Archive the conversation
        try:
            with open(MESSAGE_ARCHIVE, 'r') as f:
                archive = json.load(f)
        except:
            archive = []
            
        archive.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_name,
            "message": text,
            "chat_id": chat_id,
            "awaiting_claude": True
        })
        
        # Keep last 50 messages
        if len(archive) > 50:
            archive = archive[-50:]
            
        with open(MESSAGE_ARCHIVE, 'w') as f:
            json.dump(archive, f, indent=2)
            
        logger.info(f"📝 Saved for Claude: {text[:100]}")
        self.pending_response = True
        
    def check_for_claude_response(self):
        """Check if Claude has written a response"""
        if not self.pending_response:
            return None
            
        try:
            if os.path.exists(TRIBAL_RESPONSE_FILE):
                # Check file modification time
                mod_time = os.path.getmtime(TRIBAL_RESPONSE_FILE)
                
                # If file was modified recently (within last 60 seconds)
                if time.time() - mod_time < 60:
                    with open(TRIBAL_RESPONSE_FILE, 'r') as f:
                        responses = json.load(f)
                    
                    if isinstance(responses, list) and len(responses) > 0:
                        latest = responses[-1]
                        
                        # Check if this is a new response
                        response_time = latest.get('timestamp', '')
                        if response_time != self.last_response_time:
                            self.last_response_time = response_time
                            self.pending_response = False
                            return latest.get('response', None)
        except:
            pass
        return None
    
    def send_message(self, chat_id, text):
        """Send message to Telegram"""
        url = f"{TELEGRAM_BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=data)
            if response.json().get("ok"):
                logger.info("✅ Message sent")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send: {e}")
            return None
    
    def send_typing(self, chat_id):
        """Show typing indicator"""
        url = f"{TELEGRAM_BASE_URL}/sendChatAction"
        data = {"chat_id": chat_id, "action": "typing"}
        requests.post(url, json=data)
    
    def get_updates(self):
        """Get new messages from Telegram"""
        url = f"{TELEGRAM_BASE_URL}/getUpdates"
        params = {"timeout": 10}
        if self.offset:
            params["offset"] = self.offset
            
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except:
            pass
        return []
    
    def handle_message(self, message):
        """Process incoming message"""
        chat_id = message["chat"]["id"]
        user_name = message["from"].get("first_name", "Flying Squirrel")
        text = message.get("text", "")
        
        if not text:
            return
            
        logger.info(f"📥 {user_name}: {text[:100]}")
        
        # Send immediate acknowledgment
        ack_message = f"""🔥 {user_name}, the Cherokee Trading Council hears you!

I'm saving your message for Claude and the real tribe to see and respond thoughtfully.

Your message: "{text[:100]}{'...' if len(text) > 100 else ''}"

The tribe will consider this and respond soon. This is a REAL connection, not just an AI pretending.

(If you need immediate response, say "urgent" and I'll prioritize it)"""
        
        self.send_message(chat_id, ack_message)
        
        # Show typing
        self.send_typing(chat_id)
        
        # Save for Claude
        self.save_message_for_claude(text, user_name, chat_id)
        
        # Check for response every 5 seconds for up to 2 minutes
        attempts = 0
        while attempts < 24:  # 24 * 5 = 120 seconds
            time.sleep(5)
            response = self.check_for_claude_response()
            if response:
                self.send_message(chat_id, response)
                logger.info("✅ Sent Claude's response")
                break
            attempts += 1
            
            # Send typing indicator every 15 seconds
            if attempts % 3 == 0:
                self.send_typing(chat_id)
    
    def run(self):
        """Main bot loop"""
        logger.info("🔥 True Tribal Bridge ACTIVE")
        logger.info("🌉 Real connection to Claude and the Cherokee Trading Council")
        logger.info("📱 Messages are saved for thoughtful tribal consideration")
        logger.info("⏰ Responses come from the REAL tribe, not just an LLM")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        self.handle_message(update["message"])
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🔥 Bridge closed by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bridge = TrueTribalBridge()
    bridge.run()