#!/usr/bin/env python3
"""
📊 BTC LEVELING - CONSOLIDATION ANALYSIS
When BTC levels, it's building energy for the next move
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
║                      📊 BTC LEVELING PHASE 📊                             ║
║                   Consolidation = Energy Building                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ANALYZING CONSOLIDATION")
print("=" * 70)

# Track the leveling pattern
btc_samples = []
eth_samples = []
sol_samples = []

print("\n📍 TRACKING BTC CONSOLIDATION:")
print("-" * 50)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_samples.append(btc)
    eth_samples.append(eth)
    sol_samples.append(sol)
    
    if len(btc_samples) > 3:
        # Calculate recent range
        recent = btc_samples[-5:] if len(btc_samples) >= 5 else btc_samples
        btc_high = max(recent)
        btc_low = min(recent)
        btc_range = btc_high - btc_low
        btc_avg = statistics.mean(recent)
        btc_stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f}")
        print(f"  Range: ${btc_range:.0f} (${btc_low:,.0f} - ${btc_high:,.0f})")
        print(f"  Volatility: {(btc_stdev/btc_avg)*100:.3f}%")
        
        # Leveling detection
        if btc_range < 30:
            print("  📊 TIGHT LEVELING - Coiling spring!")
            if btc_range < 15:
                print("  ⚠️ EXTREME COMPRESSION - Breakout imminent!")
        elif btc_range < 50:
            print("  💭 Normal consolidation")
        else:
            print("  🌊 Wide range - still volatile")
        
        # Check support/resistance
        if abs(btc - 113000) < 20:
            print("  🎯 Testing $113,000 level")
        elif abs(btc - 113100) < 20:
            print("  ⚡ Testing $113,100 resistance")
        elif abs(btc - 112900) < 20:
            print("  📍 Testing $112,900 support")
    
    time.sleep(2)

# Final analysis
print("\n" + "=" * 70)
print("📊 LEVELING ANALYSIS:")
print("-" * 40)

btc_final_range = max(btc_samples) - min(btc_samples)
eth_final_range = max(eth_samples) - min(eth_samples)
sol_final_range = max(sol_samples) - min(sol_samples)

print(f"BTC Total Range: ${btc_final_range:.0f}")
print(f"ETH Total Range: ${eth_final_range:.2f}")
print(f"SOL Total Range: ${sol_final_range:.2f}")

# Compression ratio
btc_compression = (btc_final_range / btc_samples[-1]) * 100
print(f"\nBTC Compression: {btc_compression:.3f}%")

if btc_compression < 0.05:
    print("🔥 EXTREME COMPRESSION - Major move incoming!")
elif btc_compression < 0.1:
    print("⚡ Tight consolidation - Breakout setup")
elif btc_compression < 0.2:
    print("📊 Healthy consolidation")
else:
    print("🌊 Still finding equilibrium")

# What happens after leveling
print("\n💡 LEVELING IMPLICATIONS:")
print("-" * 40)
print("• Sellers exhausted at this level")
print("• Buyers accumulating")
print("• Energy building for next leg")
print("• Watch for volume spike = breakout signal")

# Check current position
accounts = client.get_accounts()['accounts']
btc_balance = 0
for acc in accounts:
    if acc['currency'] == 'BTC':
        btc_balance = float(acc['available_balance']['value'])
        break

if btc_balance > 0:
    print(f"\n💰 YOUR POSITION:")
    print(f"BTC Holdings: {btc_balance:.6f}")
    print(f"Ready to ride the breakout!")

print("\n🎯 NEXT MOVE TARGETS:")
print("• Break above $113,100 → Target $113,500")
print("• Break below $112,900 → Support at $112,500")
print("• The longer the leveling, the bigger the move!")
print("=" * 70)