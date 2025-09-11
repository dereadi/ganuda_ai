#!/usr/bin/env python3
"""
LIQUIDITY ANALYSIS
Check if we have liquidity for movement
"""

positions = {
    'USD': 17.96,
    'XRP': 35.67095800,
    'DOGE': 1568.90000000,
    'LINK': 0.38000000,
    'MATIC': 8519.50000000,
    'AVAX': 87.55769424,
    'SOL': 15.60480121,
    'ETH': 0.44080584,
    'BTC': 0.02859213
}

prices = {
    'XRP': 2.81,
    'DOGE': 0.2111,
    'LINK': 23.24,
    'MATIC': 0.2378,
    'AVAX': 23.39,
    'SOL': 203.10,
    'ETH': 4342.66,
    'BTC': 108327.00
}

print('💰 LIQUIDITY ANALYSIS FOR MOVEMENT:')
print('=' * 60)
print(f'💵 Cash Available: ${positions["USD"]:.2f} ⚠️ VERY LOW!')
print()

# Calculate liquid positions
print('🔥 HIGHLY LIQUID (instant conversion):')
liquid_total = positions['USD']
for coin in ['BTC', 'ETH', 'SOL']:
    if coin in positions:
        value = positions[coin] * prices[coin]
        liquid_total += value
        print(f'  • {coin}: ${value:,.2f} ({positions[coin]:.8f} @ ${prices[coin]:,.2f})')

print()
print('📊 MEDIUM LIQUIDITY (1-5 min to sell):')
medium_liquid = 0
for coin in ['MATIC', 'AVAX', 'DOGE']:
    if coin in positions:
        value = positions[coin] * prices[coin]
        medium_liquid += value
        print(f'  • {coin}: ${value:,.2f}')

print()
print('=' * 60)
print(f'⚡ IMMEDIATE LIQUIDITY: ${liquid_total:,.2f}')
print(f'📈 TOTAL PORTFOLIO: ${liquid_total + medium_liquid + positions["LINK"] * prices["LINK"]:,.2f}')
print()

print('🚨 LIQUIDITY VERDICT:')
print('-' * 40)
if positions['USD'] < 100:
    print('❌ CRITICAL: Only $17.96 cash!')
    print('⚠️  This is NOT enough for movement trading')
    print()
    print('🔥 RECOMMENDED ACTIONS:')
    print('  1. SELL $1000 of SOL immediately → Cash')
    print('  2. SELL $500 of ETH → Cash') 
    print('  3. Keep $1500+ cash for volatility plays')
    print()
    print('📍 POSITIONS TO LIQUIDATE:')
    sol_to_sell = 1000 / prices['SOL']
    eth_to_sell = 500 / prices['ETH']
    print(f'  • Sell {sol_to_sell:.4f} SOL (${1000:.2f})')
    print(f'  • Sell {eth_to_sell:.4f} ETH (${500:.2f})')
    print(f'  • This gives you $1,517.96 cash liquidity')
else:
    print('✅ Sufficient cash for trading')

print()
print('💡 LIQUIDITY STRATEGY:')
print('  • Keep 10-15% in cash for opportunities')
print('  • BTC/ETH/SOL are your emergency liquidity')
print('  • MATIC is largest position but less liquid')
print('  • Movement requires CASH, not just assets!')