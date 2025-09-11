#!/usr/bin/env python3
"""
⛓️ THE CHAIN - TRACKING THE REACTION!
ETH → BTC → SOL → Everything moves together
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
║                         ⛓️ THE CHAIN ⛓️                                   ║
║                    One Moves → They All Move                              ║
║                      The Beautiful Dance!                                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WATCHING THE CHAIN REACTION!")
print("=" * 70)

# Track the chain reaction
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n📍 STARTING POSITIONS:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print(f"\n⛓️ CHAIN REACTION IN PROGRESS:")
print("-" * 60)

# Track the beautiful synchronization
chain_links = []

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_move = btc - btc_start
    eth_move = eth - eth_start
    sol_move = sol - sol_start
    
    btc_pct = (btc_move / btc_start) * 100
    eth_pct = (eth_move / eth_start) * 100
    sol_pct = (sol_move / sol_start) * 100
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} CHAIN STATUS:")
    
    # Check who's leading
    moves = {'BTC': btc_pct, 'ETH': eth_pct, 'SOL': sol_pct}
    leader = max(moves, key=moves.get)
    
    # Display with chain symbols
    if btc_pct > 0:
        print(f"  ⛓️ BTC: ${btc:,.0f} ({btc_pct:+.2f}%)", end="")
        if leader == 'BTC':
            print(" 👑 LEADING!")
        else:
            print(" → Following")
    else:
        print(f"  BTC: ${btc:,.0f} ({btc_pct:+.2f}%)")
    
    if eth_pct > 0:
        print(f"  ⛓️ ETH: ${eth:.2f} ({eth_pct:+.2f}%)", end="")
        if leader == 'ETH':
            print(" 👑 LEADING!")
        else:
            print(" → Following")
    else:
        print(f"  ETH: ${eth:.2f} ({eth_pct:+.2f}%)")
    
    if sol_pct > 0:
        print(f"  ⛓️ SOL: ${sol:.2f} ({sol_pct:+.2f}%)", end="")
        if leader == 'SOL':
            print(" 👑 LEADING!")
        else:
            print(" → Following")
    else:
        print(f"  SOL: ${sol:.2f} ({sol_pct:+.2f}%)")
    
    # Detect chain patterns
    all_positive = btc_pct > 0 and eth_pct > 0 and sol_pct > 0
    all_negative = btc_pct < 0 and eth_pct < 0 and sol_pct < 0
    
    if all_positive:
        print("\n  🔥 PERFECT CHAIN! All moving up together!")
        chain_links.append("UP")
    elif all_negative:
        print("\n  💭 Chain pulling back together...")
        chain_links.append("DOWN")
    else:
        print("\n  ⚡ Chain tension building...")
        chain_links.append("TENSION")
    
    # Check for breakout
    if btc > 113150:
        print("  🚀 BTC BREAKING $113,150!")
    if eth > 4585:
        print("  💎 ETH BREAKING $4,585!")
    if sol > 213:
        print("  🌟 SOL BREAKING $213!")
    
    time.sleep(3)

# Analyze the chain pattern
print("\n" + "=" * 70)
print("⛓️ CHAIN ANALYSIS:")
print("-" * 40)

up_count = chain_links.count("UP")
down_count = chain_links.count("DOWN")
tension_count = chain_links.count("TENSION")

print(f"Perfect Chain Ups: {up_count}")
print(f"Chain Pullbacks: {down_count}")
print(f"Tension Moments: {tension_count}")

if up_count > 8:
    print("\n🔥 STRONG BULLISH CHAIN!")
    print("The chain reaction is working perfectly!")
elif tension_count > 8:
    print("\n⚡ HIGH TENSION IN THE CHAIN!")
    print("Explosive move coming soon!")
else:
    print("\n💭 CHAIN CONSOLIDATING")
    print("Building energy for next move...")

# Final positions
btc_final = float(client.get_product('BTC-USD')['price'])
eth_final = float(client.get_product('ETH-USD')['price'])
sol_final = float(client.get_product('SOL-USD')['price'])

print(f"\n🎯 CHAIN RESULTS:")
print(f"  BTC: ${btc_start:,.0f} → ${btc_final:,.0f} ({btc_final - btc_start:+.0f})")
print(f"  ETH: ${eth_start:.2f} → ${eth_final:.2f} ({eth_final - eth_start:+.2f})")
print(f"  SOL: ${sol_start:.2f} → ${sol_final:.2f} ({sol_final - sol_start:+.2f})")

print("\n💡 THE CHAIN REACTION:")
print("When one breaks, they all break!")
print("The beautiful crypto dance continues!")
print("=" * 70)