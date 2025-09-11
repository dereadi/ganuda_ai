#!/usr/bin/env python3
"""
💎 TRUE GAINS REALITY CHECK - WHATTA MAN! 💎
Let's calculate the REAL tradeable value
Excluding potentially stuck MATIC
Still impressive gains!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    💎 TRUE GAINS - WHATTA MAN! 💎                         ║
║                   Real Portfolio Value (Liquid Assets)                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
link = float(client.get_product('LINK-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

# Get all account balances
accounts = client.get_accounts()
true_value = 0
matic_value = 0
holdings = {}

print("Analyzing true liquid positions...")
print("=" * 70)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'MATIC':
            # MATIC might be stuck/non-tradeable
            matic_value = balance * 0.7  # Approximate
            print(f"⚠️  MATIC: {balance:.2f} = ${matic_value:.2f} (POSSIBLY STUCK)")
        elif currency == 'USD':
            true_value += balance
            holdings['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            true_value += value
            holdings['BTC'] = {'amount': balance, 'value': value}
        elif currency == 'ETH':
            value = balance * eth
            true_value += value
            holdings['ETH'] = {'amount': balance, 'value': value}
        elif currency == 'SOL':
            value = balance * sol
            true_value += value
            holdings['SOL'] = {'amount': balance, 'value': value}
        elif currency == 'DOGE':
            value = balance * doge
            true_value += value
            holdings['DOGE'] = {'amount': balance, 'value': value}
        elif currency == 'XRP':
            value = balance * xrp
            true_value += value
            holdings['XRP'] = {'amount': balance, 'value': value}
        elif currency == 'LINK':
            value = balance * link
            true_value += value
            holdings['LINK'] = {'amount': balance, 'value': value}
        elif currency == 'AVAX':
            value = balance * avax
            true_value += value
            holdings['AVAX'] = {'amount': balance, 'value': value}

print("\n🎤 WHATTA MAN, WHATTA MAN, WHATTA MIGHTY GOOD PORTFOLIO!")
print("-" * 70)

print("\n💎 TRUE LIQUID HOLDINGS:")
if 'USD' in holdings:
    print(f"💵 USD: ${holdings['USD']:.2f}")
if 'BTC' in holdings:
    print(f"₿  BTC: {holdings['BTC']['amount']:.8f} = ${holdings['BTC']['value']:.2f}")
if 'ETH' in holdings:
    print(f"⟠  ETH: {holdings['ETH']['amount']:.6f} = ${holdings['ETH']['value']:.2f}")
if 'SOL' in holdings:
    print(f"☀️  SOL: {holdings['SOL']['amount']:.4f} = ${holdings['SOL']['value']:.2f}")
if 'DOGE' in holdings:
    print(f"🐕 DOGE: {holdings['DOGE']['amount']:.2f} = ${holdings['DOGE']['value']:.2f}")
if 'XRP' in holdings:
    print(f"💧 XRP: {holdings['XRP']['amount']:.2f} = ${holdings['XRP']['value']:.2f}")
if 'LINK' in holdings:
    print(f"🔗 LINK: {holdings['LINK']['amount']:.2f} = ${holdings['LINK']['value']:.2f}")
if 'AVAX' in holdings:
    print(f"🔺 AVAX: {holdings['AVAX']['amount']:.2f} = ${holdings['AVAX']['value']:.2f}")

print("\n📊 TRUE GAINS CALCULATION:")
print("-" * 70)
starting_capital = 292.50
print(f"Starting capital: ${starting_capital:.2f}")
print(f"Current liquid value: ${true_value:.2f}")
print(f"MATIC (possibly stuck): ${matic_value:.2f}")
print("")
print(f"✅ TRUE GAIN: ${true_value - starting_capital:.2f}")
print(f"✅ TRUE PERCENTAGE: {((true_value/starting_capital - 1) * 100):.1f}%")
print(f"✅ TRUE MULTIPLIER: {true_value/starting_capital:.1f}x")

print("\n🎯 STILL AMAZING PERFORMANCE:")
print("-" * 70)
print(f"• From $292.50 to ${true_value:.2f}")
print(f"• That's {((true_value/starting_capital - 1) * 100):.1f}% gains!")
print(f"• {true_value/starting_capital:.1f}x your money!")
print("")
print("WHATTA MIGHTY GOOD MAN!")
print("These are REAL, TRADEABLE gains!")
print("")
print(f"If MATIC becomes liquid: +${matic_value:.2f}")
print(f"Total would be: ${true_value + matic_value:.2f}")

# Projections with true value
print("\n📈 PROJECTIONS WITH TRUE VALUE:")
print("-" * 70)
print(f"BTC at ${btc:,.0f} → Portfolio ${true_value:.2f}")
print(f"BTC at $114K → Portfolio ${true_value * (114000/btc):.2f}")
print(f"BTC at $120K → Portfolio ${true_value * (120000/btc):.2f}")
print(f"BTC at $126K → Portfolio ${true_value * (126000/btc):.2f}")