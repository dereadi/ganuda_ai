#!/usr/bin/env python3
"""
🎸⚡ SCHISM - TOOL REFERENCE DETECTED! ⚡🎸
"I know the pieces fit..."
The ninth coil is breaking apart
Creating the schism before the reunion
"""

import json
import time as time_module
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🎸 SCHISM - THE PIECES FIT 🎸                      ║
║                     "I know the pieces fit 'cause I                       ║
║                      watched them fall away" - Tool                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SCHISM DETECTED")
print("=" * 70)

# Get current market
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🎸 THE SCHISM:")
print("-" * 50)
print("I know the pieces fit 'cause I watched them fall away")
print("Mildewed and smoldering, fundamental differing")
print("Pure intention juxtaposed will set two lovers souls in motion")
print("Disintegrating as it goes testing our communication")

print(f"\nMarket reading the schism:")
print(f"  BTC: ${btc:,.0f} - The temple")
print(f"  ETH: ${eth:,.2f} - The intention")
print(f"  SOL: ${sol:,.2f} - The motion")

# The pieces
print("\n🧩 THE PIECES:")
print("-" * 50)
pieces = [
    ("Coil 1-4", "Watched them fall away"),
    ("Coil 5-7", "Mildewed and smoldering"),
    ("Coil 8", "Pure intention juxtaposed"),
    ("COIL 9", "DISINTEGRATING AS IT GOES"),
    ("BREAKOUT", "REDISCOVER COMMUNICATION")
]

for piece, meaning in pieces:
    print(f"  {piece}: {meaning}")

# Track the schism
print("\n⚡ LIVE SCHISM TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    divergence = abs(btc_now - baseline)
    
    if divergence > 50:
        status = "🎸 THE PIECES FIT!"
    elif divergence > 20:
        status = "⚡ Testing our communication"
    elif divergence > 10:
        status = "🌀 Disintegrating as it goes"
    else:
        status = "💫 Cold silence has a tendency to atrophy any"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({btc_now - baseline:+.0f})")
    print(f"  {status}")
    
    if i == 4:
        print("\n  'Between supposed lovers...'")
    
    time_module.sleep(2)

# The revelation
print("\n" + "=" * 70)
print("🎸 SCHISM REVELATION:")
print("-" * 50)
print("The ninth coil creates the schism")
print("The market must break apart")
print("Before it can reunite higher")
print("")
print("'I know the pieces fit'")
print("BTC hitting $113,007 proved it")
print("The temple and the intention aligned")
print("The lovers (BTC/ETH) move together")
print("")
print("REDISCOVER COMMUNICATION AT $114K")
print("=" * 70)