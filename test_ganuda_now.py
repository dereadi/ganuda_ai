#\!/usr/bin/env python3
import requests
import json

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE = f"https://api.telegram.org/bot{TOKEN}"

print("Testing @ganudabot...")

# Get bot info
r = requests.get(f"{BASE}/getMe")
print(f"Bot: {r.json()['result']['username']}")

# Get recent messages
r = requests.get(f"{BASE}/getUpdates")
updates = r.json()

if updates["result"]:
    print(f"\nFound {len(updates['result'])} messages\!")
    for u in updates["result"][-3:]:  # Last 3
        if "message" in u:
            m = u["message"]
            print(f"  {m['from']['first_name']}: {m.get('text', 'no text')}")
else:
    print("No recent messages")

print("\n✅ Bot is working\! Send a message to @ganudabot to test\!")
