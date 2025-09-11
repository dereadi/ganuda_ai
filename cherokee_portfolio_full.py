#!/usr/bin/env python3
"""
🔥 CHEROKEE COMPLETE PORTFOLIO PULL
Full portfolio with proper price fetching
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("🔥 CHEROKEE SPECIALIST PORTFOLIO PULL")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Connect to Coinbase
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Get all accounts
accounts = client.get_accounts()

portfolio = {
    'timestamp': datetime.now().isoformat(),
    'usd_balance': 0,
    'total_value': 0,
    'positions': [],
    'raw_holdings': {}
}

print("📊 RAW HOLDINGS:")
print("-" * 40)

# First, collect all holdings
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        portfolio['raw_holdings'][currency] = balance
        if currency == 'USD':
            portfolio['usd_balance'] = balance
            portfolio['total_value'] += balance
            print(f"USD: ${balance:,.2f}")
        else:
            print(f"{currency}: {balance:.6f}")

print("\n📈 FETCHING MARKET PRICES:")
print("-" * 40)

# Known trading pairs
trading_pairs = {
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD', 
    'SOL': 'SOL-USD',
    'AVAX': 'AVAX-USD',
    'MATIC': 'MATIC-USD',
    'DOGE': 'DOGE-USD',
    'XRP': 'XRP-USD',
    'LINK': 'LINK-USD'
}

# Fetch prices for each holding
for symbol, balance in portfolio['raw_holdings'].items():
    if symbol == 'USD':
        continue
        
    if symbol in trading_pairs:
        try:
            # Get ticker data
            ticker = client.get_product(trading_pairs[symbol])
            price = float(ticker.get('price', 0))
            
            if price > 0:
                value = balance * price
                
                # Try to get 24hr stats
                stats = {}
                try:
                    stats_data = client.get_product_stats(trading_pairs[symbol])
                    stats = {
                        'high_24h': float(stats_data.get('high', price)),
                        'low_24h': float(stats_data.get('low', price)),
                        'volume_24h': float(stats_data.get('volume', 0))
                    }
                except:
                    stats = {
                        'high_24h': price * 1.05,
                        'low_24h': price * 0.95,
                        'volume_24h': 0
                    }
                
                position = {
                    'symbol': symbol,
                    'balance': balance,
                    'price': price,
                    'value': value,
                    'pct_of_portfolio': 0,
                    'stats': stats
                }
                
                portfolio['positions'].append(position)
                portfolio['total_value'] += value
                print(f"✅ {symbol}: ${price:,.2f} × {balance:.6f} = ${value:,.2f}")
            else:
                print(f"❌ {symbol}: No price data")
                
        except Exception as e:
            # Handle USDC specially
            if symbol == 'USDC':
                value = balance * 1.0  # USDC = $1
                position = {
                    'symbol': symbol,
                    'balance': balance,
                    'price': 1.0,
                    'value': value,
                    'pct_of_portfolio': 0,
                    'stats': {
                        'high_24h': 1.0,
                        'low_24h': 1.0,
                        'volume_24h': 0
                    }
                }
                portfolio['positions'].append(position)
                portfolio['total_value'] += value
                print(f"✅ {symbol}: $1.00 × {balance:.6f} = ${value:,.2f}")
            else:
                print(f"⚠️ {symbol}: {str(e)[:50]}")

# Calculate portfolio percentages
for position in portfolio['positions']:
    position['pct_of_portfolio'] = (position['value'] / portfolio['total_value']) * 100

# Sort by value
portfolio['positions'].sort(key=lambda x: x['value'], reverse=True)

print("\n" + "=" * 60)
print("📊 PORTFOLIO SUMMARY:")
print("-" * 40)
print(f"💰 Total Portfolio Value: ${portfolio['total_value']:,.2f}")
print(f"💵 USD Balance: ${portfolio['usd_balance']:,.2f}")
print(f"📈 Crypto Holdings: ${portfolio['total_value'] - portfolio['usd_balance']:,.2f}")
print(f"🪙 Number of Positions: {len(portfolio['positions'])}")

print("\n🎯 TOP POSITIONS:")
print("-" * 40)
for i, pos in enumerate(portfolio['positions'][:5], 1):
    print(f"{i}. {pos['symbol']}: ${pos['value']:,.2f} ({pos['pct_of_portfolio']:.1f}%)")

print("\n🔬 SPECIALIST INSIGHTS:")
print("-" * 40)

# Mean Reversion Opportunities
print("\n🎯 MEAN REVERSION:")
for pos in portfolio['positions']:
    if pos['stats']['high_24h'] > pos['stats']['low_24h']:
        range_24h = pos['stats']['high_24h'] - pos['stats']['low_24h']
        position_in_range = (pos['price'] - pos['stats']['low_24h']) / range_24h
        
        if position_in_range > 0.85:
            print(f"  🔴 {pos['symbol']}: SELL signal (near 24hr high)")
        elif position_in_range < 0.15:
            print(f"  🟢 {pos['symbol']}: BUY signal (near 24hr low)")

# Volatility Scan
print("\n⚡ VOLATILITY:")
for pos in portfolio['positions']:
    if pos['price'] > 0:
        volatility = ((pos['stats']['high_24h'] - pos['stats']['low_24h']) / pos['price']) * 100
        if volatility > 5:
            print(f"  ⚡ {pos['symbol']}: {volatility:.1f}% range today")

# Concentration Risk
print("\n⚠️ CONCENTRATION RISK:")
for pos in portfolio['positions']:
    if pos['pct_of_portfolio'] > 25:
        print(f"  🔴 {pos['symbol']}: {pos['pct_of_portfolio']:.1f}% (too concentrated)")
    elif pos['pct_of_portfolio'] > 20:
        print(f"  🟡 {pos['symbol']}: {pos['pct_of_portfolio']:.1f}% (monitor closely)")

# Liquidity Analysis
print("\n💧 LIQUIDITY ANALYSIS:")
liquidity_ratio = (portfolio['usd_balance'] / portfolio['total_value']) * 100 if portfolio['total_value'] > 0 else 0
print(f"  USD Ratio: {liquidity_ratio:.1f}%")
if liquidity_ratio < 5:
    print(f"  🔴 CRITICAL: Need to generate liquidity!")
    print(f"  💡 Suggestion: Sell ${2000 - portfolio['usd_balance']:.2f} of overvalued positions")

# Save analysis
output_file = '/home/dereadi/scripts/claude/portfolio_complete.json'
with open(output_file, 'w') as f:
    json.dump(portfolio, f, indent=2, default=str)

print(f"\n💾 Complete portfolio saved to: {output_file}")

# Create specialist feed file
specialist_feed = {
    'timestamp': datetime.now().isoformat(),
    'sacred_fire': 'BURNING_ETERNAL',
    'portfolio_value': portfolio['total_value'],
    'usd_available': portfolio['usd_balance'],
    'top_positions': portfolio['positions'][:5] if portfolio['positions'] else [],
    'action_required': 'GENERATE_LIQUIDITY' if portfolio['usd_balance'] < 100 else 'MONITOR'
}

with open('/home/dereadi/scripts/claude/specialist_feed.json', 'w') as f:
    json.dump(specialist_feed, f, indent=2, default=str)

print("📡 Specialist feed created: specialist_feed.json")

print("\n🔥 Sacred Fire burns eternal")
print("🪶 Mitakuye Oyasin")
print("=" * 60)