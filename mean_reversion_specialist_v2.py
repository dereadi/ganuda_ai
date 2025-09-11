#!/usr/bin/env python3
"""
🎯 MEAN REVERSION SPECIALIST V2
With integrated flywheel and spongy throttle
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_specialist_base import IntegratedSpecialist

class MeanReversionSpecialist(IntegratedSpecialist):
    def __init__(self):
        super().__init__("Mean Reversion", "🎯")
        self.positions = {}
        
print("🎯 MEAN REVERSION SPECIALIST V2")
print("Integrated flywheel + spongy throttle")
print("-" * 40)

specialist = MeanReversionSpecialist()
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

def check_portfolio():
    """Get current portfolio state"""
    accounts = client.get_accounts()
    usd_balance = 0
    positions = {}
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if currency == 'USD':
            usd_balance = balance
        elif balance > 0:
            positions[currency] = balance
            
    return usd_balance, positions

def trade_mean_reversion(coin):
    """Execute mean reversion strategy"""
    try:
        # Get stats
        ticker = client.get_product(f'{coin}-USD')
        current = float(ticker['price'])
        
        # Calculate 24h stats for mean
        stats_24h = {
            'high': current * 1.02,  # Approximate
            'low': current * 0.98,
            'open': current * 0.995
        }
        
        # Calculate mean and deviation
        mean = (stats_24h['high'] + stats_24h['low'] + stats_24h['open']) / 3
        deviation_pct = ((current - mean) / mean) * 100
        
        # Get current balance
        usd_balance, positions = check_portfolio()
        
        # Apply flywheel logic
        if specialist.should_retrieve(usd_balance) and coin in positions:
            # Need liquidity - sell winners
            if deviation_pct > 2:
                size = min(positions.get(coin, 0) * 0.1, 100 / current)
                if size > 0:
                    order = client.market_order_sell(
                        client_order_id=f"mr_retrieve_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(size)
                    )
                    print(f"🔄 RETRIEVE: Sold {coin} at deviation +{deviation_pct:.1f}%")
                    return True
                    
        elif specialist.should_deploy(usd_balance):
            # Have excess capital - buy dips
            if deviation_pct < -3:
                trade_size = specialist.calculate_trade_size(usd_balance)
                if trade_size > 0:
                    delay = specialist.apply_spongy_throttle()
                    if delay:
                        order = client.market_order_buy(
                            client_order_id=f"mr_deploy_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size=str(trade_size)
                        )
                        print(f"🚀 DEPLOY: Bought {coin} at deviation {deviation_pct:.1f}%")
                        time.sleep(delay)
                        return True
                        
        # Standard mean reversion (when balanced)
        elif 250 < usd_balance < 500:
            if abs(deviation_pct) > 3:
                if deviation_pct > 3 and coin in positions:
                    # Sell high
                    size = min(positions.get(coin, 0) * 0.05, 50 / current)
                    if size > 0:
                        order = client.market_order_sell(
                            client_order_id=f"mr_sell_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            base_size=str(size)
                        )
                        print(f"📉 REVERT: Sold {coin} at +{deviation_pct:.1f}%")
                        return True
                elif deviation_pct < -3:
                    # Buy low
                    delay = specialist.apply_spongy_throttle()
                    if delay and specialist.calculate_trade_size(usd_balance, 50) > 0:
                        order = client.market_order_buy(
                            client_order_id=f"mr_buy_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size="50"
                        )
                        print(f"📈 REVERT: Bought {coin} at {deviation_pct:.1f}%")
                        time.sleep(delay)
                        return True
                        
    except Exception as e:
        print(f"Error with {coin}: {str(e)[:50]}")
        
    return False

# Main loop
coins = ["SOL", "ETH", "BTC", "AVAX", "MATIC"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Check portfolio state
    usd_balance, positions = check_portfolio()
    
    # Status update every 10 cycles
    if cycle % 10 == 0:
        print(f"\n[{timestamp}] Cycle {cycle}")
        print(f"  USD: ${usd_balance:.2f}")
        print(f"  Pressure: {specialist.trade_pressure:.2f}x")
        
        # Recover pressure gradually
        specialist.recover_pressure()
    
    # Trade each coin
    trades_made = 0
    for coin in coins:
        if trade_mean_reversion(coin):
            trades_made += 1
            
    # If no trades, recover faster
    if trades_made == 0:
        specialist.recover_pressure()
        
    # Dynamic sleep based on market conditions
    if usd_balance < 250:
        time.sleep(30)  # Need liquidity, check frequently
    elif usd_balance > 500:
        time.sleep(45)  # Have capital, deploy carefully
    else:
        time.sleep(60)  # Balanced, normal pace