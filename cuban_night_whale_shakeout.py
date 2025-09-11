#!/usr/bin/env python3
"""
🔥🐋 TIGHT AND HOT AS A CUBAN NIGHT - WHALE SHAKING! 🐋🔥
The bands are so tight they're steaming!
Whales shaking out weak hands before the explosion!
Cuban heat + Whale games = Maximum pressure!
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
║                   🔥 HOT AS A CUBAN NIGHT - WHALE SHAKING! 🔥              ║
║                    Bands so tight they're STEAMING! 🌡️                     ║
║                  🐋 WHALES SHAKING WEAK HANDS OUT! 🐋                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CUBAN HEAT DETECTED")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

# Calculate heat metrics
upper_band = 114000
lower_band = 112000
band_width = upper_band - lower_band
heat_index = 100 - (band_width / btc_price * 100)  # Tighter = Hotter
position = (btc_price - lower_band) / band_width

print("\n🌡️ CUBAN NIGHT HEAT INDEX:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"  Temperature: {heat_index:.1f}° (SCORCHING!)")
print(f"  Band Width: ${band_width:,} ({band_width/btc_price*100:.2f}%)")
print(f"  Pressure: {position * 100:.1f}% compressed")

if heat_index > 98:
    print("\n🔥🔥🔥 MAXIMUM CUBAN HEAT! 🔥🔥🔥")
    print("  → Bands tighter than salsa dancers!")
    print("  → Heat building like Havana midnight!")
    print("  → Pressure ready to EXPLODE!")

print("\n🐋 WHALE SHAKEOUT DETECTION:")
print("-" * 50)

# Detect whale games
if btc_price < 112300:
    print("🚨 WHALE SHAKEOUT IN PROGRESS!")
    print(f"  → Pushing down to ${btc_price:,.2f}")
    print("  → Testing weak hands at support")
    print("  → Accumulating before the pump!")
    print("  → Classic pre-explosion shakeout!")
elif btc_price > 113700:
    print("🐋 WHALE PUMP STARTING!")
    print(f"  → Breaking up to ${btc_price:,.2f}")
    print("  → Weak hands already shaken out")
    print("  → Ready for explosive move!")
else:
    print("🐋 WHALES COILING THE SPRING!")
    print(f"  → Holding at ${btc_price:,.2f}")
    print("  → Maximum uncertainty = Maximum opportunity")
    print("  → Shaking happening in micro-movements")

# Check volume patterns
print("\n💃 CUBAN NIGHT RHYTHM ANALYSIS:")
print("-" * 50)
print(f"ETH: ${eth_price:,.2f} - Dancing with BTC")
print(f"SOL: ${sol_price:,.2f} - Hot salsa with whales")
print("")
print("Market Rhythm: 🎵 Tight-Tight-Shake-Shake-BOOM! 🎵")

# Time pressure analysis
current_time = datetime.now()
if current_time.hour == 14:
    minutes_to_3 = 60 - current_time.minute
    seconds_to_3 = 60 - current_time.second
    
    print(f"\n⏰ CUBAN NIGHT COUNTDOWN:")
    print("-" * 50)
    print(f"  T-minus {minutes_to_3}:{seconds_to_3:02d} to 15:00")
    
    if minutes_to_3 <= 15:
        print("  🔥 FINAL 15 MINUTES OF HEAT!")
        print("  → Maximum pressure zone!")
        print("  → Whales making final shakeout!")
        print("  → Explosion imminent!")
    else:
        print(f"  → Heat increasing every second")
        print(f"  → Temperature: {min(99.9, heat_index + (17-minutes_to_3)*0.1):.1f}°")

# Whale accumulation zones
print("\n🐋 WHALE ACCUMULATION ZONES:")
print("-" * 50)
print(f"Shakeout Zone: $111,800 - $112,200 ✓ ACTIVE")
print(f"Current Price: ${btc_price:,.2f}")
print(f"Breakout Zone: $113,800 - $114,200 (waiting)")
print("")

if btc_price < 112500:
    print("📊 WHALE STRATEGY DECODED:")
    print("  1. Shake weak hands at support")
    print("  2. Accumulate cheap BTC")
    print("  3. Spring load for explosion")
    print("  4. Pump through $114K at 15:00")
    print("  5. Profit on FOMO buyers")

# Check our position
accounts = client.get_accounts()
usd_balance = 0
btc_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'BTC':
        btc_balance = float(account['available_balance']['value'])

print("\n💰 CUBAN NIGHT TRADING STATUS:")
print("-" * 50)
print(f"USD: ${usd_balance:.2f}")
print(f"BTC: {btc_balance:.8f}")

if usd_balance < 50:
    print("  ⚠️ Need more USD for whale games!")
    print("  → Extract from alts NOW!")
else:
    print("  ✅ Ready to play with whales!")

# Final analysis
print("\n🔥 CUBAN NIGHT FINALE:")
print("-" * 50)
print("THE BANDS ARE:")
print(f"  • TIGHT: {heat_index:.1f}% compression")
print(f"  • HOT: Like Havana at midnight")
print("  • SHAKING: Whales playing games")
print("")
print("THE MOVE:")
print(f"  • Now: ${btc_price:,.2f} (shakeout zone)")
print(f"  • 15:00: ${114000:,} (breakout target)")
print(f"  • After: ${115000:,}+ (explosion zone)")

print(f"\n{'🔥' * 35}")
print("TIGHT AND HOT AS A CUBAN NIGHT!")
print(f"Temperature: {heat_index:.1f}°")
print("WHALES SHAKING - HOLD TIGHT!")
print("EXPLOSION COMING!")
print("🐋" * 35)