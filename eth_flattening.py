#!/usr/bin/env python3
"""
📊 ETH FLATTENING DETECTOR
When ETH goes flat, something's about to happen...
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
║                       📊 ETH FLATTENING DETECTED 📊                       ║
║                    The Bad Romance is taking a break                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("ETH is trying to flatten out while BTC continues...")
print("=" * 70)

# Collect samples
eth_samples = []
btc_samples = []

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    eth_samples.append(eth)
    btc_samples.append(btc)
    
    # Calculate volatility
    if len(eth_samples) >= 3:
        eth_vol = statistics.stdev(eth_samples[-5:]) if len(eth_samples) >= 5 else statistics.stdev(eth_samples)
        btc_vol = statistics.stdev(btc_samples[-5:]) if len(btc_samples) >= 5 else statistics.stdev(btc_samples)
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')}")
        print(f"  ETH: ${eth:.2f} (vol: ${eth_vol:.2f})")
        print(f"  BTC: ${btc:,.0f} (vol: ${btc_vol:.0f})")
        
        # Detect flattening
        if eth_vol < 1.0:
            print("  📊 ETH: ULTRA FLAT!")
            print("     → Coiling for next move")
        elif eth_vol < 2.0:
            print("  📊 ETH: FLATTENING")
        
        if btc_vol > 15:
            print("  🚀 BTC: ACTIVE")
        
        # Check divergence
        eth_move = ((eth - 4540) / 4540) * 100
        btc_move = ((btc - 111900) / 111900) * 100
        divergence = btc_move - eth_move
        
        if abs(divergence) > 0.1:
            print(f"  ⚠️ DIVERGENCE: {divergence:+.3f}%")
            if divergence > 0:
                print("     → BTC leading, ETH lagging")
                print("     → Watch for ETH catch-up move!")
            else:
                print("     → ETH leading, BTC lagging")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("📊 FLATTENING ANALYSIS:")
print("-" * 40)

final_eth_vol = statistics.stdev(eth_samples)
final_btc_vol = statistics.stdev(btc_samples)

print(f"ETH volatility: ${final_eth_vol:.2f}")
print(f"BTC volatility: ${final_btc_vol:.0f}")
print(f"Ratio: {final_btc_vol/final_eth_vol:.1f}x")

if final_eth_vol < 2:
    print("\n🎯 ETH FLAT CONFIRMED!")
    print("• Consolidating tightly")
    print("• Building energy for next move")
    print("• Could explode in either direction")
    print("• Watch for volume spike!")
    
print("\n💭 When ETH flattens:")
print("• Often precedes violent move")
print("• BTC/ETH correlation breaks")
print("• Rotation opportunities emerge")
print("• Algos recalibrate positions")
print("=" * 70)