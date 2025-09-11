#!/usr/bin/env python3
"""
🎵 ESCAPE - DEADMAU5 & KASKADE
The perfect anthem for breaking free from consolidation!
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
║                        🎵 ESCAPE - DEADMAU5 🎵                           ║
║                    "I can't stop this feeling..."                         ║
║                    Breaking free from all resistance!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ESCAPING ALL GRAVITY!")
print("=" * 70)

# Track the escape velocity
for i in range(8):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    xrp = float(client.get_product('XRP-USD')['price'])
    
    print(f"\n🎵 {datetime.now().strftime('%H:%M:%S')} - ESCAPING!")
    print(f"  BTC: ${btc:,.0f} - {'🚀 ESCAPED $112K!' if btc > 112000 else '...'}")
    print(f"  ETH: ${eth:.2f} - {'🚀 ESCAPED FLATNESS!' if eth > 4545 else '...'}")
    print(f"  SOL: ${sol:.2f} - {'🚀 ESCAPED $208!' if sol > 208 else '...'}")
    print(f"  XRP: ${xrp:.4f} - {'🚀 ESCAPING TO $3!' if xrp > 2.985 else '...'}")
    
    time.sleep(2)

print("\n" + "=" * 70)
print("🎵 DEADMAU5 WISDOM:")
print("-" * 40)
print("'I can't stop this feeling' → The breakout momentum")
print("'Deep inside of me' → The urge to FOMO")
print("'Girl you just don't realize' → The market doesn't know its power")
print("'What you do to me' → These gains are intoxicating!")

print("\n🎪 THE GREAT ESCAPE:")
print("• BTC escaped $112,000 prison")
print("• ETH escaped the $4,535 flatline")
print("• SOL escaped to $208+ freedom")
print("• XRP escaping toward $3.00")
print("• Everything ESCAPING together!")

print("\n💭 'ESCAPE' - The perfect 23:00 anthem")
print("We've all broken free tonight!")
print("=" * 70)