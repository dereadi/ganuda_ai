#!/usr/bin/env python3
"""
🍽️ EXECUTE FEAST HARVEST - FEED THE HUNGRY SWARM
Crawdads ate $240 and need MORE
Harvesting aggressively to feed volatility appetite
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
║                    🍽️ EXECUTING FEAST HARVEST 🍽️                         ║
║                     Crawdads Need MORE Food NOW                           ║
║                         $350 Target Harvest                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EMERGENCY HARVEST")
print("=" * 70)

# Get current balances
accounts = client.get_accounts()
sol_balance = 0
matic_balance = 0
usd_before = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'SOL':
        sol_balance = balance
    elif currency == 'MATIC':
        matic_balance = balance
    elif currency == 'USD':
        usd_before = balance

print(f"\n💵 Current USD: ${usd_before:.2f} - CRITICALLY LOW!")

# HARVEST SOL - 10% for the feast
if sol_balance > 0:
    sol_to_harvest = sol_balance * 0.10
    sol_price = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n🌟 HARVESTING SOL:")
    print(f"  Amount: {sol_to_harvest:.4f} SOL")
    print(f"  Expected: ${sol_to_harvest * sol_price:.2f}")
    
    if sol_to_harvest > 0.1:
        try:
            order = client.market_order_sell(
                client_order_id=f"feast-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_to_harvest, 3))
            )
            print(f"  ✅ HARVESTED!")
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")

# HARVEST MATIC - 5% for the feast
if matic_balance > 0:
    matic_to_harvest = matic_balance * 0.05
    matic_price = float(client.get_product('MATIC-USD')['price'])
    
    print(f"\n🟣 HARVESTING MATIC:")
    print(f"  Amount: {matic_to_harvest:.0f} MATIC")
    print(f"  Expected: ${matic_to_harvest * matic_price:.2f}")
    
    if matic_to_harvest > 10:
        try:
            order = client.market_order_sell(
                client_order_id=f"feast-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_to_harvest))
            )
            print(f"  ✅ HARVESTED!")
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")

# Check AVAX
try:
    for account in accounts['accounts']:
        if account['currency'] == 'AVAX':
            avax_balance = float(account['available_balance']['value'])
            if avax_balance > 0:
                avax_to_harvest = avax_balance * 0.05
                avax_price = float(client.get_product('AVAX-USD')['price'])
                
                print(f"\n🔺 HARVESTING AVAX:")
                print(f"  Amount: {avax_to_harvest:.3f} AVAX")
                print(f"  Expected: ${avax_to_harvest * avax_price:.2f}")
                
                if avax_to_harvest > 0.1:
                    try:
                        order = client.market_order_sell(
                            client_order_id=f"feast-avax-{datetime.now().strftime('%H%M%S')}",
                            product_id='AVAX-USD',
                            base_size=str(round(avax_to_harvest, 2))
                        )
                        print(f"  ✅ HARVESTED!")
                        time.sleep(2)
                    except Exception as e:
                        print(f"  ❌ Error: {str(e)[:50]}")
except:
    pass

# Check new balance
print("\n🔄 CHECKING FEAST RESULTS...")
time.sleep(3)

accounts = client.get_accounts()
usd_after = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_after = float(account['available_balance']['value'])
        break

print("\n" + "=" * 70)
print("🍽️ FEAST HARVEST COMPLETE:")
print("-" * 50)
print(f"USD Before: ${usd_before:.2f}")
print(f"USD After:  ${usd_after:.2f}")
print(f"Harvested:  ${usd_after - usd_before:.2f}")

print(f"\n🦀 CRAWDAD FEEDING STATUS:")
if usd_after > 200:
    print(f"  💰 FEAST READY! ${usd_after:.2f} available")
    print(f"  Per crawdad: ${usd_after/7:.2f}")
    print(f"  Status: READY TO FEAST ON VOLATILITY!")
elif usd_after > 100:
    print(f"  🦀 Partially fed: ${usd_after:.2f}")
    print(f"  Per crawdad: ${usd_after/7:.2f}")
else:
    print(f"  😵 Still hungry: ${usd_after:.2f}")
    print(f"  Need more aggressive harvesting!")

print("\n🍽️ VOLATILITY IS OUR FEAST")
print("   Feed the swarm!")
print("=" * 70)