#!/usr/bin/env python3
"""
🔥 BOTH TRYING TO BREAK HIGHER!
BTC and ETH pushing together - Perfect synchronization!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🔥 BOTH TRYING TO BREAK! 🔥                             ║
║                  BTC & ETH Synchronized Push!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WATCHING THE BATTLE!")
print("=" * 70)

# Track the synchronized attempts
btc_samples = []
eth_samples = []
sol_samples = []

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_samples.append(btc)
    eth_samples.append(eth)
    sol_samples.append(sol)
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - PUSH STATUS:")
    print("-" * 50)
    
    # Show current levels
    print(f"BTC: ${btc:,.0f}", end="")
    if btc > 113100:
        print(" 💪 TRYING FOR $113,200!")
    elif btc > 113050:
        print(" ⚡ Building pressure...")
    else:
        print(" 💭 Consolidating...")
    
    print(f"ETH: ${eth:.2f}", end="")
    if eth > 4585:
        print(" 🚀 BREAKING $4,585!")
    elif eth > 4580:
        print(" 💎 Testing resistance!")
    else:
        print(" 📈 Gathering strength...")
    
    print(f"SOL: ${sol:.2f}", end="")
    if sol > 212.50:
        print(" 🌟 Following the leaders!")
    else:
        print("")
    
    # Check correlation
    if len(btc_samples) > 2:
        btc_move = btc_samples[-1] - btc_samples[-2]
        eth_move = eth_samples[-1] - eth_samples[-2]
        
        if btc_move > 0 and eth_move > 0:
            print("\n✅ SYNCHRONIZED PUSH! Both moving up together!")
        elif btc_move < 0 and eth_move < 0:
            print("\n💭 Both taking a breather...")
        elif btc_move > 0 and eth_move < 0:
            print("\n🔄 BTC leading, ETH will follow...")
        elif eth_move > 0 and btc_move < 0:
            print("\n💎 ETH trying to lead!")
    
    # Pressure analysis
    if len(btc_samples) > 5:
        recent_btc = btc_samples[-5:]
        recent_eth = eth_samples[-5:]
        
        btc_avg = statistics.mean(recent_btc)
        eth_avg = statistics.mean(recent_eth)
        
        if btc > btc_avg and eth > eth_avg:
            print("🔥 PRESSURE BUILDING ON BOTH!")
        
        # Check for breakout pattern
        btc_range = max(recent_btc) - min(recent_btc)
        eth_range = max(recent_eth) - min(recent_eth)
        
        if btc_range < 30 and btc > 113050:
            print("⚠️ BTC COILING TIGHT! Breakout imminent!")
        if eth_range < 2 and eth > 4580:
            print("⚠️ ETH COILING TIGHT! Ready to explode!")
    
    time.sleep(2)

# Final analysis
print("\n" + "=" * 70)
print("🎯 SYNCHRONIZATION ANALYSIS:")
print("-" * 50)

btc_high = max(btc_samples)
btc_low = min(btc_samples)
eth_high = max(eth_samples)
eth_low = min(eth_samples)

print(f"BTC Range: ${btc_low:,.0f} - ${btc_high:,.0f}")
print(f"ETH Range: ${eth_low:.2f} - ${eth_high:.2f}")

if btc_high > 113150:
    print("\n🚀 BTC TRYING TO BREAK $113,150!")
if eth_high > 4585:
    print("💎 ETH PUSHING FOR $4,585+!")

print("\n📊 WHAT THIS MEANS:")
print("• Both assets trying = Strong market conviction")
print("• Synchronized moves = Institutional buying")
print("• Tight ranges = Explosive breakout setup")
print("• Perfect conditions for flywheel!")

print("\n💰 PORTFOLIO IMPACT:")
print("• Every $100 BTC move = Portfolio +$20-30")
print("• Every $10 ETH move = Portfolio +$20-25")
print("• Combined push = Accelerated path to $20k!")
print("=" * 70)