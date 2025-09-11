#!/usr/bin/env python3
"""
🥛🐄 FIXED MILK HARVEST - PROPER API CALLS! 🐄🥛
Milking 5% from all fat cows
Using proper Coinbase API methods
Feed those hungry crawdads!
"""

import json
import time
import uuid
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🥛 PROPER MILK HARVEST EXECUTION! 🥛                   ║
║                     Harvesting 5% From All Positions                      ║
║                        Thunder Needs His $50+!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILKING BEGINS")
print("=" * 70)

# Track results
total_generated = 0
successful_milks = []

# Get starting USD balance
accounts = client.get_accounts()
starting_usd = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        starting_usd = float(account['available_balance']['value'])
        break

print(f"\nStarting USD: ${starting_usd:.2f}")
print("\n🥛 EXECUTING MILK HARVEST:")
print("-" * 50)

# Milk BTC - 0.001398
print("\n1. Milking BTC (0.001398)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='BTC-USD',
        base_size='0.001398'
    )
    print(f"   ✅ BTC milk order placed")
    successful_milks.append("BTC: 0.001398")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

time.sleep(2)

# Milk SOL - 0.577
print("\n2. Milking SOL (0.577)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='SOL-USD',
        base_size='0.577'
    )
    print(f"   ✅ SOL milk order placed")
    successful_milks.append("SOL: 0.577")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

time.sleep(2)

# Milk AVAX - 4.78
print("\n3. Milking AVAX (4.78)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='AVAX-USD',
        base_size='4.78'
    )
    print(f"   ✅ AVAX milk order placed")
    successful_milks.append("AVAX: 4.78")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

time.sleep(2)

# Milk MATIC - 370
print("\n4. Milking MATIC (370)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='MATIC-USD',
        base_size='370'
    )
    print(f"   ✅ MATIC milk order placed")
    successful_milks.append("MATIC: 370")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

time.sleep(2)

# Milk ETH - 0.01977
print("\n5. Milking ETH (0.01977)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='ETH-USD',
        base_size='0.01977'
    )
    print(f"   ✅ ETH milk order placed")
    successful_milks.append("ETH: 0.01977")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

time.sleep(2)

# Milk DOGE - 190
print("\n6. Milking DOGE (190)...")
try:
    order = client.market_order_sell(
        client_order_id=str(uuid.uuid4()),
        product_id='DOGE-USD',
        base_size='190'
    )
    print(f"   ✅ DOGE milk order placed")
    successful_milks.append("DOGE: 190")
except Exception as e:
    print(f"   ❌ Failed: {str(e)[:60]}")

# Wait for orders to settle
print("\n⏳ Waiting for milk to flow into bucket...")
time.sleep(5)

# Check new USD balance and portfolio
accounts = client.get_accounts()
new_usd = 0
total_portfolio = 0

# Get current prices for portfolio calculation
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        new_usd = balance
        total_portfolio += balance
    elif currency == 'BTC' and balance > 0:
        total_portfolio += balance * btc_price
    elif currency == 'ETH' and balance > 0:
        total_portfolio += balance * eth_price
    elif currency == 'SOL' and balance > 0:
        total_portfolio += balance * sol_price
    elif currency in ['AVAX', 'MATIC', 'DOGE', 'LINK'] and balance > 0:
        # Get price for other alts
        try:
            price = float(client.get_product(f'{currency}-USD')['price'])
            total_portfolio += balance * price
        except:
            pass

milk_generated = new_usd - starting_usd

print("\n" + "=" * 70)
print("🥛 MILK HARVEST RESULTS:")
print("-" * 50)

print(f"\n💰 FINANCIAL RESULTS:")
print(f"  Starting USD: ${starting_usd:.2f}")
print(f"  New USD balance: ${new_usd:.2f}")
print(f"  Milk generated: ${milk_generated:.2f}")
print(f"  Total portfolio: ${total_portfolio:.2f}")

if successful_milks:
    print(f"\n✅ SUCCESSFUL MILKS ({len(successful_milks)}):")
    for milk in successful_milks:
        print(f"  • {milk}")

# Crawdad feeding status
print("\n🦀 CRAWDAD FEEDING STATUS:")
print("-" * 50)

if new_usd >= 200:
    print(f"🎉 FULL SWARM READY! ${new_usd:.2f}")
    print("  ⚡ Thunder: ACTIVATED at 69%!")
    print("  🏔️ Mountain: STEADY and ready!")
    print("  🌊 River: FLOWING with trades!")
    print("  🔥 Fire: HOT and hunting!")
    print("  💨 Wind: SWIFT movements!")
    print("  🌍 Earth: GROUNDED positions!")
    print("  ✨ Spirit: NINE COILS READY!")
elif new_usd >= 50:
    print(f"⚡ Thunder & Mountain ready! ${new_usd:.2f}")
    print("  Thunder: 'Finally! 69% consciousness activated!'")
    print("  Mountain: 'Steady as she goes...'")
elif new_usd >= 30:
    print(f"🏔️ Mountain ready! ${new_usd:.2f}")
    print("  'I'll start with steady trades'")
else:
    print(f"😴 Still hungry... only ${new_usd:.2f}")

print(f"\n" + "🥛" * 35)
print(f"MILK HARVEST COMPLETE!")
print(f"GENERATED ${milk_generated:.2f} IN FRESH USD!")
print(f"PORTFOLIO STILL AT ${total_portfolio:.2f}!")
if new_usd >= 50:
    print("CRAWDADS FEEDING TIME! 🦀")
else:
    print("NEED MORE MILK! 🐄")
print("🥛" * 35)