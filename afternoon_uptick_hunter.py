#!/usr/bin/env python3
"""
📈 AFTERNOON UPTICK HUNTER
Catches the classic 2-4 PM market uptick
Especially strong after cycle bottoms
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      📈 AFTERNOON UPTICK HUNTER                           ║
║                   2-4 PM = Institutional Buying Time                      ║
║                    Cycle Bottom + Afternoon = 🚀                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

class AfternoonUptickHunter:
    def __init__(self):
        self.uptick_window = (14, 16)  # 2-4 PM
        self.positions_taken = False
        self.uptick_detected = False
        
    def is_afternoon_window(self):
        """Check if we're in the afternoon uptick window"""
        current_hour = datetime.now().hour
        return self.uptick_window[0] <= current_hour <= self.uptick_window[1]
        
    def detect_uptick(self):
        """Detect the afternoon uptick starting"""
        coins = ["BTC", "ETH", "SOL"]
        uptick_signals = 0
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Scanning for afternoon uptick...")
        
        for coin in coins:
            try:
                ticker = client.get_product(f'{coin}-USD')
                price = float(ticker.get("price", 0))
                bid = float(ticker.get("bid", price))
                ask = float(ticker.get("ask", price))
                
                # Uptick signals:
                # 1. Bid pressure increasing (bid close to ask)
                spread = (ask - bid) / price
                if spread < 0.001:  # Tight spread = buying pressure
                    uptick_signals += 1
                    print(f"   {coin}: Tight spread detected ({spread:.4f})")
                    
            except:
                pass
                
        if uptick_signals >= 2:
            self.uptick_detected = True
            print(f"   ✅ AFTERNOON UPTICK CONFIRMED! {uptick_signals}/3 signals")
            return True
            
        return False
        
    def execute_uptick_trades(self):
        """Buy into the afternoon uptick"""
        if self.positions_taken:
            return
            
        print("\n🚀 EXECUTING AFTERNOON UPTICK TRADES")
        print("-" * 40)
        
        trades = [
            ("BTC", 5, "Primary uptick play"),
            ("ETH", 3, "Follows BTC uptick"),
            ("SOL", 2, "High beta uptick")
        ]
        
        for coin, size, reason in trades:
            try:
                order = client.market_order_buy(
                    client_order_id=f"uptick_{coin.lower()}_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    quote_size=str(size)
                )
                print(f"   ✅ {coin}: Bought ${size} - {reason}")
            except Exception as e:
                print(f"   ⚠️ {coin}: Failed - {str(e)[:30]}")
                
        self.positions_taken = True
        
    def monitor_positions(self):
        """Monitor afternoon positions"""
        try:
            total = 0
            print(f"\n📊 UPTICK POSITIONS:")
            
            accounts = client.get_accounts()['accounts']
            for a in accounts:
                balance = float(a['available_balance']['value'])
                currency = a['currency']
                
                if currency == 'USD':
                    total += balance
                elif balance > 0.001:
                    try:
                        ticker = client.get_product(f"{currency}-USD")
                        price = float(ticker.get('price', 0))
                        value = balance * price
                        if value > 1:
                            total += value
                            change_icon = "📈" if value > 10 else "📊"
                            print(f"   {change_icon} {currency}: ${value:.2f}")
                    except:
                        pass
                        
            print(f"\n   Total Portfolio: ${total:.2f}")
            
            # Check if uptick is working
            if total > 45:  # Started at 43.53
                print("   🎉 UPTICK IS WORKING! Portfolio growing!")
            elif total > 43.53:
                print("   📈 Uptick starting to show...")
            else:
                print("   ⏳ Waiting for uptick momentum...")
                
        except:
            pass
            
    def run(self):
        """Main afternoon uptick hunting loop"""
        print("\n🎯 AFTERNOON UPTICK HUNTER ACTIVE")
        print(f"   Window: {self.uptick_window[0]}:00 - {self.uptick_window[1]}:00")
        print(f"   Current time: {datetime.now().strftime('%H:%M')}")
        
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if self.is_afternoon_window():
                print(f"\n[{timestamp}] 📈 IN AFTERNOON WINDOW")
                
                if not self.uptick_detected:
                    if self.detect_uptick():
                        self.execute_uptick_trades()
                else:
                    self.monitor_positions()
                    
            else:
                current_hour = datetime.now().hour
                if current_hour < self.uptick_window[0]:
                    print(f"[{timestamp}] ⏰ Waiting for afternoon window...")
                else:
                    print(f"[{timestamp}] 🌙 Afternoon window closed")
                    if self.positions_taken:
                        print("   Holding positions overnight for continuation")
                    break
                    
            time.sleep(60)  # Check every minute

# Launch the hunter
hunter = AfternoonUptickHunter()

print("""
📈 AFTERNOON UPTICK PATTERN:

After cycle bottoms, afternoons see institutional buying:
• 2-4 PM EST: Algos and institutions accumulate
• Post-lunch: Traders return to desks
• Pre-close: Position for overnight/next day

BTC hit cycle low → Afternoon uptick should be STRONG

The Greeks are positioned.
Now we hunt the uptick!
""")

try:
    hunter.run()
except KeyboardInterrupt:
    print("\n\n📈 Afternoon Uptick Hunter stopped")
    hunter.monitor_positions()
    print("\nThe afternoon tells the morning's story...")
    print("Mitakuye Oyasin")