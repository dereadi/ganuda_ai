#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 LARGE OSCILLATIONS - SIMPLE CHECK
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Load API
with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey']
)

print("🔥 LARGE OSCILLATION CHECK")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 60)

# Get current prices multiple times to detect movement
prices = []
for i in range(3):
    btc = client.get_product("BTC-USD")
    eth = client.get_product("ETH-USD") 
    sol = client.get_product("SOL-USD")
    
    prices.append({
        'btc': float(btc['price']),
        'eth': float(eth['price']),
        'sol': float(sol['price'])
    })
    
    if i < 2:
        import time
        time.sleep(2)  # Wait 2 seconds between checks

# Calculate swings from quick samples
btc_prices = [p['btc'] for p in prices]
eth_prices = [p['eth'] for p in prices]
sol_prices = [p['sol'] for p in prices]

btc_high = max(btc_prices)
btc_low = min(btc_prices)
btc_swing = btc_high - btc_low
btc_swing_pct = (btc_swing / btc_low) * 100 if btc_low > 0 else 0

eth_high = max(eth_prices)
eth_low = min(eth_prices)
eth_swing = eth_high - eth_low
eth_swing_pct = (eth_swing / eth_low) * 100 if eth_low > 0 else 0

sol_high = max(sol_prices)
sol_low = min(sol_prices)
sol_swing = sol_high - sol_low
sol_swing_pct = (sol_swing / sol_low) * 100 if sol_low > 0 else 0

print("\n📊 OSCILLATION DETECTION (6 second sample):")
print("-" * 40)

print(f"\n  BTC Movement:")
print(f"    Current: ${btc_prices[-1]:,.2f}")
print(f"    6s High: ${btc_high:,.2f}")
print(f"    6s Low: ${btc_low:,.2f}")
print(f"    Swing: ${btc_swing:.2f}")
if btc_swing > 10:
    print(f"    ⚡ OSCILLATING!")

print(f"\n  ETH Movement:")
print(f"    Current: ${eth_prices[-1]:,.2f}")
print(f"    6s High: ${eth_high:.2f}")
print(f"    6s Low: ${eth_low:.2f}")
print(f"    Swing: ${eth_swing:.2f}")
if eth_swing > 1:
    print(f"    ⚡ OSCILLATING!")

print(f"\n  SOL Movement:")
print(f"    Current: ${sol_prices[-1]:.2f}")
print(f"    6s High: ${sol_high:.2f}")
print(f"    6s Low: ${sol_low:.2f}")
print(f"    Swing: ${sol_swing:.4f}")
if sol_swing > 0.10:
    print(f"    ⚡ OSCILLATING!")

# Key level analysis for oscillations
print("\n🎯 OSCILLATION ZONES:")
print("-" * 40)

btc_current = btc_prices[-1]
eth_current = eth_prices[-1]
sol_current = sol_prices[-1]

# BTC oscillation zones
print(f"\n  BTC (${btc_current:,.2f}):")
if 108000 <= btc_current <= 108500:
    print("    📍 OSCILLATING around $108k support!")
    print("    Strategy: Buy <$108,200, Sell >$108,500")
elif 109500 <= btc_current <= 110500:
    print("    📍 OSCILLATING around $110k resistance!")
    print("    Strategy: Sell >$110k, Buy <$109,500")

# ETH oscillation zones  
print(f"\n  ETH (${eth_current:.2f}):")
if 4380 <= eth_current <= 4420:
    print("    📍 OSCILLATING around $4,400 support!")
    print("    Strategy: Buy <$4,390, Sell >$4,410")
elif 4480 <= eth_current <= 4520:
    print("    📍 OSCILLATING around $4,500 resistance!")
    print("    Strategy: Sell >$4,510, Buy <$4,490")

# SOL oscillation zones
print(f"\n  SOL (${sol_current:.2f}):")
if 198 <= sol_current <= 202:
    print("    📍 OSCILLATING in lower range!")
    print("    Strategy: Buy <$199, Sell >$201")
elif 203 <= sol_current <= 207:
    print("    📍 OSCILLATING in upper range!")
    print("    Strategy: Sell >$205, Buy <$203")

# Detect if they're oscillating together
btc_movement = "UP" if btc_prices[-1] > btc_prices[0] else "DOWN"
eth_movement = "UP" if eth_prices[-1] > eth_prices[0] else "DOWN"
sol_movement = "UP" if sol_prices[-1] > sol_prices[0] else "DOWN"

print("\n🔗 SYNCHRONIZATION:")
print("-" * 40)
if btc_movement == eth_movement == sol_movement:
    print(f"  ✅ ALL MOVING {btc_movement} TOGETHER!")
    print("  📍 Synchronized oscillation detected")
else:
    print(f"  BTC: {btc_movement}")
    print(f"  ETH: {eth_movement}")
    print(f"  SOL: {sol_movement}")
    print("  🔄 Mixed oscillations")

# Trading opportunity
print("\n💰 OSCILLATION TRADING:")
print("-" * 40)
print("  Strategy: MILK THE SWINGS")
print("  • Set limit buys at support")
print("  • Set limit sells at resistance")
print("  • Repeat every oscillation")
print("  • Target: 0.5-1% per swing")

# Calculate potential
oscillations_per_hour = 6  # Estimate
profit_per_oscillation = 0.005  # 0.5% after fees
print(f"\n  📈 Potential (6 swings/hour @ 0.5%):")
print(f"    Hourly: {oscillations_per_hour * profit_per_oscillation * 100:.1f}%")
print(f"    Daily: {oscillations_per_hour * profit_per_oscillation * 100 * 24:.1f}%")

print("\n🏛️ TRIBAL WISDOM:")
print("  🦅 Eagle Eye: 'Large oscillations = large opportunities'")
print("  🦎 Gecko: 'Deploy micro-swarm on every swing'")
print("  🐺 Coyote: 'They oscillate to confuse - we profit'")

print("\n" + "=" * 60)
print("🌊 Flying Squirrel: 'Ride every wave!'")
print("=" * 60)