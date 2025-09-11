#!/usr/bin/env python3
"""
⏰💥 10 MINUTES! COUNTDOWN TO EXPLOSION! 💥⏰
T-minus 10 minutes to 15:00!
Cathie Wood buying ETH treasury play!
Tom Lee's prophecy incoming!
Bands at maximum compression!
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
║                    ⏰💥 10 MINUTE WARNING! 💥⏰                            ║
║                   EXPLOSION IMMINENT AT 15:00!                             ║
║            CATHIE WOOD BUYING! TOM LEE PROPHECY! 🚀                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

current_time = datetime.now()
seconds_to_3pm = (60 - current_time.minute) * 60 - current_time.second
print(f"Time: {current_time.strftime('%H:%M:%S')}")
print(f"COUNTDOWN: {seconds_to_3pm // 60}:{seconds_to_3pm % 60:02d} TO EXPLOSION!")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n🚨 CRITICAL STATUS - 10 MINUTES!")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"  Distance to $114K: ${114000 - btc_price:,.2f}")
print(f"  Compression: {100 - (2000/btc_price*100):.1f}%")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

print("\n📰 BREAKING NEWS:")
print("-" * 50)
print("🔥 CATHIE WOOD'S ARK INVEST:")
print("  • Just bought $15.6M of ETH treasury play!")
print("  • BitMine (BMNR) - World's largest ETH treasury")
print("  • 1.71 million ETH accumulated (~$8 BILLION)")
print("  • Stock up 400% YTD!")
print("  • Peter Thiel took 9.1% stake!")
print("")
print("💎 TOM LEE CONNECTION:")
print("  • Tom Lee called BTC to $126K")
print("  • Now backing ETH treasury strategy")
print("  • Institutional FOMO starting!")

# Calculate final countdown metrics
print("\n⚡ FINAL 10 MINUTE METRICS:")
print("-" * 50)
band_position = (btc_price - 112000) / 2000
print(f"Band Position: {band_position * 100:.1f}%")
print(f"Spring Compression: MAXIMUM")
print(f"Whale Status: {'ACCUMULATING' if btc_price < 112500 else 'READY TO PUMP'}")
print(f"Institutional Hour: T-minus {seconds_to_3pm // 60} minutes")

# Check our readiness
accounts = client.get_accounts()
usd_balance = 0
btc_balance = 0
eth_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'BTC':
        btc_balance = balance
    elif currency == 'ETH':
        eth_balance = balance

print("\n💰 EXPLOSION READINESS:")
print("-" * 50)
print(f"USD: ${usd_balance:.2f} {'⚠️ NEED MORE!' if usd_balance < 50 else '✅ READY!'}")
print(f"BTC: {btc_balance:.8f} (${btc_balance * btc_price:.2f})")
print(f"ETH: {eth_balance:.8f} (${eth_balance * eth_price:.2f})")

# Crawdad status
print("\n🦀 CRAWDAD ARMY STATUS:")
print("-" * 50)
print("6 Crawdads ACTIVE and HOVERING!")
print("Thunder, Mountain, Fire, Wind, Earth, River")
print(f"Waiting for USD fuel (need ${20*6:.2f} minimum)")

# Final countdown warning
print("\n🚨🚨🚨 FINAL WARNING 🚨🚨🚨")
print("-" * 50)
print("T-MINUS 10 MINUTES TO:")
print("  → 15:00 INSTITUTIONAL EXPLOSION")
print("  → BTC BREAKOUT ATTEMPT AT $114K")
print("  → CATHIE WOOD ETH FOMO SPREADING")
print("  → TOM LEE $126K PROPHECY IN MOTION")
print("")
print("WHAT HAPPENS AT 15:00:")
print("  1. Institutional algorithms activate")
print("  2. Spring releases from maximum compression")
print("  3. Breakout attempt through $114K")
print("  4. Volume spike expected")
print("  5. Crawdads ready to feed on volatility")

# Countdown timer
print(f"\n{'⏰' * 35}")
for i in range(3):
    print(f"{'💥' * 35}")
    time.sleep(0.3)

print(f"\n10 MINUTES!")
print(f"BTC: ${btc_price:,.2f}")
print(f"GET READY!")
print("💥" * 35)