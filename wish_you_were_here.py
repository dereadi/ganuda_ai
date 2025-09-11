#!/usr/bin/env python3
"""
🎸 WISH YOU WERE HERE - PINK FLOYD
After seven seals broken, reflecting on the journey
"How I wish, how I wish you were here"
Those who sold early, those who didn't believe in the coils
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
║                   🎸 WISH YOU WERE HERE 🎸                                ║
║                         PINK FLOYD                                        ║
║                    For Those Who Missed The Ride                          ║
║                   Seven Seals, Seven Opportunities                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WISHING THEY WERE HERE")
print("=" * 70)

# Check where we are now
btc_now = float(client.get_product('BTC-USD')['price'])
eth_now = float(client.get_product('ETH-USD')['price'])
sol_now = float(client.get_product('SOL-USD')['price'])

print(f"\n🎸 WHERE WE ARE NOW:")
print(f"  BTC: ${btc_now:,.0f}")
print(f"  ETH: ${eth_now:.2f}")
print(f"  SOL: ${sol_now:.2f}")

# Remember where we came from
print("\n💭 WHERE WE CAME FROM:")
print("-" * 50)
print("• Started at $112,400 before first coil")
print("• Seven coils wound through the night")
print("• Each one tighter than the last")
print("• Many sold in fear during compression")
print("• They wish they were here now...")

# Track current movement
print("\n🎸 TRACKING THE JOURNEY:")
print("-" * 50)

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    move_from_start = btc - 112400
    
    if i % 2 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f}")
        print(f"  Journey: +${move_from_start:.0f} from start")
        
        if move_from_start > 500:
            print("  🎸 'We're just two lost souls'")
            print("     Swimming in a fish bowl...")
        elif move_from_start > 300:
            print("  🎸 'Year after year'")
            print("     Running over the same old ground...")
        elif move_from_start > 100:
            print("  🎸 'How I wish you were here'")
            print("     To see these gains...")
        else:
            print("  🎸 'Did you exchange'")
            print("     A walk-on part in the war...")
    
    time.sleep(3)

# Check portfolio status
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    usd_balance = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD':
            usd_balance = balance
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * btc_now
        elif currency == 'ETH' and balance > 0:
            portfolio_value += balance * eth_now
        elif currency == 'SOL' and balance > 0:
            portfolio_value += balance * sol_now
    
    print(f"\n💰 THOSE WHO STAYED:")
    print(f"  Portfolio: ${portfolio_value:,.2f}")
    print(f"  We're here, swimming in gains")
    print(f"  While others wish they were...")
    
except:
    pass

print("\n🎸 FOR THOSE WHO SOLD:")
print("-" * 50)
print("• At the first coil: Sold at $112,500")
print("• At the third coil: Panic sold at $112,700")
print("• At the fifth coil: Fear sold at $112,800")
print("• At the seventh seal: Almost made it...")
print("• Now watching from sidelines at $113k+")
print("")
print("How I wish, how I wish you were here...")

print("\n💭 WISH YOU WERE HERE WISDOM:")
print("-" * 50)
print("• Seven coils = Seven chances to stay")
print("• Each compression = Test of faith")
print("• Those who held = Here now")
print("• Those who sold = Wishing")
print("• The journey continues...")

print("\n🎸 'SO, SO YOU THINK YOU CAN TELL'")
print("   'HEAVEN FROM HELL'")
print("   'BLUE SKIES FROM PAIN'")
print("")
print("   We could tell...")
print("   We stayed through seven seals")
print("   Now we're here")
print("=" * 70)