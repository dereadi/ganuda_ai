#!/usr/bin/env python3
"""
🎯 LATENCY-COMPENSATED Q-DAD TRADER
====================================
Predicts where price WILL be, not where it IS
"""

import time
import json
from collections import deque
from coinbase.rest import RESTClient

class LatencyCompensator:
    def __init__(self):
        self.price_history = deque(maxlen=10)
        self.latency_ms = 500  # Estimated total latency
        
    def predict_price(self, current_price, symbol):
        """Predict where price will be after latency"""
        
        if len(self.price_history) < 2:
            return current_price
        
        # Calculate price velocity (price change per ms)
        prices = list(self.price_history)
        time_span = 1000  # 1 second of history
        price_change = prices[-1] - prices[0]
        velocity = price_change / time_span  # $/ms
        
        # Predict price after latency
        predicted = current_price + (velocity * self.latency_ms)
        
        # Add momentum factor for power hour
        hour = time.localtime().tm_hour
        if hour == 15:  # 3 PM power hour
            # Increase prediction during volatility
            momentum_multiplier = 1.2
            predicted = current_price + (velocity * self.latency_ms * momentum_multiplier)
        
        return predicted
    
    def calculate_slippage(self, order_size, symbol):
        """Estimate slippage based on order size"""
        
        # Typical slippage rates
        slippage_rates = {
            'BTC': 0.0001,  # 0.01% for BTC
            'ETH': 0.0002,  # 0.02% for ETH  
            'SOL': 0.0005,  # 0.05% for SOL (less liquid)
        }
        
        base_slippage = slippage_rates.get(symbol, 0.0003)
        
        # Larger orders = more slippage
        if order_size > 100:
            base_slippage *= 1.5
        if order_size > 500:
            base_slippage *= 2
            
        return base_slippage

# Test current latency
config = json.load(open("/home/dereadi/.coinbase_config.json"))
client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])

print("🎯 LATENCY COMPENSATION ANALYSIS")
print("="*60)

# Measure API latency
print("\n📡 Measuring API Latency...")
latencies = []

for i in range(5):
    start = time.time()
    ticker = client.get_product("BTC-USD")
    latency = (time.time() - start) * 1000
    latencies.append(latency)
    print(f"  Test {i+1}: {latency:.1f}ms")
    time.sleep(0.2)

avg_latency = sum(latencies) / len(latencies)
print(f"\n⚡ Average API Latency: {avg_latency:.1f}ms")

# Check current prices with prediction
compensator = LatencyCompensator()
compensator.latency_ms = avg_latency

print("\n📊 PRICE PREDICTIONS (with latency compensation):")
print("-"*60)

for symbol in ["BTC", "ETH", "SOL"]:
    ticker = client.get_product(f"{symbol}-USD")
    current = float(ticker.get('price', 0))
    
    # Add to history
    compensator.price_history.append(current)
    
    # Predict
    predicted = compensator.predict_price(current, symbol)
    difference = predicted - current
    pct_diff = (difference / current) * 100
    
    print(f"\n{symbol}:")
    print(f"  Current: ${current:,.2f}")
    print(f"  Predicted (after {avg_latency:.0f}ms): ${predicted:,.2f}")
    print(f"  Difference: ${difference:+.2f} ({pct_diff:+.4f}%)")
    
    # Slippage estimate
    slippage = compensator.calculate_slippage(50, symbol)
    print(f"  Expected slippage: {slippage*100:.3f}%")

print("\n🦀 LATENCY COMPENSATION STRATEGIES:")
print("-"*60)
print("1. LIMIT ORDERS: Place limits at predicted price")
print("2. AGGRESSIVE SIZING: Oversize by slippage %")
print("3. SPLIT ORDERS: Multiple small orders reduce slippage")
print("4. TIME ORDERS: Execute before crowd (3:29 not 3:30)")
print("5. MOMENTUM FACTOR: Increase prediction in power hour")

print("\n⏱️ TIMING ADVANTAGES:")
print(f"  • Our latency: {avg_latency:.0f}ms")
print(f"  • Retail traders: 1000-3000ms")
print(f"  • We're {1000/avg_latency:.1f}x faster than average!")

print("\n✨ The Q-Dads swim ahead of the wave!")