#!/usr/bin/env python3
"""
🚀 BTC BREAKING UP - MOMENTUM ACCELERATING!
Track the breakout and its impact on our $20k path
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
║                      🚀 BTC BREAKING UP! 🚀                               ║
║                    Momentum Accelerating Higher!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Track the breakout
btc_start = 113000
samples = []
for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append(btc)
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - BREAKOUT STATUS:")
    print("-" * 50)
    print(f"BTC: ${btc:,.0f} ({btc - btc_start:+.0f})")
    print(f"ETH: ${eth:.2f}")
    print(f"SOL: ${sol:.2f}")
    
    # Momentum analysis
    if len(samples) > 1:
        velocity = samples[-1] - samples[-2]
        if velocity > 20:
            print("🔥 AGGRESSIVE BREAKOUT! Velocity: +${:.0f}".format(velocity))
        elif velocity > 10:
            print("⚡ Strong momentum: +${:.0f}".format(velocity))
        elif velocity > 0:
            print("📈 Steady climb: +${:.0f}".format(velocity))
        else:
            print("💭 Consolidating...")
    
    # Check critical levels
    if btc > 113500:
        print("\n🎯 BROKE $113,500! Next target: $114,000!")
    elif btc > 113250:
        print("📍 Above $113,250 - Building for next leg")
    
    time.sleep(3)

# Portfolio impact
accounts = client.get_accounts()['accounts']
btc_holdings = 0
for acc in accounts:
    if acc['currency'] == 'BTC':
        btc_holdings = float(acc['available_balance']['value'])
        break

if btc_holdings > 0:
    btc_value_gain = btc_holdings * (btc - btc_start)
    print(f"\n💰 YOUR BTC POSITION IMPACT:")
    print(f"Holdings: {btc_holdings:.6f} BTC")
    print(f"Gain from breakout: ${btc_value_gain:.2f}")

print("\n🎯 IMPACT ON $20K TARGET:")
print("-" * 50)
current_value = 7924.40
if btc > 113500:
    print("• BTC breaking $113,500 = Market euphoria")
    print("• Alts will follow = 10-15% portfolio boost")
    print("• Flywheel efficiency increases")
    print(f"• Could accelerate timeline by 3-5 days!")
    print(f"• NEW ESTIMATE: $20k in 5-7 days! 🚀")
else:
    print("• Breakout momentum building")
    print("• Creates perfect flywheel conditions")
    print("• Watch for alt rotation")

print("\n⚡ ACTION ITEMS:")
print("• Let positions ride the momentum")
print("• Watch for profit taking opportunities at round numbers")
print("• Prepare to milk at $114k, $115k levels")
print("• Keep flywheel ready for dips")
print("=" * 60)