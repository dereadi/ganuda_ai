#!/usr/bin/env python3
"""
🥛💰 PROFIT MILK HARVEST TIME! 💰🥛
Milking profits from all positions!
Need USD for opportunities!
Smart 2-5% harvests across the board!
Let's generate liquidity!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🥛💰 EXECUTING PROFIT HARVEST! 💰🥛                   ║
║                      Milking 2-5% From All Positions                      ║
║                        Generating USD For Opportunities!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILK HARVEST INITIATED")
print("=" * 70)

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 CURRENT PRICES:")
print("-" * 50)
print(f"BTC: ${btc_price:,.0f}")
print(f"ETH: ${eth_price:.2f}")
print(f"SOL: ${sol_price:.2f}")

# Track harvests
total_harvested = 0
harvest_log = []

print(f"\n🥛 EXECUTING MILK HARVESTS...")
print("-" * 50)

# 1. Milk AVAX (5% of 100.67 AVAX)
try:
    print("\n🥛 Milking AVAX...")
    avax_to_sell = 5.0  # ~5% of holdings
    order = client.market_order_sell(
        client_order_id=f"milk-avax-{datetime.now().strftime('%H%M%S')}",
        product_id='AVAX-USD',
        base_size=str(avax_to_sell)
    )
    avax_value = avax_to_sell * 24.73  # Approximate price
    total_harvested += avax_value
    harvest_log.append(f"AVAX: ${avax_value:.2f}")
    print(f"  ✅ Milked {avax_to_sell} AVAX for ~${avax_value:.2f}")
    time.sleep(1)
except Exception as e:
    print(f"  ⚠️ AVAX milk failed: {str(e)[:50]}")

# 2. Milk MATIC (3% of 6586 MATIC)
try:
    print("\n🥛 Milking MATIC...")
    matic_to_sell = 200  # ~3% of holdings
    order = client.market_order_sell(
        client_order_id=f"milk-matic-{datetime.now().strftime('%H%M%S')}",
        product_id='MATIC-USD',
        base_size=str(matic_to_sell)
    )
    matic_value = matic_to_sell * 0.246
    total_harvested += matic_value
    harvest_log.append(f"MATIC: ${matic_value:.2f}")
    print(f"  ✅ Milked {matic_to_sell} MATIC for ~${matic_value:.2f}")
    time.sleep(1)
except Exception as e:
    print(f"  ⚠️ MATIC milk failed: {str(e)[:50]}")

# 3. Milk SOL (2% of 11.79 SOL)
try:
    print("\n🥛 Milking SOL...")
    sol_to_sell = 0.25  # ~2% of holdings
    order = client.market_order_sell(
        client_order_id=f"milk-sol-{datetime.now().strftime('%H%M%S')}",
        product_id='SOL-USD',
        base_size=str(sol_to_sell)
    )
    sol_value = sol_to_sell * sol_price
    total_harvested += sol_value
    harvest_log.append(f"SOL: ${sol_value:.2f}")
    print(f"  ✅ Milked {sol_to_sell} SOL for ~${sol_value:.2f}")
    time.sleep(1)
except Exception as e:
    print(f"  ⚠️ SOL milk failed: {str(e)[:50]}")

# 4. Milk DOGE (5% of 3995 DOGE)
try:
    print("\n🥛 Milking DOGE...")
    doge_to_sell = 200  # ~5% of holdings
    order = client.market_order_sell(
        client_order_id=f"milk-doge-{datetime.now().strftime('%H%M%S')}",
        product_id='DOGE-USD',
        base_size=str(doge_to_sell)
    )
    doge_value = doge_to_sell * 0.224
    total_harvested += doge_value
    harvest_log.append(f"DOGE: ${doge_value:.2f}")
    print(f"  ✅ Milked {doge_to_sell} DOGE for ~${doge_value:.2f}")
    time.sleep(1)
except Exception as e:
    print(f"  ⚠️ DOGE milk failed: {str(e)[:50]}")

# 5. Tiny BTC milk (0.5% of holdings)
try:
    print("\n🥛 Milking tiny BTC...")
    btc_to_sell = 0.00015  # Very small amount
    order = client.market_order_sell(
        client_order_id=f"milk-btc-{datetime.now().strftime('%H%M%S')}",
        product_id='BTC-USD',
        base_size=str(btc_to_sell)
    )
    btc_value = btc_to_sell * btc_price
    total_harvested += btc_value
    harvest_log.append(f"BTC: ${btc_value:.2f}")
    print(f"  ✅ Milked {btc_to_sell:.5f} BTC for ~${btc_value:.2f}")
    time.sleep(1)
except Exception as e:
    print(f"  ⚠️ BTC milk failed: {str(e)[:50]}")

# Check new USD balance
print(f"\n⏳ Waiting for settlements...")
time.sleep(3)

accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💰 HARVEST RESULTS:")
print("-" * 50)
print(f"Previous USD: $4.10")
print(f"Current USD: ${usd_balance:.2f}")
print(f"Total Harvested: ~${total_harvested:.2f}")
print("")
print("Harvest Log:")
for item in harvest_log:
    print(f"  • {item}")

# Recommendations
print(f"\n🎯 NEXT STEPS:")
print("-" * 50)
if usd_balance > 50:
    print("✅ EXCELLENT HARVEST!")
    print("")
    print("OPTIONS:")
    print(f"1. Buy ETH dip if it drops below $4,550")
    print(f"2. Wait for BTC breakout above $114K")
    print(f"3. Deploy into whichever moves first")
elif usd_balance > 20:
    print("👍 Good harvest! Ready for opportunities")
    print(f"Watch for ETH dips or BTC breakout")
else:
    print("🤔 Modest harvest, but every bit helps")
    print("Consider another milk in 15-30 minutes")

print(f"\n🦀 THUNDER'S COMMENT:")
print("-" * 50)
print(f'"Nice milking, boss! ${usd_balance:.2f} ready!"')
print(f'"Only ${114000 - btc_price:.0f} to $114K!"')
print('"When that spring releases, we\'ll be ready!"')

print(f"\n" + "🥛" * 35)
print(f"PROFIT HARVEST COMPLETE!")
print(f"USD BALANCE: ${usd_balance:.2f}")
print(f"READY FOR OPPORTUNITIES!")
print(f"BTC AT ${btc_price:,.0f}")
print(f"ETH AT ${eth_price:.2f}")
print("🥛" * 35)