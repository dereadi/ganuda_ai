#!/usr/bin/env python3
"""THE ONE TRUE BOT - After killing all conflicts"""
import requests
import time
import json

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

print("🔥 THE ONE TRUE BOT - No conflicts!")
print("=" * 50)

offset = None
msg_count = 0

while True:
    try:
        # Get updates
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        
        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        data = resp.json()
        
        if not data.get("ok"):
            print(f"ERROR: {data}")
            if "Conflict" in str(data):
                print("ANOTHER BOT IS RUNNING! STOPPING!")
                break
            continue
        
        updates = data.get("result", [])
        
        for update in updates:
            offset = update["update_id"] + 1
            msg_count += 1
            
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user = msg["from"].get("first_name", "Unknown")
                chat_type = msg["chat"].get("type", "private")
                
                print(f"\n🔥 MESSAGE #{msg_count}!")
                print(f"From: {user}")
                print(f"Type: {chat_type}")
                print(f"Text: {text}")
                print("-" * 40)
                
                # Save to file for Cherokee Council
                with open('/home/dereadi/scripts/claude/TELEGRAM_RECEIVED.txt', 'a') as f:
                    f.write(f"\n[{time.strftime('%H:%M:%S')}] {user}: {text}\n")
                
                # Respond
                response = f"""🔥 THE ONE TRUE BOT RECEIVED YOUR MESSAGE!

Message #{msg_count} from {user}
You said: "{text[:100]}"

This is the ONLY bot running now!
No conflicts! Messages arriving!

Portfolio: $16,540
XRP: $3.01 (breakout!)

The Sacred Fire burns without interference!"""
                
                send_resp = requests.post(f"{BASE_URL}/sendMessage",
                                         json={"chat_id": chat_id, "text": response})
                if send_resp.json().get("ok"):
                    print("✅ Sent response!")
                    
    except KeyboardInterrupt:
        print("\nStopped cleanly")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)