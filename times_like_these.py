#!/usr/bin/env python3
"""
🎸 TIMES LIKE THESE - FOO FIGHTERS
After seven seals, wild swings, and late night battles
These are the times that test traders
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
║                      🎸 TIMES LIKE THESE 🎸                               ║
║                         FOO FIGHTERS                                       ║
║                   After Seven Seals and Battles                           ║
║                     These Are The Testing Times                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - TIMES LIKE THESE")
print("=" * 70)

# Reflect on the journey
btc_now = float(client.get_product('BTC-USD')['price'])
eth_now = float(client.get_product('ETH-USD')['price'])
sol_now = float(client.get_product('SOL-USD')['price'])

print(f"\n🎸 IN TIMES LIKE THESE:")
print(f"  BTC: ${btc_now:,.0f}")
print(f"  ETH: ${eth_now:.2f}")
print(f"  SOL: ${sol_now:.2f}")

# Remember the journey
print("\n📖 THE JOURNEY TONIGHT:")
print("-" * 50)
print("• Seven coils wound impossibly tight")
print("• Each seal broken with anticipation")
print("• The climb above $113k")
print("• The tests, the doubts, the victories")
print("• In times like these...")

# Track current movement
print("\n🎸 LIVING IN THE MOMENT:")
print("-" * 50)

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f}")
        
        if btc > 113100:
            print("  🎸 Times like these - we rise above")
        elif btc > 113050:
            print("  🎸 Times like these - we hold strong")
        elif btc > 113000:
            print("  🎸 Times like these - we stay patient")
        else:
            print("  🎸 Times like these - we learn to live again")
    
    time.sleep(3)

# Check portfolio status
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD':
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * btc_now
        elif currency == 'ETH' and balance > 0:
            portfolio_value += balance * eth_now
        elif currency == 'SOL' and balance > 0:
            portfolio_value += balance * sol_now
    
    print(f"\n💰 Portfolio in times like these: ${portfolio_value:,.2f}")
    
except:
    pass

print("\n💭 TIMES LIKE THESE WISDOM:")
print("-" * 50)
print("• Seven seals tested our patience")
print("• The coils tested our faith")
print("• The swings tested our nerves")
print("• But we're still here")
print("• Learning to trade again")

print("\n🎸 THE LESSON:")
print("-" * 50)
print("In times like these...")
print("We learn what matters")
print("Not the minute movements")
print("Not the small fluctuations")
print("But staying the course")
print("Through seven seals")
print("Through the night")

print("\n🌅 TOMORROW:")
print("-" * 50)
print("The sun will rise")
print("Markets will move")
print("New patterns will form")
print("But tonight taught us")
print("How to handle...")
print("Times like these")

print("\n🎸 In times like these")
print("   We learn to trade again")
print("=" * 70)