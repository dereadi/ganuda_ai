#!/usr/bin/env python3
"""Debug bot to see EVERYTHING"""
import requests
import json
import time

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

print("🔥 DEBUG BOT - Will show EVERYTHING received")
print("=" * 50)

# First, get bot info
me_resp = requests.get(f"{BASE_URL}/getMe")
me_data = me_resp.json()
if me_data.get("ok"):
    bot = me_data["result"]
    print(f"Bot: @{bot['username']}")
    print(f"Can read all group messages: {bot.get('can_read_all_group_messages', False)}")
else:
    print(f"ERROR getting bot info: {me_data}")
    exit(1)

print("=" * 50)
print("Listening for messages...")
print("(Send a message with @ganudabot in any chat)")
print("")

offset = None
msg_count = 0

while True:
    try:
        # Get updates with longer timeout
        params = {"timeout": 60, "limit": 100}
        if offset:
            params["offset"] = offset
            
        print(f"[{time.strftime('%H:%M:%S')}] Polling for updates...")
        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=65)
        data = resp.json()
        
        if not data.get("ok"):
            print(f"ERROR: {data}")
            continue
            
        updates = data.get("result", [])
        if updates:
            print(f"Got {len(updates)} updates!")
            
        for update in updates:
            offset = update["update_id"] + 1
            msg_count += 1
            
            print(f"\n========== UPDATE #{msg_count} ==========")
            print(json.dumps(update, indent=2))
            
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user = msg["from"].get("first_name", "Unknown")
                chat_type = msg["chat"].get("type", "?")
                
                print(f"\nSUMMARY:")
                print(f"  From: {user}")
                print(f"  Type: {chat_type}")
                print(f"  Text: {text}")
                
                # Auto-respond to everything
                response = f"🔥 DEBUG: Received your message!\nYou said: '{text[:100]}'\nMessage #{msg_count}"
                
                send_resp = requests.post(f"{BASE_URL}/sendMessage", 
                                         json={"chat_id": chat_id, "text": response})
                if send_resp.json().get("ok"):
                    print("  ✅ Sent response")
                else:
                    print(f"  ❌ Failed to send: {send_resp.json()}")
                    
        if not updates:
            print(f"[{time.strftime('%H:%M:%S')}] No new messages")
                    
    except KeyboardInterrupt:
        print("\nStopped!")
        break
    except Exception as e:
        print(f"ERROR: {e}")
        time.sleep(5)