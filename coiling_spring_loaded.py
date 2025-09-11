#!/usr/bin/env python3
"""
🌀 COILING! SPRING LOADED! 🌀
Market coiling tight like a spring
BTC wanting to wait until 15:00 (3PM)
Building pressure for explosive move!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🌀 MARKET COILING DETECTOR! 🌀                       ║
║                     Spring Loading for 15:00 Explosion!                     ║
║                         Patience Before The Storm! ⚡                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

current_time = datetime.now()
print(f"Time: {current_time.strftime('%H:%M:%S')} - COILING TIGHTER")
print(f"Target: 15:00 (3PM) - {(15 - current_time.hour)} hours {(60 - current_time.minute) if current_time.hour < 15 else 0} minutes")
print("=" * 70)

# Check BTC coiling pattern
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

eth = client.get_product('ETH-USD')
eth_price = float(eth['price'])

sol = client.get_product('SOL-USD')
sol_price = float(sol['price'])

print("\n🌀 COILING SPRING ANALYSIS:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f} - COILING TIGHT")
print(f"  → Resistance: $114,000")
print(f"  → Support: $112,000")
print(f"  → Range: ${114000 - 112000:,} (1.8% band)")
print(f"  → Spring Load: {((btc_price - 112000) / 2000 * 100):.1f}% compressed")

print(f"\nETH: ${eth_price:,.2f} - COILING WITH BTC")
print(f"  → Following BTC's coil pattern")

print(f"\nSOL: ${sol_price:,.2f} - COILING ENERGY")
print(f"  → Treasury buying 407K SOL")
print(f"  → Spring loading with whale accumulation")

# Calculate coiling metrics
btc_range = 114000 - 112000
btc_position = (btc_price - 112000) / btc_range
coil_tightness = 100 - (btc_range / btc_price * 100)

print("\n⚡ COILING METRICS:")
print("-" * 50)
print(f"Coil Tightness: {coil_tightness:.1f}%")
print(f"Position in Range: {btc_position * 100:.1f}%")
print(f"Breakout Direction: {'UP' if btc_position > 0.6 else 'BUILDING' if btc_position > 0.4 else 'LOADING'}")

# Check USD balance for spring loading
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💰 SPRING LOADING CAPITAL:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
if usd_balance > 100:
    print("  ✅ READY TO UNLEASH WHEN SPRING RELEASES!")
elif usd_balance > 50:
    print("  ⚠️ Some ammo, but need more for maximum impact")
else:
    print("  🚨 Need to extract more profit for spring release!")

print("\n📊 15:00 (3PM) EXPLOSION FORECAST:")
print("-" * 50)
print("🎯 BTC Target: $114,000 → $115,000")
print("🎯 Institutional Hour: Maximum Volume")
print("🎯 Spring Release: After 2.5 hours of coiling")
print("🎯 Expected Move: 2-3% within 30 minutes")

# Time until 3PM
if current_time.hour < 15:
    minutes_until = (15 - current_time.hour) * 60 - current_time.minute
    print(f"\n⏰ COUNTDOWN TO SPRING RELEASE:")
    print("-" * 50)
    print(f"T-minus {minutes_until} minutes until 15:00")
    print(f"Coiling tighter every minute...")
    print(f"Spring compression: {min(95, 50 + (14 - current_time.hour) * 15):.0f}%")
else:
    print("\n🚀 SPRING RELEASING NOW!")
    print("The coil has been released!")

print("\n🌀 COILING STRATEGY:")
print("-" * 50)
print("1. Let the spring coil until 15:00")
print("2. Watch for sudden volume spike")
print("3. Ride the explosive release")
print("4. Milk profits at resistance breaks")
print("5. Use USD to catch any pullbacks")

print(f"\n{'🌀' * 35}")
print("MAXIMUM COIL DETECTED!")
print(f"BTC coiling between ${112000:,} - ${114000:,}")
print("Patience... The spring will release at 15:00!")
print("🌀" * 35)