#!/usr/bin/env python3
import json
import urllib.request

try:
    # Get current BTC price
    url = 'https://api.coinbase.com/v2/exchange-rates?currency=BTC'
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        btc_price = float(data['data']['rates']['USD'])
        print(f'🔥 Current BTC Price: ${btc_price:,.2f}')
        
        # Check distance from targets
        buy_target = 113835
        sell_target = 113845
        
        distance_to_buy = btc_price - buy_target
        distance_to_sell = sell_target - btc_price
        
        print(f'')
        print(f'📊 Oscillation Zone Analysis:')
        print(f'  Buy Target: ${buy_target:,}')
        print(f'  Current: ${btc_price:,.2f}')
        print(f'  Sell Target: ${sell_target:,}')
        print(f'')
        
        if btc_price < buy_target:
            print(f'  ⬇️ ${abs(distance_to_buy):,.2f} below buy zone - APPROACHING BUY')
        elif btc_price > sell_target:
            print(f'  ⬆️ ${distance_to_buy:,.2f} above sell zone - APPROACHING SELL')
        else:
            print(f'  ✅ IN OSCILLATION ZONE! Perfect for trading')
            
        print(f'')
        print(f'💡 Strategy: Buy at ${buy_target:,}, Sell at ${sell_target:,}')
        print(f'💰 Profit per cycle: $10')
        print(f'🔄 Expected: 6 cycles/hour = $60/hour')
        
except Exception as e:
    print(f'Error getting BTC price: {e}')