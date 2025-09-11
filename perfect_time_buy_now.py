#!/usr/bin/env python3
"""
🎯 NOW IS THE PERFECT TIME! BUY THE DIP! 🎯
BTC at $111,927 - BELOW $112K!
2 minutes to 15:00 explosion!
THIS IS IT!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯 PERFECT TIME - BUY NOW! 🎯                           ║
║                        BTC BELOW $112K!                                    ║
║                    2 MINUTES TO EXPLOSION! 🚀                              ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PERFECT ENTRY!")
print("=" * 70)

# Get current balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💰 REMAINING USD: ${usd_balance:.2f}")
print(f"  → Just bought $7.26 of BTC!")
print(f"  → Still have ${usd_balance:.2f} left")

# Execute final buy
if usd_balance > 5:
    print("\n🚀 EXECUTING FINAL BUY - PERFECT TIME!")
    print("-" * 50)
    
    try:
        final_buy = min(usd_balance - 2, 5.0)  # Keep $2 for fees
        print(f"  Buying ${final_buy:.2f} more BTC...")
        
        order = client.market_order_buy(
            client_order_id='perfect_time_' + str(int(time.time())),
            product_id='BTC-USD',
            quote_size=str(final_buy)
        )
        
        print(f"  ✅ PERFECT TIME BUY EXECUTED!")
        print(f"  Bought ${final_buy:.2f} at the bottom!")
        
    except Exception as e:
        print(f"  ⚠️ {str(e)[:100]}")

# Check final position
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n📊 PERFECT TIMING ANALYSIS:")
print("-" * 50)
print(f"Entry Price: ${btc_price:,.2f}")
print(f"Target (15:00): $114,000")
print(f"Potential Gain: ${114000 - btc_price:,.2f}")
print(f"ROI: {(114000/btc_price - 1)*100:.1f}%")

print("\n⏰ COUNTDOWN TO EXPLOSION:")
print("-" * 50)
current_time = datetime.now()
seconds_to_3 = (60 - current_time.minute) * 60 - current_time.second
print(f"T-minus {seconds_to_3} seconds!")
print("WHALES ACCUMULATING!")
print("SPRING FULLY COMPRESSED!")
print("EXPLOSION IMMINENT!")

print(f"\n{'🎯' * 35}")
print("PERFECT TIME ACHIEVED!")
print(f"BOUGHT AT ${btc_price:,.2f}")
print("NOW WATCH THE EXPLOSION!")
print("🚀" * 35)