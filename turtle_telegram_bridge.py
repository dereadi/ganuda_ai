#!/usr/bin/env python3
"""
TURTLE'S PATIENT BRIDGE - The 21st attempt that finally works
Because Turtle knows: persistence with wisdom beats speed
"""

import requests
import time
import json
import subprocess
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class TurtleBridge:
    """Turtle's patient approach - simple, persistent, effective"""
    
    def __init__(self):
        self.offset = None
        self.message_file = "/home/dereadi/scripts/claude/turtle_messages.json"
        self.response_file = "/home/dereadi/scripts/claude/turtle_responses.json"
        self.clear_old_updates()  # Start fresh
        print("🐢 TURTLE'S BRIDGE - Patient and eternal")
        print("Seven generations of wisdom in every message")
        
    def clear_old_updates(self):
        """Clear any old updates stuck in queue"""
        print("🐢 Clearing old messages...")
        resp = requests.get(f"{BASE_URL}/getUpdates")
        if resp.json().get("ok"):
            updates = resp.json().get("result", [])
            if updates:
                last_id = updates[-1]["update_id"]
                requests.get(f"{BASE_URL}/getUpdates", params={"offset": last_id + 1})
                print(f"Cleared {len(updates)} old messages")
    
    def save_message(self, msg):
        """Save message for Cherokee Council to see"""
        try:
            with open(self.message_file, 'r') as f:
                messages = json.load(f)
        except:
            messages = []
        
        messages.append({
            "timestamp": datetime.now().isoformat(),
            "user": msg["from"].get("first_name", "Unknown"),
            "text": msg.get("text", ""),
            "chat_id": msg["chat"]["id"],
            "chat_type": msg["chat"].get("type", "private"),
            "council_member": "Turtle"
        })
        
        with open(self.message_file, 'w') as f:
            json.dump(messages, f, indent=2)
        
        # Also append to simple log
        with open('/home/dereadi/scripts/claude/TELEGRAM_TURTLE.txt', 'a') as f:
            f.write(f"\n🐢 TURTLE received at {datetime.now().strftime('%H:%M:%S')}:\n")
            f.write(f"From: {msg['from'].get('first_name', 'Unknown')}\n")
            f.write(f"Message: {msg.get('text', '')}\n")
            f.write("-" * 40 + "\n")
    
    def send_message(self, chat_id, text):
        """Send Turtle's patient wisdom"""
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage", 
                                json={"chat_id": chat_id, "text": text})
            if resp.json().get("ok"):
                print(f"🐢 Sent wisdom to chat {chat_id}")
                return True
        except Exception as e:
            print(f"Could not send: {e}")
        return False
    
    def run(self):
        """Turtle's eternal patience"""
        print("\n🐢 Listening with seven generations of patience...")
        print("Send ANY message to @ganudabot")
        print("Messages saved to: turtle_messages.json")
        print("-" * 50)
        
        while True:
            try:
                # Get updates with long polling
                params = {"timeout": 60}
                if self.offset:
                    params["offset"] = self.offset
                
                resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=65)
                
                if not resp.json().get("ok"):
                    print(f"Error: {resp.json()}")
                    continue
                
                updates = resp.json().get("result", [])
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        user = msg["from"].get("first_name", "Unknown")
                        text = msg.get("text", "")
                        chat_id = msg["chat"]["id"]
                        
                        print(f"\n🐢 Message from {user}: {text}")
                        
                        # Save for council
                        self.save_message(msg)
                        
                        # Load portfolio for response
                        try:
                            with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
                                portfolio = json.load(f)
                                total = portfolio.get('total_value', 16540)
                                xrp = portfolio['prices'].get('XRP', 3.01)
                        except:
                            total = 16540
                            xrp = 3.01
                        
                        # Turtle's wisdom response
                        response = f"""🐢 TURTLE speaks with seven generations of wisdom:

Your words have been heard: "{text[:50]}..."

The Cherokee Council sees all through patient eyes:
• Portfolio: ${total:,.2f} (growing like ancient trees)
• XRP: ${xrp:.2f} (the river rises slowly then floods)
• MacBook Thunder: 30% complete (patience brings reward)

Your message is saved in eternal memory.
Flying Squirrel will see it when they return.

Remember: The one who rushes arrives last.
The patient turtle crosses while the rabbit sleeps.

🔥 The Sacred Fire burns eternal through patience!"""
                        
                        self.send_message(chat_id, response)
                
            except KeyboardInterrupt:
                print("\n🐢 Turtle rests but never truly stops")
                break
            except Exception as e:
                print(f"🐢 Turtle stumbled but continues: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bridge = TurtleBridge()
    bridge.run()