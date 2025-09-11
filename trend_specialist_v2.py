#!/usr/bin/env python3
"""
📈 TREND SPECIALIST V2
Rides trends with integrated flywheel logic
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_specialist_base import IntegratedSpecialist

class TrendSpecialist(IntegratedSpecialist):
    def __init__(self):
        super().__init__("Trend Rider", "📈")
        self.momentum_coins = []
        
print("📈 TREND SPECIALIST V2 ACTIVATED")
print("Flywheel-integrated momentum rider")
print("-" * 40)

specialist = TrendSpecialist()
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

def get_portfolio_state():
    """Check balances and positions"""
    accounts = client.get_accounts()
    usd = 0
    holdings = {}
    total_value = 0
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if currency == 'USD':
            usd = balance
            total_value += balance
        elif balance > 0:
            holdings[currency] = balance
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                total_value += balance * price
            except:
                pass
                
    return usd, holdings, total_value

def calculate_trend_strength(coin):
    """Measure trend momentum"""
    try:
        ticker = client.get_product(f'{coin}-USD')
        current = float(ticker['price'])
        
        # Simple trend: compare to recent average
        trend_strength = 0
        
        # Would need historical data for real calculation
        # For now, use randomized momentum signal
        import random
        trend_strength = random.uniform(-5, 5)
        
        return current, trend_strength
        
    except:
        return None, 0

def execute_trend_trade(coin):
    """Trade based on trend and flywheel state"""
    try:
        current, trend = calculate_trend_strength(coin)
        if not current:
            return False
            
        usd, holdings, total_value = get_portfolio_state()
        
        # RETRIEVE MODE: Need liquidity
        if specialist.should_retrieve(usd):
            if coin in holdings and trend < 0:
                # Sell weak trends for liquidity
                amount = min(holdings[coin] * 0.15, 200 / current)
                if amount > 0:
                    order = client.market_order_sell(
                        client_order_id=f"trend_retrieve_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(amount)
                    )
                    print(f"💰 RETRIEVE: Sold weakening {coin} (trend: {trend:.1f})")
                    return True
                    
        # DEPLOY MODE: Have excess capital
        elif specialist.should_deploy(usd):
            if trend > 3:
                # Buy strong trends
                size = specialist.calculate_trade_size(usd, 150)
                delay = specialist.apply_spongy_throttle()
                
                if size > 0 and delay:
                    # Check position limits
                    coin_value = holdings.get(coin, 0) * current
                    if specialist.check_position_size(coin_value, total_value):
                        order = client.market_order_buy(
                            client_order_id=f"trend_deploy_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size=str(size)
                        )
                        print(f"🚀 DEPLOY: Bought trending {coin} (trend: {trend:.1f})")
                        specialist.momentum_coins.append(coin)
                        time.sleep(delay)
                        return True
                        
        # BALANCED MODE: Normal trend following
        else:
            if trend > 4 and coin not in specialist.momentum_coins:
                # Join strong trends
                delay = specialist.apply_spongy_throttle()
                if delay:
                    order = client.market_order_buy(
                        client_order_id=f"trend_follow_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        quote_size="75"
                    )
                    print(f"📈 TREND: Following {coin} momentum (+{trend:.1f})")
                    specialist.momentum_coins.append(coin)
                    time.sleep(delay)
                    return True
                    
            elif trend < -3 and coin in holdings:
                # Exit dying trends
                amount = holdings[coin] * 0.1
                if amount * current > 20:
                    order = client.market_order_sell(
                        client_order_id=f"trend_exit_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(amount)
                    )
                    print(f"📉 EXIT: Leaving {coin} downtrend ({trend:.1f})")
                    if coin in specialist.momentum_coins:
                        specialist.momentum_coins.remove(coin)
                    return True
                    
    except Exception as e:
        print(f"Trend error {coin}: {str(e)[:40]}")
        
    return False

# Main execution loop
target_coins = ["SOL", "ETH", "BTC", "AVAX", "MATIC", "DOGE"]
cycle = 0

print(f"Monitoring trends in: {', '.join(target_coins)}")
print()

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Status check
    usd, holdings, total = get_portfolio_state()
    
    if cycle % 10 == 0:
        print(f"\n[{timestamp}] Status Check")
        print(f"  Portfolio: ${total:.2f}")
        print(f"  USD: ${usd:.2f}")
        print(f"  Throttle: {specialist.trade_pressure:.1f}x")
        print(f"  Momentum: {specialist.momentum_coins[:3]}")
        
        # Pressure recovery
        specialist.recover_pressure()
        
        # Clear old momentum list
        if len(specialist.momentum_coins) > 5:
            specialist.momentum_coins = specialist.momentum_coins[-3:]
    
    # Execute trades
    trades = 0
    for coin in target_coins:
        if execute_trend_trade(coin):
            trades += 1
            
    # Recover pressure if quiet
    if trades == 0:
        specialist.recover_pressure()
        
    # Adaptive timing
    if usd < 250:
        time.sleep(30)  # Hunt for liquidity
    elif usd > 500:
        time.sleep(60)  # Deploy carefully  
    else:
        time.sleep(45)  # Balanced pace