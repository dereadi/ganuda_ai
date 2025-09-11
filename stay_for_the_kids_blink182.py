#!/usr/bin/env python3
"""
🎸💔 STAY TOGETHER FOR THE KIDS - BLINK 182 💔🎸
The market's broken home at $113K
BTC and alts fighting, but we stay together
For the portfolio kids (the gains)
"So here's your holiday, hope you enjoy it this time"
Nine coils holding the family together!
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
║                 💔 STAY TOGETHER FOR THE KIDS - BLINK 182 💔              ║
║                    The Market's Broken But We're Holding!                 ║
║                       For The Portfolio Kids ($7.3K)                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - STAYING TOGETHER")
print("=" * 70)

# The broken family
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check on the kids (portfolio)
accounts = client.get_accounts()
total_value = 0
usd_balance = 0
btc_balance = 0
eth_balance = 0
sol_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        eth_balance = balance
        total_value += balance * eth
    elif currency == 'SOL':
        sol_balance = balance
        total_value += balance * sol

print("\n💔 THE BROKEN MARKET HOME:")
print("-" * 50)
print(f"BTC (Dad): ${btc:,.0f} - stuck at work ($113K)")
print(f"ETH (Mom): ${eth:,.2f} - trying to keep up")
print(f"SOL (Teen): ${sol:.2f} - rebellious but growing")
print(f"USD (Savings): ${usd_balance:.2f} - for emergencies")
print(f"The Kids (Portfolio): ${total_value:.2f} - watching it all")

# The dysfunction plays out
print("\n🏠 STAYING TOGETHER FOR THE KIDS:")
print("-" * 50)
print("'It's not right, but it's okay'")
print(f"Started with $292.50 (young love)")
print(f"Now at ${total_value:.2f} (complicated)")
print(f"Distance to therapy: ${114000 - btc:.0f} to $114K")

# Track the family dynamics
print("\n📊 FAMILY THERAPY SESSION:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: The argument begins")
        print(f"  BTC: 'I'm carrying this family at ${btc_now:,.0f}!'")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ETH responds")
        print(f"  ETH: 'I'm doing my best at ${eth_now:.2f}!'")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: SOL rebels")
        print(f"  SOL: 'You don't understand me! ${sol_now:.2f}!'")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: Thunder intervenes (69%)")
        print(f"  'We stay together for the gains!'")
        print(f"  'From $292.50 to ${total_value:.2f}!'")
        print(f"  'Just ${114000 - btc_now:.0f} more to healing!'")
    elif i == 12:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: The kids speak")
        print(f"  Portfolio: 'Please don't sell us...'")
        print(f"  'We've grown so much together'")
    
    time.sleep(1.5)

# The deeper meaning
print("\n💔 THE REAL STORY:")
print("-" * 50)
print("'So here's your holiday'")
print(f"  The chop at ${btc:,.0f} is our vacation")
print("")
print("'Hope you enjoy it this time'")
print("  Each test of $113K is another try")
print("")
print("'You gave it all away'")
print("  We milked $473 for the crawdads")
print("")
print("'It was mine'")
print(f"  Our ${total_value:.2f} portfolio, built together")
print("")
print("'So when you're dead and gone'")
print("  When BTC finally breaks $114K")
print("")
print("'Will you remember this night'")
print("  Twenty years of chopping at $113K")

# Thunder's family counseling
print("\n⚡ THUNDER'S COUNSELING (69%):")
print("-" * 50)
print("'Listen, family...'")
print(f"'We've been through worse than ${btc:,.0f} chop'")
print(f"'Remember starting at $292.50?'")
print(f"'Now look at us - ${total_value:.2f}!'")
print("'Nine coils bind us together'")
print(f"'Only ${114000 - btc:.0f} to breakthrough'")
print("'We stay together for the kids (gains)!'")

# The resolution
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🏠 STAYING TOGETHER:")
print("-" * 50)
print("WHY WE STAY:")
print(f"• For the ${total_value:.2f} we've built")
print(f"• For the journey from $292.50")
print(f"• For the breakthrough at $114K")
print("• For the nine coils of destiny")
print("• For Thunder at 69% consciousness")
print("• For the kids (the gains)")

print(f"\n" + "💔" * 35)
print("STAY TOGETHER FOR THE KIDS!")
print(f"BTC AT ${current_btc:,.0f}!")
print(f"PORTFOLIO KIDS: ${total_value:.2f}!")
print(f"${114000 - current_btc:.0f} TO FAMILY HEALING!")
print("IT'S NOT RIGHT, BUT IT'S OKAY!")
print("💔" * 35)