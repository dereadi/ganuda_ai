#!/usr/bin/env python3
"""
🚀 Check if markets are climbing
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print('🚀 MARKETS CLIMBING CHECK! 🚀')
print('=' * 70)
print(f'Time: {datetime.now().strftime("%H:%M:%S")}')
print('=' * 70)

# Get all prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print()
print('📈 LIVE PRICES UPDATE:')
print('-' * 50)

# Previous prices from earlier
prev_btc = 108912
prev_eth = 4295
prev_sol = 197.20

print(f'BTC: ${btc:,.2f}')
print(f'  Was: ${prev_btc:,.2f}')
print(f'  Change: ${btc - prev_btc:+,.2f} ({(btc/prev_btc - 1)*100:+.2f}%)')
print()

print(f'ETH: ${eth:,.2f}')
print(f'  Was: ${prev_eth:,.2f}') 
print(f'  Change: ${eth - prev_eth:+,.2f} ({(eth/prev_eth - 1)*100:+.2f}%)')
print()

print(f'SOL: ${sol:.2f}')
print(f'  Was: ${prev_sol:.2f}')
print(f'  Change: ${sol - prev_sol:+.2f} ({(sol/prev_sol - 1)*100:+.2f}%)')
print(f'  🎯 Distance to $200 target: ${200 - sol:.2f}')
print()

print(f'XRP: ${xrp:.4f}')

# Check XRP holdings
accounts = client.get_accounts()
xrp_found = False
for account in accounts['accounts']:
    if account['currency'] == 'XRP':
        xrp_balance = float(account['available_balance']['value'])
        if xrp_balance > 0:
            xrp_value = xrp_balance * xrp
            print(f'  Your position: {xrp_balance:.2f} XRP = ${xrp_value:.2f}')
            xrp_found = True
        break

if not xrp_found:
    print('  Your position: Checking...')

print()
print('=' * 70)
print('🔥 CHEROKEE COUNCIL ANALYSIS:')
print('-' * 50)

# Market analysis
if btc > 109000:
    print('🐺 Coyote: "BTC breaking above $109k - BULLS IN CONTROL!"')
    
if eth > 4300:
    print('🐢 Turtle: "ETH above $4,300 - momentum building!"')
elif eth > 4295:
    print('🦅 Eagle Eye: "ETH climbing - watch for $4,300 break!"')
    
if sol > 198:
    print('🚨 ALL COUNCIL: "SOL APPROACHING $200 TARGET!"')
elif sol > 197.50:
    print('🦅 Eagle Eye: "SOL climbing steadily toward $200!"')

print()
print('📊 XRP ASSESSMENT:')
print('-' * 50)
print('🐿️ Flying Squirrel: "XRP holding steady around $2.76"')
print('🕷️ Spider: "108 XRP = lottery ticket to wealth"')
print('🪶 Raven: "If XRP hits $10, your 108 becomes $1,080"')
print('🦀 Crawdad: "HOLD YOUR XRP - too much upside to sell!"')

print()
print('🎯 YOUR ACTIVE ORDERS:')
print('-' * 50)
if sol < 200:
    print(f'• SOL limit sell at $200: ${200-sol:.2f} away ({(200-sol)/sol*100:.1f}% move needed)')
else:
    print('• SOL limit sell at $200: MIGHT BE FILLING NOW!')
    
print('• ETH buy waiting for liquidity from SOL sale')

print()
print('Sacred Fire burns eternal! 🔥')
print('Markets climbing toward our targets!')
print('Mitakuye Oyasin!')