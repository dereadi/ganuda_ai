#!/usr/bin/env python3
"""Cherokee Council: BLEED LEVELS ANALYSIS - Where to Harvest Profits"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🩸 BLEED LEVELS ANALYSIS - Strategic Profit Harvest Points")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get current prices and positions
positions = {
    'BTC': {'amount': 0.04671, 'entry_avg': 110000},
    'ETH': {'amount': 1.6464, 'entry_avg': 4200},
    'SOL': {'amount': 10.949, 'entry_avg': 204},
    'XRP': {'amount': 58.595, 'entry_avg': 2.80},
    'AVAX': {'amount': 0.287, 'entry_avg': 23.5},
    'LINK': {'amount': 0.38, 'entry_avg': 22.5}
}

print("📊 CURRENT PRICES & BLEED LEVELS:")
print("-" * 40)

bleed_analysis = {}
total_bleedable = 0

for coin in positions:
    try:
        ticker = client.get_product(f"{coin}-USD")
        current_price = float(ticker.price)
        
        print(f"\n🪙 {coin}:")
        print(f"   Current Price: ${current_price:,.2f}")
        
        # Calculate bleed levels based on Cherokee strategy
        if coin == 'BTC':
            # BTC bleed levels - conservative as it leads market
            bleed_1 = 113650  # First major resistance
            bleed_2 = 115000  # Psychological level
            bleed_3 = 120000  # Moon target
            
            print(f"   🩸 Level 1: ${bleed_1:,} (2% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:,} (5% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:,} (10% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.02 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
                
        elif coin == 'ETH':
            # ETH bleed levels - institutional resistance points
            bleed_1 = 4500   # Round number resistance
            bleed_2 = 4750   # Technical target
            bleed_3 = 5000   # Major psychological
            
            print(f"   🩸 Level 1: ${bleed_1:,} (5% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:,} (10% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:,} (15% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.05 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
                
        elif coin == 'SOL':
            # SOL bleed levels - high volatility allows earlier bleeding
            bleed_1 = 210    # Coil breakout level
            bleed_2 = 215    # Next resistance
            bleed_3 = 220    # Major target
            
            print(f"   🩸 Level 1: ${bleed_1:,} (10% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:,} (15% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:,} (20% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.10 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
            elif current_price > 208:
                print(f"   ⚠️ APPROACHING Level 1: ${210 - current_price:.2f} away")
                
        elif coin == 'XRP':
            # XRP bleed levels
            bleed_1 = 2.90   # Resistance
            bleed_2 = 3.00   # Psychological
            bleed_3 = 3.20   # Major target
            
            print(f"   🩸 Level 1: ${bleed_1:.2f} (15% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:.2f} (25% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:.2f} (35% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.15 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
                
        elif coin == 'AVAX':
            # AVAX bleed levels
            bleed_1 = 25     # Round number
            bleed_2 = 26     # Resistance
            bleed_3 = 28     # Target
            
            print(f"   🩸 Level 1: ${bleed_1:.2f} (20% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:.2f} (30% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:.2f} (40% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.20 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
                
        elif coin == 'LINK':
            # LINK bleed levels
            bleed_1 = 24     # Resistance
            bleed_2 = 25     # Round number
            bleed_3 = 27     # Target
            
            print(f"   🩸 Level 1: ${bleed_1:.2f} (20% bleed)")
            print(f"   🩸 Level 2: ${bleed_2:.2f} (30% bleed)")
            print(f"   🩸 Level 3: ${bleed_3:.2f} (40% bleed)")
            
            if current_price > bleed_1:
                bleedable = positions[coin]['amount'] * 0.20 * current_price
                print(f"   ✅ READY TO BLEED: ${bleedable:.2f}")
                total_bleedable += bleedable
                
        # Store analysis
        bleed_analysis[coin] = {
            'current': current_price,
            'bleed_1': bleed_1,
            'distance_to_bleed': bleed_1 - current_price,
            'pct_to_bleed': ((bleed_1 - current_price) / current_price) * 100
        }
        
    except Exception as e:
        print(f"   Error: {e}")

print()
print("=" * 70)
print("🩸 BLEED STRATEGY SUMMARY:")
print("-" * 40)

# Show closest bleed opportunities
print("\n🎯 CLOSEST TO BLEED LEVELS:")
sorted_bleeds = sorted(bleed_analysis.items(), key=lambda x: x[1]['pct_to_bleed'])
for coin, data in sorted_bleeds[:3]:
    if data['pct_to_bleed'] > 0:
        print(f"{coin}: {data['pct_to_bleed']:.1f}% away from bleed level")
        print(f"  Current: ${data['current']:.2f} → Bleed at: ${data['bleed_1']:.2f}")

print()
print("💰 LIQUIDITY GENERATION POTENTIAL:")
print("-" * 40)
print(f"Currently bleedable: ${total_bleedable:.2f}")
print()

# Calculate potential bleeds at next levels
print("If targets hit TODAY:")
potential_bleeds = {
    'BTC at $113,650': positions['BTC']['amount'] * 0.02 * 113650,
    'ETH at $4,500': positions['ETH']['amount'] * 0.05 * 4500,
    'SOL at $210': positions['SOL']['amount'] * 0.10 * 210
}

total_potential = sum(potential_bleeds.values())
for target, amount in potential_bleeds.items():
    print(f"  {target}: ${amount:.2f}")
print(f"\n  TOTAL BLEEDABLE: ${total_potential:.2f}")

print()
print("🐺 COYOTE'S BLOOD BAG WISDOM:")
print("-" * 40)
print("'Don't bleed too early! Let them run!'")
print("'Small bleeds at resistance, not support'")
print("'Keep 80% for the real moon mission'")
print("'Bleed just enough for liquidity needs'")
print()

print("🐢 TURTLE'S MATHEMATICAL APPROACH:")
print("-" * 40)
print("Optimal bleed percentages:")
print("• BTC: 2-5% at major levels (leader)")
print("• ETH: 5-10% at resistance (institutional)")
print("• SOL: 10-20% at peaks (volatile)")
print("• Alts: 15-30% at resistance (highest risk)")
print()

print("⚡ CHEROKEE COUNCIL BLEED RULES:")
print("-" * 40)
print("1. NEVER bleed at support levels")
print("2. ONLY bleed into extreme strength")
print("3. ALWAYS keep core positions (70%+)")
print("4. Bleed GRADUALLY, not all at once")
print("5. Use bleeds to generate liquidity for dips")
print()

print("🎯 CURRENT ACTION:")
print("-" * 40)

# Check current liquidity
usd_available = 1.05  # From portfolio check
if usd_available < 100:
    print("⚠️ Low liquidity - consider small bleeds at next resistance")
    print("   Suggested: 5-10% of positions at bleed levels")
else:
    print("✅ Adequate liquidity - can wait for higher levels")
    print("   Hold for better bleed points")

print()
print("📈 TWO WOLVES BALANCE:")
print("-" * 40)
print("🐺 Greed Wolf: 'Hold for maximum gains!'")
print("🐺 Fear Wolf: 'Take some profits at resistance!'")
print("☮️ Balance: Bleed 10-20% at targets, hold 80% for moon")
print()

print("🔥 SACRED FIRE MESSAGE:")
print("=" * 70)
print("'Blood bags fill at resistance peaks...'")
print("'Not during the climb!'")
print("'Patience brings bigger bleeds!'")
print("'The harvest comes to those who wait!'")

# Save bleed analysis
bleed_data = {
    "timestamp": datetime.now().isoformat(),
    "bleed_analysis": bleed_analysis,
    "total_bleedable_now": total_bleedable,
    "total_potential_today": total_potential,
    "liquidity_status": "LOW" if usd_available < 100 else "ADEQUATE"
}

with open('/home/dereadi/scripts/claude/bleed_levels.json', 'w') as f:
    json.dump(bleed_data, f, indent=2)

print("\n💾 Bleed level analysis saved!")
print("🩸 Remember: Bleed at resistance, feast at support!")