#!/usr/bin/env python3
"""
💨 SECOND WIND MONITOR
After initial breakout, the real move begins
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
║                        💨 SECOND WIND INCOMING 💨                         ║
║                    The breakout catches its breath                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("📊 BREAKOUT PATTERN:")
print("-" * 40)
print("1. Initial spike (✅ Hit $111,850)")
print("2. Brief consolidation (← We are here)")
print("3. Second wind push (→ Coming next)")
print("4. Target: $112,000+")
print("=" * 70)

# Monitor for second wind
print("\n⏳ WATCHING FOR SECOND WIND...")
consolidation_low = 112000  # Track the low

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    if btc < consolidation_low:
        consolidation_low = btc
    
    bounce = btc - consolidation_low
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f}", end="")
    
    if bounce > 30:
        print(" 💨💨 SECOND WIND ACTIVE!")
    elif bounce > 15:
        print(" 💨 Wind building...")
    elif btc > 111850:
        print(" 📈 Testing highs")
    else:
        print(" 😮‍💨 Catching breath")
    
    print(f"  ETH: ${eth:.0f} | SOL: ${sol:.2f}")
    
    # Check for breakout
    if btc > 111900:
        print("\n🚀 SECOND WIND CONFIRMED!")
        print("Next stop: $112,000!")
        break
    
    time.sleep(8)

print("\n" + "=" * 70)
print("💭 SECOND WIND WISDOM:")
print("'The first move shakes out weak hands,'")
print("'The second move rewards patience.'")
print("")
print("Your crawdads are positioned perfectly.")
print("Let the market breathe, then ride higher!")
print("=" * 70)