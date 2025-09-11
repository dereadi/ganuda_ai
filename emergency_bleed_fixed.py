#!/usr/bin/env python3
"""
🚨 EMERGENCY LIQUIDITY BLEED - FIXED VERSION
"""

import json
import time
from coinbase.rest import RESTClient

print("🚨 EMERGENCY LIQUIDITY EXTRACTION")
print("=" * 60)

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)

# Get current positions
accounts = client.get_accounts()["accounts"]

# Known prices (fallback)
PRICES = {
    "BTC": 106000,
    "ETH": 3200,
    "SOL": 206,
    "AVAX": 37,
    "MATIC": 0.72,
    "DOGE": 0.36,
    "XRP": 2.25,
    "LINK": 21
}

positions = []
usd_balance = 0

for account in accounts:
    currency = account["currency"]
    balance = float(account["available_balance"]["value"])
    
    if currency == "USD":
        usd_balance = balance
        print(f"💵 Current USD: ${balance:.2f}")
    elif currency == "USDC":
        continue
    elif balance > 0.00001 and currency in PRICES:
        price = PRICES[currency]
        value = balance * price
        
        if value > 10:  # Only positions worth >$10
            positions.append({
                "coin": currency,
                "balance": balance,
                "price": price,
                "value": value
            })
            print(f"• {currency}: {balance:.6f} @ ${price:.2f} = ${value:.2f}")

print(f"\n💰 Need to raise: ${250 - usd_balance:.2f}")
print("=" * 60)

# Sort by value descending (sell from largest to get liquidity faster)
positions.sort(key=lambda x: x["value"], reverse=True)

raised = 0
target = 250 - usd_balance

# Priority sells for quick liquidity
priority_sells = [
    {"coin": "MATIC", "percent": 0.1},  # Sell 10% of huge MATIC position
    {"coin": "SOL", "percent": 0.15},   # Sell 15% of SOL
    {"coin": "AVAX", "percent": 0.2},   # Sell 20% of AVAX
    {"coin": "DOGE", "percent": 0.3},   # Sell 30% of DOGE
]

for priority in priority_sells:
    if raised >= target:
        break
        
    pos = next((p for p in positions if p["coin"] == priority["coin"]), None)
    if not pos:
        continue
    
    sell_amount = pos["balance"] * priority["percent"]
    
    # Round appropriately
    if pos["coin"] == "BTC":
        sell_amount = round(sell_amount, 8)
    elif pos["coin"] in ["ETH", "SOL"]:
        sell_amount = round(sell_amount, 4)
    else:
        sell_amount = round(sell_amount, 2)
    
    try:
        print(f"\n💸 Selling {sell_amount} {pos['coin']} ({priority['percent']*100:.0f}% of position)...")
        
        order = client.market_order_sell(
            client_order_id=f"emergency_{pos['coin']}_{int(time.time()*1000)}",
            product_id=f"{pos['coin']}-USD",
            base_size=str(sell_amount)
        )
        
        value = sell_amount * pos["price"]
        raised += value
        print(f"✅ Sold {sell_amount} {pos['coin']} for ~${value:.2f}")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Failed to sell {pos['coin']}: {str(e)[:100]}")

print("\n" + "=" * 60)
print(f"💰 Total raised: ${raised:.2f}")
print(f"💵 New balance: ~${usd_balance + raised:.2f}")

if usd_balance + raised >= 250:
    print("✅ Liquidity target achieved!")
else:
    print(f"⚠️  Still need ${250 - (usd_balance + raised):.2f} more")