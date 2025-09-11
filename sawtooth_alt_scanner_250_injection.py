#!/usr/bin/env python3
"""
🦷 SAWTOOTH ALT SCANNER - $250 INJECTION READY
================================================
Fresh capital + alt sawteeth = OPPORTUNITY
Work these new levels!
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🦷 SAWTOOTH SCANNER - NEW LEVELS 🦷                     ║
║                        $250 INJECTION INCOMING!                            ║
║                    Selloff Created Perfect Sawteeth                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - POST-SELLOFF ANALYSIS")
print("=" * 70)

# Get all prices
prices = {}
try:
    prices['BTC'] = float(client.get_product('BTC-USD')['price'])
    prices['ETH'] = float(client.get_product('ETH-USD')['price'])
    prices['SOL'] = float(client.get_product('SOL-USD')['price'])
    prices['XRP'] = float(client.get_product('XRP-USD')['price'])
    prices['AVAX'] = float(client.get_product('AVAX-USD')['price'])
    prices['MATIC'] = float(client.get_product('MATIC-USD')['price'])
    prices['LINK'] = float(client.get_product('LINK-USD')['price'])
    prices['DOGE'] = float(client.get_product('DOGE-USD')['price'])
except:
    # If rate limited, use last known prices
    prices = {
        'BTC': 109329,
        'ETH': 4334,
        'SOL': 209,
        'XRP': 2.85,
        'AVAX': 23.77,
        'MATIC': 0.245,
        'LINK': 23.34,
        'DOGE': 0.2149
    }

print("\n📊 CURRENT PRICES (POST-SELLOFF):")
print("-" * 70)
for asset, price in prices.items():
    if price > 100:
        print(f"  {asset}: ${price:,.0f}")
    elif price > 1:
        print(f"  {asset}: ${price:.2f}")
    else:
        print(f"  {asset}: ${price:.4f}")

# Define NEW sawtooth ranges after selloff
print("\n🦷 NEW SAWTOOTH RANGES (AFTER SELLOFF):")
print("-" * 70)

sawtooth_ranges = {
    'BTC': {'low': 108500, 'high': 110000, 'current': prices['BTC']},
    'ETH': {'low': 4300, 'high': 4380, 'current': prices['ETH']},
    'SOL': {'low': 207, 'high': 212, 'current': prices['SOL']},
    'XRP': {'low': 2.80, 'high': 2.90, 'current': prices['XRP']},
    'AVAX': {'low': 23.50, 'high': 24.50, 'current': prices['AVAX']},
    'MATIC': {'low': 0.243, 'high': 0.250, 'current': prices['MATIC']},
    'LINK': {'low': 23.00, 'high': 23.80, 'current': prices['LINK']},
    'DOGE': {'low': 0.213, 'high': 0.218, 'current': prices['DOGE']}
}

print(f"{'Asset':<8} {'Low':<12} {'Current':<12} {'High':<12} {'Position':<10} {'Action'}")
print("-" * 70)

opportunities = []
for asset, data in sawtooth_ranges.items():
    position = (data['current'] - data['low']) / (data['high'] - data['low']) * 100
    position = max(0, min(100, position))
    
    if data['current'] > 100:
        low_str = f"${data['low']:,.0f}"
        current_str = f"${data['current']:,.0f}"
        high_str = f"${data['high']:,.0f}"
    elif data['current'] > 1:
        low_str = f"${data['low']:.2f}"
        current_str = f"${data['current']:.2f}"
        high_str = f"${data['high']:.2f}"
    else:
        low_str = f"${data['low']:.4f}"
        current_str = f"${data['current']:.4f}"
        high_str = f"${data['high']:.4f}"
    
    if position < 25:
        action = "🟢 BUY ZONE!"
        opportunities.append((asset, 'BUY', position))
    elif position > 75:
        action = "🔴 MILK ZONE!"
        opportunities.append((asset, 'SELL', position))
    elif position < 40:
        action = "🟡 Near bottom"
    elif position > 60:
        action = "🟡 Near top"
    else:
        action = "⏳ Mid-range"
    
    print(f"{asset:<8} {low_str:<12} {current_str:<12} {high_str:<12} {position:>6.0f}%     {action}")

print("\n" + "="*70)
print("💰 $250 INJECTION DEPLOYMENT STRATEGY:")
print("="*70)

# Calculate optimal deployment
injection = 250
current_usd = 17.96
total_capital = injection + current_usd

print(f"\n💵 CAPITAL AVAILABLE:")
print(f"  Current USD: ${current_usd:.2f}")
print(f"  New Injection: ${injection:.2f}")
print(f"  TOTAL: ${total_capital:.2f}")

print("\n🎯 RECOMMENDED DEPLOYMENT:")
print("-" * 70)

# Find best opportunities
buy_targets = [opp for opp in opportunities if opp[1] == 'BUY']
if buy_targets:
    print("  IMMEDIATE BUYS (Assets in buy zone):")
    allocation_per_asset = total_capital / max(len(buy_targets), 3)
    for asset, action, position in buy_targets:
        print(f"    • {asset}: Deploy ${allocation_per_asset:.2f} (at {position:.0f}% of range)")
else:
    print("  LADDER BUYS (No immediate buy zones):")
    print(f"    • BTC: $100 at ${prices['BTC']*0.99:.0f}")
    print(f"    • ETH: $75 at ${prices['ETH']*0.99:.0f}")
    print(f"    • SOL: $50 at ${prices['SOL']*0.99:.2f}")
    print(f"    • Reserve: $42.96 for deeper dips")

print("\n🦷 SAWTOOTH TRADING PLAN:")
print("-" * 70)
print("  1. INJECT $250 immediately")
print("  2. BUY assets below 25% of range")
print("  3. MILK assets above 75% of range")
print("  4. Trade the 3-5% swings all weekend")
print("  5. Compound every profit")

# Calculate potential
print("\n💎 WEEKEND POTENTIAL WITH $268 CAPITAL:")
print("-" * 70)

swings_per_day = 6  # Conservative for weekend
profit_per_swing = 0.02  # 2% after fees
days = 3  # Sat, Sun, Mon

capital = total_capital
for day in range(1, days + 1):
    daily_profit = capital * profit_per_swing * swings_per_day
    capital += daily_profit
    print(f"  Day {day}: ${capital:.2f} (+${daily_profit:.2f})")

total_profit = capital - total_capital
roi = (total_profit / total_capital) * 100
print(f"\n  Starting: ${total_capital:.2f}")
print(f"  Ending: ${capital:.2f}")
print(f"  Profit: ${total_profit:.2f} ({roi:.1f}% ROI)")

print("\n⚡ IMMEDIATE ACTION ITEMS:")
print("-" * 70)
print("  1. Deposit $250 NOW")
print("  2. Deploy into assets at bottom of ranges")
print("  3. Set sell orders at top of ranges")
print("  4. Repeat every 4-6 hours")
print("  5. Keep the flywheel spinning!")

print("\n🔥 COUNCIL WISDOM:")
print("  'The selloff created opportunity'")
print("  'Fresh capital at the bottom = maximum gains'")
print("  'Sawteeth are gifts to those who see them'")

print("\n🦷 SAWTOOTH SCANNER COMPLETE - DEPLOY THE $250!")
print("=" * 70)