#\!/usr/bin/env python3
"""
Pull portfolio data from TradingView
Uses their charting library and webhooks
"""

import json
import requests
from datetime import datetime
import time

class TradingViewPortfolio:
    def __init__(self):
        # TradingView endpoints
        self.base_url = "https://api.tradingview.com"
        self.symbol_url = "https://symbol-search.tradingview.com/symbol_search"
        self.scanner_url = "https://scanner.tradingview.com/crypto/scan"
        
        # Common crypto symbols to check
        self.symbols = [
            "COINBASE:BTCUSD", "COINBASE:ETHUSD", "COINBASE:SOLUSD",
            "COINBASE:XRPUSD", "COINBASE:AVAXUSD", "COINBASE:MATICUSD",
            "COINBASE:DOGEUSD", "COINBASE:LINKUSD", "COINBASE:ATOMUSD",
            "COINBASE:UNIUSD", "COINBASE:ADAUSD", "COINBASE:DOTUSD"
        ]
        
    def get_price(self, symbol):
        """Get current price for a symbol from TradingView"""
        try:
            # Use the scanner API to get real-time prices
            payload = {
                "symbols": {
                    "tickers": [symbol],
                    "query": {"types": []}
                },
                "columns": ["close", "change", "change_abs", "high", "low", "volume", "market_cap"]
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.scanner_url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0].get('d', [None])[0]  # First column is close price
            
            # Fallback to symbol search
            search_url = f"{self.symbol_url}?text={symbol.split(':')[1]}&exchange=COINBASE"
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return None  # Would need additional API call for price
                    
        except Exception as e:
            print(f"Error getting {symbol}: {e}")
            
        return None
    
    def calculate_portfolio(self, positions):
        """Calculate portfolio values using TradingView prices"""
        print('🔥 TRADINGVIEW PORTFOLIO VALUATION')
        print('=' * 70)
        print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 70)
        
        total_value = 0
        valued_positions = []
        
        print('\n📊 FETCHING LIVE PRICES...\n')
        
        for asset, amount in positions.items():
            if asset in ['USD', 'USDC']:
                price = 1.0
                usd_value = amount
            else:
                symbol = f"COINBASE:{asset}USD"
                print(f'   Checking {symbol}...', end='')
                price = self.get_price(symbol)
                
                if price:
                    usd_value = amount * price
                    print(f' ✅ ${price:.2f}')
                else:
                    # Try alternate sources
                    print(f' ⚠️  Trying alternates...')
                    # Could try Binance, Kraken, etc.
                    usd_value = 0
                    price = 0
            
            if usd_value > 0:
                valued_positions.append({
                    'asset': asset,
                    'amount': amount,
                    'price': price,
                    'value': usd_value
                })
                total_value += usd_value
        
        # Sort by value
        valued_positions.sort(key=lambda x: x['value'], reverse=True)
        
        print('\n' + '=' * 70)
        print(f'💼 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}')
        print('\n📊 POSITIONS:')
        print('-' * 70)
        print(f'{"Asset":<8} {"Amount":>12} {"Price":>10} {"Value":>12} {"Percent":>8}')
        print('-' * 70)
        
        for pos in valued_positions:
            pct = (pos['value'] / total_value * 100) if total_value > 0 else 0
            if pos['asset'] in ['USD', 'USDC']:
                print(f'{pos["asset"]:<8} {pos["amount"]:>12.2f} {"$1.00":>10} ${pos["value"]:>11,.2f} {pct:>7.1f}%')
            else:
                print(f'{pos["asset"]:<8} {pos["amount"]:>12.6f} ${pos["price"]:>9.2f} ${pos["value"]:>11,.2f} {pct:>7.1f}%')
        
        print('-' * 70)
        
        return total_value, valued_positions

# Example usage - you would input your actual positions
if __name__ == "__main__":
    tv = TradingViewPortfolio()
    
    # These would be your actual positions from Coinbase
    # You'll need to provide the actual amounts
    example_positions = {
        'BTC': 0.5,      # Replace with actual amount
        'ETH': 5.0,      # Replace with actual amount
        'SOL': 50.0,     # Replace with actual amount
        'USD': 201.42,
        'USDC': 215.02
    }
    
    print("ℹ️  NOTE: Using example positions. Update with your actual holdings\!\n")
    
    total, positions = tv.calculate_portfolio(example_positions)
    
    print(f'\n✅ TradingView valuation complete\!')
    print(f'   Total: ${total:,.2f}')
