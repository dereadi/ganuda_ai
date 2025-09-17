#\!/usr/bin/env python3
"""Test Telegram connection"""

import requests

# Test with ganudabot
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

print("🔥 Testing Telegram connection...")

# Test getMe
try:
    response = requests.get(f"{BASE_URL}/getMe")
    data = response.json()
    if data["ok"]:
        bot_info = data["result"]
        print(f"✅ Connected to: @{bot_info['username']}")
        print(f"   Bot name: {bot_info['first_name']}")
        print(f"   Bot ID: {bot_info['id']}")
    else:
        print(f"❌ Connection failed: {data}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🔥 Ready to bridge worlds\!")
