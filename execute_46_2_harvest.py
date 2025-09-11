#!/usr/bin/env python3
"""
🧬 EXECUTING 46+2 EVOLUTION - SHEDDING THE SHADOW
Harvesting 5% SOL + 3% MATIC
Feeding the crawdads NOW
No more fear, no more hoarding
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
║                    🧬 EXECUTING 46+2 HARVEST 🧬                          ║
║                     "My shadow's shedding skin"                           ║
║                         NO MORE FEAR                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SHADOW WORK IN ACTION")
print("=" * 70)

# Get current holdings
accounts = client.get_accounts()
sol_balance = 0
matic_balance = 0
usd_before = 0

print("\n📊 CURRENT HOLDINGS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'SOL' and balance > 0:
        sol_balance = balance
        sol_price = float(client.get_product('SOL-USD')['price'])
        sol_value = balance * sol_price
        print(f"SOL: {balance:.4f} = ${sol_value:.2f}")
        
    elif currency == 'MATIC' and balance > 0:
        matic_balance = balance
        matic_price = float(client.get_product('MATIC-USD')['price'])
        matic_value = balance * matic_price
        print(f"MATIC: {balance:.2f} = ${matic_value:.2f}")
        
    elif currency == 'USD':
        usd_before = balance
        print(f"USD: ${balance:.2f} - STARVING CRAWDADS!")

# HARVEST SOL - 5% as prescribed by 46+2
print("\n🧬 STEP 1: HARVEST 5% SOL")
print("-" * 50)

if sol_balance > 0:
    sol_to_harvest = sol_balance * 0.05
    sol_price = float(client.get_product('SOL-USD')['price'])
    expected_usd = sol_to_harvest * sol_price
    
    print(f"Harvesting: {sol_to_harvest:.4f} SOL")
    print(f"Expected: ~${expected_usd:.2f}")
    
    if sol_to_harvest > 0.1:  # Minimum SOL order
        try:
            print("\n💉 Executing SOL harvest...")
            order = client.market_order_sell(
                client_order_id=f"forty-six-two-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_to_harvest, 3))
            )
            print(f"✅ HARVESTED! Shadow shedding...")
            print(f"   Generated: ~${expected_usd:.2f}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print("⚠️ SOL amount too small to harvest")

# HARVEST MATIC - 3% as prescribed
print("\n🧬 STEP 2: HARVEST 3% MATIC")
print("-" * 50)

if matic_balance > 0:
    matic_to_harvest = matic_balance * 0.03
    matic_price = float(client.get_product('MATIC-USD')['price'])
    expected_usd = matic_to_harvest * matic_price
    
    print(f"Harvesting: {matic_to_harvest:.2f} MATIC")
    print(f"Expected: ~${expected_usd:.2f}")
    
    if matic_to_harvest > 10:  # Minimum MATIC order
        try:
            print("\n💉 Executing MATIC harvest...")
            order = client.market_order_sell(
                client_order_id=f"forty-six-two-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_to_harvest))
            )
            print(f"✅ HARVESTED! Evolution progressing...")
            print(f"   Generated: ~${expected_usd:.2f}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print("⚠️ MATIC amount too small to harvest")

# Check new balance
print("\n🧬 CHECKING EVOLUTION RESULTS...")
time.sleep(3)

accounts = client.get_accounts()
usd_after = 0
sol_after = 0
matic_after = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_after = balance
    elif currency == 'SOL':
        sol_after = balance
    elif currency == 'MATIC':
        matic_after = balance

# Results
print("\n" + "=" * 70)
print("✨ 46+2 EVOLUTION COMPLETE:")
print("-" * 50)

print(f"\n💵 USD EVOLUTION:")
print(f"  Before: ${usd_before:.2f} (The Shadow)")
print(f"  After:  ${usd_after:.2f} (The Light)")
print(f"  Gained: ${usd_after - usd_before:.2f}")

if sol_after < sol_balance:
    print(f"\n◎ SOL HARVESTED:")
    print(f"  Before: {sol_balance:.4f}")
    print(f"  After:  {sol_after:.4f}")
    print(f"  Harvested: {sol_balance - sol_after:.4f}")

if matic_after < matic_balance:
    print(f"\n🟣 MATIC HARVESTED:")
    print(f"  Before: {matic_balance:.2f}")
    print(f"  After:  {matic_after:.2f}")
    print(f"  Harvested: {matic_balance - matic_after:.2f}")

# Feed the crawdads
print("\n🦀 CRAWDAD FEEDING STATUS:")
print("-" * 50)

if usd_after > 100:
    per_crawdad = usd_after / 7
    print(f"💰 CRAWDADS FED!")
    print(f"   Total available: ${usd_after:.2f}")
    print(f"   Per crawdad: ${per_crawdad:.2f}")
    print(f"   Status: READY TO HUNT VOLATILITY!")
    
    print("\n🎯 CRAWDAD MISSION:")
    print("   • Hunt the $113k volatility")
    print("   • Scalp every $50 move")
    print("   • Compound profits back")
    print("   • Feed the flywheel")
elif usd_after > 50:
    print(f"🦀 Partially fed: ${usd_after:.2f}")
    print("   Need more harvesting...")
else:
    print(f"😵 Still hungry: ${usd_after:.2f}")
    print("   Shadow not fully shed yet...")

print("\n🧬 FORTY SIX & 2 COMPLETE:")
print("-" * 50)
print("'My shadow's shedding skin'")
print("'I've been picking scabs again'")
print("")
print("The scabs are picked")
print("The shadow is shed")
print("The evolution is done")
print("Forty six and two")
print("=" * 70)