#!/usr/bin/env python3
"""
🔴 THE RED - CHEVELLE
"They say freak when you're singled out"
"The red, it filters through"
The blood in the water... The red candles... The pressure...
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

# Gentle with API
time.sleep(3)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           🔴 THE RED 🔴                                   ║
║                            CHEVELLE                                       ║
║                   "They say freak when you're singled out"                ║
║                      "The red, it filters through"                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE RED FILTERS THROUGH")
print("=" * 70)

print("\n🔴 THE RED IS SHOWING:")
print("-" * 50)
print("The pressure before 01:00...")
print("The blood in the water...")
print("The red candles appearing...")
print("'So lay down, the threat is real'")

# Check the red
try:
    btc = float(client.get_product('BTC-USD')['price'])
    time.sleep(2)
    eth = float(client.get_product('ETH-USD')['price'])
    time.sleep(2)
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n🔴 CURRENT RED:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    if btc < 112800:
        print("\n🔴 THE RED IS SPREADING")
        print("'They say freak when you're singled out'")
    elif btc < 112850:
        print("\n🔴 THE RED FILTERS THROUGH")
        print("'When you see them coming'")
    else:
        print("\n⚫ Darkness before the red...")
    
except Exception as e:
    print(f"\n🔴 The red overwhelmed the API: {str(e)[:50]}")

print("\n🎵 THE RED - CHEVELLE LYRICS:")
print("-" * 50)
print("'They say freak'")
print("'When you're singled out'")
print("'The red'")
print("'It filters through'")
print("")
print("'So lay down'")
print("'The threat is real'")
print("'When his sight'")
print("'Goes red again'")

# Track the red movements
print("\n🔴 WATCHING THE RED FLOW:")
print("-" * 50)

for i in range(5):
    try:
        btc_now = float(client.get_product('BTC-USD')['price'])
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc_now:,.0f}")
        
        if btc_now < btc:
            print("  🔴 THE RED DEEPENS")
            print("  'Seeing red again'")
        elif btc_now > btc:
            print("  ⚫ The red recedes... for now")
        else:
            print("  🔴 The red holds steady")
        
        btc = btc_now
        
    except:
        print("  🔴 Too much red for the API")
    
    time.sleep(5)

# Time to 01:00
minutes_to_0100 = 60 - datetime.now().minute if datetime.now().hour == 0 else 0

print("\n⏰ THE RED COUNTDOWN:")
print("-" * 50)
print(f"Minutes until 01:00: {minutes_to_0100}")

if minutes_to_0100 < 5:
    print("\n🔴🔴🔴 THE RED HOUR APPROACHES!")
    print("'This change'")
    print("'He won't contain'")
    print("'Slip away'")
    print("'To clear your mind'")
    print("\nWhen 01:00 hits...")
    print("THE RED WILL EITHER:")
    print("• EXPLODE INTO GREEN")
    print("• OR DEEPEN INTO BLOOD")

print("\n🔴 THE RED PROPHECY:")
print("-" * 50)
print("• The red before 01:00 is the pressure")
print("• Four coils wound in red tension")
print("• When the sight goes red again...")
print("• The explosion will be violent")
print("• Red turns to green, or deeper red")

print("\n'THEY SAY FREAK'")
print("'WHEN YOU'RE SINGLED OUT'")
print("'THE RED'")
print("'IT FILTERS THROUGH'")
print("=" * 70)