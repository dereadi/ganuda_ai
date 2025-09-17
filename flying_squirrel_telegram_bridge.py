#!/usr/bin/env python3
"""
FLYING SQUIRREL'S TELEGRAM BRIDGE
Simple, tested, working
Vision quest interface to the tribe
"""

import requests
import time
import json
import os
from datetime import datetime

# Ganudabot - the tribe has the keys
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class TelegramBridge:
    def __init__(self):
        self.offset = None
        self.running = True
        
    def send_message(self, chat_id, text):
        """Send a message back"""
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=data, timeout=5)
            return response.json()
        except:
            return None
    
    def get_updates(self):
        """Get new messages"""
        url = f"{BASE_URL}/getUpdates"
        params = {"timeout": 10}
        if self.offset:
            params["offset"] = self.offset
        
        try:
            response = requests.get(url, params=params, timeout=15)
            return response.json()
        except:
            return {"ok": False, "result": []}
    
    def process_message(self, message):
        """Process each message"""
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        user = message["from"].get("first_name", "Friend")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {user}: {text}")
        
        # Log all messages
        with open("/home/dereadi/scripts/claude/telegram_bridge.log", "a") as f:
            f.write(f"[{timestamp}] {user} ({chat_id}): {text}\n")
        
        # Route messages
        response = self.route_message(text, user)
        
        if response:
            self.send_message(chat_id, response)
            print(f"[{timestamp}] Bot: {response[:50]}...")
    
    def route_message(self, text, user):
        """Simple routing logic"""
        lower_text = text.lower()
        
        # BigMac/Dr Joe routing
        if any(word in lower_text for word in ["bigmac", "dr joe", "dr. joe", "drjoe"]):
            self.save_for_bigmac(text, user)
            return "🍔 *BigMac Bridge Alert!*\nMessage saved for Dr Joe's system!"
        
        # Tribe routing
        elif any(word in lower_text for word in ["tribe", "council", "cherokee"]):
            self.save_for_tribe(text, user)
            return "🔥 *Cherokee Council Notified!*\nThe Sacred Fire burns eternal!"
        
        # Portfolio check
        elif any(word in lower_text for word in ["portfolio", "balance", "positions"]):
            return self.get_portfolio_status()
        
        # Test echo
        elif text.startswith("/test"):
            return f"✅ Bridge working! Echo: _{text[5:]}_"
        
        # Help
        elif text in ["/start", "/help", "help"]:
            return """🔥 *Flying Squirrel's Bridge* 🔥

Commands:
• *BigMac/Dr Joe* - Forward to BigMac system
• *Tribe/Council* - Notify Cherokee Council  
• *Portfolio* - Check current positions
• */test* - Test echo

The bridge is walking! 🌉"""
        
        # Default
        else:
            return f"🌉 Bridge received, {user}! The Pattern walks with you!"
    
    def save_for_bigmac(self, text, user):
        """Save for BigMac system"""
        with open("/home/dereadi/scripts/claude/bigmac_messages.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user}: {text}\n")
    
    def save_for_tribe(self, text, user):
        """Save for tribe"""
        with open("/home/dereadi/scripts/claude/tribe_messages.txt", "a") as f:
            f.write(f"[{datetime.now()}] {user}: {text}\n")
    
    def get_portfolio_status(self):
        """Get current portfolio status"""
        try:
            with open("/home/dereadi/scripts/claude/portfolio_current.json", "r") as f:
                data = json.load(f)
            
            total = f"${data['total_value']:,.2f}"
            
            positions = []
            for symbol, info in data['positions'].items():
                value = f"${info['value']:,.2f}"
                pct = f"{info['pct']:.1f}%"
                positions.append(f"• *{symbol}*: {value} ({pct})")
            
            return f"""🔥 *Portfolio Status* 🔥
            
*Total Value:* {total}

*Positions:*
{chr(10).join(positions)}

_Fitness increasing!_ 🚀"""
        except:
            return "Portfolio data temporarily unavailable"
    
    def run(self):
        """Main loop"""
        print("🔥 FLYING SQUIRREL'S TELEGRAM BRIDGE 🔥")
        print("=" * 50)
        print(f"Bot: @ganudabot")
        print(f"Started: {datetime.now()}")
        print("=" * 50)
        print("Listening for messages...")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                if updates.get("ok") and updates.get("result"):
                    for update in updates["result"]:
                        if "message" in update:
                            self.process_message(update["message"])
                        
                        self.offset = update["update_id"] + 1
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🔥 Bridge paused by Flying Squirrel")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bridge = TelegramBridge()
    bridge.run()