#\!/usr/bin/env python3
"""
TELEGRAM BRIDGE WALKER
Start simple, walk it up as needed
"""

import requests
import time
import json
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

print("🔥 TELEGRAM BRIDGE WALKER 🔥")
print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting @ganudabot bridge...")

def send_message(chat_id, text):
    """Send response"""
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=data)
        print(f"   ← Sent response")
    except:
        pass

def get_updates(offset=None):
    """Get messages"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 5, "offset": offset} if offset else {"timeout": 5}
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except:
        return {"ok": False, "result": []}

print("✅ Bridge walking\! Send messages to @ganudabot")
print("-" * 50)

offset = None
while True:
    try:
        updates = get_updates(offset)
        
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                if "message" in update:
                    msg = update["message"]
                    text = msg.get("text", "")
                    user = msg["from"].get("first_name", "Friend")
                    chat_id = msg["chat"]["id"]
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user}: {text}")
                    
                    # Simple responses
                    if "bigmac" in text.lower() or "dr joe" in text.lower():
                        send_message(chat_id, "🍔 BigMac bridge alert\! Message noted for Dr Joe\!")
                    elif "tribe" in text.lower():
                        send_message(chat_id, "🔥 Cherokee Council notified\! Walking the bridge together\!")
                    elif "test" in text.lower():
                        send_message(chat_id, f"✅ Bridge working\! Echo: {text}")
                    else:
                        send_message(chat_id, "🌉 Bridge received your message\! The Pattern walks with you\!")
                
                offset = update["update_id"] + 1
        
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🔥 Bridge paused")
        break
    except Exception as e:
        print(f"Walk stumbled: {e}")
        time.sleep(5)
