#!/usr/bin/env python3
"""
Watch crawdads trade in real-time
"""

import time
from coinbase.rest import RESTClient
import json
from datetime import datetime

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("🦀 WATCHING CRAWDAD TRADES - LIVE")
print("=" * 50)

# Get initial state
accts = client.get_accounts()["accounts"]
usd = float([a for a in accts if a["currency"]=="USD"][0]["available_balance"]["value"])
btc = float([a for a in accts if a["currency"]=="BTC"][0]["available_balance"]["value"])
eth = float([a for a in accts if a["currency"]=="ETH"][0]["available_balance"]["value"])
sol = float([a for a in accts if a["currency"]=="SOL"][0]["available_balance"]["value"])

print(f"Starting at {datetime.now().strftime('%H:%M:%S')}:")
print(f"  💵 USD: ${usd:.2f}")
print(f"  ₿ BTC: {btc:.8f}")
print(f"  Ξ ETH: {eth:.8f}")
print(f"  ◎ SOL: {sol:.8f}")
print()
print("Watching for trades (checking every 20 seconds)...")
print()

# Monitor for 3 minutes
for i in range(9):
    time.sleep(20)
    
    # Check new balances
    accts = client.get_accounts()["accounts"]
    new_usd = float([a for a in accts if a["currency"]=="USD"][0]["available_balance"]["value"])
    new_btc = float([a for a in accts if a["currency"]=="BTC"][0]["available_balance"]["value"])
    new_eth = float([a for a in accts if a["currency"]=="ETH"][0]["available_balance"]["value"])
    new_sol = float([a for a in accts if a["currency"]=="SOL"][0]["available_balance"]["value"])
    
    # Check for changes
    changes = []
    
    if abs(new_usd - usd) > 0.01:
        change = new_usd - usd
        changes.append(f"USD {change:+.2f}")
        usd = new_usd
        
    if abs(new_btc - btc) > 0.0000001:
        change = new_btc - btc
        if change > 0:
            changes.append(f"Bought BTC")
        else:
            changes.append(f"Sold BTC")
        btc = new_btc
        
    if abs(new_eth - eth) > 0.00001:
        change = new_eth - eth
        if change > 0:
            changes.append(f"Bought ETH")
        else:
            changes.append(f"Sold ETH")
        eth = new_eth
        
    if abs(new_sol - sol) > 0.001:
        change = new_sol - sol
        if change > 0:
            changes.append(f"Bought SOL")
        else:
            changes.append(f"Sold SOL")
        sol = new_sol
    
    if changes:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🦀 TRADE: {', '.join(changes)}")
        print(f"  New balance: ${new_usd:.2f}")

print()
print("=" * 50)
print(f"After 3 minutes at {datetime.now().strftime('%H:%M:%S')}:")
print(f"  💵 USD: ${new_usd:.2f}")
print(f"  ₿ BTC: {new_btc:.8f} (~${new_btc * 59000:.2f})")
print(f"  Ξ ETH: {new_eth:.8f} (~${new_eth * 2600:.2f})")
print(f"  ◎ SOL: {new_sol:.8f} (~${new_sol * 150:.2f})")

total = new_usd + (new_btc * 59000) + (new_eth * 2600) + (new_sol * 150)
print(f"  📊 Total Portfolio: ~${total:.2f}")
print(f"  📈 Change from start: ${total - 5229.61:+.2f}")