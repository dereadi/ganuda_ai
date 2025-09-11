#\!/usr/bin/env python3
"""
Get live prices from TradingView for portfolio valuation
"""

import json
import requests
from datetime import datetime

def get_crypto_prices():
    """Fetch current crypto prices from TradingView scanner"""
    
    url = "https://scanner.tradingview.com/crypto/scan"
    
    # Request top cryptos by market cap
    payload = {
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "COINBASE"},
            {"left": "market_cap", "operation": "greater", "right": 1000000}
        ],
        "options": {
            "lang": "en"
        },
        "symbols": {},
        "columns": [
            "name",
            "close",
            "change",
            "change_abs", 
            "high",
            "low",
            "volume",
            "market_cap",
            "description"
        ],
        "sort": {
            "sortBy": "market_cap",
            "sortOrder": "desc"
        },
        "range": [0, 50]
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print('🔥 TRADINGVIEW LIVE PRICES (COINBASE)')
            print('=' * 70)
            print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            print('=' * 70)
            
            prices = {}
            
            if 'data' in data:
                print('\n📊 CURRENT PRICES:\n')
                
                for item in data['data']:
                    d = item.get('d', [])
                    if len(d) >= 2:
                        symbol = d[0]  # Symbol name
                        price = d[1]   # Close price
                        change = d[2]  # Change %
                        
                        # Extract base currency (remove USD suffix)
                        if 'USD' in symbol:
                            base = symbol.replace('USD', '').replace('COINBASE:', '')
                            prices[base] = price
                            
                            if price > 100:
                                print(f'{base:<6}: ${price:>10,.2f} ({change:+.2f}%)')
                            else:
                                print(f'{base:<6}: ${price:>10.4f} ({change:+.2f}%)')
                
                print('\n' + '-' * 70)
                return prices
            else:
                print("No data returned")
                
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching prices: {e}")
    
    return {}

def value_portfolio(holdings, prices):
    """Calculate portfolio value using TradingView prices"""
    
    print('\n💼 PORTFOLIO VALUATION:')
    print('-' * 70)
    
    total = 0
    valued = []
    
    for asset, amount in holdings.items():
        if asset in ['USD', 'USDC']:
            value = amount
            price = 1.0
        elif asset in prices:
            price = prices[asset]
            value = amount * price
        else:
            print(f'⚠️  No price found for {asset}')
            continue
            
        if value > 0.01:
            valued.append((asset, amount, price, value))
            total += value
    
    # Sort by value
    valued.sort(key=lambda x: x[3], reverse=True)
    
    print(f'{"Asset":<8} {"Amount":>12} {"Price":>10} {"Value":>12}')
    print('-' * 70)
    
    for asset, amount, price, value in valued:
        if asset in ['USD', 'USDC']:
            print(f'{asset:<8} {amount:>12.2f} {"$1.00":>10} ${value:>11,.2f}')
        else:
            if price > 100:
                print(f'{asset:<8} {amount:>12.6f} ${price:>9,.2f} ${value:>11,.2f}')
            else:
                print(f'{asset:<8} {amount:>12.6f} ${price:>9.4f} ${value:>11,.2f}')
    
    print('-' * 70)
    print(f'{"TOTAL":<8} {"":<12} {"":<10} ${total:>11,.2f}')
    print('=' * 70)
    
    return total

if __name__ == "__main__":
    # Get live prices
    prices = get_crypto_prices()
    
    if prices:
        print('\n📋 Enter your holdings to calculate portfolio value.')
        print('   Or update the script with your actual positions.\n')
        
        # Example holdings - UPDATE WITH YOUR ACTUAL AMOUNTS
        my_holdings = {
            'BTC': 0.0,    # Update with your amount
            'ETH': 0.0,    # Update with your amount
            'SOL': 0.0,    # Update with your amount
            'XRP': 0.0,    # Update with your amount
            'USD': 201.42,
            'USDC': 215.02
        }
        
        # Calculate total
        total = value_portfolio(my_holdings, prices)
        
        # Compare with known total
        known_total = 30609.76
        difference = known_total - total
        
        if abs(difference) > 100:
            print(f'\n📊 RECONCILIATION:')
            print(f'   Known Total: ${known_total:,.2f}')
            print(f'   Calculated:  ${total:,.2f}')
            print(f'   Difference:  ${difference:,.2f}')
            print(f'\n   ℹ️  Update holdings above with actual amounts\!')
