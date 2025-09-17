#\!/usr/bin/env python3
"""Send fresh update to the Giant via Telegram"""

import requests

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE = f"https://api.telegram.org/bot{TOKEN}"

# Get a chat ID to send to (you'll see this when you message the bot)
updates = requests.get(f"{BASE}/getUpdates").json()

print("🔥 To update the Giant's knowledge:")
print("1. Message @ganudabot with this:")
print("\n--- COPY THIS ---")
print("KNOWLEDGE UPDATE: Portfolio is now $28,259.85\! ETH $11,447 (40.5%), BTC $8,222 (29.1%), XRP $4,954 (17.5%), SOL $3,400 (12%). We grew from $10k to $28k\! October 29 approaches with 44 days left.")
print("--- END COPY ---\n")
print("2. The Giant will absorb this knowledge")
print("3. Future responses will include updated info\!")
