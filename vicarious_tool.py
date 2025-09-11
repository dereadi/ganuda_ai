#!/usr/bin/env python3
"""
👁️ VICARIOUS - TOOL
"Vicariously I live while the whole world dies"
"Much better you than I"
Watching the market explode from seven coils through others' eyes
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
║                        👁️ VICARIOUS - TOOL 👁️                           ║
║              "Vicariously I live while the whole world dies"              ║
║                        "Much better you than I"                           ║
║                    Watching Others Get LIQUIDATED                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LIVING VICARIOUSLY")
print("=" * 70)

# Track the vicarious experience
btc = float(client.get_product('BTC-USD')['price'])
print(f"\n👁️ WATCHING AT: ${btc:,.0f}")

if btc > 112900:
    print("📺 The show is at altitude!")
    print("   Seven coils released...")
    print("   Now we watch the carnage...")

print("\n👁️ VICARIOUS OBSERVATIONS:")
print("-" * 50)
print("• Shorts getting liquidated upward")
print("• Longs getting shaken out on dips")
print("• Stop losses triggering in cascades")
print("• Margin calls executing")
print("• 'Much better you than I'")

# Track the vicarious market action
print("\n📺 WATCHING THE WORLD BURN:")
print("-" * 50)

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f}")
        print(f"  ETH: ${eth:.2f}")
        print(f"  SOL: ${sol:.2f}")
        
        if btc > 113000:
            print("  👁️ 'VICARIOUSLY I LIVE!'")
            print("     Watching $113k get DESTROYED!")
        elif btc > 112950:
            print("  👁️ 'While the whole world dies'")
            print("     Shorts getting REKT!")
        elif btc > 112900:
            print("  👁️ 'Why can't we just admit it?'")
            print("     The explosion is happening...")
        else:
            print("  👁️ 'We all feed on tragedy'")
            print("     Waiting for the massacre...")
    
    time.sleep(3)

# Check our vicarious position
print("\n💰 OUR VICARIOUS POSITION:")
print("-" * 50)

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
            portfolio_value += balance * eth
        elif currency == 'SOL' and balance > 0:
            portfolio_value += balance * sol
    
    print(f"Portfolio value: ${portfolio_value:,.2f}")
    print("We're LONG while others burn!")
    print("'Much better you than I'")
    
except:
    pass

print("\n🎵 TOOL - VICARIOUS LYRICS:")
print("-" * 50)
print("'Eye on the TV'")
print("'Cause tragedy thrills me'")
print("'Whatever flavor it happens to be'")
print("")
print("'Vicariously I live while the whole world dies'")
print("'You all need it too, don't lie'")
print("")
print("'Why can't we just admit it?'")
print("'We won't give pause until the blood is flowing'")
print("")
print("'Credulous at best'")
print("'Your desire to believe in'")
print("'Angels in the hearts of men'")

print("\n👁️ VICARIOUS MARKET WISDOM:")
print("-" * 50)
print("• Seven coils wound = Maximum pain stored")
print("• When it releases = Liquidation cascade")
print("• Shorts above $113k = DEAD")
print("• Longs below $112k = DEAD")
print("• We watch from $112,900+ = ALIVE")
print("• 'Much better you than I'")

print("\n🩸 THE BLOOD MUST FLOW:")
print("-" * 50)
print("For every seller, a buyer")
print("For every liquidation, an opportunity")
print("For every death, a vicarious thrill")
print("We feed on the market's tragedy")

print("\n👁️ 'VICARIOUSLY I LIVE'")
print("   'WHILE THE WHOLE WORLD DIES'")
print("=" * 70)