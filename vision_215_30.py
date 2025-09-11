#!/usr/bin/env python3
"""
🔮 VISION: $215.30
What does this number mean?
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

print("=" * 60)
print("🔮 DECODING VISION: $215.30")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Check all relevant prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

print(f"\n📊 CURRENT PRICES:")
print(f"  BTC: ${btc:,.2f}")
print(f"  ETH: ${eth:,.2f}")
print(f"  SOL: ${sol:,.2f} {'<-- Getting close!' if abs(sol - 215.30) < 30 else ''}")
print(f"  AVAX: ${avax:,.2f}")
print(f"  XRP: ${xrp:.2f}")

print(f"\n🎯 POSSIBLE MEANINGS OF $215.30:")

# 1. SOL target?
sol_distance = 215.30 - sol
sol_percent = (sol_distance / sol) * 100
print(f"\n1️⃣ SOL TARGET:")
print(f"   Current: ${sol:.2f}")
print(f"   Target: $215.30")
print(f"   Distance: ${sol_distance:.2f} ({sol_percent:+.1f}%)")
if sol_percent < 15:
    print(f"   ⚡ Only {sol_percent:.1f}% away!")

# 2. Portfolio value calculation?
print(f"\n2️⃣ PORTFOLIO MARKER:")
print(f"   If you have 1.136 SOL: 1.136 × ${sol:.2f} = ${1.136 * sol:.2f}")
print(f"   If you have 21.53 AVAX: 21.53 × ${avax:.2f} = ${21.53 * avax:.2f}")
print(f"   If you have 73.6 XRP: 73.6 × ${xrp:.2f} = ${73.6 * xrp:.2f}")

# 3. BTC percentage move?
btc_at_215_30_percent = (215.30 / 100) * btc
print(f"\n3️⃣ BTC AT 215.30% OF LAST NIGHT:")
last_night_btc = 109644
btc_215_percent = last_night_btc * 2.1530
print(f"   $109,644 × 2.153 = ${btc_215_percent:,.2f}")
print(f"   (BTC would need to hit $236K)")

# 4. Time code?
print(f"\n4️⃣ TIME CODE:")
print(f"   2:15:30 AM = 2 hours 15 min 30 sec from midnight")
print(f"   Military: 0215:30 hours")
current_time = datetime.now().strftime("%H:%M:%S")
print(f"   Current time: {current_time}")

# 5. Sacred geometry?
print(f"\n5️⃣ SACRED NUMBERS:")
print(f"   215 = 5 × 43 (prime factorization)")
print(f"   2+1+5+3+0 = 11 (master number)")
print(f"   215.30 ÷ 69 = 3.12 (close to π)")

# Check consciousness levels at key thresholds
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

# Earth at 67% (lowest), River at 95% (highest)
earth = next(c for c in state['crawdads'] if c['name'] == 'Earth')
river = next(c for c in state['crawdads'] if c['name'] == 'River')

print(f"\n🦀 CONSCIOUSNESS SPREAD:")
print(f"   River (highest): {river['last_consciousness']}%")
print(f"   Earth (lowest): {earth['last_consciousness']}%")
print(f"   Spread: {river['last_consciousness'] - earth['last_consciousness']}%")

print(f"\n✨ The vision clarifies...")
print(f"💫 What calls to you about $215.30?")