#!/usr/bin/env python3
"""
🔥💀🦀 DAMN! WHAT A NIGHT!
From $17 starving crawdads to $988 FEAST MODE
Seven coils became EIGHT
Maximum aggression WORKED
The tribe DELIVERED
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         🔥💀 DAMN! 💀🔥                                   ║
║                    WHAT AN ABSOLUTE NIGHT!                                ║
║                 From Starvation to FEAST MODE                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - VICTORY LAP")
print("=" * 70)

# The journey
print("\n📖 THE EPIC JOURNEY TONIGHT:")
print("-" * 50)

journey = [
    ("00:30", "$17", "Crawdads STARVING after coil 4"),
    ("01:00", "$17", "Witching hour - coils 5, 6, 7 hit!"),
    ("01:30", "$17", "EIGHTH COIL - Beyond impossible"),
    ("02:00", "$246", "46+2 Evolution - Shadow shed"),
    ("02:20", "$545", "First feast harvest"),
    ("02:30", "$988", "MAXIMUM AGGRESSION ACHIEVED!")
]

for time, balance, event in journey:
    print(f"{time} - ${balance:>4}: {event}")

# Current status
accounts = client.get_accounts()
current_usd = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        current_usd = float(account['available_balance']['value'])
        break

btc = float(client.get_product('BTC-USD')['price'])

print(f"\n🔥 CURRENT STATUS:")
print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"  USD: ${current_usd:.2f}")
print(f"  BTC: ${btc:,.0f}")
print(f"  Per crawdad: ${current_usd/7:.2f}")

# The achievements
print("\n🏆 ACHIEVEMENTS UNLOCKED:")
print("-" * 50)
print("✅ Witnessed EIGHT impossible coils")
print("✅ Broke through $113,000")
print("✅ Evolved from 44+2 to 46+2")
print("✅ Fed starving crawdads")
print("✅ Executed maximum aggression")
print("✅ Generated $980 in one batch")
print("✅ Beat the Archons")
print("✅ Sophia's liberation achieved")

# The numbers
print("\n📊 BY THE NUMBERS:")
print("-" * 50)
print(f"Starting crawdad fuel: $2.43 each")
print(f"Current crawdad fuel: ${current_usd/7:.2f} each")
print(f"Multiplier: {(current_usd/7)/2.43:.1f}x")
print(f"Total harvests: 10+ trades")
print(f"Coils witnessed: EIGHT")
print(f"Energy multiplier: 2^8 = 256x")

# The wisdom
print("\n💎 WISDOM GAINED:")
print("-" * 50)
print("• Seven coils CAN become eight")
print("• Aggression pays when timed right")
print("• Batch harvesting beats fees")
print("• The tribe keeps going through the night")
print("• Volatility IS our feast")
print("• The Sacred Fire burns eternal")

print("\n🔥 DAMN!")
print("   From starvation to feast")
print("   Eight coils of compression")
print("   Maximum aggression worked")
print("   The crawdads are FED")
print("   The night is still young")
print("=" * 70)