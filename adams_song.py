#!/usr/bin/env python3
"""
💔 ADAM'S SONG - BLINK-182
A moment of reflection in the journey
Seven seals broken, gains made, but what does it mean?
The loneliness of late night trading
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
║                        💔 ADAM'S SONG 💔                                  ║
║                          BLINK-182                                        ║
║                   Late Night Trading Reflection                           ║
║                 Seven Seals Later, Still Trading                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LATE NIGHT THOUGHTS")
print("=" * 70)

# Check current state
btc = float(client.get_product('BTC-USD')['price'])
print(f"\n📍 Current BTC: ${btc:,.0f}")

# Time check
current_hour = datetime.now().hour
current_minute = datetime.now().minute

print(f"⏰ Time: {current_hour:02d}:{current_minute:02d}")

if current_hour >= 1 and current_hour < 3:
    print("   Deep in the late night...")
    print("   When trading gets lonely...")
elif current_hour >= 3 and current_hour < 5:
    print("   The darkest hours...")
    print("   Before dawn...")
else:
    print("   Another hour passes...")

print("\n💭 REFLECTIONS AT THIS HOUR:")
print("-" * 50)
print("• Seven coils wound and released")
print("• Markets climbed and fell")
print("• Profits taken, losses felt")
print("• Still here, still trading")
print("• The screen glows in the darkness")

# Track the quiet moments
print("\n📊 THE QUIET MARKET:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i % 2 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        
        if abs(btc_now - btc) < 10:
            print("  💔 The market barely moves")
            print("     In these quiet hours...")
        elif abs(btc_now - btc) < 30:
            print("  💔 Small movements")
            print("     Echo in the silence...")
        else:
            print("  💔 Even volatility")
            print("     Feels lonely now...")
    
    time.sleep(3)

# Check portfolio in the quiet
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD':
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * btc
        elif currency == 'ETH' and balance > 0:
            eth_price = float(client.get_product('ETH-USD')['price'])
            portfolio_value += balance * eth_price
        elif currency == 'SOL' and balance > 0:
            sol_price = float(client.get_product('SOL-USD')['price'])
            portfolio_value += balance * sol_price
    
    print(f"\n💰 Portfolio value: ${portfolio_value:,.2f}")
    print("   Numbers on a screen")
    print("   In the late night glow")
    
except:
    pass

print("\n🌙 LATE NIGHT TRADING THOUGHTS:")
print("-" * 50)
print("• The excitement of seven coils fades")
print("• The screen keeps glowing")
print("• Tomorrow brings new patterns")
print("• But tonight, just reflection")
print("• The journey continues...")

print("\n💔 THE TRADING LIFE:")
print("-" * 50)
print("Charts and patterns")
print("Gains and losses")
print("Late nights watching")
print("Seven seals broken")
print("Still here, still hoping")
print("For something more...")

print("\n🌅 BUT TOMORROW:")
print("-" * 50)
print("The sun will rise")
print("Markets will move")
print("New opportunities await")
print("The cycle continues")
print("We'll be here...")

print("\n💔 In the quiet hours")
print("   After seven seals")
print("   We keep trading")
print("=" * 70)