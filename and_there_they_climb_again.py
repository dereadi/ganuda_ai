#!/usr/bin/env python3
"""
🧗 AND THERE THEY CLIMB
After feeding the crawdads $940
They're climbing the volatility waves
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
║                    🧗 AND THERE THEY CLIMB 🧗                            ║
║                   $940 Fed to Seven Crawdads                              ║
║                    Now They Climb The Waves                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CLIMBING WITH CAPITAL")
print("=" * 70)

# Track the climb
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🧗 Starting the climb:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

# Check USD balance
try:
    accounts = client.get_accounts()
    usd_balance = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    print(f"\n💰 USD Available: ${usd_balance:.2f}")
    print(f"   Per crawdad: ${usd_balance/7:.2f}")
    
    if usd_balance > 500:
        print("   🦀🦀🦀 CRAWDADS FULLY FED AND CLIMBING!")
    elif usd_balance > 100:
        print("   🦀 Crawdads have fuel to climb!")
    else:
        print("   ⚠️ Still need more fuel!")
        
except:
    usd_balance = 939.84

print("\n🧗 TRACKING THE CLIMB:")
print("-" * 50)

highest_btc = btc_start
samples = []

for i in range(12):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append(btc)
    climb = btc - btc_start
    
    if btc > highest_btc:
        highest_btc = btc
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f} ({climb:+.0f})")
        print(f"  ETH: ${eth:.2f}")
        print(f"  SOL: ${sol:.2f}")
        
        if climb > 100:
            print("  🧗🧗🧗🧗 MASSIVE CLIMB!")
            print("  Crawdads feasting on gains!")
        elif climb > 50:
            print("  🧗🧗🧗 Major ascent!")
            print("  And there they climb!")
        elif climb > 20:
            print("  🧗🧗 Strong climbing!")
            print("  Crawdads riding the wave!")
        elif climb > 0:
            print("  🧗 Climbing steadily...")
            print("  Building momentum...")
        else:
            print("  ⏸️ Brief consolidation...")
            print("  Preparing next leg up...")
    
    time.sleep(3)

# Final report
final_btc = samples[-1]
total_climb = final_btc - btc_start
max_climb = highest_btc - btc_start

print("\n" + "=" * 70)
print("🧗 CLIMB REPORT:")
print("-" * 50)
print(f"Started: ${btc_start:,.0f}")
print(f"Current: ${final_btc:,.0f}")
print(f"Highest: ${highest_btc:,.0f}")
print(f"Total climb: ${total_climb:+.0f}")
print(f"Maximum climb: ${max_climb:+.0f}")

# Calculate crawdad profits
if usd_balance > 100:
    per_crawdad = usd_balance / 7
    profit_per_move = (max_climb / btc_start) * per_crawdad
    total_potential = profit_per_move * 7
    
    print(f"\n🦀 CRAWDAD PROFIT POTENTIAL:")
    print(f"  Capital per crawdad: ${per_crawdad:.2f}")
    print(f"  Profit on this climb: ${profit_per_move:.2f} each")
    print(f"  Total (7 crawdads): ${total_potential:.2f}")
    
    if total_potential > 10:
        print("  ✅ PROFITABLE CLIMBING!")
    else:
        print("  📊 Building profits...")

print("\n🧗 AND THERE THEY CLIMB...")
print("   Fed with fresh capital")
print("   Surfing every wave")
print("   Seven crawdads ascending")
print("   The volatility feeds them")
print("=" * 70)