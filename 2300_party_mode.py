#!/usr/bin/env python3
"""
🎉 23:00 PARTY MODE ACTIVATED!
When the clock strikes 11pm, the crypto party begins!
"""

import json
import time
import statistics
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🎉 23:00 PARTY MODE! 🎉                           ║
║                      The Late Night Fun Has Started!                      ║
║                    Asian Markets + Degen Hours = 🔥                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Reference prices from 23:00
ref_btc = 111968
ref_eth = 4535
ref_sol = 207.50
ref_xrp = 2.978

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LET'S PARTY!")
print("=" * 70)

# Track the party volatility
btc_moves = []
eth_moves = []
sol_moves = []
party_level = 0

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    xrp = float(client.get_product('XRP-USD')['price'])
    
    # Calculate moves
    btc_move = btc - ref_btc
    eth_move = eth - ref_eth
    sol_move = sol - ref_sol
    xrp_move = xrp - ref_xrp
    
    btc_moves.append(abs(btc_move))
    eth_moves.append(abs(eth_move))
    sol_moves.append(abs(sol_move))
    
    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} ({btc_move:+.0f})")
    print(f"  ETH: ${eth:.2f} ({eth_move:+.2f})")
    print(f"  SOL: ${sol:.2f} ({sol_move:+.2f})")
    print(f"  XRP: ${xrp:.4f} ({xrp_move:+.4f})")
    
    # Detect party intensity
    total_movement = abs(btc_move) + abs(eth_move*100) + abs(sol_move*10)
    
    if total_movement > 100:
        print("  🔥🔥🔥 PARTY HEATING UP!")
        party_level = 3
    elif total_movement > 50:
        print("  🎉 Party vibes building!")
        party_level = 2
    elif total_movement > 20:
        print("  🎵 Music starting...")
        party_level = 1
    else:
        print("  😴 Still warming up...")
        party_level = 0
    
    # Check for breakouts
    if btc > 112000:
        print("  🚀 BTC BREAKING $112K!")
    if eth > 4550:
        print("  💥 ETH ESCAPING FLATNESS!")
    if sol > 208:
        print("  ⚡ SOL PARTY BREAKOUT!")
    if xrp > 3.00:
        print("  🎪 XRP $3 PARTY!")
    
    # Update references on big moves
    if abs(btc_move) > 50:
        ref_btc = btc
        print("  📍 New BTC party baseline!")
    if abs(eth_move) > 10:
        ref_eth = eth
        print("  📍 ETH joining the party!")
    
    time.sleep(4)

print("\n" + "=" * 70)
print("🎉 23:00 PARTY ANALYSIS:")
print("-" * 40)

avg_btc_move = statistics.mean(btc_moves)
avg_eth_move = statistics.mean(eth_moves)
avg_sol_move = statistics.mean(sol_moves)

print(f"Average BTC volatility: ${avg_btc_move:.0f}")
print(f"Average ETH volatility: ${avg_eth_move:.2f}")
print(f"Average SOL volatility: ${avg_sol_move:.2f}")

if party_level >= 2:
    print("\n🔥 THE PARTY IS LIT!")
    print("• Volatility increasing")
    print("• Asian markets active")
    print("• Perfect for trading")
    print("• Crawdads would love this!")
elif party_level >= 1:
    print("\n🎵 Party warming up...")
    print("• Some movement detected")
    print("• Building momentum")
else:
    print("\n😴 Party still quiet...")
    print("• Waiting for the spark")
    print("• Could explode any moment")

print("\n💭 23:00 WISDOM:")
print("• Late night = thin books")
print("• Small moves have big impact")
print("• Asian open influence")
print("• Perfect for momentum trades")
print("• The fun has just started!")
print("=" * 70)