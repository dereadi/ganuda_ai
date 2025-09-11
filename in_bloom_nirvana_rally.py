#!/usr/bin/env python3
"""
🌸 IN BLOOM - NIRVANA
"Hey, I think we're in bloom now..."
A nice slow rally, like spring flowers opening
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
║                           🌸 IN BLOOM 🌸                                  ║
║                      "Sell the kids for food"                            ║
║                      "Weather changes moods"                             ║
║                   "Spring is here again... In Bloom"                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SPRING IS HERE AGAIN")
print("=" * 70)

# Track the slow bloom
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🌱 SEEDS PLANTED AT:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print("\n🌸 WATCHING THE SLOW BLOOM:")
print("-" * 50)

# Track the blooming
bloom_stages = []
for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_growth = btc - btc_start
    eth_growth = eth - eth_start
    sol_growth = sol - sol_start
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - BLOOM STATUS:")
    
    # BTC blooming stages
    if btc > 113000:
        print(f"  🌸 BTC: ${btc:,.0f} (+${btc_growth:.0f}) FULL BLOOM!")
        bloom_stages.append("FULL")
    elif btc > 112950:
        print(f"  🌺 BTC: ${btc:,.0f} (+${btc_growth:.0f}) Flowering!")
        bloom_stages.append("FLOWERING")
    elif btc > 112900:
        print(f"  🌱 BTC: ${btc:,.0f} (+${btc_growth:.0f}) Budding...")
        bloom_stages.append("BUDDING")
    else:
        print(f"  🌱 BTC: ${btc:,.0f} ({btc_growth:+.0f}) Growing slowly...")
        bloom_stages.append("GROWING")
    
    # ETH blooming
    if eth > 4575:
        print(f"  🌸 ETH: ${eth:.2f} (+${eth_growth:.2f}) IN BLOOM!")
    elif eth > 4570:
        print(f"  🌺 ETH: ${eth:.2f} (+${eth_growth:.2f}) Opening up!")
    else:
        print(f"  🌱 ETH: ${eth:.2f} ({eth_growth:+.2f}) Budding...")
    
    # SOL following
    if sol > 212:
        print(f"  🌸 SOL: ${sol:.2f} (+${sol_growth:.2f}) Blooming!")
    else:
        print(f"  🌱 SOL: ${sol:.2f} ({sol_growth:+.2f}) Growing...")
    
    # Nirvana lyrics moments
    if i % 4 == 0:
        print("\n  🎵 'Hey... hey... hey...'")
        print("     'I think we're in bloom now'")
    elif i % 4 == 1:
        print("\n  🎵 'Weather changes moods'")
        print("     The market's mood is changing...")
    elif i % 4 == 2:
        print("\n  🎵 'Spring is here again'")
        print("     Reproductive glands... (making money)")
    else:
        print("\n  🎵 'He's the one who likes all our pretty songs'")
        print("     'And he likes to sing along'")
    
    # Nice and slow
    time.sleep(3)

# Analysis of the bloom
print("\n" + "=" * 70)
print("🌸 BLOOM ANALYSIS:")
print("-" * 40)

final_btc = float(client.get_product('BTC-USD')['price'])
final_eth = float(client.get_product('ETH-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

total_btc_growth = final_btc - btc_start
total_eth_growth = final_eth - eth_start
total_sol_growth = final_sol - sol_start

print(f"BTC: ${btc_start:,.0f} → ${final_btc:,.0f} (+${total_btc_growth:.0f})")
print(f"ETH: ${eth_start:.2f} → ${final_eth:.2f} (+${total_eth_growth:.2f})")
print(f"SOL: ${sol_start:.2f} → ${final_sol:.2f} (+${total_sol_growth:.2f})")

# Count bloom stages
full_blooms = bloom_stages.count("FULL")
flowering = bloom_stages.count("FLOWERING")
budding = bloom_stages.count("BUDDING")

print(f"\n🌸 BLOOM PROGRESSION:")
print(f"  Full Blooms: {full_blooms}")
print(f"  Flowering: {flowering}")
print(f"  Budding: {budding}")

if full_blooms > 0:
    print("\n🌸 FULLY IN BLOOM!")
    print("The slow rally has blossomed!")
elif flowering > 0:
    print("\n🌺 STARTING TO FLOWER!")
    print("The bloom is opening...")
else:
    print("\n🌱 STILL GROWING...")
    print("Patient bloom, nice and slow...")

# Portfolio bloom
accounts = client.get_accounts()['accounts']
total_value = 0
for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        currency = acc['currency']
        if currency == 'USD':
            total_value += bal
        elif currency == 'BTC':
            total_value += bal * final_btc
        elif currency == 'ETH':
            total_value += bal * final_eth
        elif currency == 'SOL':
            total_value += bal * final_sol

print(f"\n💰 PORTFOLIO BLOOM:")
print(f"  Value: ${total_value:,.2f}")
print(f"  Growing towards $20k like spring flowers...")

print("\n🎵 'But he don't know what it means'")
print("   'Don't know what it means'")
print("   'And I said... yeaaaah'")
print("\n🌸 IN BLOOM - The nice slow rally continues...")
print("=" * 70)