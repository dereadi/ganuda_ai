#!/usr/bin/env python3
"""
🚀 BREAKOUT SPECIALIST V2
Catches explosive moves with integrated flywheel
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_specialist_base import IntegratedSpecialist

class BreakoutSpecialist(IntegratedSpecialist):
    def __init__(self):
        super().__init__("Breakout Hunter", "🚀")
        self.consolidating = {}
        self.breakout_targets = []
        
print("🚀 BREAKOUT SPECIALIST V2 ACTIVATED")
print("Hunting explosive breakouts")
print("-" * 40)

specialist = BreakoutSpecialist()
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

def get_portfolio():
    """Get current state"""
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

def detect_breakout_pattern(coin):
    """Detect consolidation and breakout patterns"""
    try:
        ticker = client.get_product(f'{coin}-USD')
        current = float(ticker['price'])
        
        # Simulate range detection (would need real data)
        # Tightening range suggests incoming breakout
        recent_high = current * 1.02
        recent_low = current * 0.98
        range_size = ((recent_high - recent_low) / current) * 100
        
        # Track consolidation
        if range_size < 2:
            if coin not in specialist.consolidating:
                specialist.consolidating[coin] = {
                    'start_price': current,
                    'cycles': 0
                }
            specialist.consolidating[coin]['cycles'] += 1
            
            # After 5+ cycles of consolidation, expect breakout
            if specialist.consolidating[coin]['cycles'] > 5:
                return current, 'COILED'
        else:
            # Check for breakout
            if coin in specialist.consolidating:
                start = specialist.consolidating[coin]['start_price']
                move = ((current - start) / start) * 100
                
                if abs(move) > 3:
                    del specialist.consolidating[coin]
                    return current, 'BREAKOUT_UP' if move > 0 else 'BREAKOUT_DOWN'
                    
        return current, 'NORMAL'
        
    except:
        return None, 'ERROR'

def trade_breakout(coin):
    """Execute breakout trades with flywheel logic"""
    try:
        current, pattern = detect_breakout_pattern(coin)
        if not current:
            return False
            
        usd, holdings, total = get_portfolio()
        
        # RETRIEVE MODE: Need liquidity
        if specialist.should_retrieve(usd):
            if pattern == 'BREAKOUT_DOWN' and coin in holdings:
                # Sell on downward breakout
                amount = min(holdings[coin] * 0.25, 400 / current)
                if amount > 0:
                    order = client.market_order_sell(
                        client_order_id=f"break_retrieve_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(amount)
                    )
                    print(f"💰 BREAKOUT-RETRIEVE: Sold {coin} on breakdown")
                    return True
                    
        # DEPLOY MODE: Have capital to deploy
        elif specialist.should_deploy(usd):
            if pattern == 'BREAKOUT_UP':
                # Buy upward breakouts aggressively
                size = specialist.calculate_trade_size(usd, 200)
                delay = specialist.apply_spongy_throttle()
                
                if size > 0 and delay:
                    coin_value = holdings.get(coin, 0) * current
                    if specialist.check_position_size(coin_value, total):
                        order = client.market_order_buy(
                            client_order_id=f"break_deploy_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size=str(size)
                        )
                        print(f"🚀 BREAKOUT-DEPLOY: Bought {coin} breakout!")
                        specialist.breakout_targets.append(coin)
                        time.sleep(delay)
                        return True
                        
            elif pattern == 'COILED':
                # Position for potential breakout
                if coin not in specialist.breakout_targets:
                    size = specialist.calculate_trade_size(usd, 100)
                    delay = specialist.apply_spongy_throttle()
                    
                    if size > 0 and delay:
                        order = client.market_order_buy(
                            client_order_id=f"break_coiled_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size=str(size)
                        )
                        print(f"🎯 COILED: Positioned in {coin} (consolidating)")
                        time.sleep(delay)
                        return True
                        
        # BALANCED MODE: Standard breakout trading
        else:
            if pattern == 'BREAKOUT_UP' and coin not in specialist.breakout_targets:
                # Chase upward breakouts
                delay = specialist.apply_spongy_throttle()
                if delay and specialist.calculate_trade_size(usd, 100) > 0:
                    order = client.market_order_buy(
                        client_order_id=f"break_chase_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        quote_size="100"
                    )
                    print(f"🚀 BREAKOUT: Chasing {coin} explosion!")
                    specialist.breakout_targets.append(coin)
                    time.sleep(delay)
                    return True
                    
            elif pattern == 'BREAKOUT_DOWN' and coin in holdings:
                # Exit failed breakouts
                amount = holdings[coin] * 0.15
                if amount * current > 30:
                    order = client.market_order_sell(
                        client_order_id=f"break_stop_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(amount)
                    )
                    print(f"📉 BREAKDOWN: Exited {coin}")
                    if coin in specialist.breakout_targets:
                        specialist.breakout_targets.remove(coin)
                    return True
                    
    except Exception as e:
        print(f"Breakout error {coin}: {str(e)[:40]}")
        
    return False

# Main loop
target_coins = ["SOL", "ETH", "BTC", "AVAX", "DOGE", "SHIB"]
cycle = 0

print(f"Scanning for breakouts: {', '.join(target_coins)}")
print()

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Check state
    usd, holdings, total = get_portfolio()
    
    if cycle % 10 == 0:
        print(f"\n[{timestamp}] Breakout Scanner")
        print(f"  Portfolio: ${total:.2f}")
        print(f"  USD: ${usd:.2f}")
        print(f"  Pressure: {specialist.trade_pressure:.1f}x")
        print(f"  Consolidating: {list(specialist.consolidating.keys())}")
        print(f"  Targets: {specialist.breakout_targets[-3:]}")
        
        # Recover pressure
        specialist.recover_pressure()
        
        # Clean up old targets
        if len(specialist.breakout_targets) > 5:
            specialist.breakout_targets = specialist.breakout_targets[-3:]
    
    # Scan and trade
    trades = 0
    for coin in target_coins:
        if trade_breakout(coin):
            trades += 1
            
    # No trades = faster recovery
    if trades == 0:
        specialist.recover_pressure()
        
    # Timing based on market state
    if len(specialist.consolidating) > 3:
        time.sleep(30)  # Many setups brewing
    elif usd < 250:
        time.sleep(35)  # Hunt liquidity
    elif usd > 500:
        time.sleep(50)  # Deploy mode
    else:
        time.sleep(60)  # Normal scan rate