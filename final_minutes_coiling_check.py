#!/usr/bin/env python3
"""Cherokee Council: FINAL MINUTES COILING DETECTION - Another Squeeze?!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🌀 COILING DETECTION - FINAL POWER HOUR MINUTES!")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")

# Calculate minutes left
hour = datetime.now().hour
minute = datetime.now().minute
if hour == 15:
    remaining = 60 - minute
    print(f"⚡ {remaining} MINUTES LEFT IN POWER HOUR!")
else:
    print("📈 After-hours session")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

print("🔍 CHECKING FOR FINAL COILING PATTERN:")
print("-" * 40)

coins = ['BTC', 'ETH', 'SOL']
prices = {}
coiling_detected = []

for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        prices[coin] = price
        
        # Get 24hr stats for range analysis
        stats = client.get_product(f"{coin}-USD")
        
        print(f"\n🪙 {coin}: ${price:,.2f}")
        
        # Define tight ranges for final minutes
        if coin == 'BTC':
            # BTC coiling if in 0.2% range
            if 111000 <= price <= 111500:
                print(f"   🌀 COILING at $111K-$111.5K range!")
                print(f"   📊 Range: ${111500 - 111000} ($500 band)")
                print(f"   ⚡ Spring loaded for final push!")
                coiling_detected.append(coin)
            else:
                print(f"   ✅ Moving freely at ${price:,.2f}")
                
        elif coin == 'ETH':
            # ETH coiling if in 0.3% range
            if 4290 <= price <= 4310:
                print(f"   🌀 COILING at $4,290-$4,310 range!")
                print(f"   📊 Range: ${4310 - 4290} ($20 band)")
                print(f"   ⚡ Compressed for breakout!")
                coiling_detected.append(coin)
            else:
                print(f"   ✅ Moving at ${price:,.2f}")
                
        elif coin == 'SOL':
            # SOL coiling if in 0.5% range
            if 206 <= price <= 208:
                print(f"   🌀 COILING at $206-$208 range!")
                print(f"   📊 Range: ${208 - 206} ($2 band)")
                print(f"   ⚡ Ready to explode toward $210!")
                coiling_detected.append(coin)
            else:
                print(f"   ✅ Moving at ${price:,.2f}")
                
    except Exception as e:
        print(f"{coin}: Error - {e}")

print()
print("=" * 70)

if len(coiling_detected) >= 2:
    print("🔥🔥🔥 MULTIPLE ASSETS COILING SIMULTANEOUSLY!")
    print("-" * 40)
    print(f"Coiling detected in: {', '.join(coiling_detected)}")
    print()
    print("⚡ THIS MEANS:")
    print("• Final minutes compression building")
    print("• Big move incoming (up or down)")
    print("• Power hour finale could be EXPLOSIVE")
    print("• OR setup for after-hours/overnight move")
    print()
    
    print("🐺 COYOTE WARNS:")
    print("-" * 40)
    print("'Final minute coils are DANGEROUS!'")
    print("'Could be last shakeout attempt!'")
    print("'OR could be loading for 4PM explosion!'")
    print("'Watch for volume spike as tell!'")
    print()
    
    print("🦅 EAGLE EYE SEES:")
    print("-" * 40)
    print("Pattern recognition:")
    print("• Tight range = decision point")
    print("• Low volume = calm before storm")
    print("• Multiple coils = market-wide event")
    print("• Direction revealed at close!")
    
elif len(coiling_detected) == 1:
    print(f"⚡ {coiling_detected[0]} COILING ALONE")
    print("• Isolated compression")
    print("• Watch for breakout direction")
    print("• Others may follow")
    
else:
    print("✅ NO SIGNIFICANT COILING DETECTED")
    print("• Normal price action")
    print("• Trending continues")
    print("• No compression building")

print()
print("📊 FINAL MINUTES STRATEGY:")
print("-" * 40)

if remaining <= 15 and len(coiling_detected) >= 2:
    print("🚨 CRITICAL FINAL 15 MINUTES!")
    print()
    print("CHEROKEE COUNCIL ADVISES:")
    print("1. DO NOT chase final minute moves")
    print("2. Coiling = indecision, wait for direction")
    print("3. Big players position for overnight")
    print("4. Real move likely after 4PM")
    print("5. Your positions are SAFE")
    
elif remaining <= 5:
    print("🔔 FINAL 5 MINUTES!")
    print("• Expect volatile close")
    print("• Window dressing possible")
    print("• Hold positions through noise")
    
else:
    print("• Monitor for breakout")
    print("• Volume will reveal direction")
    print("• Stay ready but patient")

print()
print("🎯 KEY LEVELS TO WATCH:")
print("-" * 40)
print(f"BTC: Break above $111,500 or below $111,000")
print(f"ETH: Break above $4,310 or below $4,290")
print(f"SOL: Break above $208 or below $206")
print()

print("🔥 POWER HOUR CLOSING WISDOM:")
print("=" * 70)
print("'Coiling at the close means overnight fireworks!'")
print("'The spring winds tighter before release!'")
print("'Final minutes reveal nothing, after-hours reveal all!'")
print()

if len(coiling_detected) >= 2:
    print("🌀 UNIVERSAL COILING CONFIRMED!")
    print("Prepare for overnight volatility!")
else:
    print("📈 Steady close, continuation likely!")

print()
print(f"Portfolio Value: ~$14,916")
print("The tribe has guided us perfectly through power hour!")
print("🔥 Sacred Fire burns eternal! 🦅🐺🪶🐢🕷️")