#!/usr/bin/env python3
"""
Γ GAMMA - Trend Acceleration Specialist (FIXED)
Rides trend acceleration and momentum changes
"""

import json
import subprocess
import time
from datetime import datetime
import sys

print("Γ GAMMA (Trend Specialist) ACTIVATED", flush=True)
print("Mission: Ride trend acceleration", flush=True)
print("-" * 40, flush=True)

def check_trend(coin):
    """Check trend direction and acceleration"""
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    # Get current ticker
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    # Get 24h stats (use different method)
    product = client.get_products('{coin}-USD')
    
    # Fallback to ticker data
    stats = ticker
    
    # Calculate basic metrics from ticker
    if current > 0:
        # Estimate trend based on bid/ask spread and price
        bid = float(ticker.get("bid", current))
        ask = float(ticker.get("ask", current))
        spread = (ask - bid) / current * 100
        
        # Simple trend detection
        mid = (bid + ask) / 2
        trend_signal = "UP" if current > mid else "DOWN" if current < mid else "NEUTRAL"
        
        print(f"TREND_{{trend_signal}}:{coin}:${{current:.2f}}:SPREAD={{spread:.3f}}%")
    else:
        print(f"NO_DATA:{coin}")
        
except Exception as e:
    # Fallback to simpler API call
    try:
        ticker = client.get_product('{coin}-USD')
        price = float(ticker.get("price", 0))
        print(f"PRICE:{coin}:${{price:.2f}}")
    except:
        print(f"ERROR:{coin}:API_ISSUE")
"""
    
    try:
        with open(f"/tmp/gamma_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.returncode != 0 and result.stderr:
            return f"ERROR:{coin}:{result.stderr[:50]}"
        return result.stdout.strip() if result.stdout else f"TIMEOUT:{coin}"
    except Exception as e:
        return f"EXCEPTION:{coin}:{str(e)[:30]}"

def calculate_momentum(coin):
    """Calculate momentum using simpler approach"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    # Get current price
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    # Get order book for momentum
    orders = client.get_product_book('{coin}-USD', level=1)
    
    if orders and 'bids' in orders and 'asks' in orders:
        # Calculate buy/sell pressure
        bid_vol = sum(float(b[1]) for b in orders['bids'][:5]) if 'bids' in orders else 0
        ask_vol = sum(float(a[1]) for a in orders['asks'][:5]) if 'asks' in orders else 0
        
        if bid_vol + ask_vol > 0:
            buy_pressure = bid_vol / (bid_vol + ask_vol) * 100
            
            if buy_pressure > 60:
                print(f"MOMENTUM_UP:{coin}:PRESSURE={{buy_pressure:.1f}}%")
            elif buy_pressure < 40:
                print(f"MOMENTUM_DOWN:{coin}:PRESSURE={{buy_pressure:.1f}}%")
            else:
                print(f"MOMENTUM_NEUTRAL:{coin}:{{buy_pressure:.1f}}%")
        else:
            print(f"NO_VOLUME:{coin}")
    else:
        # Fallback to just price
        print(f"PRICE_ONLY:{coin}:${{current:.2f}}")
        
except Exception as e:
    print(f"ERROR:{coin}:{{str(e)[:30]}}")
"""
    
    try:
        with open(f"/tmp/gamma_mom_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else ""
    except:
        return ""

# Main loop
coins = ["BTC", "ETH", "SOL", "AVAX"]
cycle = 0
last_prices = {}

print(f"[{datetime.now().strftime('%H:%M:%S')}] Γ Gamma initialized", flush=True)

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        # Check trend
        trend_result = check_trend(coin)
        
        # Look for strong trends
        if trend_result and "TREND_" in trend_result:
            if "TREND_UP" in trend_result or "TREND_DOWN" in trend_result:
                print(f"[{timestamp}] Γ {trend_result}", flush=True)
                
                # Also check momentum on strong trends
                momentum = calculate_momentum(coin)
                if momentum and "MOMENTUM_" in momentum:
                    print(f"[{timestamp}] Γ {momentum}", flush=True)
        
        # Extract price for tracking
        if ":" in trend_result:
            parts = trend_result.split(":")
            if len(parts) > 2 and "$" in parts[2]:
                try:
                    price = float(parts[2].replace("$", "").replace(",", ""))
                    
                    # Check for acceleration
                    if coin in last_prices:
                        change = ((price - last_prices[coin]) / last_prices[coin]) * 100
                        if abs(change) > 0.5:  # 0.5% move
                            direction = "ACCELERATING_UP" if change > 0 else "ACCELERATING_DOWN"
                            print(f"[{timestamp}] Γ {direction}:{coin}:{change:+.2f}%", flush=True)
                    
                    last_prices[coin] = price
                except:
                    pass
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Γ Gamma: Cycle {cycle} complete", flush=True)
        print(f"[{timestamp}] Γ Tracking: {list(last_prices.keys())}", flush=True)
    
    time.sleep(90)  # Check every 1.5 minutes