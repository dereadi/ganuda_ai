#!/usr/bin/env python3
"""
🔥 QUICK MARKET CHECK
"""

import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("🔥 AFTERNOON MARKET SNAPSHOT")
print("=" * 50)

coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "DOGE"]

for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker["price"])
        print(f"{coin:6} ${price:>12,.2f}")
    except:
        pass

print("=" * 50)

# Check our positions
accounts = client.get_accounts()["accounts"]
eth_found = False

for acc in accounts:
    currency = acc["currency"]
    balance = float(acc["available_balance"]["value"])
    
    if currency == "ETH" and balance > 0:
        ticker = client.get_product("ETH-USD")
        eth_price = float(ticker["price"])
        value = balance * eth_price
        
        print(f"\n🔷 ETH POSITION UPDATE:")
        print(f"  Balance: {balance:.6f} ETH")
        print(f"  Current: ${eth_price:.2f}")
        print(f"  Value: ${value:.2f}")
        print(f"  Entry: $4575.70")
        
        pnl = ((eth_price - 4575.70) / 4575.70) * 100
        pnl_usd = (eth_price - 4575.70) * balance
        
        print(f"  P&L: {pnl:+.2f}% (${pnl_usd:+.2f})")
        
        if pnl > 2:
            print("  🎯 Near +3% target ($4712.97)!")
        elif pnl < -1.5:
            print("  ⚠️ Approaching -2% stop ($4484.19)")
        else:
            print("  ✅ Trade in progress")
        eth_found = True
        
    elif currency == "USD":
        if balance > 0:
            print(f"\n💰 USD: ${balance:.2f}")

if not eth_found:
    print("\n⚠️ No ETH position found - may have been stopped out or sold")

# Check if specialists are running
import subprocess
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
specialists = result.stdout.count("specialist.py")
print(f"\n🤖 Active Specialists: {specialists}")

print("=" * 50)