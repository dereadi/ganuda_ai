#!/usr/bin/env python3
"""
🎸⚡ ROCK AND ROLL - LED ZEPPELIN
"It's been a long time since I rock and rolled"
Seven coils wound, $112,900+ altitude achieved
Time to ROCK AND ROLL!
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
║                    🎸⚡ ROCK AND ROLL ⚡🎸                               ║
║                         LED ZEPPELIN                                      ║
║         "It's been a long time since I rock and rolled"                   ║
║                    SEVEN COILS → EXPLOSION                                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - TIME TO ROCK AND ROLL!")
print("=" * 70)

# Check if we're ready to rock
btc_start = float(client.get_product('BTC-USD')['price'])
print(f"\n🎸 Starting altitude: ${btc_start:,.0f}")

if btc_start > 112900:
    print("⚡ WE'RE ABOVE $112,900!")
    print("   IT'S TIME TO ROCK AND ROLL!")
elif btc_start > 112850:
    print("🎸 Building up to rock...")
else:
    print("📊 Still winding up...")

print("\n🎸 ROCK AND ROLL TRACKER:")
print("-" * 50)

# Track the rock and roll
rock_detected = False
max_move = 0

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    move = btc - btc_start
    
    if abs(move) > max_move:
        max_move = abs(move)
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f} ({move:+.0f})")
        
        if abs(move) < 10:
            print("  🎸 'It's been a long time...'")
            print("     Still coiled, building energy")
        elif abs(move) < 50:
            print("  🎸⚡ 'Since I rock and rolled!'")
            print("     Starting to move!")
        elif abs(move) < 100:
            print("  🎸⚡🎸 'IT'S BEEN A LONG LONELY TIME!'")
            print("     ROCKING NOW!")
            rock_detected = True
        else:
            print("  🎸⚡🎸⚡ 'ROCK AND ROLL!!!'")
            print("     FULL EXPLOSION MODE!")
            rock_detected = True
    
    time.sleep(2)

print("\n" + "=" * 70)
print("🎸 ROCK AND ROLL REPORT:")
print("-" * 50)

final_btc = float(client.get_product('BTC-USD')['price'])
total_move = final_btc - btc_start

print(f"Started: ${btc_start:,.0f}")
print(f"Current: ${final_btc:,.0f}")
print(f"Movement: ${total_move:+.0f}")
print(f"Max swing: ${max_move:.0f}")

if rock_detected or max_move > 50:
    print("\n🎸⚡ WE'RE ROCKING AND ROLLING!")
    print("The seven coils are releasing!")
    print("Led Zeppelin would be proud!")
elif max_move > 20:
    print("\n🎸 Starting to rock...")
    print("The rhythm is building...")
else:
    print("\n🎸 Still winding up...")
    print("The rock and roll is coming...")

# Check portfolio rock status
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD':
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * final_btc
        elif currency == 'ETH' and balance > 0:
            eth_price = float(client.get_product('ETH-USD')['price'])
            portfolio_value += balance * eth_price
        elif currency == 'SOL' and balance > 0:
            sol_price = float(client.get_product('SOL-USD')['price'])
            portfolio_value += balance * sol_price
    
    print(f"\n💰 Portfolio rocking at: ${portfolio_value:,.2f}")
    
except:
    pass

print("\n🎵 LED ZEPPELIN WISDOM:")
print("-" * 50)
print("'It's been a long time since I rock and rolled'")
print("'It's been a long time since I did the stroll'")
print("'Let me get back, let me get back'")
print("'Let me get back to rock and roll'")
print("")
print("Tonight we wound SEVEN COILS...")
print("Now it's time to ROCK AND ROLL!")

print("\n⚡ ROCK AND ROLL ENERGY:")
print("-" * 50)
print("• Seven coils = 128x energy")
print("• Upper tight coil at $112,900")
print("• When this rocks, it ROLLS")
print("• Target: The MOON ($115k+)")
print("• Then: VALHALLA ($120k+)")

print("\n🎸 'IT'S BEEN A LONG TIME'")
print("   'SINCE I ROCK AND ROLLED'")
print("   Tonight... WE ROCK!")
print("=" * 70)