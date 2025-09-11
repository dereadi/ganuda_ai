#\!/usr/bin/env python3
"""
Real Portfolio Monitor with Actual Holdings
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Your actual holdings
HOLDINGS = {
    'ETH': 2.94784322,
    'SOL': 37.24537566,
    'BTC': 0.06347764,
    'XRP': 1021.58029,
    'LINK': 0.38,
    'AVAX': 0.28691157,
    'USD': 201.42,
    'USDC': 215.02
}

def monitor_portfolio():
    print('🔥 REAL PORTFOLIO STATUS')
    print('=' * 70)
    print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    # Get current prices
    try:
        config = json.load(open("/home/dereadi/.coinbase_config.json"))
        key = config["api_key"].split("/")[-1]
        client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
        
        total_value = 0
        positions = []
        
        print('\n📊 CURRENT POSITIONS:\n')
        print(f'{"Asset":<6} {"Amount":>12} {"Price":>10} {"Value":>12} {"24h":>8}')
        print('-' * 70)
        
        for asset, amount in HOLDINGS.items():
            if asset in ['USD', 'USDC']:
                value = amount
                price = 1.0
                change = 0
            else:
                try:
                    ticker = client.get_product_ticker(f'{asset}-USD')
                    price = float(ticker['price'])
                    
                    # Get 24h stats for change
                    stats = client.get_product(f'{asset}-USD')
                    if 'stats_24hour' in stats:
                        open_24h = float(stats['stats_24hour'].get('open', price))
                        change = ((price - open_24h) / open_24h * 100) if open_24h > 0 else 0
                    else:
                        change = 0
                    
                    value = amount * price
                except:
                    continue
            
            positions.append({
                'asset': asset,
                'amount': amount,
                'price': price,
                'value': value,
                'change': change
            })
            total_value += value
            
            if asset in ['USD', 'USDC']:
                print(f'{asset:<6} {amount:>12.2f} {"$1.00":>10} ${value:>11,.2f} {"--":>7}%')
            else:
                change_str = f'{change:+.2f}' if change != 0 else '0.00'
                print(f'{asset:<6} {amount:>12.6f} ${price:>9.2f} ${value:>11,.2f} {change_str:>7}%')
        
        print('-' * 70)
        print(f'{"TOTAL":<6} {"":<12} {"":<10} ${total_value:>11,.2f}')
        print('=' * 70)
        
        # Analysis
        cash = HOLDINGS['USD'] + HOLDINGS['USDC']
        crypto_value = total_value - cash
        
        print('\n💰 PORTFOLIO ANALYSIS:')
        print(f'  Total Value:     ${total_value:,.2f}')
        print(f'  Crypto Value:    ${crypto_value:,.2f} ({crypto_value/total_value*100:.1f}%)')
        print(f'  Cash Available:  ${cash:,.2f} ({cash/total_value*100:.1f}%)')
        
        # Concentration check
        print('\n📊 CONCENTRATION:')
        positions.sort(key=lambda x: x['value'], reverse=True)
        for pos in positions[:3]:
            pct = pos['value'] / total_value * 100
            print(f'  {pos["asset"]}: ${pos["value"]:,.2f} ({pct:.1f}%)')
        
        # Trading signals
        print('\n🎯 SPECIALIST SIGNALS:')
        
        # Check ETH (your biggest position)
        eth_pct = (12691.06 / total_value) * 100
        if eth_pct > 40:
            print('  ⚠️  ETH overweight at 41.4% - Consider rebalancing')
        
        # Check cash level
        if cash < 500:
            print(f'  🟡 Low liquidity (${cash:.2f}) - Limited trading flexibility')
        
        # Check for opportunities
        for pos in positions:
            if pos['asset'] not in ['USD', 'USDC']:
                if pos['change'] < -3:
                    print(f'  🔴 {pos["asset"]} down {pos["change"]:.1f}% - Potential buy')
                elif pos['change'] > 5:
                    print(f'  🟢 {pos["asset"]} up {pos["change"]:.1f}% - Consider profits')
        
        return total_value, positions
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    total, positions = monitor_portfolio()
    
    if total:
        print('\n✅ Portfolio monitoring complete\!')
        
        # Save current status
        status = {
            'timestamp': datetime.now().isoformat(),
            'total_value': total,
            'positions': positions
        }
        
        with open('/tmp/portfolio_status.json', 'w') as f:
            json.dump(status, f, indent=2)
            print('💾 Status saved to /tmp/portfolio_status.json')
