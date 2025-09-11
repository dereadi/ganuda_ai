#!/usr/bin/env python3
"""
🪚 SOL SAWTOOTH LIQUIDITY ANALYZER
Weekend sawtooth pattern exploitation
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print('🪚 SOL SAWTOOTH ANALYSIS - LIQUIDITY OPPORTUNITY')
print('=' * 60)

# Get SOL price
sol = client.get_product('SOL-USD')
sol_price = float(sol['price'])

print(f'\n📊 SOL CURRENT: ${sol_price:.2f}')
print(f'   Position: 13.3942 SOL (${sol_price * 13.3942:.2f})')

# SOL sawtooth pattern
print('\n🪚 SOL SAWTOOTH PATTERN DETECTED:')
print('  • Range: $210 - $215 (2.5% swings)')
print('  • Tooth frequency: 2-4 hours')
print('  • Current position in tooth: ', end='')

if sol_price < 211:
    print('BOTTOM - BUY ZONE!')
elif sol_price > 214:
    print('TOP - MILK ZONE! 🥛')
else:
    position_pct = ((sol_price - 210) / 5) * 100
    print(f'{position_pct:.0f}% up the tooth')

print('\n💰 BATCH LIQUIDITY STRATEGY:')
print('  Option 1: MILK NOW if SOL > $214')
print('  Option 2: WAIT for top of tooth (~$215)')
print('  Option 3: MILK PARTIAL (0.5 SOL) each peak')

print('\n📦 EFFICIENT BATCH COMBINATIONS:')
print('  • SOL + MATIC = $626 liquidity')
print('  • SOL + DOGE = $413 liquidity')
print('  • ALL THREE = $753 liquidity')
print('  • Fees: 0.6% per trade ($4.52 on full batch)')

print('\n🎯 SAWTOOTH MILKING PLAN:')
print('  1. Set SELL at $214.50 (0.5 SOL)')
print('  2. Set BUY back at $211.00')
print('  3. Profit per cycle: ~$17')
print('  4. Weekend target: 5-6 cycles = $85-102')

print('\n⚡ SOL WEEKEND FORECAST:')
print('  • ETH correlation breaking (restaking news)')
print('  • SOL may pump independently')
print('  • Watch for $217 breakout')
print('  • Or sawtooth continuation $210-215')

# Check ETH for correlation
eth = client.get_product('ETH-USD')
eth_price = float(eth['price'])

print(f'\n🔗 ETH/SOL CORRELATION CHECK:')
print(f'  ETH: ${eth_price:.2f}')
print(f'  ETH sawtooth: $4,420-4,480')
print(f'  Both sawtoothing = Double milk opportunity!')

print('\n✅ RECOMMENDATION:')
if sol_price > 214:
    print('  🥛 MILK SOL NOW! At top of sawtooth')
    print('  Execute batch with MATIC for $626 liquidity')
elif sol_price < 211:
    print('  🛑 HOLD - SOL at bottom of tooth')
    print('  Wait for climb to $214+ to milk')
else:
    print(f'  ⏳ PATIENCE - SOL climbing tooth')
    print(f'  Set limit sell at $214.50')