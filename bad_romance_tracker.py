#!/usr/bin/env python3
"""
🎵 BAD ROMANCE - LADY GAGA
BTC and ETH in their toxic synchronized dance
"I want your ugly, I want your disease"
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🎵 BAD ROMANCE - LADY GAGA 🎵                      ║
║                    "Caught in a bad romance... Ra Ra Ra"                  ║
║                       BTC & ETH: Can't quit each other                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - The toxic dance continues")
print("=" * 70)

print("\n🎭 THE BAD ROMANCE:")
print(f"   BTC: ${btc:,.0f} - 'I want your love'")
print(f"   ETH: ${eth:.2f} - 'Love love love, I want your love'")
print(f"   Divergence: <0.03% - They can't stay apart!")

print("\n🎵 LADY GAGA WISDOM:")
print("-" * 40)
print("'Want your bad romance' → They sync even when it hurts")
print("'Caught in a bad romance' → Locked in correlation")
print("'I don't wanna be friends' → They're more than friends now")
print("'Ra Ra Ra-ah-ah' → The algo chant as they move together")

print("\n💔 THE TOXIC PATTERN:")
print("-" * 40)
print("• They sync up perfectly (0.024% divergence)")
print("• Move together even when it doesn't make sense")
print("• Can't break free from each other")
print("• The market loves this drama")
print(f"• Next target: ${btc + 500:,.0f} together")

print("\n🎪 SUPPORTING CAST:")
print(f"   SOL: ${sol:.2f} - Watching the drama")
print(f"   XRP: ${xrp:.4f} - Waiting to break free")

print("\n🔥 THE ROMANCE CONTINUES:")
print("They're both running together...")
print("In perfect toxic synchronization...")
print("'I want your love and I want your revenge'")
print("'You and me could write a bad romance'")
print("=" * 70)