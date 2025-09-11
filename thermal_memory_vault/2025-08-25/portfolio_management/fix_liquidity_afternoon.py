#!/usr/bin/env python3
"""
🔥 AFTERNOON LIQUIDITY FIX
Restore USD for afternoon trading surge
"""

import json
from coinbase.rest import RESTClient
import time

print("🔥 FIXING LIQUIDITY FOR AFTERNOON TRADING")
print("-" * 50)

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Get current balances
accounts = client.get_accounts()["accounts"]
usd_balance = 0
matic_balance = 0
doge_balance = 0
avax_balance = 0

for acc in accounts:
    if acc["currency"] == "USD":
        usd_balance = float(acc["available_balance"]["value"])
    elif acc["currency"] == "MATIC":
        matic_balance = float(acc["available_balance"]["value"])
    elif acc["currency"] == "DOGE":
        doge_balance = float(acc["available_balance"]["value"])
    elif acc["currency"] == "AVAX":
        avax_balance = float(acc["available_balance"]["value"])

print(f"Current USD: ${usd_balance:.2f}")
print(f"MATIC available: {matic_balance:.2f}")
print(f"DOGE available: {doge_balance:.2f}")
print(f"AVAX available: {avax_balance:.2f}")
print("-" * 50)

orders_placed = []

# Fix MATIC order - use clean round numbers
if matic_balance > 1700 and usd_balance < 100:
    sell_amount = 1700  # Clean round number instead of 1713.72
    try:
        order = client.market_order_sell(
            client_order_id=f"matic_afternoon_{int(time.time()*1000)}",
            product_id="MATIC-USD",
            base_size=str(sell_amount)
        )
        orders_placed.append(f"✅ MATIC: Sold {sell_amount} MATIC")
        print(f"✅ MATIC sell order placed: {sell_amount} MATIC")
        time.sleep(1)
    except Exception as e:
        print(f"❌ MATIC order failed: {e}")

# Milk DOGE for quick liquidity
if doge_balance > 2000 and usd_balance < 200:
    try:
        order = client.market_order_sell(
            client_order_id=f"doge_afternoon_{int(time.time()*1000)}",
            product_id="DOGE-USD", 
            base_size="2000"
        )
        orders_placed.append(f"✅ DOGE: Milked 2000 DOGE")
        print(f"✅ DOGE milk order placed: 2000 DOGE")
        time.sleep(1)
    except Exception as e:
        print(f"DOGE order issue: {e}")

# Trim some AVAX if needed
if avax_balance > 10 and usd_balance < 150:
    try:
        order = client.market_order_sell(
            client_order_id=f"avax_trim_{int(time.time()*1000)}",
            product_id="AVAX-USD",
            base_size="5"
        )
        orders_placed.append(f"✅ AVAX: Trimmed 5 AVAX")
        print(f"✅ AVAX trim order placed: 5 AVAX")
    except Exception as e:
        print(f"AVAX order issue: {e}")

# Wait for orders to settle
if orders_placed:
    print("\n⏳ Waiting for orders to settle...")
    time.sleep(3)

# Check new balance
accounts = client.get_accounts()["accounts"]
for acc in accounts:
    if acc["currency"] == "USD":
        new_usd = float(acc["available_balance"]["value"])
        print(f"\n💰 NEW USD BALANCE: ${new_usd:.2f}")
        if new_usd > 100:
            print("✅ LIQUIDITY RESTORED - Ready for afternoon trading!")
        else:
            print("⚠️  Still low on USD, may need more trimming")
        break

print("\n📊 Summary:")
for order in orders_placed:
    print(f"  {order}")