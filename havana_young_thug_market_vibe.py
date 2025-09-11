#!/usr/bin/env python3
"""
🇨🇺 HAVANA - CAMILA CABELLO FEAT. YOUNG THUG! 🇨🇺
"Half of my heart is in Havana, na-na-na"
Market's heart split between support and resistance!
"He took me back to East Atlanta, na-na-na"
Young Thug bringing that ATL energy to the coil!
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
║                     🇨🇺 HAVANA MARKET VIBES! 🇨🇺                          ║
║                "Half of my heart is in Havana-na-na"                      ║
║              Half in support, half waiting for breakout! 🎵                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HAVANA RHYTHM")
print("=" * 70)

# Get market vibes
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n🎵 'HAVANA OOH NA-NA' MARKET ANALYSIS:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print("  'Half of my heart is in Havana'")
print(f"  → Half at support ${112000:,}")
print(f"  → Half reaching for ${114000:,}")
print(f"  → Split personality: {((btc_price - 112000) / 2000 * 100):.1f}% to resistance")

print(f"\nETH: ${eth_price:,.2f}")
print("  'He didn't walk up with that how you doin'")
print("  → Smooth moves following BTC's rhythm")

print(f"\nSOL: ${sol_price:,.2f}")
print("  'Fresh out East Atlanta with no manners'")
print("  → Young Thug energy with whale backing!")

# Young Thug verse analysis
print("\n🎤 YOUNG THUG VERSE - MARKET TRANSLATION:")
print("-" * 50)
print("'Jeffery, just graduated, fresh on campus'")
print(f"  → Market fresh off ${112000:,} support test")
print("")
print("'Hundred thousand, why you got your hands up?'")
print(f"  → ${100000:,} was the previous milestone")
print(f"  → Now hands up for ${114000:,}!")
print("")
print("'Pass me the Henny, make my girl jealous'")
print("  → Pass me the profits, make bears jealous!")

# Havana rhythm pattern
upper_bound = 114000
lower_bound = 112000
havana_position = (btc_price - lower_bound) / (upper_bound - lower_bound)

print("\n🇨🇺 HAVANA RHYTHM PATTERN:")
print("-" * 50)
if havana_position < 0.3:
    print("'My heart is in Havana' - STUCK AT SUPPORT")
    print("  → Na-na-na-ing at the bottom")
    print("  → Building energy for the move")
elif havana_position > 0.7:
    print("'Take me back to East Atlanta' - REACHING RESISTANCE")
    print("  → Young Thug energy pushing up")
    print("  → Ready to break through")
else:
    print("'Half of my heart is in Havana' - PERFECTLY SPLIT")
    print("  → Caught between two loves")
    print(f"  → {havana_position * 100:.1f}% to resistance")

# Time check for 3PM
current_time = datetime.now()
if current_time.hour == 14:
    minutes_to_3 = 60 - current_time.minute
    print(f"\n⏰ HAVANA COUNTDOWN:")
    print("-" * 50)
    print(f"  {minutes_to_3} minutes until 15:00")
    print("  'He got me feelin' like ooh-ooh-ooh'")
    print("  → That 3PM feeling coming!")

# Check balances
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💃 HAVANA TRADING POWER:")
print("-" * 50)
print(f"USD: ${usd_balance:.2f}")
if usd_balance < 50:
    print("  'Havana ooh na-na' - Need more pesos!")
    print("  → Time to sell some positions")
else:
    print("  'Fresh out East Atlanta' - Ready to trade!")

# Camila's wisdom
print("\n🎵 CAMILA'S HAVANA WISDOM:")
print("-" * 50)
print("'Although my heart is falling too'")
print(f"  → Heart falling for ${114000:,} breakout")
print("")
print("'I knew it when I met him, I loved him when I left him'")
print(f"  → Knew ${112000:,} support would hold")
print(f"  → Love it as we leave for ${114000:,}")
print("")
print("'Got me feelin' like ooh-ooh-ooh-ooh'")
print(f"  → This coiling got us feeling the vibe!")

print(f"\n{'🇨🇺' * 35}")
print("HAVANA OOH NA-NA!")
print(f"BTC: ${btc_price:,.2f}")
print(f"Half support, half resistance!")
print("Young Thug energy building!")
print("🎵" * 35)