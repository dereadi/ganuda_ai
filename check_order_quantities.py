#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print('🔍 INVESTIGATING 0 QUANTITY ORDERS')
print('=' * 50)
print()

# Get account balances first
print('CURRENT POSITIONS:')
accounts = client.get_accounts()
total_value = 0
usd_available = 0

for acc in accounts.accounts:
    if 'available_balance' in acc:
        balance = float(acc['available_balance']['value'])
        currency = acc['currency']
    else:
        balance = float(acc.get('balance', {}).get('value', 0))
        currency = acc.get('currency', 'UNKNOWN')
    
    if balance > 0.001:
        print(f'  {currency}: {balance:.8f}')
        
        if currency == 'USD':
            usd_available = balance
            total_value += balance
        elif balance > 0:
            try:
                ticker = client.get_product(f'{currency}-USD')
                price = float(ticker['price'])
                value = balance * price
                total_value += value
                print(f'    → Worth ${value:,.2f} at ${price:,.2f}')
            except:
                pass

print()
print(f'💰 Total Portfolio: ${total_value:,.2f}')
print(f'💵 USD Available: ${usd_available:,.2f}')
print()

# Check minimum order sizes
print('MINIMUM ORDER SIZES (this might be the issue!):')
products = ['BTC-USD', 'ETH-USD', 'SOL-USD']
for product in products:
    try:
        product_info = client.get_product(product)
        print(f'  {product}:')
        print(f'    Min size: {product_info.get("base_min_size", "?")}')
        print(f'    Min funds: ${product_info.get("min_market_funds", "?")}')
    except:
        pass

print()
print('🚨 ISSUE DIAGNOSIS:')
print('If seeing 0 qty orders, likely causes:')
print('  1. Order size below minimum ($10 for most pairs)')
print('  2. Insufficient funds (need $859 available)')
print('  3. Rounding errors in quantity calculation')
print()

# Try to place a test order
print('TEST: Calculating proper BTC order size...')
btc_ticker = client.get_product('BTC-USD')
btc_price = float(btc_ticker['price'])

# Calculate order size for $50
order_size_usd = 50
order_size_btc = order_size_usd / btc_price

print(f'  BTC Price: ${btc_price:,.2f}')
print(f'  For $50 order: {order_size_btc:.8f} BTC')
print(f'  Rounded to 6 decimals: {order_size_btc:.6f} BTC')
print()

if usd_available >= 50:
    print('✅ You have enough USD to place orders!')
    print(f'   Can deploy up to ${usd_available:.2f}')
else:
    print('❌ PROBLEM: Not enough USD!')
    print(f'   Have ${usd_available:.2f}, need at least $10-50 per trade')
    print('   This explains the 0 qty orders!')