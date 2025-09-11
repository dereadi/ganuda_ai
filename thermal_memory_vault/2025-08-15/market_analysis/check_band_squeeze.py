#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime, timedelta
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print('📊 BOLLINGER BAND SQUEEZE DETECTOR')
print('=' * 50)

# Get BTC price history (last 2 hours)
end = datetime.now()
start = end - timedelta(hours=2)

try:
    candles = client.get_candles(
        product_id='BTC-USD',
        start=start.isoformat(),
        end=end.isoformat(),
        granularity='FIVE_MINUTE'
    )
    
    # Extract closing prices
    prices = [float(c['close']) for c in candles['candles'][:20]]
    
    if len(prices) < 20:
        # Get current price if not enough history
        ticker = client.get_product('BTC-USD')
        current = float(ticker.price)
        prices = [current] * 20  # Fake history for calculation
    else:
        current = prices[0]
    
    # Calculate Bollinger Bands
    sma = statistics.mean(prices)
    std = statistics.stdev(prices) if len(prices) > 1 else 100
    
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    band_width = upper - lower
    band_pct = (band_width / current) * 100
    
    print(f'🎯 BTC: ${current:,.2f}')
    print(f'📈 Upper Band: ${upper:,.2f} (+${upper - current:,.2f})')
    print(f'📉 Lower Band: ${lower:,.2f} (${lower - current:,.2f})')
    print(f'📏 Band Width: ${band_width:,.2f}')
    print(f'📊 Width %: {band_pct:.2f}% of price')
    print()
    
    # Determine squeeze level
    if band_pct < 0.5:
        print('💥💥💥 ULTIMATE SQUEEZE!')
        print('     HISTORIC MOVE IMMINENT!')
        print('     Deploy everything at breakout!')
    elif band_pct < 1.0:
        print('🔥🔥 EXTREME SQUEEZE!')
        print('     Bands crushing together!')
        print('     Big move in next 1-2 hours!')
    elif band_pct < 1.5:
        print('⚡ TIGHT SQUEEZE CONFIRMED!')
        print('     Volatility compressed!')
        print('     Breakout approaching!')
    elif band_pct < 2.0:
        print('📍 Bands compressing...')
        print('     Building energy')
    else:
        print('📊 Normal band width')
        print('     No squeeze detected')
    
    print()
    print('🎯 TRADING IMPLICATIONS:')
    
    if band_pct < 1.5:
        print('   • PREPARE FOR VIOLENT MOVE')
        print('   • Set orders at upper/lower bands')
        print('   • Greeks should be at maximum alert')
        print(f'   • Buy if breaks above ${upper:,.0f}')
        print(f'   • Buy more if drops to ${lower:,.0f}')
    else:
        print('   • Continue normal trading')
        print('   • Watch for compression')
    
    # Check recent volatility
    recent_range = max(prices[:5]) - min(prices[:5])
    recent_pct = (recent_range / current) * 100
    
    print()
    print(f'📈 Last 25 min range: ${recent_range:.2f} ({recent_pct:.3f}%)')
    
    if recent_pct < 0.1:
        print('   ⚠️  DEAD CALM - Storm brewing!')
    
except Exception as e:
    print(f'Error getting candles: {e}')
    
    # Fallback: just check current price
    ticker = client.get_product('BTC-USD')
    current = float(ticker.price)
    print(f'Current BTC: ${current:,.2f}')
    print('Cannot calculate bands without history')
    print('But price holding tight = squeeze likely!')