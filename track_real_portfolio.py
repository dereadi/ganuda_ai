#\!/usr/bin/env python3
"""
Track your REAL portfolio with known holdings
"""

import json
import requests
from datetime import datetime

# YOUR ACTUAL HOLDINGS
PORTFOLIO = {
    'ETH': {'amount': 2.94784322, 'cost_basis': 12986.44},  # Cost basis from unrealized
    'SOL': {'amount': 37.24537566, 'cost_basis': 7600.08},
    'BTC': {'amount': 0.06347764, 'cost_basis': 6930.66},
    'XRP': {'amount': 1021.58029, 'cost_basis': 2929.11},
    'LINK': {'amount': 0.38, 'cost_basis': 8.35},
    'AVAX': {'amount': 0.28691157, 'cost_basis': 6.75},
    'USD': {'amount': 201.42, 'cost_basis': 201.42},
    'USDC': {'amount': 215.02, 'cost_basis': 215.02}
}

def get_current_prices():
    """Get current prices from Coinbase public API"""
    prices = {}
    
    try:
        response = requests.get("https://api.coinbase.com/v2/exchange-rates?currency=USD", timeout=5)
        if response.status_code == 200:
            rates = response.json()['data']['rates']
            
            for symbol in ['ETH', 'BTC', 'SOL', 'XRP', 'LINK', 'AVAX']:
                if symbol in rates:
                    prices[symbol] = 1.0 / float(rates[symbol])
    except:
        # Fallback prices from your screenshot
        prices = {
            'ETH': 4306.22,
            'SOL': 203.86,
            'BTC': 110785.18,
            'XRP': 2.83,
            'LINK': 22.35,
            'AVAX': 24.38
        }
    
    return prices

def main():
    print('🔥 REAL PORTFOLIO TRACKER - YOUR ACTUAL HOLDINGS')
    print('=' * 70)
    print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    prices = get_current_prices()
    
    total_value = 0
    total_cost = 0
    crypto_value = 0
    cash_value = 0
    
    print('\n📊 POSITIONS:\n')
    print(f'{"Asset":<6} {"Amount":>12} {"Price":>10} {"Value":>12} {"P&L":>12} {"P&L%":>8}')
    print('-' * 70)
    
    positions = []
    
    for symbol, data in PORTFOLIO.items():
        amount = data['amount']
        cost_basis = data['cost_basis']
        
        if symbol in ['USD', 'USDC']:
            current_value = amount
            price = 1.0
            cash_value += current_value
        else:
            price = prices.get(symbol, 0)
            current_value = amount * price
            crypto_value += current_value
        
        pnl = current_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        total_value += current_value
        total_cost += cost_basis
        
        positions.append({
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'value': current_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        # Print position
        if symbol in ['USD', 'USDC']:
            print(f'{symbol:<6} {amount:>12.2f} {"$1.00":>10} ${current_value:>11,.2f} ${pnl:>11,.2f} {pnl_pct:>7.1f}%')
        else:
            if price > 1000:
                print(f'{symbol:<6} {amount:>12.6f} ${price:>9,.0f} ${current_value:>11,.2f} ${pnl:>11,.2f} {pnl_pct:>7.1f}%')
            else:
                print(f'{symbol:<6} {amount:>12.6f} ${price:>9.2f} ${current_value:>11,.2f} ${pnl:>11,.2f} {pnl_pct:>7.1f}%')
    
    print('-' * 70)
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    print(f'{"TOTAL":<6} {"":<12} {"":<10} ${total_value:>11,.2f} ${total_pnl:>11,.2f} {total_pnl_pct:>7.1f}%')
    print('=' * 70)
    
    # Portfolio Analysis
    print('\n📈 PORTFOLIO ANALYSIS:')
    print(f'  Total Value:     ${total_value:,.2f}')
    print(f'  Crypto Value:    ${crypto_value:,.2f} ({crypto_value/total_value*100:.1f}%)')
    print(f'  Cash Available:  ${cash_value:,.2f} ({cash_value/total_value*100:.1f}%)')
    print(f'  Total P&L:       ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)')
    
    # Concentration
    print('\n🎯 TOP HOLDINGS:')
    positions.sort(key=lambda x: x['value'], reverse=True)
    for i, pos in enumerate(positions[:3], 1):
        pct = pos['value'] / total_value * 100
        print(f'  {i}. {pos["symbol"]}: ${pos["value"]:,.2f} ({pct:.1f}%)')
    
    # Trading Recommendations
    print('\n💡 SPECIALIST RECOMMENDATIONS:')
    
    # Check concentration
    eth_pct = (positions[0]['value'] / total_value * 100) if positions[0]['symbol'] == 'ETH' else 0
    if eth_pct > 40:
        print(f'  ⚠️  ETH is {eth_pct:.1f}% of portfolio - Consider rebalancing')
    
    # Check liquidity
    if cash_value < 500:
        print(f'  🟡 Low cash (${cash_value:.2f}) - Limited flexibility for dips')
    elif cash_value < 1000:
        print(f'  🟢 Moderate cash (${cash_value:.2f}) - Ready for opportunities')
    
    # Check for harvest opportunities
    for pos in positions:
        if pos['symbol'] not in ['USD', 'USDC']:
            if pos['pnl_pct'] > 10:
                print(f'  🟢 {pos["symbol"]}: Up {pos["pnl_pct"]:.1f}% - Consider taking profits')
            elif pos['pnl_pct'] < -10:
                print(f'  🔴 {pos["symbol"]}: Down {pos["pnl_pct"]:.1f}% - Potential averaging opportunity')
    
    print('\n' + '=' * 70)
    print('✅ Specialists now have full portfolio visibility\!')
    
    # Save for specialists
    with open('/tmp/real_portfolio.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'crypto_value': crypto_value,
            'cash_value': cash_value,
            'positions': positions,
            'prices': prices
        }, f, indent=2)
        print('💾 Saved to /tmp/real_portfolio.json for specialists')

if __name__ == "__main__":
    main()
