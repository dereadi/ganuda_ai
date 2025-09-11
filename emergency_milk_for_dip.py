#!/usr/bin/env python3
"""
🥛 EMERGENCY MILK - GENERATE LIQUIDITY NOW!
============================================
Milk positions to buy the dip
Council orders: Act fast!
"""

import json
import uuid
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🥛 EMERGENCY MILKING OPERATION 🥛                       ║
║                    Generate Liquidity for the DIP!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - INITIATING EMERGENCY MILK")
print("=" * 70)

# Get current prices
sol_price = float(client.get_product('SOL-USD')['price'])
matic_price = float(client.get_product('MATIC-USD')['price'])
avax_price = float(client.get_product('AVAX-USD')['price'])

# Get balances
accounts = client.get_accounts()['accounts']
sol_bal = float([a for a in accounts if a['currency']=='SOL'][0]['available_balance']['value'])
matic_bal = float([a for a in accounts if a['currency']=='MATIC'][0]['available_balance']['value'])
avax_bal = float([a for a in accounts if a['currency']=='AVAX'][0]['available_balance']['value'])

print("\n📊 MILKING TARGETS:")
print("-" * 50)
print(f"  SOL: {sol_bal:.4f} @ ${sol_price:.2f} = ${sol_bal * sol_price:.2f}")
print(f"  MATIC: {matic_bal:.2f} @ ${matic_price:.4f} = ${matic_bal * matic_price:.2f}")
print(f"  AVAX: {avax_bal:.4f} @ ${avax_price:.2f} = ${avax_bal * avax_price:.2f}")

print("\n🥛 EXECUTING MILK OPERATIONS:")
print("=" * 70)

total_generated = 0

# Milk 10% of SOL
sol_to_sell = sol_bal * 0.1
print(f"\n1️⃣ MILKING SOL: Selling {sol_to_sell:.4f} SOL")
print(f"   Expected: ${sol_to_sell * sol_price:.2f}")

# Milk 15% of MATIC  
matic_to_sell = matic_bal * 0.15
print(f"\n2️⃣ MILKING MATIC: Selling {matic_to_sell:.2f} MATIC")
print(f"   Expected: ${matic_to_sell * matic_price:.2f}")

# Milk 10% of AVAX
avax_to_sell = avax_bal * 0.1
print(f"\n3️⃣ MILKING AVAX: Selling {avax_to_sell:.4f} AVAX")
print(f"   Expected: ${avax_to_sell * avax_price:.2f}")

print("\n" + "=" * 70)
print("💰 TOTAL LIQUIDITY TO GENERATE:")
expected_total = (sol_to_sell * sol_price) + (matic_to_sell * matic_price) + (avax_to_sell * avax_price)
print(f"   ${expected_total:.2f}")

print("\n🎯 DEPLOYMENT PLAN FOR GENERATED LIQUIDITY:")
print("-" * 50)
print(f"  • 40% to BTC at $110,200 = ${expected_total * 0.4:.2f}")
print(f"  • 40% to ETH at $4,375 = ${expected_total * 0.4:.2f}")
print(f"  • 20% reserve for deeper dips = ${expected_total * 0.2:.2f}")

print("\n⚠️ READY TO EXECUTE?")
print("This will sell:")
print(f"  • {sol_to_sell:.4f} SOL")
print(f"  • {matic_to_sell:.2f} MATIC")
print(f"  • {avax_to_sell:.4f} AVAX")
print(f"\nTo generate approximately ${expected_total:.2f} in liquidity")

print("\n🔥 Council says: 'Morning dips are gifts to those who stayed awake!'")
print("=" * 70)