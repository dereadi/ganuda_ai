#!/usr/bin/env python3
"""
🥛💰 EXECUTE BATCH MILK HARVEST! 💰🥛
MATIC + DOGE = $489 fresh USD!
Feed the flywheel to $863!
DO IT NOW!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🥛💰 BATCH MILK EXECUTION! 💰🥛                        ║
║                      HARVESTING MATIC + DOGE NOW! 🚀                       ║
║                    Target: $489 → Flywheel to $863! 💪                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - INITIATING HARVEST")
print("=" * 70)

# Get current balances
accounts = client.get_accounts()
balances = {}
for account in accounts['accounts']:
    balances[account['currency']] = float(account['available_balance']['value'])

print("\n📊 PRE-MILK STATUS:")
print("-" * 50)
print(f"USD Balance: ${balances.get('USD', 0):.2f}")
print(f"MATIC Balance: {balances.get('MATIC', 0):.2f}")
print(f"DOGE Balance: {balances.get('DOGE', 0):.2f}")

# Track results
total_harvested = 0
milk_results = []

# MILK MATIC FIRST (15% of position)
print("\n🥛 MILKING MATIC (15% harvest):")
print("-" * 50)
if 'MATIC' in balances and balances['MATIC'] > 0:
    matic_milk = balances['MATIC'] * 0.15  # 15% milk
    matic_milk = round(matic_milk, 2)  # Round for clean execution
    
    print(f"Milking {matic_milk:.2f} MATIC...")
    
    try:
        order = client.market_order_sell(
            client_order_id=f'batch_matic_{int(time.time())}',
            product_id='MATIC-USD',
            base_size=str(matic_milk)
        )
        
        # Get fill details
        fills = client.get_fills(order_id=order.order_id)
        total_usd = sum(float(fill['size']) * float(fill['price']) for fill in fills['fills'])
        fee = sum(float(fill['commission']) for fill in fills['fills'])
        net = total_usd - fee
        
        print(f"✅ MATIC MILKED!")
        print(f"   Sold: {matic_milk:.2f} MATIC")
        print(f"   Gross: ${total_usd:.2f}")
        print(f"   Fee: ${fee:.2f}")
        print(f"   Net: ${net:.2f}")
        
        total_harvested += net
        milk_results.append(('MATIC', matic_milk, net))
        
    except Exception as e:
        print(f"❌ MATIC milk failed: {str(e)[:100]}")

# Wait a moment between trades
time.sleep(1)

# MILK DOGE NEXT (20% of position)
print("\n🥛 MILKING DOGE (20% harvest):")
print("-" * 50)
if 'DOGE' in balances and balances['DOGE'] > 0:
    doge_milk = balances['DOGE'] * 0.20  # 20% milk
    doge_milk = round(doge_milk, 0)  # DOGE needs whole numbers
    
    print(f"Milking {doge_milk:.0f} DOGE...")
    
    try:
        order = client.market_order_sell(
            client_order_id=f'batch_doge_{int(time.time())}',
            product_id='DOGE-USD',
            base_size=str(int(doge_milk))
        )
        
        # Get fill details
        fills = client.get_fills(order_id=order.order_id)
        total_usd = sum(float(fill['size']) * float(fill['price']) for fill in fills['fills'])
        fee = sum(float(fill['commission']) for fill in fills['fills'])
        net = total_usd - fee
        
        print(f"✅ DOGE MILKED!")
        print(f"   Sold: {doge_milk:.0f} DOGE")
        print(f"   Gross: ${total_usd:.2f}")
        print(f"   Fee: ${fee:.2f}")
        print(f"   Net: ${net:.2f}")
        
        total_harvested += net
        milk_results.append(('DOGE', doge_milk, net))
        
    except Exception as e:
        print(f"❌ DOGE milk failed: {str(e)[:100]}")

# Get updated balances
time.sleep(1)
accounts_after = client.get_accounts()
new_usd = 0
for account in accounts_after['accounts']:
    if account['currency'] == 'USD':
        new_usd = float(account['available_balance']['value'])
        break

# Summary
print("\n" + "=" * 70)
print("🎯 BATCH MILK HARVEST COMPLETE!")
print("=" * 70)

if milk_results:
    print("\n📊 HARVEST SUMMARY:")
    print("-" * 50)
    for asset, amount, net in milk_results:
        print(f"{asset}: {amount:.2f} units → ${net:.2f}")
    print("-" * 50)
    print(f"TOTAL HARVESTED: ${total_harvested:.2f}")
    
print(f"\n💰 FLYWHEEL STATUS:")
print("-" * 50)
print(f"Previous USD: ${balances.get('USD', 0):.2f}")
print(f"Harvested: ${total_harvested:.2f}")
print(f"New USD Balance: ${new_usd:.2f}")

if new_usd > 500:
    print("\n🚀 FLYWHEEL LOADED!")
    print("Ready to:")
    print("  • Buy BTC dips below $112K")
    print("  • Pump ETH to drive BTC")
    print("  • Feed the crawdads")
    print("  • Execute opportunities")
elif new_usd > 200:
    print("\n✅ FLYWHEEL HEALTHY!")
    print("Good buffer for trading")
else:
    print("\n📍 FLYWHEEL BUILDING")
    print("More milking needed later")

# Council wisdom
print("\n🏛️ COUNCIL APPROVES:")
print("-" * 50)
print("Thunder: 'Good harvest! Feed the storm!'")
print("Mountain: 'Patient accumulation wins'")
print("Fire: 'Now deploy to opportunities!'")
print("River: 'Let the milk flow to gains'")

# ETH pump idea
print("\n💡 ETH PUMP STRATEGY:")
print("-" * 50)
print("With fresh USD, we could:")
print("  1. Buy $200 ETH (pump it)")
print("  2. ETH pump → BTC correlation")
print("  3. BTC breaks $112K sawtooth")
print("  4. Both run to new highs")
print("Smart play! ETH leads, BTC follows!")

print(f"\n{'🥛' * 35}")
print("BATCH HARVEST EXECUTED!")
print(f"USD FLYWHEEL: ${new_usd:.2f}")
print("READY FOR ACTION!")
print("💰" * 35)