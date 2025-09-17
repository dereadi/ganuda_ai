#!/usr/bin/env python3
"""Test if we can connect to Telegram at all"""
import requests

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
url = f"https://api.telegram.org/bot{TOKEN}/getMe"

print("Testing Telegram connection...")
resp = requests.get(url)
data = resp.json()

if data.get("ok"):
    bot_info = data.get("result", {})
    print(f"✅ Connected! Bot: @{bot_info.get('username')}")
    print(f"Bot name: {bot_info.get('first_name')}")
    print(f"Can join groups: {bot_info.get('can_join_groups')}")
    print(f"Can read all group messages: {bot_info.get('can_read_all_group_messages')}")
    
    # Now get recent messages
    print("\nChecking for messages...")
    updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    updates_resp = requests.get(updates_url)
    updates_data = updates_resp.json()
    
    if updates_data.get("ok"):
        messages = updates_data.get("result", [])
        print(f"Found {len(messages)} pending updates")
        
        for update in messages[-5:]:  # Last 5 messages
            if "message" in update:
                msg = update["message"]
                text = msg.get("text", "")
                user = msg["from"].get("first_name", "Unknown")
                chat_type = msg["chat"].get("type", "unknown")
                print(f"  [{chat_type}] {user}: {text[:50]}")
else:
    print(f"❌ Failed: {data}")