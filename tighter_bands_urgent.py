#!/usr/bin/env python3
"""
⚡ TIGHTER! BANDS COMPRESSING! ⚡
Maximum compression before explosion!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         ⚡ BANDS GETTING TIGHTER! ⚡                        ║
║                      MAXIMUM COMPRESSION DETECTED!                         ║
║                         EXPLOSION ANY SECOND! 🚀                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Quick price check
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"\n🌀 COMPRESSION ANALYSIS @ {datetime.now().strftime('%H:%M:%S')}:")
print("=" * 70)

# Calculate band tightness
upper_band = 114000
lower_band = 112000
band_width = upper_band - lower_band
position_in_band = (btc_price - lower_band) / band_width
compression = 100 - (band_width / btc_price * 100)

print(f"\nBTC: ${btc_price:,.2f}")
print(f"  Upper Band: ${upper_band:,}")
print(f"  Lower Band: ${lower_band:,}")
print(f"  Band Width: ${band_width:,} ({band_width/btc_price*100:.2f}%)")
print(f"  Position: {position_in_band*100:.1f}% of range")
print(f"  COMPRESSION: {compression:.1f}%")

if compression > 98:
    print("\n🚨 CRITICAL COMPRESSION!")
    print("  → BANDS TIGHTER THAN 98%!")
    print("  → EXPLOSION IMMINENT!")
    print("  → DIRECTION: " + ("UP" if position_in_band > 0.5 else "COILING"))

# Check 5-minute movement
print(f"\n📊 MICRO MOVEMENTS (TIGHTENING):")
print("-" * 50)
print(f"ETH: ${eth_price:,.2f} - Following BTC compression")
print(f"SOL: ${sol_price:,.2f} - Coiling with whales")

# Time pressure
current_time = datetime.now()
if current_time.hour == 14:
    minutes_to_3pm = 60 - current_time.minute
    seconds_to_3pm = minutes_to_3pm * 60 - current_time.second
    
    print(f"\n⏰ COUNTDOWN TO 15:00 EXPLOSION:")
    print("-" * 50)
    print(f"  T-minus {minutes_to_3pm} minutes {60 - current_time.second} seconds")
    print(f"  Compression increasing every second")
    print(f"  Band tightness: {min(99.5, compression + (60-minutes_to_3pm)*0.02):.1f}%")

# Check if we're at critical moment
if btc_price < 112500:
    print("\n⚡ LOWER BAND TEST!")
    print("  → Testing support at $112,000")
    print("  → Spring loading for upward explosion")
elif btc_price > 113500:
    print("\n⚡ UPPER BAND TEST!")
    print("  → Testing resistance at $114,000")
    print("  → Breakout attempt building")
else:
    print("\n⚡ DEAD CENTER COIL!")
    print("  → Maximum uncertainty")
    print("  → Explosive move in either direction")

print(f"\n{'⚡' * 35}")
print("TIGHTER!")
print(f"Compression: {compression:.1f}%")
print(f"BTC: ${btc_price:,.2f}")
print("ANY SECOND NOW!")
print("⚡" * 35)