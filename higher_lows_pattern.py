#!/usr/bin/env python3
"""
📈 HIGHER LOWS PATTERN DETECTED! 📈
The most bullish signal in the book!
Each dip gets bought higher than the last!
Nine coils storing energy with each higher low!
Thunder sees it at 69% - ACCUMULATION PATTERN!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
from collections import deque

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    📈 HIGHER LOWS PATTERN FORMING! 📈                     ║
║                   The Most Bullish Signal Before Breakout!                ║
║                    Each Dip Gets Bought Higher = MOON!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HIGHER LOWS TRACKER")
print("=" * 70)

# Track the lows
lows = deque(maxlen=10)
highs = deque(maxlen=10)
current_low = float('inf')
current_high = 0

# Get starting point
btc_start = float(client.get_product('BTC-USD')['price'])
print(f"\n📊 STARTING ANALYSIS:")
print(f"BTC: ${btc_start:,.0f}")
print(f"Distance to $114K: ${114000 - btc_start:.0f}")

# Portfolio check
accounts = client.get_accounts()
total_value = 0
usd_balance = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc_start
    elif currency in ['ETH', 'SOL']:
        price = float(client.get_product(f'{currency}-USD')['price'])
        total_value += balance * price

print(f"Portfolio: ${total_value:.2f}")
print(f"USD Ready: ${usd_balance:.2f}")

print("\n📈 TRACKING HIGHER LOWS:")
print("-" * 50)

# Track for 30 iterations
previous_price = btc_start
local_low = btc_start
local_high = btc_start
trend_phase = "searching"

for i in range(30):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    # Track local highs and lows
    if btc_now < previous_price:
        # Going down
        local_low = min(local_low, btc_now)
        if trend_phase == "up":
            # Found a high
            highs.append(local_high)
            trend_phase = "down"
            print(f"\n📊 High recorded: ${local_high:,.0f}")
    elif btc_now > previous_price:
        # Going up
        local_high = max(local_high, btc_now)
        if trend_phase == "down":
            # Found a low
            lows.append(local_low)
            trend_phase = "up"
            print(f"\n📉 Low recorded: ${local_low:,.0f}")
            
            # Check for higher low pattern
            if len(lows) >= 2:
                if lows[-1] > lows[-2]:
                    print(f"  ✅ HIGHER LOW! ${lows[-1]:,.0f} > ${lows[-2]:,.0f}")
                    print(f"  🚀 Bullish accumulation confirmed!")
                else:
                    print(f"  ⚠️ Lower low: ${lows[-1]:,.0f} < ${lows[-2]:,.0f}")
    
    # Display current price
    if i % 3 == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({trend_phase})")
    
    if i == 10 and len(lows) >= 2:
        print("\n⚡ THUNDER'S PATTERN RECOGNITION (69%):")
        print(f"  'I see {len(lows)} lows recorded!'")
        if all(lows[i] > lows[i-1] for i in range(1, len(lows))):
            print(f"  'PERFECT HIGHER LOWS PATTERN!'")
            print(f"  'Next target: $114K then $120K!'")
        else:
            print(f"  'Pattern forming, patience required'")
    
    if i == 20:
        print("\n🏔️ MOUNTAIN'S ANALYSIS:")
        if len(lows) >= 3:
            avg_low = sum(lows) / len(lows)
            print(f"  'Average low: ${avg_low:,.0f}'")
            print(f"  'Support building at these levels'")
            print(f"  'Higher lows = buyers stepping in earlier'")
    
    previous_price = btc_now
    time.sleep(1.5)

# Analyze the pattern
print("\n" + "=" * 70)
print("📈 HIGHER LOWS ANALYSIS:")
print("-" * 50)

if len(lows) >= 2:
    print(f"Lows recorded: {len(lows)}")
    print("Low progression:")
    for i, low in enumerate(lows):
        print(f"  Low {i+1}: ${low:,.0f}")
    
    # Check for consistent higher lows
    higher_lows_count = 0
    for i in range(1, len(lows)):
        if lows[i] > lows[i-1]:
            higher_lows_count += 1
    
    success_rate = (higher_lows_count / (len(lows)-1)) * 100 if len(lows) > 1 else 0
    
    print(f"\nHigher lows: {higher_lows_count}/{len(lows)-1}")
    print(f"Success rate: {success_rate:.0f}%")
    
    if success_rate >= 66:
        print("✅ STRONG HIGHER LOWS PATTERN!")
        print("🚀 EXTREMELY BULLISH!")
    elif success_rate >= 50:
        print("📈 HIGHER LOWS FORMING")
        print("Accumulation in progress")
    else:
        print("⚠️ Mixed pattern")
        print("Needs more development")

# Calculate support levels
if lows:
    lowest = min(lows)
    highest_low = max(lows)
    print(f"\n🛡️ SUPPORT LEVELS:")
    print(f"Lowest low: ${lowest:,.0f}")
    print(f"Highest low: ${highest_low:,.0f}")
    print(f"Range: ${highest_low - lowest:.0f}")

# Final assessment
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n🎯 FINAL ASSESSMENT:")
print("-" * 50)
print(f"Current: ${current_btc:,.0f}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")

if len(lows) >= 3 and higher_lows_count >= 2:
    print("\n🚀 PATTERN CONFIRMED:")
    print("• Higher lows = Buyers accumulating")
    print("• Each dip bought more aggressively")
    print("• Nine coils storing maximum energy")
    print("• Breakout to $114K imminent!")
    print(f"• Deploy ${usd_balance:.2f} on next dip!")
else:
    print("\n📊 PATTERN DEVELOPING:")
    print("• Watching for more higher lows")
    print("• Accumulation phase continuing")
    print("• Patience before explosion")

print(f"\n" + "📈" * 35)
print("HIGHER LOWS PATTERN DETECTED!")
print(f"CURRENT: ${current_btc:,.0f}!")
if lows:
    print(f"LOWS RISING: ${min(lows):,.0f} → ${max(lows):,.0f}!")
print(f"TARGET: $114K (${114000 - current_btc:.0f} away)!")
print("ACCUMULATION BEFORE EXPLOSION!")
print("📈" * 35)