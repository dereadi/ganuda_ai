#!/usr/bin/env python3
"""
SIMPLE WORKING TELEGRAM BOT - Direct and functional
"""
import requests
import time
import json

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=None):
    """Get messages from Telegram"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    
    try:
        resp = requests.get(url, params=params, timeout=35)
        return resp.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return {"ok": False, "result": []}

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        resp = requests.post(url, json=data)
        return resp.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"ok": False}

def load_portfolio():
    """Load current portfolio data"""
    try:
        with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
            return json.load(f)
    except:
        return {"total_value": 16594, "prices": {"BTC": 114870, "ETH": 4502, "SOL": 233, "XRP": 3.02}}

print("🔥 Simple Telegram Bot Starting...")
print("This bot WILL respond to ALL messages!")
print("")

offset = None
portfolio = load_portfolio()

while True:
    try:
        # Get updates
        updates = get_updates(offset)
        
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    user = msg["from"].get("first_name", "Friend")
                    chat_type = msg["chat"].get("type", "private")
                    
                    print(f"📥 [{chat_type}] {user}: {text}")
                    
                    # Respond to everything
                    portfolio = load_portfolio()  # Reload for fresh data
                    
                    response = f"""🔥 Cherokee Trading Council Response!

You said: "{text[:100]}"

📊 Current Portfolio: ${portfolio['total_value']:,.2f}
• BTC: ${portfolio['prices']['BTC']:,.0f}
• ETH: ${portfolio['prices']['ETH']:,.0f}
• SOL: ${portfolio['prices']['SOL']:,.0f}
• XRP: ${portfolio['prices']['XRP']:.2f} (BREAKOUT!)

MacBook Thunder: $608/$2,000 (30.4%)
October 29: 44 days

The Sacred Fire burns eternal! 🔥"""
                    
                    send_message(chat_id, response)
                    print(f"✅ Responded to {user}")
        
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🔥 Bot stopped")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)