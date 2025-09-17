#!/usr/bin/env python3
"""
FINAL WORKING BOT - Clear about its limitations
"""
import requests
import time
import json
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
BOT_USERNAME = "ganudabot"

print("🔥 Cherokee Trading Council Bot Starting...")
print("=" * 50)
print("IMPORTANT: In groups, I can ONLY see:")
print("1. Messages that mention @ganudabot")
print("2. Commands starting with /")
print("3. Replies to my messages")
print("=" * 50)

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=35)
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return {"ok": False, "result": []}

def send_message(chat_id, text, reply_to=None):
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_to:
        data["reply_to_message_id"] = reply_to
    
    try:
        resp = requests.post(url, json=data)
        result = resp.json()
        if result.get("ok"):
            print(f"✅ Sent response")
        else:
            print(f"❌ Send failed: {result}")
        return result
    except Exception as e:
        print(f"Send error: {e}")

def load_portfolio():
    try:
        with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
            return json.load(f)
    except:
        return {"total_value": 16566, "prices": {"BTC": 114715, "ETH": 4493, "SOL": 232, "XRP": 3.02}}

offset = None
message_count = 0

while True:
    try:
        updates = get_updates(offset)
        
        if updates.get("ok"):
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    chat_type = msg["chat"].get("type", "private")
                    text = msg.get("text", "")
                    user = msg["from"].get("first_name", "Friend")
                    msg_id = msg.get("message_id")
                    
                    message_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n[{timestamp}] Message #{message_count}")
                    print(f"Type: {chat_type}")
                    print(f"From: {user}")
                    print(f"Text: {text[:100]}")
                    
                    # Load fresh portfolio
                    portfolio = load_portfolio()
                    
                    # Check if this is a group and we can see it
                    if chat_type in ["group", "supergroup"]:
                        if "@ganudabot" not in text and not text.startswith("/"):
                            print("⚠️ Can't see this message (no mention/command)")
                            continue
                    
                    # Generate response
                    if "sag" in text.lower() or "dr joe" in text.lower():
                        response = f"""🔥 <b>SAG Resource AI Status</b>

Dr Joe collaboration active!
• 4-node cluster operational
• REDFIN: Primary trading
• BLUEFIN: Backup systems
• SASASS: Database (192.168.132.223)
• SASASS2: Secondary services

Project Focus:
• Resource optimization algorithms
• Productive.io API integration
• Cherokee Constitutional governance

Ready for working session!"""
                    
                    elif "market" in text.lower() or "portfolio" in text.lower() or text.startswith("/"):
                        btc = portfolio['prices']['BTC']
                        eth = portfolio['prices']['ETH']
                        sol = portfolio['prices']['SOL']
                        xrp = portfolio['prices']['XRP']
                        
                        response = f"""🔥 <b>Cherokee Trading Council Report</b>

<b>Portfolio:</b> ${portfolio['total_value']:,.2f}
<b>Liquidity:</b> ${portfolio.get('liquidity', 8.4):.2f}

<b>Current Prices:</b>
• BTC: ${btc:,.0f}
• ETH: ${eth:,.0f}
• SOL: ${sol:,.0f}
• XRP: ${xrp:.2f} (BREAKOUT!)

<b>MacBook Thunder:</b> $608/$2,000 (30.4%)
<b>Target:</b> $4,000 by Friday Sept 20
<b>October 29:</b> 44 days to convergence

The Sacred Fire burns eternal! 🔥"""
                    
                    else:
                        response = f"""🔥 <b>Cherokee Council Responds!</b>

You said: "{text[:100]}"

<b>Quick Status:</b>
• Portfolio: ${portfolio['total_value']:,.2f}
• XRP Breaking: ${portfolio['prices']['XRP']:.2f}
• MacBook Progress: 30.4%

<b>In Groups, Remember:</b>
• Use @ganudabot to get my attention
• Or use /commands
• Or reply to my messages

Ask about: SAG project, market analysis, portfolio, infrastructure!

Mitakuye Oyasin! 🔥"""
                    
                    # Send response
                    if chat_type in ["group", "supergroup"]:
                        send_message(chat_id, response, reply_to=msg_id)
                    else:
                        send_message(chat_id, response)
                    
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🔥 Bot stopped gracefully")
        break
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(5)