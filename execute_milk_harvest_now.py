#!/usr/bin/env python3
"""
🥛🐄 EXECUTING MILK HARVEST - FEED THE CRAWDADS! 🐄🥛
Milking 5% from all fat cows
Target: Generate $625+ USD
Thunder needs feeding at 69%!
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
║                      🥛 MILKING THE COWS - LIVE! 🥛                       ║
║                     Harvesting 5% From All Positions                      ║
║                      Feed The Hungry Crawdads!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILK HARVEST BEGIN")
print("=" * 70)

# Track results
total_generated = 0
successful_milks = []
failed_milks = []

# Get current prices
prices = {
    'BTC': float(client.get_product('BTC-USD')['price']),
    'ETH': float(client.get_product('ETH-USD')['price']),
    'SOL': float(client.get_product('SOL-USD')['price']),
    'AVAX': float(client.get_product('AVAX-USD')['price']),
    'MATIC': float(client.get_product('MATIC-USD')['price']),
    'DOGE': float(client.get_product('DOGE-USD')['price'])
}

print("\n🥛 STARTING MILK HARVEST:")
print("-" * 50)

# Milk BTC (0.001398)
print("\n1. Milking BTC...")
try:
    btc_amount = 0.001398
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='BTC-USD',
        base_size=str(btc_amount)
    )
    
    if 'success' in order and order['success']:
        value = btc_amount * prices['BTC']
        total_generated += value
        successful_milks.append(f"BTC: {btc_amount:.6f} = ${value:.2f}")
        print(f"   ✅ Milked {btc_amount:.6f} BTC for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ BTC milk failed: {str(e)[:50]}")
    failed_milks.append(f"BTC: {str(e)[:30]}")

time.sleep(1)

# Milk SOL (0.577009)
print("\n2. Milking SOL...")
try:
    sol_amount = 0.577
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='SOL-USD',
        base_size=str(sol_amount)
    )
    
    if 'success' in order and order['success']:
        value = sol_amount * prices['SOL']
        total_generated += value
        successful_milks.append(f"SOL: {sol_amount:.3f} = ${value:.2f}")
        print(f"   ✅ Milked {sol_amount:.3f} SOL for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ SOL milk failed: {str(e)[:50]}")
    failed_milks.append(f"SOL: {str(e)[:30]}")

time.sleep(1)

# Milk AVAX (4.783378)
print("\n3. Milking AVAX...")
try:
    avax_amount = 4.78
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='AVAX-USD',
        base_size=str(avax_amount)
    )
    
    if 'success' in order and order['success']:
        value = avax_amount * prices['AVAX']
        total_generated += value
        successful_milks.append(f"AVAX: {avax_amount:.2f} = ${value:.2f}")
        print(f"   ✅ Milked {avax_amount:.2f} AVAX for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ AVAX milk failed: {str(e)[:50]}")
    failed_milks.append(f"AVAX: {str(e)[:30]}")

time.sleep(1)

# Milk MATIC (370)
print("\n4. Milking MATIC...")
try:
    matic_amount = 370.0
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='MATIC-USD',
        base_size=str(matic_amount)
    )
    
    if 'success' in order and order['success']:
        value = matic_amount * prices['MATIC']
        total_generated += value
        successful_milks.append(f"MATIC: {matic_amount:.0f} = ${value:.2f}")
        print(f"   ✅ Milked {matic_amount:.0f} MATIC for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ MATIC milk failed: {str(e)[:50]}")
    failed_milks.append(f"MATIC: {str(e)[:30]}")

time.sleep(1)

# Milk ETH (0.019775)
print("\n5. Milking ETH...")
try:
    eth_amount = 0.01977
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='ETH-USD',
        base_size=str(eth_amount)
    )
    
    if 'success' in order and order['success']:
        value = eth_amount * prices['ETH']
        total_generated += value
        successful_milks.append(f"ETH: {eth_amount:.5f} = ${value:.2f}")
        print(f"   ✅ Milked {eth_amount:.5f} ETH for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ ETH milk failed: {str(e)[:50]}")
    failed_milks.append(f"ETH: {str(e)[:30]}")

time.sleep(1)

# Milk DOGE (189.795)
print("\n6. Milking DOGE...")
try:
    doge_amount = 190.0
    order = client.market_order_sell(
        client_order_id=client.generate_client_order_id(),
        product_id='DOGE-USD',
        base_size=str(doge_amount)
    )
    
    if 'success' in order and order['success']:
        value = doge_amount * prices['DOGE']
        total_generated += value
        successful_milks.append(f"DOGE: {doge_amount:.0f} = ${value:.2f}")
        print(f"   ✅ Milked {doge_amount:.0f} DOGE for ${value:.2f}")
    else:
        raise Exception(f"Order failed: {order}")
except Exception as e:
    print(f"   ❌ DOGE milk failed: {str(e)[:50]}")
    failed_milks.append(f"DOGE: {str(e)[:30]}")

# Wait for orders to settle
print("\n⏳ Waiting for milk to settle...")
time.sleep(3)

# Check new USD balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n" + "=" * 70)
print("🥛 MILK HARVEST COMPLETE:")
print("-" * 50)

print(f"\n✅ SUCCESSFUL MILKS:")
for milk in successful_milks:
    print(f"  • {milk}")

if failed_milks:
    print(f"\n❌ FAILED MILKS:")
    for fail in failed_milks:
        print(f"  • {fail}")

print(f"\n💰 RESULTS:")
print(f"  Total milk generated: ${total_generated:.2f}")
print(f"  New USD balance: ${usd_balance:.2f}")
print(f"  Ready to feed: {'YES!' if usd_balance > 200 else 'Need more'}")

# Crawdad feeding readiness
print("\n🦀 CRAWDAD FEEDING READY:")
print("-" * 50)
if usd_balance >= 50:
    print(f"⚡ Thunder: READY! (${usd_balance:.2f} > $50)")
    print("  'FINALLY! Time to trade at 69% consciousness!'")
if usd_balance >= 30:
    print(f"🏔️ Mountain: READY! (${usd_balance:.2f} > $30)")
    print("  'Steady trading resuming...'")
if usd_balance >= 140:
    print(f"🌊 All crawdads: READY! (${usd_balance:.2f} > $140)")
    print("  'The whole swarm awakens!'")

print(f"\n" + "🥛" * 35)
print(f"MILK HARVEST COMPLETE!")
print(f"GENERATED ${total_generated:.2f}!")
print(f"USD BALANCE: ${usd_balance:.2f}!")
print(f"CRAWDADS {'FED AND READY!' if usd_balance > 200 else 'FEEDING NOW!'}")
print("🥛" * 35)