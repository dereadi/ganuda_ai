#!/usr/bin/env python3
"""
🚨 EMERGENCY LIQUIDITY BLEED - GET CASH NOW
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

positions = []
usd_balance = 0

for account in accounts:
    currency = account["currency"]
    balance = float(account["available_balance"]["value"])
    
    if currency == "USD":
        usd_balance = balance
        print(f"💵 Current USD: ${balance:.2f}")
    elif currency == "USDC":
        # Skip USDC - can't trade it directly
        continue
    elif balance > 0.00001:
        try:
            ticker = client.get_product(f"{currency}-USD")
            price = float(ticker.get("price", 0))
            value = balance * price
            
            if value > 10:  # Only care about positions worth >$10
                positions.append({
                    "coin": currency,
                    "balance": balance,
                    "price": price,
                    "value": value
                })
                print(f"• {currency}: {balance:.6f} @ ${price:.2f} = ${value:.2f}")
        except:
            pass

print(f"\n💰 Need to raise: ${250 - usd_balance:.2f}")
print("=" * 60)

# Sort by value (sell smallest first to preserve larger positions)
positions.sort(key=lambda x: x["value"])

raised = 0
target = 250 - usd_balance

for pos in positions:
    if raised >= target:
        break
    
    # Calculate how much to sell
    if pos["value"] < 100:
        # Sell entire small positions
        sell_amount = pos["balance"]
    else:
        # Sell partial of larger positions (20%)
        sell_amount = pos["balance"] * 0.2
    
    # Round appropriately
    if pos["coin"] == "BTC":
        sell_amount = round(sell_amount, 8)
    elif pos["coin"] in ["ETH", "SOL"]:
        sell_amount = round(sell_amount, 4)
    else:
        sell_amount = round(sell_amount, 2)
    
    if sell_amount < 0.001:
        continue
    
    try:
        print(f"\n💸 Selling {sell_amount} {pos['coin']}...")
        
        order = client.market_order_sell(
            client_order_id=f"emergency_{pos['coin']}_{int(time.time()*1000)}",
            product_id=f"{pos['coin']}-USD",
            base_size=str(sell_amount)
        )
        
        value = sell_amount * pos["price"]
        raised += value
        print(f"✅ Sold {sell_amount} {pos['coin']} for ~${value:.2f}")
        
        time.sleep(0.5)  # Small delay between orders
        
    except Exception as e:
        print(f"❌ Failed to sell {pos['coin']}: {str(e)[:100]}")

print("\n" + "=" * 60)
print(f"💰 Total raised: ${raised:.2f}")
print(f"💵 New balance: ~${usd_balance + raised:.2f}")

if usd_balance + raised >= 250:
    print("✅ Liquidity target achieved!")
else:
    print(f"⚠️  Still need ${250 - (usd_balance + raised):.2f} more")