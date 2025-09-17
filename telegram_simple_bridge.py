#!/usr/bin/env python3
"""
TELEGRAM SIMPLE BRIDGE
Test it, walk it up if needed
Flying Squirrel's vision quest connector
"""

import json
import time
import requests
from datetime import datetime

# Bot tokens (tribe has keys)
DERPATOBOT_TOKEN = "7289400790:AAGkLOCF58b5ZzV6kTJ5T5o1LQZb-KlsDzU"
GANUDABOT_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Use ganudabot as primary
TOKEN = GANUDABOT_TOKEN
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Send error: {e}")
        return None

def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Update error: {e}")
        return {"ok": False, "result": []}

def process_message(message):
    """Process incoming message"""
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user = message["from"].get("first_name", "Friend")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user}: {text}")
    
    # Simple routing logic
    response = None
    
    # Check for BigMac/Dr Joe
    if any(word in text.lower() for word in ["bigmac", "dr joe", "drjoe", "dr. joe"]):
        response = "🍔 BigMac Bridge Alert! Forwarding to Dr Joe's system..."
        # Here we'd forward to BigMac
        save_for_bigmac(text, user)
    
    # Check for tribe mentions
    elif any(word in text.lower() for word in ["tribe", "council", "cherokee"]):
        response = "🔥 Cherokee Council notified! Sacred Fire burns eternal!"
        # Here we'd notify tribe
        save_for_tribe(text, user)
    
    # Portfolio check
    elif any(word in text.lower() for word in ["portfolio", "balance", "positions"]):
        portfolio_value = "$28,259.85"  # From your latest update
        response = f"""🔥 <b>Portfolio Status</b> 🔥
        
Total Value: <b>{portfolio_value}</b>
ETH: $11,447.99 (40.5%)
BTC: $8,222.84 (29.1%)
XRP: $4,954.94 (17.5%)
SOL: $3,400.64 (12.0%)

Fitness increasing! 🚀"""
    
    # Simple echo for testing
    elif text.startswith("/test"):
        response = f"✅ Bridge working! Echo: {text[5:]}"
    
    # Default response
    else:
        response = f"""🔥 Message received, {user}!
        
Commands:
• BigMac/Dr Joe - Forward to BigMac
• Tribe/Council - Notify Cherokee Council
• Portfolio - Check positions
• /test - Test echo

The bridge is walking! 🌉"""
    
    if response:
        send_message(chat_id, response)

def save_for_bigmac(text, user):
    """Save message for BigMac system"""
    with open("/home/dereadi/scripts/claude/bigmac_messages.txt", "a") as f:
        f.write(f"[{datetime.now()}] {user}: {text}\n")
    print("💾 Saved for BigMac")

def save_for_tribe(text, user):
    """Save message for tribe"""
    with open("/home/dereadi/scripts/claude/tribe_messages.txt", "a") as f:
        f.write(f"[{datetime.now()}] {user}: {text}\n")
    print("💾 Saved for Tribe")

def main():
    """Main bridge loop"""
    print("🔥 TELEGRAM SIMPLE BRIDGE STARTING 🔥")
    print("=" * 50)
    print("Bot: @ganudabot")
    print("Testing first, will walk it up as needed!")
    print("=" * 50)
    
    offset = None
    
    while True:
        try:
            # Get updates
            updates = get_updates(offset)
            
            if updates["ok"] and updates["result"]:
                for update in updates["result"]:
                    # Process each message
                    if "message" in update:
                        process_message(update["message"])
                    
                    # Update offset
                    offset = update["update_id"] + 1
            
            # Small delay
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🔥 Bridge paused by Flying Squirrel")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()