#!/usr/bin/env python3
import json
import subprocess

print('🔍 DIAGNOSING 0 QTY ORDER ISSUE')
print('=' * 50)

# Run quick check in subprocess to avoid timeout
cmd = """
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]  
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=2)

# Get USD balance
accounts = client.get_accounts()
for acc in accounts.accounts:
    if hasattr(acc, 'currency') and acc.currency == 'USD':
        if hasattr(acc, 'available_balance'):
            usd = float(acc.available_balance.value)
            print(f'USD_AVAILABLE:{usd}')
            
# Get BTC info
product = client.get_product('BTC-USD')
print(f'BTC_PRICE:{product.price}')
print(f'MIN_SIZE:{product.base_min_size}')
print(f'MIN_FUNDS:{product.min_market_funds}')
"""

try:
    result = subprocess.run(['python3', '-c', cmd], 
                          capture_output=True, text=True, timeout=5)
    
    output = result.stdout
    
    # Parse results
    usd_available = 0
    btc_price = 0
    min_size = 0
    min_funds = 0
    
    for line in output.split('\n'):
        if 'USD_AVAILABLE:' in line:
            usd_available = float(line.split(':')[1])
        elif 'BTC_PRICE:' in line:
            btc_price = float(line.split(':')[1])
        elif 'MIN_SIZE:' in line:
            min_size = float(line.split(':')[1])
        elif 'MIN_FUNDS:' in line:
            min_funds = float(line.split(':')[1])
    
    print(f'💵 USD Available: ${usd_available:.2f}')
    print(f'📈 BTC Price: ${btc_price:,.2f}')
    print(f'📏 Min BTC Order: {min_size} BTC')
    print(f'💰 Min USD Order: ${min_funds}')
    print()
    
    # Diagnosis
    print('🚨 DIAGNOSIS:')
    if usd_available < min_funds:
        print(f'❌ PROBLEM FOUND: Not enough USD!')
        print(f'   You have ${usd_available:.2f}')
        print(f'   Need at least ${min_funds} per order')
        print('   This causes 0 qty orders!')
        print()
        print('   SOLUTION: Your $1000 injection should have added funds.')
        print('   If not showing, may need to wait for settlement.')
    elif usd_available < 100:
        print(f'⚠️  Low USD: Only ${usd_available:.2f} available')
        print('   Orders may be too small after fees')
    else:
        print(f'✅ USD looks good: ${usd_available:.2f} available')
        print('   0 qty might be from order size calculation')
        
    # Show proper order calculation
    if btc_price > 0 and usd_available >= min_funds:
        order_amount = 50 if usd_available >= 50 else usd_available * 0.5
        btc_qty = order_amount / btc_price
        print()
        print(f'📊 PROPER ORDER CALCULATION:')
        print(f'   For ${order_amount:.2f} order:')
        print(f'   Quantity = ${order_amount:.2f} / ${btc_price:,.2f}')
        print(f'   = {btc_qty:.8f} BTC')
        print(f'   Rounded: {btc_qty:.6f} BTC')
        
except subprocess.TimeoutExpired:
    print('❌ Coinbase API timeout - this might be the root issue!')
    print('   The trading bots may be failing to place orders')
except Exception as e:
    print(f'Error: {e}')