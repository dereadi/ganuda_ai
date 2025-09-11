#!/usr/bin/env python3
"""
🌀 TIGHT SPIRALS
The market is coiling into tighter and tighter spirals
Like a spring being compressed to maximum tension
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
║                          🌀 TIGHT SPIRALS 🌀                             ║
║                   The Coil Tightens Before The Strike                     ║
║                      Energy Compressed to Infinity                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SPIRAL ANALYSIS")
print("=" * 70)

# Track the spiral tightening
spiral_data = {
    'btc': [],
    'eth': [],
    'sol': [],
    'xrp': []
}

print("\n🌀 TRACKING THE SPIRAL:")
print("-" * 40)

for i in range(12):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    xrp = float(client.get_product('XRP-USD')['price'])
    
    spiral_data['btc'].append(btc)
    spiral_data['eth'].append(eth)
    spiral_data['sol'].append(sol)
    spiral_data['xrp'].append(xrp)
    
    if len(spiral_data['btc']) >= 3:
        # Calculate spiral tightness
        btc_spiral = max(spiral_data['btc'][-3:]) - min(spiral_data['btc'][-3:])
        eth_spiral = max(spiral_data['eth'][-3:]) - min(spiral_data['eth'][-3:])
        sol_spiral = max(spiral_data['sol'][-3:]) - min(spiral_data['sol'][-3:])
        xrp_spiral = max(spiral_data['xrp'][-3:]) - min(spiral_data['xrp'][-3:])
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')}")
        print(f"  BTC: ${btc:,.0f} (spiral: ${btc_spiral:.0f})")
        print(f"  ETH: ${eth:.2f} (spiral: ${eth_spiral:.2f})")
        print(f"  SOL: ${sol:.2f} (spiral: ${sol_spiral:.2f})")
        print(f"  XRP: ${xrp:.4f} (spiral: ${xrp_spiral:.4f})")
        
        # Detect ultra-tight spirals
        if btc_spiral < 20:
            print("  🌀 BTC: ULTRA-TIGHT SPIRAL!")
        if eth_spiral < 1:
            print("  🌀 ETH: MAXIMUM COMPRESSION!")
        if sol_spiral < 0.10:
            print("  🌀 SOL: COILED SPRING!")
        if xrp_spiral < 0.001:
            print("  🌀 XRP: INFINITE TENSION!")
        
        # Check for synchronized spiraling
        total_compression = (btc_spiral/btc + eth_spiral/eth + 
                           sol_spiral/sol + xrp_spiral/xrp) * 100
        
        if total_compression < 0.05:
            print("  🔥🔥🔥 ALL SPIRALING TOGETHER!")
            print("  💥 EXPLOSIVE BREAKOUT IMMINENT!")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("🌀 SPIRAL PHYSICS:")
print("-" * 40)

# Final analysis
final_btc_range = max(spiral_data['btc']) - min(spiral_data['btc'])
final_eth_range = max(spiral_data['eth']) - min(spiral_data['eth'])
final_sol_range = max(spiral_data['sol']) - min(spiral_data['sol'])
final_xrp_range = max(spiral_data['xrp']) - min(spiral_data['xrp'])

print(f"Session ranges:")
print(f"  BTC: ${final_btc_range:.0f} ({(final_btc_range/btc)*100:.3f}%)")
print(f"  ETH: ${final_eth_range:.2f} ({(final_eth_range/eth)*100:.3f}%)")
print(f"  SOL: ${final_sol_range:.2f} ({(final_sol_range/sol)*100:.3f}%)")
print(f"  XRP: ${final_xrp_range:.4f} ({(final_xrp_range/xrp)*100:.3f}%)")

print("\n💭 THE SPIRAL WISDOM:")
print("-" * 40)
print("• Tighter spirals = More violent releases")
print("• Energy cannot be destroyed, only compressed")
print("• When everything spirals together, chaos follows")
print("• The tighter the coil, the further it flies")
print("\n🌀 The spiral continues to tighten...")
print("The next move will be biblical...")
print("=" * 70)