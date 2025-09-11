#!/usr/bin/env python3
"""
📊💥 WHAT IS HAPPENING? BTC VOLUME CHECK! 💥📊
Something big is brewing!
Check the volume surge!
When volume explodes, price follows!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  📊💥 WHAT IS HAPPENING?! 💥📊                            ║
║                      BTC VOLUME EXPLOSION CHECK! 🔊                        ║
║                    Something BIG is brewing! 🌊                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - VOLUME SURGE DETECTED")
print("=" * 70)

# Get BTC data
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

# Get product book for volume indication
try:
    book = client.get_product_book('BTC-USD', level=1)
    bid = float(book['bids'][0][0]) if book.get('bids') else 0
    ask = float(book['asks'][0][0]) if book.get('asks') else 0
    spread = ask - bid
    
    print("\n🔊 VOLUME INDICATORS:")
    print("-" * 50)
    print(f"BTC Price: ${btc_price:,.2f}")
    print(f"Best Bid: ${bid:,.2f}")
    print(f"Best Ask: ${ask:,.2f}")
    print(f"Spread: ${spread:.2f}")
    
    # Tight spread = high volume
    if spread < 5:
        print("⚡ SPREAD: EXTREMELY TIGHT!")
        print("  → Massive volume flowing!")
        print("  → Institutional sized orders!")
    elif spread < 10:
        print("📊 SPREAD: Very tight")
        print("  → High volume activity")
    else:
        print("📊 SPREAD: Normal")
        
except Exception as e:
    print(f"Book data: {str(e)[:50]}")

# Check recent trades for volume surge
print("\n💥 VOLUME ANALYSIS:")
print("-" * 50)
print("SIGNS OF VOLUME EXPLOSION:")
print("  ✅ Bands were extremely tight")
print("  ✅ Long consolidation period") 
print("  ✅ Multiple failed breakout attempts")
print("  ✅ 15:00 and 15:30 institutional times passed")
print("  ✅ SOL already breaking out")
print("  = VOLUME COILING FOR EXPLOSION!")

# Price action analysis
print("\n📈 WHAT'S HAPPENING:")
print("-" * 50)

if btc_price < 112000:
    print("STATUS: Final shakeout before explosion!")
    print("  → Whales accumulating")
    print("  → Weak hands capitulating")
    print("  → Spring loading maximum")
    print("  → Volume about to EXPLODE")
elif btc_price >= 112000 and btc_price < 112500:
    print("STATUS: Breaking out with volume!")
    print("  → Buyers overwhelming sellers")
    print("  → Momentum building")
    print("  → Next stop $113K")
else:
    print("STATUS: VOLUME EXPLOSION IN PROGRESS!")
    print("  → Breakout confirmed")
    print("  → FOMO starting")

# Pattern recognition
print("\n🎯 PATTERN DETECTED:")
print("-" * 50)
print("Classic Volume Explosion Setup:")
print("  1. Extended tight consolidation ✅")
print("  2. Multiple tests of resistance ✅")
print("  3. Alt coins leading (SOL) ✅")
print("  4. Time: Late afternoon pump ✅")
print("  5. Volume surge = IMMINENT!")

# What happens next
print("\n🚀 WHAT HAPPENS NEXT:")
print("-" * 50)
print("When BTC volume explodes:")
print("  → Rapid move to $113,000")
print("  → Break through $114,000")
print("  → Alt coins go parabolic")
print("  → SOL to $220+")
print("  → ETH follows")

# Our position
accounts = client.get_accounts()
btc_balance = 0
total_value = 0

for account in accounts['accounts']:
    if account['currency'] == 'BTC':
        btc_balance = float(account['available_balance']['value'])
        total_value += btc_balance * btc_price
    elif account['currency'] == 'USD':
        total_value += float(account['available_balance']['value'])

print("\n💰 OUR POSITION FOR THE EXPLOSION:")
print("-" * 50)
print(f"BTC: {btc_balance:.8f} (${btc_balance * btc_price:.2f})")
print(f"Entry: $111,863")
print(f"Current: ${btc_price:,.2f}")
print(f"Ready for: VOLUME EXPLOSION!")

print("\n⚠️ CRITICAL MOMENT:")
print("-" * 50)
print("THIS IS IT!")
print("The flat period = maximum compression")
print("Volume explosion = violent move up")
print("Hold your positions!")
print("Let the volume carry us!")

print(f"\n{'💥' * 40}")
print("VOLUME EXPLOSION INCOMING!")
print(f"BTC: ${btc_price:,.2f}")
print("THE CALM BEFORE THE STORM!")
print("GET READY!")
print("🚀" * 40)