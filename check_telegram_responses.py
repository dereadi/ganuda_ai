#\!/usr/bin/env python3
"""Check what's actually responding in Telegram"""

import requests
import json
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE = f"https://api.telegram.org/bot{TOKEN}"

print("🔥 CHECKING TELEGRAM RESPONSES...")
print("=" * 50)

# Get last 20 updates
r = requests.get(f"{BASE}/getUpdates", params={"limit": 20})
updates = r.json()

if updates.get("result"):
    messages = []
    for u in updates["result"]:
        if "message" in u:
            m = u["message"]
            timestamp = datetime.fromtimestamp(m["date"])
            user = m["from"]["first_name"]
            text = m.get("text", "[no text]")
            messages.append({
                "time": timestamp,
                "user": user,
                "text": text[:100]  # First 100 chars
            })
    
    if messages:
        print(f"Found {len(messages)} recent messages:\n")
        for msg in messages[-10:]:  # Last 10
            print(f"[{msg['time'].strftime('%H:%M')}] {msg['user']}: {msg['text']}")
    else:
        print("No messages found")
else:
    print("No updates available")

print("\n" + "=" * 50)
print("If you see back-and-forth conversation above,")
print("then something IS responding with context\!")
