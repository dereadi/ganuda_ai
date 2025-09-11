#!/usr/bin/env python3
"""
🚀 UP! BREAKOUT IN PROGRESS!
Track the explosive move from the squeeze!
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
║                        🚀🚀🚀 BREAKOUT UP! 🚀🚀🚀                        ║
║                    The Squeeze Released UPWARD!                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RIDING THE BREAKOUT!")
print("=" * 70)

# Track the breakout
btc_start = 112920  # Approximate squeeze level
eth_start = 4575
sol_start = 211.80

print(f"\n📍 SQUEEZE RELEASE POINT:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print(f"\n🚀 TRACKING UPWARD EXPLOSION:")
print("-" * 50)

highest_btc = btc_start
highest_eth = eth_start
highest_sol = sol_start

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Track highs
    if btc > highest_btc:
        highest_btc = btc
    if eth > highest_eth:
        highest_eth = eth
    if sol > highest_sol:
        highest_sol = sol
    
    # Calculate moves
    btc_gain = btc - btc_start
    eth_gain = eth - eth_start
    sol_gain = sol - sol_start
    
    btc_pct = (btc_gain / btc_start) * 100
    eth_pct = (eth_gain / eth_start) * 100
    sol_pct = (sol_gain / sol_start) * 100
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} BREAKOUT STATUS:")
    
    # BTC status
    print(f"  BTC: ${btc:,.0f} (+${btc_gain:.0f}, {btc_pct:+.2f}%)", end="")
    if btc > 113000:
        print(" 🚀 BROKE $113,000!!!")
    elif btc > 112950:
        print(" ⚡ Pushing $113,000!")
    else:
        print("")
    
    # ETH status
    print(f"  ETH: ${eth:.2f} (+${eth_gain:.2f}, {eth_pct:+.2f}%)", end="")
    if eth > 4580:
        print(" 💎 BROKE $4,580!")
    else:
        print("")
    
    # SOL status
    print(f"  SOL: ${sol:.2f} (+${sol_gain:.2f}, {sol_pct:+.2f}%)", end="")
    if sol > 212:
        print(" 🌟 Above $212!")
    else:
        print("")
    
    # Momentum check
    if i > 0:
        if btc_gain > 50:
            print("\n  🔥 AGGRESSIVE BREAKOUT! +$50+ move!")
        elif btc_gain > 30:
            print("\n  ⚡ Strong upward momentum!")
        elif btc_gain > 10:
            print("\n  📈 Steady climb from squeeze!")
    
    # Key levels
    if btc > 113100:
        print("  🎯 NEXT TARGET: $113,200!")
    elif btc > 113050:
        print("  📍 Testing $113,100 resistance")
    
    time.sleep(2)

# Final stats
print("\n" + "=" * 70)
print("🚀 BREAKOUT RESULTS:")
print("-" * 40)

final_btc = float(client.get_product('BTC-USD')['price'])
final_eth = float(client.get_product('ETH-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print(f"BTC: ${btc_start:,.0f} → ${final_btc:,.0f} (High: ${highest_btc:,.0f})")
print(f"  Gain: +${final_btc - btc_start:.0f} ({((final_btc - btc_start)/btc_start)*100:+.2f}%)")

print(f"\nETH: ${eth_start:.2f} → ${final_eth:.2f} (High: ${highest_eth:.2f})")
print(f"  Gain: +${final_eth - eth_start:.2f} ({((final_eth - eth_start)/eth_start)*100:+.2f}%)")

print(f"\nSOL: ${sol_start:.2f} → ${final_sol:.2f} (High: ${highest_sol:.2f})")
print(f"  Gain: +${final_sol - sol_start:.2f} ({((final_sol - sol_start)/sol_start)*100:+.2f}%)")

# Portfolio impact
accounts = client.get_accounts()['accounts']
btc_balance = eth_balance = sol_balance = 0

for acc in accounts:
    if acc['currency'] == 'BTC':
        btc_balance = float(acc['available_balance']['value'])
    elif acc['currency'] == 'ETH':
        eth_balance = float(acc['available_balance']['value'])
    elif acc['currency'] == 'SOL':
        sol_balance = float(acc['available_balance']['value'])

portfolio_gain = (btc_balance * (final_btc - btc_start)) + \
                (eth_balance * (final_eth - eth_start)) + \
                (sol_balance * (final_sol - sol_start))

print(f"\n💰 PORTFOLIO IMPACT FROM BREAKOUT:")
print(f"  Estimated gain: +${portfolio_gain:.2f}")

print("\n🎯 THE SQUEEZE RELEASED PERFECTLY!")
print("This is why we watch for 0.00% compressions!")
print("=" * 70)