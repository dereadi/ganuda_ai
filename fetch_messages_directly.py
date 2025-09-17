#!/usr/bin/env python3
"""Fetch messages directly from Telegram API"""
import requests
import json
from datetime import datetime

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# First, get the latest update ID
response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"limit": 1})
if response.status_code == 200:
    data = response.json()
    if data["ok"] and data["result"]:
        last_update = data["result"][-1]["update_id"]
        
        # Now get ALL updates after that ID minus 10
        response2 = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates", 
            params={"offset": last_update - 10, "limit": 20}
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            if data2["ok"]:
                print(f"🔥 LAST 10 MESSAGES FROM TELEGRAM")
                print("="*60)
                
                messages = []
                for update in data2["result"]:
                    if "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        messages.append({
                            "user": msg["from"]["first_name"],
                            "text": msg["text"],
                            "time": datetime.fromtimestamp(msg["date"]).strftime("%H:%M:%S")
                        })
                
                # Show last 5 messages
                for msg in messages[-5:]:
                    print(f"\n👤 {msg['user']} at {msg['time']}:")
                    print(f"   📝 {msg['text']}")
                    print("-"*40)
            else:
                print("Error:", data2)
else:
    print(f"Failed: {response.status_code}")
    print(response.text)