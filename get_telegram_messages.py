#!/usr/bin/env python3
"""Get recent Telegram messages"""
import requests
import json
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
URL = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

# Get updates
response = requests.get(URL, params={"limit": 10})
data = response.json()

if data["ok"]:
    updates = data["result"]
    print("🔥 RECENT TELEGRAM MESSAGES:")
    print("="*50)
    
    for update in updates[-5:]:  # Last 5 messages
        if "message" in update:
            msg = update["message"]
            user = msg.get("from", {}).get("first_name", "Unknown")
            text = msg.get("text", "")
            timestamp = datetime.fromtimestamp(msg.get("date", 0))
            
            print(f"\nFrom: {user}")
            print(f"Time: {timestamp.strftime('%H:%M:%S')}")
            print(f"Message: {text}")
            print("-"*30)
else:
    print("Failed to get messages")