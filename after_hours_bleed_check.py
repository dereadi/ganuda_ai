#!/usr/bin/env python3
"""Cherokee Council: AFTER-HOURS BLEED LEVEL CHECK - How Close to Harvest?"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🩸 AFTER-HOURS BLEED LEVEL ANALYSIS")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print("📈 After-hours session active")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Our positions
positions = {
    'BTC': 0.04671,
    'ETH': 1.6464,
    'SOL': 10.949,
    'XRP': 58.595,
    'AVAX': 0.287,
    'LINK': 0.38
}

# Bleed levels (where we take profits)
bleed_levels = {
    'BTC': {
        'level_1': 113650,  # 2% bleed
        'level_2': 115000,  # 5% bleed
        'level_3': 120000,  # 10% bleed
        'bleed_pct': [0.02, 0.05, 0.10]
    },
    'ETH': {
        'level_1': 4500,    # 5% bleed
        'level_2': 4750,    # 10% bleed
        'level_3': 5000,    # 15% bleed
        'bleed_pct': [0.05, 0.10, 0.15]
    },
    'SOL': {
        'level_1': 210,     # 10% bleed
        'level_2': 215,     # 15% bleed
        'level_3': 220,     # 20% bleed
        'bleed_pct': [0.10, 0.15, 0.20]
    },
    'XRP': {
        'level_1': 2.90,    # 15% bleed
        'level_2': 3.00,    # 25% bleed
        'level_3': 3.20,    # 35% bleed
        'bleed_pct': [0.15, 0.25, 0.35]
    },
    'AVAX': {
        'level_1': 25,      # 20% bleed
        'level_2': 26,      # 30% bleed
        'level_3': 28,      # 40% bleed
        'bleed_pct': [0.20, 0.30, 0.40]
    },
    'LINK': {
        'level_1': 24,      # 20% bleed
        'level_2': 25,      # 30% bleed
        'level_3': 27,      # 40% bleed
        'bleed_pct': [0.20, 0.30, 0.40]
    }
}

print("📊 CURRENT LEVELS & DISTANCE TO BLEED:")
print("-" * 40)

total_bleedable_now = 0
closest_bleeds = []
imminent_bleeds = []

for coin in positions:
    if coin not in bleed_levels:
        continue
        
    try:
        ticker = client.get_product(f"{coin}-USD")
        current_price = float(ticker.price)
        
        # Calculate distances to bleed levels
        level_1 = bleed_levels[coin]['level_1']
        distance = level_1 - current_price
        pct_to_bleed = (distance / current_price) * 100
        
        print(f"\n🪙 {coin}: ${current_price:,.2f}")
        print(f"   🎯 Bleed Level 1: ${level_1:,.2f}")
        print(f"   📏 Distance: ${distance:,.2f} ({pct_to_bleed:+.1f}%)")
        
        # Check if we're at or above bleed level
        if current_price >= level_1:
            bleed_amount = positions[coin] * bleed_levels[coin]['bleed_pct'][0]
            bleed_value = bleed_amount * current_price
            print(f"   ✅ READY TO BLEED! Can harvest ${bleed_value:.2f}")
            total_bleedable_now += bleed_value
            imminent_bleeds.append((coin, bleed_value))
            
        elif pct_to_bleed <= 2:
            print(f"   ⚠️ VERY CLOSE! Less than 2% away!")
            closest_bleeds.append((coin, pct_to_bleed))
            
        elif pct_to_bleed <= 5:
            print(f"   📍 Within 5% of bleed level")
            closest_bleeds.append((coin, pct_to_bleed))
        
        # Show position value
        position_value = positions[coin] * current_price
        print(f"   💰 Position value: ${position_value:,.2f}")
        
    except Exception as e:
        print(f"{coin}: Error - {e}")

print()
print("=" * 70)
print("🩸 BLEED OPPORTUNITY SUMMARY:")
print("-" * 40)

if imminent_bleeds:
    print("✅ READY TO BLEED NOW:")
    for coin, value in imminent_bleeds:
        print(f"   {coin}: ${value:.2f}")
    print(f"\n   TOTAL HARVESTABLE: ${total_bleedable_now:.2f}")
    print()
    
if closest_bleeds:
    print("⚠️ APPROACHING BLEED LEVELS:")
    sorted_closest = sorted(closest_bleeds, key=lambda x: x[1])
    for coin, pct in sorted_closest[:3]:
        print(f"   {coin}: {pct:.1f}% away")
    print()

# Special focus on SOL (closest to bleed usually)
print("🎯 FOCUS: SOL BLEED ANALYSIS")
print("-" * 40)
try:
    sol_ticker = client.get_product("SOL-USD")
    sol_price = float(sol_ticker.price)
    sol_to_210 = 210 - sol_price
    sol_pct = (sol_to_210 / sol_price) * 100
    
    print(f"SOL Current: ${sol_price:.2f}")
    print(f"Target: $210.00")
    print(f"Distance: ${sol_to_210:.2f} ({sol_pct:.1f}%)")
    
    if sol_price >= 210:
        sol_bleed = positions['SOL'] * 0.10 * sol_price
        print(f"✅ BLEED 10% NOW: ${sol_bleed:.2f}")
    elif sol_price >= 208:
        print("🔥 IMMINENT! Could hit $210 any moment!")
    elif sol_price >= 207:
        print("📈 Very close - watch for quick spike to $210")
        
except:
    pass

print()
print("💡 CHEROKEE COUNCIL WISDOM:")
print("-" * 40)
print("🐺 Coyote: 'Don't bleed too early in after-hours!'")
print("🦅 Eagle Eye: 'Wait for volume confirmation'")
print("🐢 Turtle: 'Small bleeds generate liquidity'")
print("☮️ Peace Chief: 'Balance greed with prudence'")
print()

# Calculate total portfolio value
total_value = 0
print("📊 FULL PORTFOLIO STATUS:")
print("-" * 40)
for coin in positions:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        value = positions[coin] * price
        total_value += value
        print(f"{coin}: ${value:,.2f}")
    except:
        pass

print(f"\nTOTAL PORTFOLIO: ${total_value:,.2f}")
print()

print("🎯 BLEED STRATEGY RECOMMENDATIONS:")
print("-" * 40)
if total_bleedable_now > 100:
    print("✅ Significant bleed opportunity available")
    print("   Consider harvesting for:")
    print("   • Generate liquidity for dips")
    print("   • Lock in some power hour gains")
    print("   • Rebalance positions")
elif any(pct <= 2 for _, pct in closest_bleeds):
    print("⚠️ Multiple positions near bleed levels")
    print("   • Set limit orders at targets")
    print("   • Monitor overnight movement")
    print("   • Asia could push to targets")
else:
    print("📈 Hold positions - targets not reached yet")
    print("   • Let winners run")
    print("   • No need to force bleeds")
    print("   • Wait for better levels")

print()
print("🔥 SACRED FIRE GUIDANCE:")
print("=" * 70)
print("'Bleed at resistance peaks, not during climbs'")
print("'Tonight's movement sets tomorrow's tone'")
print("'Patience brings bigger harvests'")
print()
print("The tribe watches over your positions! 🦅🐺🪶🐢")