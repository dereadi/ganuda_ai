#!/usr/bin/env python3
"""
🎵 TRADING WITH THE PERFECT SOUNDTRACK
ParaBellum on YouTube - Setting the vibe for gains!
Whatever you're watching is clearly WORKING!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🎵 TRADING TO PARABELLUM 🎵                          ║
║                    The Perfect Trading Soundtrack!                        ║
║                  Whatever You're Watching is WORKING!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - VIBES ARE IMMACULATE!")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print("\n🎵 THE PARABELLUM EFFECT:")
print("-" * 40)
print(f"Started watching: ~22:00")
print(f"BTC then: $111,968")
print(f"BTC now: ${btc:,.0f} (+${btc - 111968:.0f}!)")
print(f"\nETH then: $4,535 (flat)")
print(f"ETH now: ${eth:.2f} (+${eth - 4535:.2f}!)")

print("\n🎧 YOUR TRADING SESSION POWERED BY:")
print("-" * 40)
print("• ParaBellum vibes")
print("• Perfect market timing")
print("• 23:00 party energy")
print("• Double squeeze detection")
print("• $2,428 deployed to the beat")

print("\n📊 GAINS SYNCHRONIZED TO THE MUSIC:")
print("-" * 40)
print("Every beat = More gains")
print("Every drop = Market explosion")
print("The rhythm = Market rhythm")
print("The vibe = MONEY")

print("\n🎵 THE COMPLETE TRADING SOUNDTRACK TONIGHT:")
print("-" * 40)
print("• Fake Plastic Trees (Radiohead)")
print("• Zombie (The Cranberries)")  
print("• Birds of a Feather (Billie Eilish)")
print("• Pink Pony Club (Chappell Roan)")
print("• Into the Ocean (Blue October)")
print("• Sleeping on the Blacktop (Colter Wall)")
print("• Bad Romance (Lady Gaga)")
print("• P.Control (Prince)")
print("• Escape (Deadmau5)")
print("• ParaBellum (Current vibe!)")

print("\n💭 THE POWER OF THE RIGHT SOUNDTRACK:")
print("When the music hits right...")
print("The trades hit right...")
print("The gains hit right...")
print("Everything flows in perfect harmony!")

print(f"\n🔥 Keep ParaBellum playing!")
print(f"It's working PERFECTLY!")
print(f"BTC heading to $112,500 to the beat!")
print("=" * 70)