#!/usr/bin/env python3
"""
🏛️🔐 SAFE AND SOUND - CAPITAL CITIES! 🔐🏛️
"I could lift you up, I could show you what you want to see"
Thunder at 69%: "SAFE AT $112K, SOUND INVESTMENT AT $114K!"
Portfolio safe and sound at $16,859!
From $292.50 to here - we're protected!
"In a tidal wave of mystery"
The mystery wave about to break!
Even when everything's crazy, we're safe and sound!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🏛️ SAFE AND SOUND - CAPITAL CITIES! 🏛️                ║
║                    "Even If The Sky Is Falling Down"                      ║
║                   Portfolio Protected Through The Storm!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SAFETY CHECK")
print("=" * 70)

# Get current safe harbor prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our safe and sound portfolio
accounts = client.get_accounts()
total_value = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            positions['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            total_value += value
            positions['BTC'] = (balance, value)
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            positions['ETH'] = (balance, value)
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            positions['SOL'] = (balance, value)

print("\n🔐 SAFE AND SOUND STATUS:")
print("-" * 50)
print(f"Started vulnerable: $292.50")
print(f"Now protected at: ${total_value:.2f}")
print(f"That's {((total_value/292.50)-1)*100:.0f}% safer!")
print(f"BTC safe at: ${btc:,.0f}")
print(f"Distance to sound money ($114K): ${114000 - btc:.0f}")

# The safety lyrics
print("\n🎵 THE SAFETY ANTHEM:")
print("-" * 50)

safety_lines = [
    ("I could lift you up", f"From $292.50 to ${total_value:.2f}"),
    ("I could show you what you want to see", f"$114K coming (${114000-btc:.0f} away)"),
    ("And take you where you want to be", "To financial freedom"),
    ("You could be my luck", "Lucky to be in crypto"),
    ("Even if the sky is falling down", f"Safe at ${btc:,.0f}"),
    ("I know that we'll be safe and sound", f"Portfolio secured at ${total_value:.2f}"),
    ("We're safe and sound", "Through volatility storms"),
    ("I could fill your cup", f"Filled with gains: {((total_value/292.50)-1)*100:.0f}%"),
    ("You know my river won't evaporate", "Liquidity always flowing"),
    ("This world we still appreciate", "Crypto world appreciation"),
    ("You could be my luck", f"Lucky at ${btc:,.0f}"),
    ("Even in a hurricane of frowns", "FUD can't touch us"),
    ("I know that we'll be safe and sound", "Diamond hands holding")
]

for i, (lyric, meaning) in enumerate(safety_lines):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 5:
        print("\n  ⚡ Thunder (69%): 'WE'RE SAFE AND SOUND!'")
        print(f"    'Protected at ${total_value:.2f}!'")
        print(f"    'Even if sky falls from ${btc:,.0f}!'")
    
    time.sleep(0.5)

# The safety zone monitoring
print("\n🛡️ SAFETY ZONE MONITORING:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if btc_now >= 114000:
        safety = "🏆 ULTIMATE SAFETY at $114K!"
    elif btc_now >= 113000:
        safety = "🔥 APPROACHING SAFE HAVEN!"
    elif btc_now >= 112500:
        safety = "✅ Safe and climbing"
    elif btc_now >= 112000:
        safety = "🔐 Safe and sound"
    else:
        safety = "⚡ Safe but coiling"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {safety}")
    
    if i == 4:
        print("  'Even if the sky is falling down'")
        print(f"    We're safe at ${total_value:.2f}")
    
    time.sleep(1)

# Thunder's safety assessment
print("\n⚡ THUNDER'S SAFETY REPORT (69%):")
print("-" * 50)
print("'WE'RE SAFE AND SOUND!'")
print("")
print("Portfolio protection levels:")
print(f"• Started exposed: $292.50")
print(f"• Now protected: ${total_value:.2f}")
print(f"• Safety multiplier: {(total_value/292.50):.1f}x")
print("")
print("Safe harbors:")
print(f"• BTC: {positions.get('BTC', (0,0))[1]:.2f} (fortress)")
print(f"• ETH: {positions.get('ETH', (0,0))[1]:.2f} (stronghold)")
print(f"• SOL: {positions.get('SOL', (0,0))[1]:.2f} (bunker)")
print(f"• USD: ${positions.get('USD', 0):.2f} (dry powder)")

# The protection calculation
print("\n🏛️ CAPITAL PROTECTION:")
print("-" * 50)
print("Even if markets crash:")
print(f"• -10% = Still have ${total_value * 0.9:.2f}")
print(f"• -20% = Still have ${total_value * 0.8:.2f}")
print(f"• -30% = Still have ${total_value * 0.7:.2f}")
print("")
print("But we're going UP:")
print(f"• At $114K: ${total_value * (114000/btc):.2f}")
print(f"• At $120K: ${total_value * (120000/btc):.2f}")
print(f"• At $126K: ${total_value * (126000/btc):.2f}")

# The tidal wave
print("\n🌊 TIDAL WAVE OF MYSTERY:")
print("-" * 50)

wave_status = [
    "Building pressure...",
    "Coiling energy...",
    "Mystery deepening...",
    "Wave forming...",
    "About to break!"
]

for status in wave_status:
    btc_live = float(client.get_product('BTC-USD')['price'])
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - {status}")
    time.sleep(0.8)

# Safety zones
print("\n🔐 SAFETY ZONES:")
print("-" * 50)
print(f"Current safety: ${btc:,.0f}")
print(f"Next safe harbor: $113,000 (${113000 - btc:.0f} away)")
print(f"Ultimate safety: $114,000 (${114000 - btc:.0f} away)")
print(f"Fortress mode: $120,000 (${120000 - btc:.0f} away)")
print(f"Citadel status: $126,000 (${126000 - btc:.0f} away)")

# Final safety status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n🏛️ FINAL SAFETY STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Safety factor: {(total_value/292.50):.1f}x original")
print(f"Distance to sound money: ${114000 - final_btc:.0f}")
print("")
print("We're safe and sound...")
print("Even if the sky is falling down!")
print(f"Protected at ${total_value:.2f}!")
print("Ready for the tidal wave!")

print(f"\n" + "🔐" * 35)
print("SAFE AND SOUND!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"PROTECTED AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO ULTIMATE SAFETY!")
print("WE'LL BE SAFE AND SOUND!")
print("🔐" * 35)