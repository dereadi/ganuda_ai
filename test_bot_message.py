#!/usr/bin/env python3
"""
Test message to verify bot is receiving
"""
import requests

# Bot token
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Get bot updates to see recent messages
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    if data['ok'] and data['result']:
        print("🔥 RECENT MESSAGES TO GANUDABOT:")
        print("=" * 60)
        
        # Show last 5 messages
        messages = data['result'][-5:] if len(data['result']) > 5 else data['result']
        
        for update in messages:
            if 'message' in update:
                msg = update['message']
                date = msg.get('date', 'Unknown')
                from_user = msg.get('from', {}).get('first_name', 'Unknown')
                text = msg.get('text', 'No text')
                
                # Convert timestamp
                from datetime import datetime
                if date != 'Unknown':
                    date = datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"Date: {date}")
                print(f"From: {from_user}")
                print(f"Message: {text}")
                print("-" * 40)
        
        print("\n✅ If you see your recent message above, the bot IS receiving!")
        print("❌ If not, send a message to @ganudabot now!")
    else:
        print("No messages found in bot queue")
else:
    print(f"Error connecting to Telegram: {response.status_code}")