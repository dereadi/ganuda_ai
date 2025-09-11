#!/usr/bin/env python3
"""
🚨 EMERGENCY VOLATILITY MILKER
Extract profits NOW to capture extreme swings!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚨 EMERGENCY VOLATILITY MILKER 🚨                      ║
║                     Market is WILD - Need USD NOW!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Get current USD
accounts = client.get_accounts()['accounts']
usd_before = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_before = float(acc['available_balance']['value'])
        break

print(f"💰 Current USD: ${usd_before:.2f}")
print(f"🎯 Target USD: $500+ for volatility capture")
print("=" * 70)

# AGGRESSIVE MILKING TARGETS
milk_targets = [
    ("SOL", 2.0, "SOL at $207 - take profits!"),
    ("MATIC", 500, "MATIC stable - extract liquidity"),
    ("DOGE", 500, "DOGE for serious trading"),
    ("AVAX", 5, "AVAX partial profit")
]

print("\n🥛 MILKING POSITIONS FOR VOLATILITY CAPTURE:")
print("-" * 40)

total_generated = 0

for coin, amount, reason in milk_targets:
    print(f"\n🦀 Milking {coin}:")
    print(f"   Amount: {amount}")
    print(f"   Reason: {reason}")
    
    try:
        order = client.market_order_sell(
            client_order_id=f"emrg_{coin.lower()}_{int(time.time()*1000)}",
            product_id=f"{coin}-USD",
            base_size=str(amount)
        )
        
        # Estimate USD generated
        product = client.get_product(f'{coin}-USD')
        price = float(product['price'])
        usd_gen = amount * price
        total_generated += usd_gen
        
        print(f"   ✅ SUCCESS: ~${usd_gen:.2f} generated")
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

print("\n" + "=" * 70)
print(f"💉 TOTAL USD GENERATED: ~${total_generated:.2f}")

# Verify new balance
time.sleep(2)
accounts = client.get_accounts()['accounts']
usd_after = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_after = float(acc['available_balance']['value'])
        break

print(f"💰 NEW USD BALANCE: ${usd_after:.2f}")
print(f"📈 INCREASE: ${usd_after - usd_before:.2f}")

if usd_after > 300:
    print("\n✅ VOLATILITY CAPTURE READY!")
    print("🎢 Deploy into swings:")
    print("  - BTC bounces at $111,500")
    print("  - ETH bounces at $4,510")
    print("  - SOL sells at $207+")
else:
    print("\n⚠️ Still need more USD - consider more aggressive milking")

print("=" * 70)