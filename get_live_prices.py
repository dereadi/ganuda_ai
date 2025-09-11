#\!/usr/bin/env python3
"""
Get live crypto prices to value your portfolio
"""

import json
import requests
from datetime import datetime

def get_prices_from_coinbase():
    """Get prices directly from Coinbase public API"""
    
    print('🔥 FETCHING LIVE PRICES FROM COINBASE')
    print('=' * 70)
    
    prices = {}
    
    # List of cryptocurrencies to check
    cryptos = ['BTC', 'ETH', 'SOL', 'XRP', 'AVAX', 'MATIC', 'DOGE', 
               'LINK', 'ATOM', 'UNI', 'ADA', 'DOT', 'LTC', 'BCH']
    
    base_url = "https://api.coinbase.com/v2/exchange-rates"
    
    try:
        # Get all rates at once
        response = requests.get(f"{base_url}?currency=USD", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get('data', {}).get('rates', {})
            
            print('\n📊 CURRENT PRICES (USD):\n')
            
            for crypto in cryptos:
                if crypto in rates:
                    # Rates are inverted (1 USD = X crypto), so we invert back
                    rate = float(rates[crypto])
                    if rate > 0:
                        price = 1.0 / rate
                        prices[crypto] = price
                        
                        if price > 1000:
                            print(f'{crypto:<6}: ${price:>12,.2f}')
                        elif price > 1:
                            print(f'{crypto:<6}: ${price:>12.2f}')
                        else:
                            print(f'{crypto:<6}: ${price:>12.4f}')
            
            print('\n' + '-' * 70)
            
    except Exception as e:
        print(f"Error: {e}")
    
    return prices

def calculate_portfolio_value(prices):
    """Calculate portfolio value with known cash and estimated crypto"""
    
    print('\n💼 PORTFOLIO CALCULATION:')
    print('-' * 70)
    
    # Known values
    known_total = 30609.76
    cash_total = 416.45  # USD + USDC
    crypto_total = known_total - cash_total  # ~30,193
    
    print(f'Known Total:     ${known_total:>12,.2f}')
    print(f'Known Cash:      ${cash_total:>12,.2f}')
    print(f'Crypto Value:    ${crypto_total:>12,.2f}')
    print('-' * 70)
    
    # Since we don't know exact holdings, show what combinations could make ~$30,193
    print('\n🎯 POSSIBLE PORTFOLIO COMPOSITIONS:')
    print('(To reach ~$30,193 in crypto)')
    print('-' * 70)
    
    if 'BTC' in prices and 'ETH' in prices:
        btc_price = prices['BTC']
        eth_price = prices['ETH']
        sol_price = prices.get('SOL', 200)
        
        # Example composition 1: BTC heavy
        btc_amount = 0.2
        btc_value = btc_amount * btc_price
        remaining = crypto_total - btc_value
        eth_amount = remaining / eth_price
        
        print(f'\nOption 1 (BTC Heavy):')
        print(f'  BTC: {btc_amount:.4f} = ${btc_value:,.2f}')
        print(f'  ETH: {eth_amount:.4f} = ${remaining:,.2f}')
        
        # Example composition 2: Balanced
        btc_value2 = crypto_total * 0.4  # 40% BTC
        eth_value2 = crypto_total * 0.35  # 35% ETH
        sol_value2 = crypto_total * 0.25  # 25% SOL
        
        print(f'\nOption 2 (Balanced):')
        print(f'  BTC: {btc_value2/btc_price:.4f} = ${btc_value2:,.2f} (40%)')
        print(f'  ETH: {eth_value2/eth_price:.4f} = ${eth_value2:,.2f} (35%)')
        print(f'  SOL: {sol_value2/sol_price:.2f} = ${sol_value2:,.2f} (25%)')
        
        # Example composition 3: ETH heavy
        eth_amount3 = 5.0
        eth_value3 = eth_amount3 * eth_price
        remaining3 = crypto_total - eth_value3
        
        print(f'\nOption 3 (ETH Heavy):')
        print(f'  ETH: {eth_amount3:.4f} = ${eth_value3:,.2f}')
        print(f'  Others: ${remaining3:,.2f}')
    
    print('\n' + '=' * 70)
    print('\n📝 To get exact holdings:')
    print('   1. Check your Coinbase app/website')
    print('   2. Note each crypto amount')
    print('   3. Update the specialists with real positions')

if __name__ == "__main__":
    prices = get_prices_from_coinbase()
    
    if prices:
        calculate_portfolio_value(prices)
        
        # Save prices for other scripts
        with open('/tmp/current_prices.json', 'w') as f:
            json.dump(prices, f)
            print(f'\n💾 Prices saved to /tmp/current_prices.json')
