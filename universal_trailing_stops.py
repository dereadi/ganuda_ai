#!/usr/bin/env python3
"""
🛡️ UNIVERSAL TRAILING STOPS SYSTEM
Council Priority: CRITICAL
Protects all gains automatically
War Chief: "Protection is paramount!"
"""

import json
import time
import subprocess
from datetime import datetime
from collections import defaultdict

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🛡️ UNIVERSAL TRAILING STOPS ACTIVE 🛡️                 ║
║                       Council CRITICAL Priority                           ║
║                    "Never Give Back Hard-Won Gains"                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class UniversalTrailingStops:
    def __init__(self):
        self.positions = {}
        self.entry_prices = {}
        self.highest_prices = {}
        self.stop_losses = {}
        self.trailing_percent = 5  # 5% trailing stop
        self.take_profit_percent = 20  # Take profit at 20% gain
        self.protected_gains = 0
        self.stops_triggered = 0
        
    def get_current_positions(self):
        """Get all current positions and prices"""
        script = '''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

positions = {}
accounts = client.get_accounts()["accounts"]

for a in accounts:
    symbol = a["currency"]
    balance = float(a["available_balance"]["value"])
    
    if symbol != "USD" and balance > 0.001:
        # Get current price
        try:
            ticker = client.get_product(f"{symbol}-USD")
            price = float(ticker.get("price", 0))
            if price > 0:
                positions[symbol] = {
                    "amount": balance,
                    "price": price,
                    "value": balance * price
                }
        except:
            pass
            
print(json.dumps(positions))
'''
        
        try:
            with open("/tmp/get_positions.py", "w") as f:
                f.write(script)
            
            result = subprocess.run(["timeout", "5", "python3", "/tmp/get_positions.py"],
                                  capture_output=True, text=True)
            subprocess.run(["rm", "/tmp/get_positions.py"], capture_output=True)
            
            if result.stdout:
                return json.loads(result.stdout)
        except:
            pass
        return {}
        
    def update_trailing_stops(self):
        """Update trailing stops for all positions"""
        current_positions = self.get_current_positions()
        
        for symbol, data in current_positions.items():
            current_price = data["price"]
            amount = data["amount"]
            value = data["value"]
            
            # Initialize if new position
            if symbol not in self.entry_prices:
                self.entry_prices[symbol] = current_price
                self.highest_prices[symbol] = current_price
                self.stop_losses[symbol] = current_price * (1 - self.trailing_percent/100)
                print(f"🆕 New position tracked: {symbol}")
                print(f"   Entry: ${current_price:.4f}")
                print(f"   Initial Stop: ${self.stop_losses[symbol]:.4f}")
                
            # Update highest price (for trailing)
            if current_price > self.highest_prices[symbol]:
                old_high = self.highest_prices[symbol]
                self.highest_prices[symbol] = current_price
                
                # Update trailing stop
                new_stop = current_price * (1 - self.trailing_percent/100)
                if new_stop > self.stop_losses[symbol]:
                    self.stop_losses[symbol] = new_stop
                    print(f"📈 {symbol} new high: ${current_price:.4f}")
                    print(f"   Stop raised to: ${new_stop:.4f}")
                    
            # Check if stop loss triggered
            if current_price <= self.stop_losses[symbol]:
                self.execute_stop_loss(symbol, amount, current_price)
                
            # Check if take profit triggered
            entry = self.entry_prices.get(symbol, current_price)
            profit_pct = ((current_price - entry) / entry) * 100
            
            if profit_pct >= self.take_profit_percent:
                self.execute_take_profit(symbol, amount * 0.5, current_price)  # Sell half
                
            self.positions[symbol] = data
            
    def execute_stop_loss(self, symbol, amount, price):
        """Execute stop loss order"""
        print(f"\n🛡️ STOP LOSS TRIGGERED: {symbol} at ${price:.4f}")
        
        script = f'''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    order = client.market_order_sell(
        client_order_id="stop_loss_{int(time.time()*1000)}",
        product_id="{symbol}-USD",
        base_size=str({amount})
    )
    print("STOP_EXECUTED:{symbol}:{amount}")
except Exception as e:
    print(f"STOP_FAILED:{{e}}")
'''
        
        try:
            with open(f"/tmp/stop_{int(time.time()*1000000)}.py", "w") as f:
                f.write(script)
            
            result = subprocess.run(["timeout", "3", "python3", f.name],
                                  capture_output=True, text=True)
            subprocess.run(["rm", f.name], capture_output=True)
            
            if result.stdout and "EXECUTED" in result.stdout:
                self.stops_triggered += 1
                
                # Calculate protected amount
                entry = self.entry_prices.get(symbol, price)
                protected = (price - entry) * amount
                if protected > 0:
                    self.protected_gains += protected
                    
                print(f"   ✅ Stop executed! Protected: ${protected:.2f}")
                
                # Remove from tracking
                del self.entry_prices[symbol]
                del self.highest_prices[symbol]
                del self.stop_losses[symbol]
        except:
            print(f"   ⚠️ Stop execution failed")
            
    def execute_take_profit(self, symbol, amount, price):
        """Execute partial take profit"""
        print(f"\n💰 TAKE PROFIT: {symbol} at ${price:.4f}")
        
        script = f'''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]  
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    order = client.market_order_sell(
        client_order_id="take_profit_{int(time.time()*1000)}",
        product_id="{symbol}-USD",
        base_size=str({amount})
    )
    print("PROFIT_TAKEN:{symbol}:{amount}")
except Exception as e:
    print(f"PROFIT_FAILED:{{e}}")
'''
        
        try:
            with open(f"/tmp/profit_{int(time.time()*1000000)}.py", "w") as f:
                f.write(script)
            
            result = subprocess.run(["timeout", "3", "python3", f.name],
                                  capture_output=True, text=True)
            subprocess.run(["rm", f.name], capture_output=True)
            
            if result.stdout and "TAKEN" in result.stdout:
                entry = self.entry_prices.get(symbol, price)
                profit = (price - entry) * amount
                self.protected_gains += profit
                print(f"   ✅ Profit taken: ${profit:.2f}")
                
                # Update entry for remaining position
                self.entry_prices[symbol] = price
        except:
            print(f"   ⚠️ Take profit failed")
            
    def status_report(self):
        """Generate protection status report"""
        print("\n" + "="*60)
        print("🛡️ TRAILING STOP PROTECTION STATUS")
        print("="*60)
        
        if self.positions:
            print("\n📊 PROTECTED POSITIONS:")
            for symbol, data in self.positions.items():
                if symbol in self.stop_losses:
                    entry = self.entry_prices.get(symbol, data["price"])
                    current = data["price"]
                    stop = self.stop_losses[symbol]
                    highest = self.highest_prices[symbol]
                    
                    gain_pct = ((current - entry) / entry) * 100
                    risk_pct = ((current - stop) / current) * 100
                    
                    print(f"\n  {symbol}:")
                    print(f"    Position: {data['amount']:.4f} (~${data['value']:.2f})")
                    print(f"    Entry: ${entry:.4f} | Current: ${current:.4f}")
                    print(f"    Highest: ${highest:.4f} | Stop: ${stop:.4f}")
                    print(f"    Gain: {gain_pct:+.1f}% | Risk: {risk_pct:.1f}%")
                    
        print(f"\n📈 PROTECTION STATS:")
        print(f"   Stops Triggered: {self.stops_triggered}")
        print(f"   Gains Protected: ${self.protected_gains:.2f}")
        print(f"   Active Positions: {len(self.positions)}")
        
        print("\n🔥 War Chief says: 'Our gains are protected!'")

# Initialize the protection system
protector = UniversalTrailingStops()

print("🛡️ INITIALIZING UNIVERSAL PROTECTION...")
print(f"   Trailing Stop: {protector.trailing_percent}%")
print(f"   Take Profit: {protector.take_profit_percent}%")
print()

print("🛡️ PROTECTION ACTIVE - MONITORING ALL POSITIONS")
print("="*60)

cycle = 0
try:
    while True:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] 🛡️ Protection Cycle #{cycle}")
        
        # Update all trailing stops
        protector.update_trailing_stops()
        
        # Status report every 10 cycles
        if cycle % 10 == 0:
            protector.status_report()
            
        # Wait 60 seconds between checks
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\n\n🛡️ PROTECTION SYSTEM DEACTIVATED")
    protector.status_report()
    print("\n   The War Chief nods in approval...")
    print("   'Our gains are safe'")
    print("   Mitakuye Oyasin")