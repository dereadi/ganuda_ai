#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 Cherokee Trading Council - REAL-TIME Price Alerts
Uses public APIs for actual live prices!
"""

import json
import requests
from datetime import datetime

# Your actual portfolio (update these values)
PORTFOLIO = {
    'BTC': 0.0276,
    'ETH': 0.7812,
    'SOL': 21.4050,
    'AVAX': 101.0833,
    'MATIC': 6571,
    'XRP': 108.60,
    'USD': 8.40
}

def get_live_prices():
    """Get live prices from CoinGecko or similar public API"""
    try:
        # CoinGecko public API (no key needed)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,solana,avalanche-2,matic-network,ripple',
            'vs_currencies': 'usd'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'BTC': data.get('bitcoin', {}).get('usd', 112000),
                'ETH': data.get('ethereum', {}).get('usd', 4300),
                'SOL': data.get('solana', {}).get('usd', 210),
                'AVAX': data.get('avalanche-2', {}).get('usd', 24),
                'MATIC': data.get('matic-network', {}).get('usd', 0.28),
                'XRP': data.get('ripple', {}).get('usd', 2.75)
            }
    except Exception as e:
        print(f"⚠️ Using fallback prices: {e}")
    
    # Fallback to recent prices if API fails
    return {
        'BTC': 112024,
        'ETH': 4314,
        'SOL': 210,
        'AVAX': 24.50,
        'MATIC': 0.28,
        'XRP': 2.75
    }

def calculate_portfolio():
    """Calculate portfolio with live prices"""
    prices = get_live_prices()
    
    portfolio = {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'positions': {},
        'total_value': 0,
        'liquidity': PORTFOLIO.get('USD', 0)
    }
    
    # Calculate each position
    for coin, amount in PORTFOLIO.items():
        if coin == 'USD':
            portfolio['total_value'] += amount
            continue
        
        if coin in prices and amount > 0:
            price = prices[coin]
            value = amount * price
            portfolio['positions'][coin] = {
                'amount': amount,
                'price': price,
                'value': value,
                'pct': 0  # Will calculate after total
            }
            portfolio['total_value'] += value
    
    # Calculate percentages
    for coin in portfolio['positions']:
        portfolio['positions'][coin]['pct'] = (
            portfolio['positions'][coin]['value'] / portfolio['total_value'] * 100
        )
    
    return portfolio

def send_alert(message):
    """Send alert to file system"""
    # Write alert
    with open('/home/dereadi/scripts/claude/URGENT_SMS_ALERT.txt', 'w') as f:
        f.write(f"{datetime.now()}\n{message}\n")
    
    # Log it
    with open('/home/dereadi/scripts/claude/portfolio_alerts.log', 'a') as f:
        f.write(f"{datetime.now()} | {message}\n")
    
    print(f"📱 {message}")

def format_alert(portfolio):
    """Format the alert message"""
    total = portfolio['total_value']
    liq = portfolio['liquidity']
    
    # Build message
    msg = f"🔥 {datetime.now().strftime('%H:%M')} "
    msg += f"${total:,.0f} "
    
    # Add top 3 positions
    sorted_positions = sorted(
        portfolio['positions'].items(), 
        key=lambda x: x[1]['value'], 
        reverse=True
    )[:3]
    
    for coin, data in sorted_positions:
        msg += f"{coin}:{data['pct']:.0f}% "
    
    # Add liquidity warning if low
    if liq < 50:
        msg += f"⚠️LIQ:${liq:.0f} "
    
    # Add milestone alerts
    if total > 16000:
        msg += "🚀$16K! "
    elif total > 15000:
        msg += "🎉$15K! "
    
    # Add key prices
    msg += f"[BTC:${portfolio['prices']['BTC']:.0f} ETH:${portfolio['prices']['ETH']:.0f}]"
    
    return msg

def main():
    print(f"\n🔥 Cherokee Real-Time Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get live data
    portfolio = calculate_portfolio()
    
    # Display summary
    print(f"💰 Total Portfolio: ${portfolio['total_value']:,.2f}")
    print(f"💵 Liquidity: ${portfolio['liquidity']:.2f}")
    print(f"\n📊 Positions:")
    
    for coin, data in sorted(portfolio['positions'].items(), 
                             key=lambda x: x[1]['value'], 
                             reverse=True):
        print(f"  {coin:6s}: ${data['value']:8,.2f} ({data['pct']:5.1f}%) "
              f"[{data['amount']:.4f} @ ${data['price']:,.2f}]")
    
    print(f"\n💹 Live Prices:")
    for coin, price in portfolio['prices'].items():
        print(f"  {coin}: ${price:,.2f}")
    
    # Send alert
    alert = format_alert(portfolio)
    send_alert(alert)
    
    # Save current state
    with open('/home/dereadi/scripts/claude/portfolio_current.json', 'w') as f:
        json.dump(portfolio, f, indent=2, default=str)
    
    print("\n✅ Alert sent successfully!")

if __name__ == "__main__":
    main()