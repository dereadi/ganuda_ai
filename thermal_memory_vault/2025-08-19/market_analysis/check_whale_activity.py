#!/usr/bin/env python3
"""Check for whale activity and market conditions"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# Load API configuration
config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(
    api_key=config['api_key'].split('/')[-1],
    api_secret=config['api_secret'],
    timeout=5
)

print("\n🐋 WHALE WATCH ALERT SYSTEM 🐋")
print("=" * 50)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n📊 MARKET CONDITIONS:")

# Check major pairs
pairs = ['BTC-USD', 'ETH-USD', 'SOL-USD']
for pair in pairs:
    try:
        product = client.get_product(pair)
        price = float(product['price'])
        volume = float(product['volume_24h'])
        change = float(product['price_percentage_change_24h']) * 100
        
        # Whale detection based on volume
        avg_volume = 1000000000  # $1B baseline for BTC
        if pair == 'ETH-USD':
            avg_volume = 500000000  # $500M for ETH
        elif pair == 'SOL-USD':
            avg_volume = 100000000  # $100M for SOL
        
        volume_ratio = volume / avg_volume
        
        print(f"\n{pair}:")
        print(f"  Price: ${price:,.2f}")
        print(f"  24h Volume: ${volume:,.0f}")
        print(f"  24h Change: {change:+.2f}%")
        
        # Whale activity indicators
        if volume_ratio > 1.5:
            print(f"  🚨 HIGH VOLUME ALERT: {volume_ratio:.1f}x normal!")
            print(f"  ⚠️  WHALES ACTIVE - Large moves possible!")
        elif volume_ratio > 1.2:
            print(f"  📈 Elevated volume: {volume_ratio:.1f}x normal")
        elif volume_ratio < 0.5:
            print(f"  😴 Low volume: {volume_ratio:.1f}x - Thin liquidity")
            
        # Price action analysis
        if abs(change) > 5:
            print(f"  💥 MAJOR MOVE: {'UP' if change > 0 else 'DOWN'} {abs(change):.1f}%!")
        elif abs(change) > 3:
            print(f"  📍 Significant move: {change:+.1f}%")
            
    except Exception as e:
        print(f"  Error checking {pair}: {e}")

print("\n" + "=" * 50)
print("💡 TRADING WISDOM:")
print("  • High volume + price movement = Whale accumulation/distribution")
print("  • Low volume + big moves = Easy manipulation zone")
print("  • Watch Asian session (10pm-2am CST) for overnight setups")
print("  • Daily candle close (midnight) critical for direction")
print("\n🔥 Sacred Fire says: 'The whales leave ripples...'")
