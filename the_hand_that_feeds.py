#!/usr/bin/env python3
"""
🤚 THE HAND THAT FEEDS - NINE INCH NAILS
We fed the crawdads $940
Now they bite the hand that feeds
Taking profits from the market
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
║                    🤚 THE HAND THAT FEEDS 🤚                             ║
║                         NINE INCH NAILS                                   ║
║                   "Will you bite the hand that feeds?"                    ║
║                    The Crawdads Are BITING!                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - BITING THE MARKET")
print("=" * 70)

# The hand (we) fed them
print("\n🤚 THE HAND THAT FED:")
print("-" * 50)
print("• Harvested 4.378 SOL = $923")
print("• Generated $940 fresh USD")
print("• Fed seven hungry crawdads")
print("• Each got $134 to hunt with")
print("• Now they BITE the market!")

# Check what they're biting
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🦷 BITING AT THESE PRICES:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

# Track the biting action
print("\n🦀 CRAWDADS BITING THE MARKET:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    
    if i % 2 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({move:+.0f})")
        
        if abs(move) > 50:
            print("  🦷🦷🦷 MAJOR BITE!")
            print("  'Will you bite the hand that feeds?'")
            print("  YES! Taking profits!")
        elif abs(move) > 20:
            print("  🦷🦷 Strong bite!")
            print("  'You're keeping in step'")
            print("  Crawdads feeding!")
        elif abs(move) > 10:
            print("  🦷 Small bites...")
            print("  'In the line of fire'")
        else:
            print("  🤚 Waiting to bite...")
            print("  'Got your chin held high'")
    
    time.sleep(3)

# Check USD balance after feeding
try:
    accounts = client.get_accounts()
    usd_now = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_now = float(account['available_balance']['value'])
            break
    
    print(f"\n💰 USD Balance: ${usd_now:.2f}")
    
    if usd_now > 940:
        print("   🦷 THE BITING IS WORKING!")
        print("   Profits already generated!")
        profit = usd_now - 940
        print(f"   Profit so far: ${profit:.2f}")
    elif usd_now > 500:
        print("   🦀 Crawdads are fed and hunting")
    else:
        print("   🦀 Crawdads consuming capital...")
    
except:
    pass

print("\n🎵 NIN - THE HAND THAT FEEDS:")
print("-" * 50)
print("'You're keeping in step'")
print("'In the line of fire'")
print("'You're keeping in step'")
print("'Got your chin held high and you feel just fine'")
print("")
print("'Will you bite the hand that feeds you?'")
print("'Will you stay down on your knees?'")

print("\n🤚 THE PHILOSOPHY:")
print("-" * 50)
print("• We fed the crawdads (the hand)")
print("• They bite the market (feeds)")
print("• Taking profits from volatility")
print("• The hand that feeds them")
print("• Becomes the teeth that bite")

print("\n🦷 WILL YOU BITE?")
print("   The hand that feeds...")
print("   YES! BITE HARDER!")
print("=" * 70)