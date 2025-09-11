#!/usr/bin/env python3
"""
🏛️ THE RISE AND FALL OF BABYLON
As you watch empires rise and fall...
BTC rises to empire status at $112,300!
The perfect trading documentary!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🏛️ BABYLON RISES, BTC RISES 🏛️                       ║
║            Watching Ancient Empires While Building New Ones               ║
║                  From Hammurabi to $112,500 BTC                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EMPIRE BUILDING!")
print("=" * 70)

# Get current empire status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print("\n🏛️ THE CRYPTO BABYLON:")
print("-" * 40)
print(f"BTC: ${btc:,.0f} - The New Empire Rising")
print(f"ETH: ${eth:.2f} - The Hanging Gardens of DeFi")
print(f"SOL: ${sol:.2f} - The Processional Way")
print(f"XRP: ${xrp:.4f} - The Ishtar Gate ($3.00)")

print("\n📜 PARALLELS TO BABYLON:")
print("-" * 40)
print("• Babylon rose from small outpost → BTC from $0")
print("• Hammurabi's Code → Bitcoin's immutable code")
print("• Tower of Babel → BTC reaching for heaven")
print("• Neo-Babylonian Empire → The crypto empire")
print("• Nebuchadnezzar's conquests → BTC conquering $112k")

print("\n🎬 DOCUMENTARY TIMESTAMPS vs BTC:")
print("-" * 40)
print("0:00 Origins → BTC at $111,968 (22:00)")
print("2:56 Rise of Kingdom → First breakout (22:30)")
print("5:28 Social organization → Crawdad hierarchy")
print("7:35 Hammurabi's Code → Trading rules established")
print("11:15 Decline → The flatness period")
print("20:55 Neo-Babylonian Empire → 23:00 PARTY!")
print(f"NOW: Empire at peak → BTC ${btc:,.0f}!")

print("\n💭 THE BABYLON WISDOM:")
print("-" * 40)
print("As Babylon rose to control ancient trade routes...")
print("BTC rises to control digital value transfer...")
print("As Babylon fell to Persian conquest...")
print("Traditional finance falls to crypto conquest...")

print("\n🏛️ YOUR EMPIRE STATUS:")
accounts = client.get_accounts()['accounts']
total = 0
for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        currency = acc['currency']
        if currency == 'BTC':
            empire_value = bal * btc
            total += empire_value
            print(f"BTC Empire: ${empire_value:,.2f}")
        elif currency == 'ETH':
            gardens_value = bal * eth
            total += gardens_value
            print(f"ETH Gardens: ${gardens_value:.2f}")
        elif currency == 'SOL':
            processional_value = bal * sol
            total += processional_value
            print(f"SOL Processional: ${processional_value:,.2f}")

print(f"\n👑 TOTAL EMPIRE: ${total:,.2f}")

print("\n🔥 THE PROPHECY:")
print("As you watch Babylon's 2000-year story...")
print("BTC writes its own empire story in real-time...")
print("From the Tower of Babel to BTC $112,500...")
print("History doesn't repeat, but it rhymes!")

print("\n📺 Keep watching - the energy is PERFECT!")
print("Babylon documentary + BTC breakout = DESTINY!")
print("=" * 70)