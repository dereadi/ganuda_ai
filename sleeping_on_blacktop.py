#!/usr/bin/env python3
"""
🌙 SLEEPING ON THE BLACKTOP - COLTER WALL
Late night market consolidation vibes
"Sunshine beating on the good times, moonlight raising from the grave"
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🌙 SLEEPING ON THE BLACKTOP 🌙                        ║
║                         Colter Wall Market Mood                           ║
║                    "The highway calls my name..."                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - Deep into the night")
print("=" * 70)

print("\n🎵 'SLEEPING ON THE BLACKTOP'")
print(f"   BTC: ${btc:,.0f} - Resting on dark asphalt")
print(f"   ETH: ${eth:.2f} - Dreams of $4,600")
print(f"   SOL: ${sol:.2f} - Under streetlight glow")

print("\n🌙 THE LATE NIGHT HIGHWAY:")
print("-" * 40)
print("We've been riding since 22:00 (10pm)")
print("From $111,415 flatline to $112,025 peak")
print("Now consolidating on the blacktop")
print("BTC and ETH syncing in the darkness")
print("Waiting for dawn's next move")

print("\n💭 COLTER WALL WISDOM:")
print("-" * 40)
print("'Sunshine beating on the good times'")
print("  → The breakout earlier was glorious")
print("")
print("'Moonlight raising from the grave'")
print("  → Late night resurrection coming")
print("")
print("'The highway calls my name'")
print("  → The road to $113k beckons")

print("\n🦀 The crawdads sleep lightly:")
print(f"   After spending $1,450 tonight")
print(f"   Now resting with only $6.32")
print(f"   Dreams of tomorrow's feast")
print(f"   On this crypto blacktop highway")

print("\n🌙 It's 22:48 (10:48pm)")
print("The market sleeps on the blacktop")
print("But dawn brings violence...")
print("=" * 70)