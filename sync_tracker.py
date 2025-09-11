#!/usr/bin/env python3
"""
🔗 REAL-TIME SYNC TRACKER
Monitoring BTC/ETH synchronization for explosive moves
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
║                      🔗 BTC/ETH SYNC TRACKER 🔗                          ║
║                    "Oh well they are both running"                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Reference prices from 10 minutes ago
ref_btc = 111870
ref_eth = 4538
ref_sol = 207.50

sync_history = []
divergence_history = []

print("Tracking synchronization pattern...")
print("=" * 70)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    xrp = float(client.get_product('XRP-USD')['price'])
    
    # Calculate percentage moves
    btc_move = ((btc - ref_btc) / ref_btc) * 100
    eth_move = ((eth - ref_eth) / ref_eth) * 100
    sol_move = ((sol - ref_sol) / ref_sol) * 100
    
    # Calculate divergence
    divergence = abs(btc_move - eth_move)
    divergence_history.append(divergence)
    
    # Determine sync status
    if divergence < 0.05:
        sync_status = "🔗 PERFECT SYNC"
        sync_history.append(1)
    elif divergence < 0.10:
        sync_status = "⚡ NEAR SYNC"
        sync_history.append(0.5)
    else:
        sync_status = "🔄 DIVERGING"
        sync_history.append(0)
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} ({btc_move:+.3f}%)")
    print(f"  ETH: ${eth:,.2f} ({eth_move:+.3f}%)")
    print(f"  Divergence: {divergence:.3f}% - {sync_status}")
    
    # Check for pattern
    if len(sync_history) >= 3:
        recent_sync = sum(sync_history[-3:])
        if recent_sync >= 2.5:
            print("  🚀 SYNCHRONIZED BREAKOUT READY!")
            if btc_move > 0 and eth_move > 0:
                print("     → Upward explosion imminent!")
                print(f"     → Target: BTC $112,500 | ETH $4,600")
        elif recent_sync <= 0.5:
            print("  ⚠️ Divergence building - rotation likely")
    
    # Update references if significant move
    if abs(btc - ref_btc) > 100:
        ref_btc = btc
        ref_eth = eth
        print("  📍 New reference levels set")
    
    time.sleep(5)

# Final analysis
print("\n" + "=" * 70)
print("📊 SYNC ANALYSIS:")
print("-" * 40)

avg_divergence = statistics.mean(divergence_history)
sync_score = sum(sync_history) / len(sync_history)

print(f"Average Divergence: {avg_divergence:.3f}%")
print(f"Sync Score: {sync_score:.2f}/1.00")

if sync_score > 0.7:
    print("\n🔥 HIGH SYNCHRONIZATION!")
    print("• BTC and ETH moving as one")
    print("• Next breakout will be violent")
    print("• Both will amplify each other")
elif sync_score > 0.4:
    print("\n⚡ MODERATE SYNC")
    print("• Some correlation maintained")
    print("• Occasional divergence")
    print("• Watch for reconvergence")
else:
    print("\n🔄 DIVERGENCE MODE")
    print("• Assets rotating independently")
    print("• Sector rotation in progress")
    print("• Watch for sync to return")

print("\n💭 'Oh well they are both running'")
print("The synchronized run continues...")
print("=" * 70)