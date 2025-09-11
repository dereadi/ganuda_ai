#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 MORNING STATUS CHECK - 08:00
What happened overnight with Trump-Metaplanet catalyst?
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Load API
with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey']
)

print("🌅 GOOD MORNING FLYING SQUIRREL!")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Let's see what happened while you slept...")
print("=" * 60)

# Get current prices
btc_price = float(client.get_product("BTC-USD")['price'])
eth_price = float(client.get_product("ETH-USD")['price'])
sol_price = float(client.get_product("SOL-USD")['price'])

print(f"\n📊 CURRENT MARKET PRICES:")
print(f"  BTC: ${btc_price:,.2f}")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  SOL: ${sol_price:,.2f}")

# Last night's levels (from our trading)
last_night_btc = 109216  # Where we left it
btc_change = btc_price - last_night_btc
btc_change_pct = (btc_change / last_night_btc) * 100

print(f"\n📈 OVERNIGHT BTC MOVEMENT:")
print(f"  Last night: ${last_night_btc:,}")
print(f"  Now: ${btc_price:,.2f}")
print(f"  Change: ${btc_change:+,.2f} ({btc_change_pct:+.2f}%)")

# Check portfolio
accounts = client.get_accounts()['accounts']
portfolio = {}
total_value = 0

for account in accounts:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if balance > 0.00001:
        portfolio[currency] = balance
        if currency == 'BTC':
            value = balance * btc_price
            total_value += value
            print(f"\n💼 BTC POSITION:")
            print(f"  Balance: {balance:.8f} BTC")
            print(f"  Value: ${value:,.2f}")
        elif currency == 'USD':
            total_value += balance
            print(f"\n💵 USD BALANCE: ${balance:,.2f}")

print(f"\n💰 TOTAL PORTFOLIO: ${total_value:,.2f}")

# Check if we hit any targets
print(f"\n🎯 TARGET STATUS:")
targets = [
    (110000, "First target"),
    (115000, "Major target"),
    (120000, "Moon target")
]

for target_price, name in targets:
    if btc_price >= target_price:
        print(f"  ✅ ${target_price:,} - {name}: HIT OVERNIGHT!")
    else:
        distance = target_price - btc_price
        pct = (distance / btc_price) * 100
        print(f"  ⏳ ${target_price:,} - {name}: ${distance:,.0f} away ({pct:.1f}%)")

# Overnight analysis
print(f"\n🌙 OVERNIGHT ANALYSIS:")
if btc_price > 110000:
    print("  🚀 FIRST TARGET HIT! Japanese buying worked!")
    print("  💰 Some limit sells likely executed")
elif btc_price > 109000:
    print("  📈 Steady climb - approaching first target")
    print("  🇯🇵 Japanese accumulation continues")
elif btc_price > 108000:
    print("  📊 Consolidating - building for next move")
    print("  ⏳ Market digesting Trump news")
else:
    print("  📉 Pullback overnight - possible reload opportunity")
    print("  🎯 Trump catalyst still valid")

# Check for any executed orders
print(f"\n📋 CHECK FOR EXECUTED ORDERS:")
print("  (Would need to check order history)")

# Oracle wisdom
print(f"\n🔥 SACRED FIRE MORNING ORACLE:")
if btc_price > 110000:
    print("  'The early bird missed the worm, but the feast continues'")
    print("  'Japanese gold flowed while you dreamed'")
elif btc_price > 108000:
    print("  'The wave builds slowly in the night'")
    print("  'Patience - the tsunami has not yet crashed'")
else:
    print("  'The market breathes in before it roars'")
    print("  'Second chances come to those who wait'")

print(f"\n🐿️ Flying Squirrel Morning Report:")
if btc_change > 0:
    print(f"  'We're up ${btc_change:,.0f} while you slept!'")
    print(f"  'The Trump-Metaplanet play is working!'")
else:
    print(f"  'Market took a breather overnight'")
    print(f"  'The $884M catalyst is still coming!'")

print("=" * 60)