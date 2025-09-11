#!/usr/bin/env python3
"""
⚡ VOLATILITY SPECIALIST V2
Harvests volatility with integrated flywheel
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_specialist_base import IntegratedSpecialist

class VolatilitySpecialist(IntegratedSpecialist):
    def __init__(self):
        super().__init__("Volatility Harvester", "⚡")
        self.high_vol_coins = []
        
print("⚡ VOLATILITY SPECIALIST V2 ACTIVATED")
print("Integrated volatility harvester")
print("-" * 40)

specialist = VolatilitySpecialist()
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

def get_portfolio():
    """Get current portfolio state"""
    accounts = client.get_accounts()
    usd = 0
    holdings = {}
    total = 0
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if currency == 'USD':
            usd = balance
            total += balance
        elif balance > 0:
            holdings[currency] = balance
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                total += balance * price
            except:
                pass
                
    return usd, holdings, total

def calculate_volatility(coin):
    """Calculate current volatility metrics"""
    try:
        ticker = client.get_product(f'{coin}-USD')
        current = float(ticker['price'])
        
        # Approximate daily range (would need real stats)
        high = current * 1.03
        low = current * 0.97
        
        # Calculate volatility
        volatility = ((high - low) / current) * 100
        position_in_range = (current - low) / (high - low) if high != low else 0.5
        
        return current, volatility, position_in_range
        
    except:
        return None, 0, 0.5

def trade_volatility(coin):
    """Trade based on volatility conditions"""
    try:
        current, vol, position = calculate_volatility(coin)
        if not current:
            return False
            
        usd, holdings, total = get_portfolio()
        
        # High volatility environment (>3%)
        if vol > 3:
            specialist.high_vol_coins.append(coin)
            
            # RETRIEVE MODE: Need liquidity
            if specialist.should_retrieve(usd):
                if position > 0.8 and coin in holdings:
                    # Sell at range highs
                    amount = min(holdings[coin] * 0.2, 300 / current)
                    if amount > 0:
                        order = client.market_order_sell(
                            client_order_id=f"vol_retrieve_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            base_size=str(amount)
                        )
                        print(f"💰 VOL-RETRIEVE: Sold {coin} at range high (vol: {vol:.1f}%)")
                        return True
                        
            # DEPLOY MODE: Have capital
            elif specialist.should_deploy(usd):
                if position < 0.2:
                    # Buy at range lows in high vol
                    size = specialist.calculate_trade_size(usd, 150)
                    delay = specialist.apply_spongy_throttle()
                    
                    if size > 0 and delay:
                        coin_value = holdings.get(coin, 0) * current
                        if specialist.check_position_size(coin_value, total):
                            order = client.market_order_buy(
                                client_order_id=f"vol_deploy_{int(time.time()*1000)}",
                                product_id=f"{coin}-USD",
                                quote_size=str(size)
                            )
                            print(f"🚀 VOL-DEPLOY: Bought {coin} at range low (vol: {vol:.1f}%)")
                            time.sleep(delay)
                            return True
                            
            # BALANCED MODE: Trade the extremes
            else:
                if position > 0.85 and coin in holdings:
                    # Extreme overbought in high vol
                    amount = holdings[coin] * 0.1
                    if amount * current > 30:
                        order = client.market_order_sell(
                            client_order_id=f"vol_extreme_sell_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            base_size=str(amount)
                        )
                        print(f"⚡ VOL-SELL: {coin} extreme overbought (pos: {position:.2f})")
                        return True
                        
                elif position < 0.15:
                    # Extreme oversold in high vol
                    delay = specialist.apply_spongy_throttle()
                    if delay and specialist.calculate_trade_size(usd, 75) > 0:
                        order = client.market_order_buy(
                            client_order_id=f"vol_extreme_buy_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size="75"
                        )
                        print(f"⚡ VOL-BUY: {coin} extreme oversold (pos: {position:.2f})")
                        time.sleep(delay)
                        return True
                        
        # Low volatility - look for breakout setups
        elif vol < 2 and len(specialist.high_vol_coins) < 3:
            if coin not in specialist.high_vol_coins:
                # Track as potential breakout candidate
                pass
                
    except Exception as e:
        print(f"Vol error {coin}: {str(e)[:40]}")
        
    return False

# Main loop
target_coins = ["SOL", "ETH", "BTC", "AVAX", "MATIC", "ATOM"]
cycle = 0

print(f"Monitoring volatility: {', '.join(target_coins)}")
print()

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Portfolio check
    usd, holdings, total = get_portfolio()
    
    if cycle % 10 == 0:
        print(f"\n[{timestamp}] Volatility Status")
        print(f"  Portfolio: ${total:.2f}")
        print(f"  USD: ${usd:.2f}")
        print(f"  Pressure: {specialist.trade_pressure:.1f}x")
        print(f"  High Vol: {specialist.high_vol_coins[-3:]}")
        
        # Pressure recovery
        specialist.recover_pressure()
        
        # Clear old high vol list
        if len(specialist.high_vol_coins) > 10:
            specialist.high_vol_coins = specialist.high_vol_coins[-5:]
    
    # Execute trades
    trades = 0
    for coin in target_coins:
        if trade_volatility(coin):
            trades += 1
            
    # Faster recovery if no trades
    if trades == 0:
        specialist.recover_pressure()
        
    # Adaptive timing based on volatility
    if len(specialist.high_vol_coins) > 3:
        time.sleep(30)  # High vol = check frequently
    elif usd < 250:
        time.sleep(35)  # Need liquidity
    elif usd > 500:
        time.sleep(60)  # Deploy carefully
    else:
        time.sleep(45)  # Normal pace