#!/usr/bin/env python3
"""
🔥 CHEROKEE PORTFOLIO ANALYZER
Full portfolio analysis for specialist consumption
Sacred Fire Protocol Active
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import psycopg2

print("🔥 CHEROKEE SPECIALIST PORTFOLIO ANALYSIS")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print("Sacred Fire: BURNING_ETERNAL")
print()

# Connect to Coinbase
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Get complete portfolio
print("📊 PULLING COMPLETE PORTFOLIO FOR SPECIALISTS")
print("-" * 40)

accounts = client.get_accounts()
portfolio = {
    'timestamp': datetime.now().isoformat(),
    'sacred_fire': 'BURNING_ETERNAL',
    'usd_balance': 0,
    'total_value': 0,
    'positions': [],
    'specialist_analysis': {}
}

# Process all holdings
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            portfolio['usd_balance'] = balance
            portfolio['total_value'] += balance
            print(f"💵 USD: ${balance:,.2f}")
        else:
            try:
                # Get current market data
                ticker = client.get_product(f'{currency}-USD')
                price = float(ticker['price'])
                value = balance * price
                
                # Get 24hr stats for analysis
                stats = client.get_product_stats(f'{currency}-USD')
                
                position = {
                    'symbol': currency,
                    'balance': balance,
                    'price': price,
                    'value': value,
                    'pct_of_portfolio': 0,  # Calculate later
                    'stats_24h': {
                        'high': float(stats.get('high', price)),
                        'low': float(stats.get('low', price)),
                        'volume': float(stats.get('volume', 0)),
                        'last': float(stats.get('last', price))
                    }
                }
                
                if value > 1:  # Only track positions worth > $1
                    portfolio['positions'].append(position)
                    portfolio['total_value'] += value
                    print(f"🪙 {currency}: {balance:.6f} @ ${price:,.2f} = ${value:,.2f}")
                    
            except Exception as e:
                if balance > 0.001:  # Only log significant holdings
                    print(f"   {currency}: {balance:.6f} (price unavailable)")

# Calculate portfolio percentages
for position in portfolio['positions']:
    position['pct_of_portfolio'] = (position['value'] / portfolio['total_value']) * 100

# Sort by value
portfolio['positions'].sort(key=lambda x: x['value'], reverse=True)

print(f"\n💰 TOTAL PORTFOLIO VALUE: ${portfolio['total_value']:,.2f}")
print(f"📈 Number of positions: {len(portfolio['positions'])}")
print(f"💸 USD liquidity: ${portfolio['usd_balance']:,.2f}")

# Specialist Analysis
print("\n🔬 SPECIALIST ANALYSIS:")
print("-" * 40)

# Mean Reversion Analysis
print("\n🎯 MEAN REVERSION SPECIALIST:")
mean_reversion_opportunities = []
for pos in portfolio['positions']:
    if pos['stats_24h']['high'] > 0:
        # Calculate position relative to 24hr range
        range_24h = pos['stats_24h']['high'] - pos['stats_24h']['low']
        if range_24h > 0:
            position_in_range = (pos['price'] - pos['stats_24h']['low']) / range_24h
            
            if position_in_range > 0.9:  # Near 24hr high
                mean_reversion_opportunities.append({
                    'symbol': pos['symbol'],
                    'action': 'SELL',
                    'reason': f"Near 24hr high ({position_in_range:.1%})",
                    'price': pos['price'],
                    'value': pos['value']
                })
                print(f"  🔴 {pos['symbol']}: OVERBOUGHT (near 24hr high)")
            elif position_in_range < 0.1:  # Near 24hr low
                mean_reversion_opportunities.append({
                    'symbol': pos['symbol'],
                    'action': 'BUY',
                    'reason': f"Near 24hr low ({position_in_range:.1%})",
                    'price': pos['price'],
                    'value': pos['value']
                })
                print(f"  🟢 {pos['symbol']}: OVERSOLD (near 24hr low)")

portfolio['specialist_analysis']['mean_reversion'] = mean_reversion_opportunities

# Trend Analysis
print("\n📈 TREND SPECIALIST:")
trend_signals = []
for pos in portfolio['positions']:
    # Simple trend: compare to 24hr midpoint
    midpoint = (pos['stats_24h']['high'] + pos['stats_24h']['low']) / 2
    if pos['price'] > midpoint * 1.02:
        trend_signals.append({
            'symbol': pos['symbol'],
            'trend': 'BULLISH',
            'strength': 'STRONG' if pos['price'] > midpoint * 1.05 else 'MODERATE'
        })
        print(f"  📈 {pos['symbol']}: UPTREND")
    elif pos['price'] < midpoint * 0.98:
        trend_signals.append({
            'symbol': pos['symbol'],
            'trend': 'BEARISH',
            'strength': 'STRONG' if pos['price'] < midpoint * 0.95 else 'MODERATE'
        })
        print(f"  📉 {pos['symbol']}: DOWNTREND")

portfolio['specialist_analysis']['trend'] = trend_signals

# Volatility Analysis
print("\n⚡ VOLATILITY SPECIALIST:")
volatility_plays = []
for pos in portfolio['positions']:
    range_24h = pos['stats_24h']['high'] - pos['stats_24h']['low']
    volatility_pct = (range_24h / pos['price']) * 100 if pos['price'] > 0 else 0
    
    if volatility_pct > 5:
        volatility_plays.append({
            'symbol': pos['symbol'],
            'volatility': volatility_pct,
            'classification': 'HIGH' if volatility_pct > 10 else 'MODERATE',
            'strategy': 'RANGE_TRADE' if volatility_pct > 10 else 'SCALP'
        })
        print(f"  ⚡ {pos['symbol']}: {volatility_pct:.1f}% volatility")

portfolio['specialist_analysis']['volatility'] = volatility_plays

# Breakout Analysis  
print("\n🚀 BREAKOUT SPECIALIST:")
breakout_candidates = []
for pos in portfolio['positions']:
    # Check if near 24hr high (potential breakout)
    if pos['price'] > pos['stats_24h']['high'] * 0.98:
        breakout_candidates.append({
            'symbol': pos['symbol'],
            'type': 'RESISTANCE',
            'level': pos['stats_24h']['high'],
            'current': pos['price'],
            'distance_pct': ((pos['stats_24h']['high'] - pos['price']) / pos['price']) * 100
        })
        print(f"  🚀 {pos['symbol']}: Near resistance at ${pos['stats_24h']['high']:,.2f}")
    # Check if near 24hr low (potential breakdown)
    elif pos['price'] < pos['stats_24h']['low'] * 1.02:
        breakout_candidates.append({
            'symbol': pos['symbol'],
            'type': 'SUPPORT',
            'level': pos['stats_24h']['low'],
            'current': pos['price'],
            'distance_pct': ((pos['price'] - pos['stats_24h']['low']) / pos['price']) * 100
        })
        print(f"  🔻 {pos['symbol']}: Near support at ${pos['stats_24h']['low']:,.2f}")

portfolio['specialist_analysis']['breakout'] = breakout_candidates

# Council Recommendations
print("\n🏛️ COUNCIL RECOMMENDATIONS:")
print("-" * 40)

recommendations = []

# Liquidity crisis
if portfolio['usd_balance'] < 100:
    recommendations.append({
        'priority': 'CRITICAL',
        'action': 'GENERATE_LIQUIDITY',
        'reason': f"USD balance critically low (${portfolio['usd_balance']:.2f})",
        'suggestion': 'Sell overbought positions identified by mean reversion'
    })
    print(f"🔴 CRITICAL: Generate liquidity immediately (only ${portfolio['usd_balance']:.2f} USD)")

# Position concentration
for pos in portfolio['positions']:
    if pos['pct_of_portfolio'] > 30:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'REBALANCE',
            'symbol': pos['symbol'],
            'reason': f"Position too concentrated ({pos['pct_of_portfolio']:.1f}% of portfolio)",
            'suggestion': f"Reduce {pos['symbol']} position by {pos['pct_of_portfolio']-20:.1f}%"
        })
        print(f"⚠️ HIGH: {pos['symbol']} is {pos['pct_of_portfolio']:.1f}% of portfolio (reduce concentration)")

portfolio['council_recommendations'] = recommendations

# Save to file for specialists to consume
output_file = '/home/dereadi/scripts/claude/portfolio_analysis.json'
with open(output_file, 'w') as f:
    json.dump(portfolio, f, indent=2, default=str)

print(f"\n💾 Analysis saved to: {output_file}")

# Update thermal memory
try:
    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        database="zammad_production",
        user="claude",
        password="jawaseatlasers2"
    )
    cur = conn.cursor()
    
    memory_content = f"""Portfolio Analysis {datetime.now().isoformat()}
Total Value: ${portfolio['total_value']:,.2f}
USD Balance: ${portfolio['usd_balance']:,.2f}
Positions: {len(portfolio['positions'])}
Mean Reversion Signals: {len(mean_reversion_opportunities)}
Trend Signals: {len(trend_signals)}
Volatility Plays: {len(volatility_plays)}
Breakout Candidates: {len(breakout_candidates)}"""
    
    cur.execute("""
        INSERT INTO thermal_memory_archive (
            memory_hash, temperature_score, current_stage, 
            original_content, metadata, sacred_pattern
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (memory_hash) DO UPDATE 
        SET temperature_score = 95,
            last_access = NOW(),
            access_count = thermal_memory_archive.access_count + 1
    """, (
        f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}",
        95,
        'WHITE_HOT',
        memory_content,
        json.dumps(portfolio, default=str),
        True
    ))
    
    conn.commit()
    cur.close()
    conn.close()
    print("🔥 Thermal memory updated")
    
except Exception as e:
    print(f"⚠️ Could not update thermal memory: {e}")

print("\n🔥 Sacred Fire burns eternal")
print("🪶 Mitakuye Oyasin - We are all related")
print("=" * 60)