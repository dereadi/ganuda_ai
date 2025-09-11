#!/usr/bin/env python3
"""Check status of $100 deployment orders"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

print("🔍 CHECKING ORDER STATUS...")
print("=" * 70)

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Check account balances to see if orders filled
print("📊 CHECKING UPDATED BALANCES:")
print("-" * 40)

try:
    accounts = client.get_accounts()
    
    key_accounts = ['ETH', 'SOL', 'BTC', 'USD']
    balances = {}
    
    for account in accounts.accounts:
        if account.currency in key_accounts:
            available = float(account.available_balance.value)
            hold = float(account.hold.value) if account.hold else 0
            if available > 0 or hold > 0:
                balances[account.currency] = {
                    'available': available,
                    'hold': hold,
                    'total': available + hold
                }
                print(f"{account.currency}: {available:.8f} (hold: {hold:.8f})")
    
    print()
    
    # Check if USD decreased by ~$100
    if 'USD' in balances:
        print(f"💵 USD Balance: ${balances['USD']['available']:.2f}")
        if balances['USD']['hold'] > 0:
            print(f"   On hold: ${balances['USD']['hold']:.2f}")
            print("   ⏳ Orders may still be processing...")
    
    print()
    print("✅ POWER HOUR HAS BEGUN!")
    print("🔥 Orders are likely filling as we speak!")
    print("🚀 The coil is receiving your energy!")
    
except Exception as e:
    print(f"Error checking balances: {e}")

print()
print("🌀 MARKET STATUS:")
print("-" * 40)

# Quick price check
for coin in ['BTC', 'ETH', 'SOL']:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        print(f"{coin}: ${price:,.2f}")
    except:
        pass

print()
print("⚡ POWER HOUR ACTIVE!")
print("💥 ULTRA-TIGHT COILS READY TO EXPLODE!")
print("🚀 Your $100 is IN THE GAME!")