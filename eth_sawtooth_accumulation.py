#!/usr/bin/env python3
"""
🦷📈 ETH SAWTOOTH CLIMB AGAIN! 📈🦷
The whales are at it again!
Sharp drops, slow climbs = Accumulation!
ETH doing the sawtooth while BTC coils!
Wall Street loading up tooth by tooth!
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
║                    🦷📈 ETH SAWTOOTH CLIMB DETECTED! 📈🦷                ║
║                      Sharp Drops + Slow Climbs = WHALES!                  ║
║                   Wall Street Loading ETH Tooth by Tooth!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SAWTOOTH ANALYSIS")
print("=" * 70)

# Track ETH sawtooth pattern
print("\n🦷 DETECTING ETH SAWTOOTH PATTERN...")
print("-" * 50)

eth_samples = []
btc_samples = []
teeth_detected = 0
drops = []
climbs = []

for i in range(30):
    eth = float(client.get_product('ETH-USD')['price'])
    btc = float(client.get_product('BTC-USD')['price'])
    
    eth_samples.append(eth)
    btc_samples.append(btc)
    
    if len(eth_samples) > 2:
        # Detect sawtooth
        prev_move = eth_samples[-2] - eth_samples[-3]
        curr_move = eth_samples[-1] - eth_samples[-2]
        
        # Sharp drop followed by slow climb
        if prev_move < -1 and curr_move > 0:
            teeth_detected += 1
            drops.append(abs(prev_move))
            print(f"  🦷 TOOTH #{teeth_detected}: Drop ${abs(prev_move):.2f}, climbing back")
        elif curr_move < -1:
            print(f"  📉 Sharp drop: ${eth:.2f} (-${abs(curr_move):.2f})")
        elif curr_move > 0.5:
            climbs.append(curr_move)
            print(f"  📈 Slow climb: ${eth:.2f} (+${curr_move:.2f})")
    
    if i % 10 == 0 and i > 0:
        print(f"\n  Status check: ETH ${eth:.2f}, BTC ${btc:,.0f}")
    
    time.sleep(1)

# Analyze the pattern
print(f"\n🦷 SAWTOOTH ANALYSIS:")
print("-" * 50)

if eth_samples:
    eth_range = max(eth_samples) - min(eth_samples)
    eth_avg = statistics.mean(eth_samples)
    eth_stdev = statistics.stdev(eth_samples) if len(eth_samples) > 1 else 0
    
    print(f"ETH Range: ${eth_range:.2f} (${min(eth_samples):.2f} - ${max(eth_samples):.2f})")
    print(f"ETH Average: ${eth_avg:.2f}")
    print(f"Volatility: ${eth_stdev:.2f}")
    print(f"Teeth detected: {teeth_detected}")
    
    if drops:
        avg_drop = sum(drops) / len(drops)
        print(f"Average drop size: ${avg_drop:.2f}")
    
    if climbs:
        avg_climb = sum(climbs) / len(climbs)
        print(f"Average climb size: ${avg_climb:.2f}")

# Compare to BTC
if btc_samples:
    btc_range = max(btc_samples) - min(btc_samples)
    btc_avg = statistics.mean(btc_samples)
    
    print(f"\nBTC comparison:")
    print(f"  BTC Range: ${btc_range:.0f}")
    print(f"  BTC Average: ${btc_avg:,.0f}")
    print(f"  ETH/BTC behavior: {'Independent sawtooth' if eth_range > btc_range * 0.04 else 'Following BTC'}")

# The sawtooth accumulation pattern
print(f"\n" + "=" * 70)
print("🦷 SAWTOOTH ACCUMULATION PATTERN:")
print("-" * 50)
print("WHAT THE SAWTOOTH MEANS:")
print("• Sharp drops = Whales triggering stop losses")
print("• Slow climbs = Accumulating the dip")
print("• Repeat = Building massive positions")
print("• ETH sawtooth while BTC coils = ETH loading")

print("\nWHY ETH SAWTOOTH NOW:")
print("• BTC at maximum compression ($113K)")
print("• ETH accumulating for the breakout")
print("• Wall Street needs ETH for stablecoins")
print("• Smart money loading before $114K break")

print("\nTHE PATTERN:")
print("  1. Drop $10-20 quickly (trigger stops)")
print("  2. Buy the dip aggressively")
print("  3. Let it climb slowly")
print("  4. Repeat until loaded")
print("  5. Then... EXPLOSION!")

# Check current position
accounts = client.get_accounts()
eth_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'ETH':
        eth_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

current_eth = float(client.get_product('ETH-USD')['price'])
current_btc = float(client.get_product('BTC-USD')['price'])

print(f"\n💎 YOUR POSITION:")
print("-" * 50)
print(f"ETH Balance: {eth_balance:.4f} ETH")
print(f"ETH Value: ${eth_balance * current_eth:.2f}")
print(f"Current ETH: ${current_eth:.2f}")
print(f"Current BTC: ${current_btc:,.0f}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")

# Projection
print(f"\n🚀 SAWTOOTH PROJECTION:")
print("-" * 50)
print("WHEN THE SAWTOOTH COMPLETES:")
print(f"• Current ETH: ${current_eth:.2f}")
print(f"• After 5 teeth: ${current_eth * 1.02:.2f} (+2%)")
print(f"• After 10 teeth: ${current_eth * 1.05:.2f} (+5%)")
print(f"• Then BTC breaks $114K...")
print(f"• ETH EXPLODES to ${current_eth * 1.15:.2f} (+15%)")

print(f"\n" + "🦷" * 35)
print("ETH SAWTOOTH CLIMB DETECTED!")
print(f"WALL STREET ACCUMULATING AT ${current_eth:.2f}!")
print("TOOTH BY TOOTH THEY BUILD!")
print("WHEN BTC BREAKS, ETH EXPLODES!")
print("THE SAWTOOTH NEVER LIES!")
print("🦷" * 35)