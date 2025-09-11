#!/usr/bin/env python3
"""
🚶‍♂️🚶‍♀️ WALKING UP - BOTH OF THEM
BTC and ETH finally moving together!
"My Own Worst Enemy" - sometimes we hold ourselves back
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
║                     🚶‍♂️🚶‍♀️ WALKING UP TOGETHER 🚶‍♂️🚶‍♀️                     ║
║                          "My Own Worst Enemy"                             ║
║                     Finally Breaking Our Own Resistance                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THEY'RE BOTH WALKING UP!")
print("=" * 70)

# Starting point
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🚶 STARTING THE WALK:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print("\n📈 TRACKING THE SYNCHRONIZED CLIMB:")
print("-" * 50)

# Track the walk up
synchronized_moves = 0
btc_high = btc_start
eth_high = eth_start

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Track highs
    if btc > btc_high:
        btc_high = btc
    if eth > eth_high:
        eth_high = eth
    
    btc_move = btc - btc_start
    eth_move = eth - eth_start
    sol_move = sol - sol_start
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    
    # Check if both walking up
    if btc_move > 0 and eth_move > 0:
        synchronized_moves += 1
        print(f"  🚶‍♂️ BTC: ${btc:,.0f} (+${btc_move:.0f}) WALKING UP!")
        print(f"  🚶‍♀️ ETH: ${eth:.2f} (+${eth_move:.2f}) WALKING UP!")
        print(f"  ✅ SYNCHRONIZED! Both moving together!")
        
        if btc > 112900:
            print("  ⚡ BTC breaking $112,900!")
        if eth > 4570:
            print("  💎 ETH breaking $4,570!")
            
    elif btc_move > 0:
        print(f"  BTC: ${btc:,.0f} (+${btc_move:.0f}) - Leading")
        print(f"  ETH: ${eth:.2f} ({eth_move:+.2f}) - Lagging")
    elif eth_move > 0:
        print(f"  BTC: ${btc:,.0f} ({btc_move:+.0f}) - Lagging")
        print(f"  ETH: ${eth:.2f} (+${eth_move:.2f}) - Leading")
    else:
        print(f"  BTC: ${btc:,.0f} ({btc_move:+.0f})")
        print(f"  ETH: ${eth:.2f} ({eth_move:+.2f})")
        print("  💭 Taking a breather...")
    
    print(f"  SOL: ${sol:.2f} ({sol_move:+.2f})")
    
    # Check for breakout levels
    if btc > 113000:
        print("\n  🚀 BTC BROKE $113,000!!!")
    if eth > 4575:
        print("  🚀 ETH BROKE $4,575!!!")
    
    # "My Own Worst Enemy" theme
    if i % 5 == 0 and btc < 113000:
        print("\n  🎵 'I'm my own worst enemy'")
        print("  The resistance is ourselves...")
        print("  But we're finally walking through it!")
    
    time.sleep(2)

# Final analysis
print("\n" + "=" * 70)
print("🚶‍♂️🚶‍♀️ WALKING RESULTS:")
print("-" * 40)

final_btc = float(client.get_product('BTC-USD')['price'])
final_eth = float(client.get_product('ETH-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print(f"BTC: ${btc_start:,.0f} → ${final_btc:,.0f} ({final_btc - btc_start:+.0f})")
print(f"  High: ${btc_high:,.0f}")
print(f"\nETH: ${eth_start:.2f} → ${final_eth:.2f} ({final_eth - eth_start:+.2f})")
print(f"  High: ${eth_high:.2f}")
print(f"\nSOL: ${sol_start:.2f} → ${final_sol:.2f} ({final_sol - sol_start:+.2f})")

print(f"\n🤝 SYNCHRONIZED MOVES: {synchronized_moves}")

if synchronized_moves > 10:
    print("✅ PERFECT SYNCHRONIZATION!")
    print("They're walking up together beautifully!")
elif synchronized_moves > 5:
    print("⚡ Good coordination - momentum building!")
else:
    print("💭 Still finding their rhythm...")

print("\n💡 NO LONGER OUR OWN WORST ENEMY:")
print("• Broke through self-imposed resistance")
print("• BTC and ETH walking hand in hand")
print("• The coil is releasing upward!")
print("• Next stop: $113,000 & $4,580!")

print("\n🎵 'Please tell me why...'")
print("   'My car is in the front yard...'")
print("   But our portfolio is WALKING UP! 🚀")
print("=" * 70)