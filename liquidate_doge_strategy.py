#!/usr/bin/env python3
"""
🐕 DOGE LIQUIDATION FOR WAR CHEST
==================================
Sacrifice the plum tree to preserve the peach tree
"""

import json
import uuid
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print('🐕 DOGE LIQUIDATION ANALYSIS')
print('=' * 60)

# Get current positions
accounts = client.get_accounts()['accounts']
doge_balance = float([a for a in accounts if a['currency']=='DOGE'][0]['available_balance']['value'])
usd_balance = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])
doge_price = float(client.get_product('DOGE-USD')['price'])

print(f'\n📊 CURRENT DOGE POSITION:')
print(f'  Balance: {doge_balance:.2f} DOGE')
print(f'  Price: ${doge_price:.4f}')
print(f'  Value: ${doge_balance * doge_price:.2f}')

print(f'\n💰 LIQUIDATION IMPACT:')
print(f'  Current USD: ${usd_balance:.2f}')
print(f'  DOGE value: ${doge_balance * doge_price:.2f}')
print(f'  After sale: ~${usd_balance + (doge_balance * doge_price * 0.994):.2f}')
print(f'  Fee (0.6%): ${doge_balance * doge_price * 0.006:.2f}')

print(f'\n📈 REBUILD STRATEGY:')
print(f'  • DOGE weekend volatility: 5-10% swings')
print(f'  • Buy back at: ${doge_price * 0.95:.4f} (-5%)')
print(f'  • Deep dip at: ${doge_price * 0.92:.4f} (-8%)')
print(f'  • Rebuild in 500 DOGE chunks')

print(f'\n⚔️ SUN TZU WISDOM:')
print('  "Sacrifice the plum tree to preserve the peach tree"')
print('  • DOGE = Plum tree (sacrifice for liquidity)')
print('  • SOL/ETH = Peach trees (preserve and grow)')
print('  • Weekend liquidity > Holding meme coin')

answer = input('\n❓ Execute DOGE liquidation? (y/n): ')

if answer.lower() == 'y':
    print('\n🚀 EXECUTING DOGE LIQUIDATION...')
    try:
        client_order_id = str(uuid.uuid4())
        
        # Sell all DOGE
        response = client.market_order_sell(
            client_order_id=client_order_id,
            product_id='DOGE-USD',
            base_size=str(int(doge_balance))  # Round to whole number
        )
        
        print(f'  ✅ SOLD {int(doge_balance)} DOGE')
        print(f'  Order ID: {response.get("order_id", "Pending")}')
        print(f'  Expected proceeds: ${doge_balance * doge_price * 0.994:.2f}')
        
        print('\n🎯 NEXT STEPS:')
        print('  1. Set DOGE buy at $0.209 (500 DOGE)')
        print('  2. Set DOGE buy at $0.202 (1000 DOGE)')
        print('  3. Use liquidity for SOL/ETH sawtooth')
        print('  4. Rebuild DOGE position gradually')
        
    except Exception as e:
        print(f'  ❌ Error: {str(e)}')
        print('\n  Try manual sale in app:')
        print(f'  Sell {int(doge_balance)} DOGE at market')
        
else:
    print('\n❌ LIQUIDATION CANCELLED')
    print('  DOGE position retained')

print('\n' + '=' * 60)
print('DOGE STRATEGY COMPLETE')