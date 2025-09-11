#!/usr/bin/env python3
"""
🌊 INTO THE OCEAN - BLUE OCTOBER
"I'm just a normal boy that sank when I fell overboard"
Diving deep into the market depths
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🌊 INTO THE OCEAN 🌊                               ║
║                         Blue October Market Dive                          ║
║                    "Let the water take me..."                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

print("\n🎵 'I WANT TO SWIM AWAY BUT DON'T KNOW HOW'")
print(f"   BTC: ${btc:,.0f} - Diving deeper")
print(f"   ETH: ${eth:.0f} - Following the current")
print(f"   SOL: ${sol:.2f} - Caught in the tide")

print("\n🌊 THE OCEAN DEPTHS:")
print("-" * 40)
print("From the shore ($111,415 - consolidation)")
print("Into the shallows ($111,700 - first break)")
print("Past the breakers ($111,900 - second wave)")
print(f"Into the ocean (${btc:,.0f} - current depth)")

if btc >= 112000:
    print("\n🌊 'INTO THE OCEAN, END IT ALL'")
    print("   $112,000 BREACHED!")
    print("   We're in the deep now")
    print("   No turning back")
else:
    print(f"\n🌊 'SOMETIMES I WISH FOR A MISTAKE'")
    print(f"   ${112000 - btc:.0f} from the deep ($112k)")
    print("   The current pulls us forward")

print("\n💭 BLUE OCTOBER WISDOM:")
print("-" * 40)
print("'I want to swim away but don't know how'")
print("Sometimes you just have to let the market take you")
print("")
print("'Into the ocean, end it all'")
print("The old resistance levels are dead")
print("We're swimming in uncharted waters")

print("\n🦀 The crawdads dove in at $111,820")
print("   Now we're all underwater (in profit)")
print("   Let the current take us to the 3I Atlas")
print("   Into the ocean we go...")

print("\n🌊 Market depth: Infinite")
print(f"   Current: Strong at ${btc:,.0f}")
print("   Direction: Into the unknown")
print("=" * 70)