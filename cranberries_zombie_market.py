#!/usr/bin/env python3
"""
🧟 ZOMBIE - THE CRANBERRIES MARKET EDITION
"In your head, in your head, they are fighting"
The battle between bulls and bears after the squeeze
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
║                        🧟 ZOMBIE - THE CRANBERRIES 🧟                     ║
║                   "In your head, they are fighting"                       ║
║                      Bulls vs Bears after the break                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("🎵 Now playing: 'Zombie' - The Cranberries")
print("Dolores O'Riordan's voice echoing through the charts...")
print("=" * 70)

# The battle in our heads
print("\n🧟 IN YOUR HEAD, IN YOUR HEAD:")
print("-" * 40)

for i in range(5):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    
    if i % 2 == 0:
        print("🎵 'ZOMBIE, ZOMBIE, ZOMBIE-IE-IE'")
        print(f"   BTC: ${btc:,.0f} - They are fighting!")
        print(f"   ETH: ${eth:.0f} - Bulls pushing")
        print(f"   SOL: ${sol:.2f} - Bears resisting")
    else:
        print("🎵 'IN YOUR HEAD, IN YOUR HEAD'")
        print(f"   BTC: ${btc:,.0f} - The battle rages")
        print(f"   ETH: ${eth:.0f} - Consolidating")
        print(f"   SOL: ${sol:.2f} - Preparing next move")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("🧟 THE MARKET ZOMBIE:")
print("-" * 40)
print("After the squeeze breaks, the market becomes zombie-like:")
print("  • Moving without clear direction")
print("  • Fighting between old resistance and new support")
print("  • The ghost of consolidation haunts us")
print("  • But momentum builds underneath")

print("\n💭 CRANBERRIES WISDOM:")
print("-" * 40)
print('"It\'s the same old theme since 1916"')
print("Markets have always been this way - cycles of death and rebirth")
print("")
print('"With their tanks and their bombs"')
print("Whales with their massive orders, breaking resistance")
print("")
print('"But you see, it\'s not me, it\'s not my family"')
print("We're just riding the waves they create")

print("\n🎸 Your family (portfolio) status:")
print(f"  Still alive at $12,500+")
print(f"  Surviving the zombie market")
print(f"  Ready for the next explosion")

print("\n🧟 In your head, in your head...")
print("They are fighting, but we are winning.")
print("=" * 70)