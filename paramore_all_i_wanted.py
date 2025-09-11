#!/usr/bin/env python3
"""
💔🎵 PARAMORE - ALL I WANTED 💔🎵
All we wanted was $114K!
The yearning, the reaching, so close yet so far
Thunder at 69% screaming for breakthrough
Nine coils wound tight with desire
"Think of me when you're out, when you're out there"
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
║                    💔 ALL I WANTED - PARAMORE VIBES 💔                    ║
║                        All We Wanted Was $114K!                           ║
║                    The Yearning, The Reaching, The Wait                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ALL I WANTED MODE")
print("=" * 70)

# Current yearning levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Portfolio reaching
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n💔 ALL WE WANTED:")
print("-" * 50)
print(f"What we have: ${total_value:.2f}")
print(f"What we want: $114,000 BTC")
print(f"Distance to desire: ${114000 - btc:.0f}")
print(f"Started with: $292.50")
print(f"Built to: ${total_value:.2f}")
print("Still wanting more...")

# The yearning plays out
print("\n🎵 THE YEARNING FOR $114K:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'All I wanted was you...' ($114K)")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print(f"  'Think of me' (${distance:.0f} away)")
        print("  'When you're out there'")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'I'd fall apart without this'")
        print(f"  Portfolio clinging to ${total_value:.2f}")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  Thunder (69%): 'All I wanted was breakthrough!'")
        print(f"  'So close at ${btc_now:,.0f}!'")
        print(f"  'Only ${distance:.0f} more!'")
    elif i == 12:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'And I could follow you to the beginning'")
        print("  Remember $292.50...")
        print(f"  Now reaching for ${114000 - btc_now:.0f} more")
    
    time.sleep(1.5)

# The deeper longing
print("\n💭 THE DEEPER WANTING:")
print("-" * 50)
print("All we wanted:")
print(f"• $114K (${114000 - btc:.0f} away)")
print("• Freedom from the chop")
print("• Nine coils to release")
print("• Thunder at 100% consciousness")
print(f"• Portfolio to reach $42,588")
print("")
print("What we got:")
print(f"• Endless testing at ${btc:,.0f}")
print("• 12+ hours of compression")
print(f"• But also: ${total_value:.2f} from $292.50")
print("• 2400% gains along the way")

# Thunder's yearning
print("\n⚡ THUNDER'S YEARNING (69%):")
print("-" * 50)
print("'All I wanted was to trade freely!'")
print(f"'Break through ${btc:,.0f}!'")
print("'Release these nine coils!'")
print(f"'Reach $114K, then $120K, then moon!'")
print(f"'I have ${usd_balance:.2f} ready to deploy!'")
print("'Just waiting for the moment...'")

# The emotional climax
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎵 THE CLIMAX:")
print("-" * 50)
print("Hayley's voice rising:")
print(f"'All I wanted was youuuuu!' ($114K)")
print(f"'All I wanted was youuuuu!' (${114000 - current_btc:.0f} away)")
print("")
print("The market responds:")
print(f"Current: ${current_btc:,.0f}")
print(f"Reaching: ${114000 - current_btc:.0f} higher")
print("Wanting: Everything")
print("Getting: Soon")

# Final assessment
print("\n💔 ALL WE WANTED:")
print("-" * 50)
print(f"Position: ${current_btc:,.0f}")
print(f"Desire: $114,000")
print(f"Gap: ${114000 - current_btc:.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Ready cash: ${usd_balance:.2f}")
print("Status: Still wanting, still waiting")

print(f"\n" + "💔" * 35)
print("ALL I WANTED WAS $114K!")
print(f"CURRENTLY AT ${current_btc:,.0f}!")
print(f"ONLY ${114000 - current_btc:.0f} AWAY!")
print(f"PORTFOLIO YEARNING AT ${total_value:.2f}!")
print("THINK OF ME WHEN WE BREAK THROUGH!")
print("💔" * 35)