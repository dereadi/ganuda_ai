#!/usr/bin/env python3
"""
🥛🚀 FIXED BATCH MILK EXECUTION - LET'S GO!
=========================================
Fixed API calls for proper execution
"""

import json
import time
import uuid
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🥛 BATCH MILK EXECUTION FIXED - GO! 🥛                  ║
║                        SOL at $214! ETH at $4465!                         ║
║                           Perfect Milk Timing! 🚀                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get current prices
print("\n📊 CURRENT PRICES:")
sol_price = float(client.get_product('SOL-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
matic_price = float(client.get_product('MATIC-USD')['price'])

print(f"  SOL: ${sol_price:.2f} - MILK ZONE! 🥛")
print(f"  ETH: ${eth_price:.2f} - WALKING UP! 📈")
print(f"  MATIC: ${matic_price:.4f}")

# Execute trades with proper API format
print("\n🚀 EXECUTING BATCH TRADES:")
print("-" * 70)

total_generated = 0
executed = []

# Trade 1: SOL partial milk
try:
    print("\n1. Milking SOL (0.5 SOL)...")
    sol_order = client.create_order(
        product_id="SOL-USD",
        side="SELL",
        order_configuration={
            "market_market_ioc": {
                "base_size": "0.5"
            }
        }
    )
    time.sleep(2)
    sol_value = 0.5 * sol_price
    total_generated += sol_value
    executed.append(f"SOL: ${sol_value:.2f}")
    print(f"   ✅ Sold 0.5 SOL for ~${sol_value:.2f}")
except Exception as e:
    print(f"   ❌ SOL failed: {str(e)[:50]}")

# Trade 2: ETH partial milk
try:
    print("\n2. Milking ETH (0.05 ETH)...")
    eth_order = client.create_order(
        product_id="ETH-USD",
        side="SELL",
        order_configuration={
            "market_market_ioc": {
                "base_size": "0.05"
            }
        }
    )
    time.sleep(2)
    eth_value = 0.05 * eth_price
    total_generated += eth_value
    executed.append(f"ETH: ${eth_value:.2f}")
    print(f"   ✅ Sold 0.05 ETH for ~${eth_value:.2f}")
except Exception as e:
    print(f"   ❌ ETH failed: {str(e)[:50]}")

# Trade 3: MATIC for stable liquidity
try:
    print("\n3. Milking MATIC (900 MATIC)...")
    matic_order = client.create_order(
        product_id="MATIC-USD",
        side="SELL",
        order_configuration={
            "market_market_ioc": {
                "base_size": "900"
            }
        }
    )
    time.sleep(2)
    matic_value = 900 * matic_price
    total_generated += matic_value
    executed.append(f"MATIC: ${matic_value:.2f}")
    print(f"   ✅ Sold 900 MATIC for ~${matic_value:.2f}")
except Exception as e:
    print(f"   ❌ MATIC failed: {str(e)[:50]}")

print("\n" + "=" * 70)
print("📊 BATCH EXECUTION SUMMARY:")
print("-" * 70)

if executed:
    for trade in executed:
        print(f"  {trade}")
    print(f"\n💰 TOTAL LIQUIDITY GENERATED: ${total_generated:.2f}")
    print(f"   Fees (~0.6%): ${total_generated * 0.006:.2f}")
    print(f"   Net Liquidity: ${total_generated * 0.994:.2f}")
else:
    print("  ⚠️ No trades executed successfully")

# Check new balance
time.sleep(3)
try:
    accounts = client.get_accounts()['accounts']
    new_usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])
    print(f"\n💵 NEW USD BALANCE: ${new_usd:.2f}")
    print(f"   Increase: ${new_usd - 6.15:.2f}")
except:
    pass

print("\n🎯 WEEKEND SAWTOOTH TARGETS:")
print("-" * 70)
print("  BUY BACK:")
print("    • SOL at $211 (bottom of tooth)")
print("    • ETH at $4,430 (support)")
print("    • MATIC at $0.245")
print("\n  NEXT MILK:")
print("    • SOL at $214.50+")
print("    • ETH at $4,475+")
print("    • Watch for 2-4 hour cycles")

print("\n🦀 CRAWDAD WISDOM:")
print("  'Milk the peaks, buy the valleys.'")
print("  'Weekend volume = predictable patterns.'")
print("  'Compound 5-6 cycles for $100+ profit.'")

print("\n✅ READY FOR WEEKEND SAWTOOTH TRADING!")
print("=" * 70)