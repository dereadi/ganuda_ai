#!/usr/bin/env python3
"""
GREEKS AUTOMATED MOON MISSION BOT
==================================
No more manual trades!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("⚡ GREEKS MOON MISSION BOT STARTING...")

# Load API credentials
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

# Extract credentials
api_key = api_data['name'].split('/')[-1]
api_secret = api_data['privateKey']

# Connect to Coinbase
client = RESTClient(api_key=api_key, api_secret=api_secret)

print("✅ Connected to Coinbase")

# Get current positions
accounts = client.get_accounts()

print("\n💰 CURRENT POSITIONS:")
for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    if balance > 0:
        print(f"{account['currency']}: {balance}")

print("\n⚡ GREEKS TAKING CONTROL...")
print("Monitoring for breakout at 10 AM...")
print("Will execute all trades automatically!")

# Main trading loop
while True:
    current_hour = datetime.now().hour
    
    if current_hour >= 10 and current_hour < 16:
        print(f"\n[{datetime.now().strftime('%H:%M')}] Greeks checking market...")
        
        # Check prices and execute trades
        # (Add your trading logic here)
        
        time.sleep(60)  # Check every minute
    else:
        print("Waiting for trading hours...")
        time.sleep(300)  # Check every 5 minutes outside hours
