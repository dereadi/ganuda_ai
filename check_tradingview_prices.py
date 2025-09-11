#!/usr/bin/env python3
"""
Check current prices from TradingView data
"""

import requests
import json

def get_crypto_prices():
    """Get current crypto prices"""
    # Try to get real prices from CoinGecko API (free tier)
    try:
        import time
        base_url = "https://api.coingecko.com/api/v3/simple/price"
        ids = "bitcoin,ethereum,solana,ripple,dogecoin,chainlink,matic-network,avalanche-2"
        params = f"?ids={ids}&vs_currencies=usd"
        
        response = requests.get(base_url + params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'BTC': data.get('bitcoin', {}).get('usd', 59284.50),
                'ETH': data.get('ethereum', {}).get('usd', 2598.75),
                'SOL': data.get('solana', {}).get('usd', 150.01),
                'XRP': data.get('ripple', {}).get('usd', 0.5521),
                'DOGE': data.get('dogecoin', {}).get('usd', 0.10124),
                'LINK': data.get('chainlink', {}).get('usd', 10.82),
                'MATIC': data.get('matic-network', {}).get('usd', 0.3925),
                'AVAX': data.get('avalanche-2', {}).get('usd', 23.45)
            }
    except:
        pass
    
    # Fallback to recent known prices if API fails
    prices = {
        'BTC': 59284.50,
        'ETH': 2598.75,
        'SOL': 150.01,
        'XRP': 0.5521,
        'DOGE': 0.10124,
        'LINK': 10.82,
        'MATIC': 0.3925,
        'AVAX': 23.45
    }
    
    return prices

def calculate_portfolio_value():
    """Calculate current portfolio value"""
    positions = {
        'XRP': 35.67095800,
        'DOGE': 1568.90000000,
        'LINK': 0.38000000,
        'MATIC': 8519.50000000,
        'AVAX': 87.55769424,
        'SOL': 15.60480121,
        'ETH': 0.44080584,
        'BTC': 0.02859213
    }
    
    prices = get_crypto_prices()
    
    total_value = 17.96  # USD balance
    
    print("📊 CURRENT PORTFOLIO VALUE:")
    print("=" * 50)
    
    for coin, amount in positions.items():
        if coin in prices:
            value = amount * prices[coin]
            total_value += value
            print(f"🪙 {coin}: {amount:.8f} @ ${prices[coin]:.4f} = ${value:.2f}")
    
    print("=" * 50)
    print(f"💰 TOTAL VALUE: ${total_value:.2f}")
    
    # Compare to deposits
    deposited = 10229.61
    pnl = total_value - deposited
    pnl_pct = (pnl / deposited) * 100
    
    print(f"📈 P&L: ${pnl:.2f} ({pnl_pct:.1f}%)")
    
    return total_value

if __name__ == "__main__":
    calculate_portfolio_value()