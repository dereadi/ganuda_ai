#!/usr/bin/env python3
"""
👤 MY NAME IS HUMAN - HIGHLY SUSPECT
"I'm feeling the way that I'm feeling myself"
"Fuck everyone else"
Six coils wound, portfolio growing, human in control
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
║                    👤 MY NAME IS HUMAN 👤                                 ║
║                       HIGHLY SUSPECT                                      ║
║            "I'm feeling the way that I'm feeling myself"                  ║
║                      "Fuck everyone else"                                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HUMAN IN CONTROL")
print("=" * 70)

print("\n👤 HUMAN STATUS CHECK:")
print("-" * 50)
print("• Name: HUMAN")
print("• Status: IN CONTROL")
print("• Coils wound: SIX")
print("• Fear level: DEAD")
print("• Confidence: MAXIMUM")

# Check current state
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 HUMAN'S MARKET:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

# Check portfolio
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
            portfolio_value += balance * btc
        elif currency == 'ETH' and balance > 0:
            portfolio_value += balance * eth
        elif currency == 'SOL' and balance > 0:
            portfolio_value += balance * sol
    
    print(f"\n💰 HUMAN'S PORTFOLIO:")
    print(f"  Total value: ${portfolio_value:,.2f}")
    print(f"  USD ready: ${usd_balance:.2f}")
    
except Exception as e:
    print(f"Error: {str(e)[:50]}")

print("\n🎵 'MY NAME IS HUMAN' LYRICS:")
print("-" * 50)
print("'Hello, my name is human'")
print("'And I came down from the stars'")
print("'Hello, my name is human'")
print("'I'm ready for love'")
print("")
print("'I'm feeling the way that I'm feeling myself'")
print("'Fuck everyone else'")
print("'Gotta remember that nobody is better than anyone else'")
print("'Here we are'")

print("\n👤 HUMAN WISDOM AFTER SIX COILS:")
print("-" * 50)
print("• The market tried to break me - I didn't break")
print("• Six coils of pressure - I held through all")
print("• The death of fear - I killed it myself")
print("• Everyone else panicked - I stayed human")
print("• The explosion is coming - I'm ready")

# Track human control
print("\n⚡ HUMAN TAKING CONTROL:")
print("-" * 50)

for i in range(5):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({move:+.0f})")
    
    if abs(move) < 10:
        print("  👤 'I'm feeling myself'")
        print("     Human controls the coil")
    elif abs(move) < 50:
        print("  👤 'Hello, my name is human'")
        print("     The market recognizes me")
    else:
        print("  👤 'I CAME DOWN FROM THE STARS!'")
        print("     Human transcends the market!")
    
    time.sleep(3)

print("\n🌟 HUMAN ACHIEVEMENTS TONIGHT:")
print("-" * 50)
print("✓ Survived six market coils")
print("✓ Killed fear completely")
print("✓ Generated $1,300+ in profit harvests")
print("✓ Fed the crawdads to hunt")
print("✓ Stayed human through it all")
print("✓ Ready for the explosion")

print("\n👤 MY NAME IS HUMAN")
print("   I'm ready for what comes next")
print("   'Fuck everyone else'")
print("   I control my destiny")
print("=" * 70)