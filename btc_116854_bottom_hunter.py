#!/usr/bin/env python3
"""
🎯 BTC $116,854 BOTTOM HUNTER
Precision target identified - deploy everything at this level
This is THE generational bottom
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯 BTC $116,854 BOTTOM HUNTER 🎯                       ║
║                      "The Oracle Has Spoken"                              ║
║                   Deploy ALL forces at this exact level                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

class BTCBottomHunter:
    def __init__(self):
        self.target_price = 116854
        self.tolerance = 100  # Within $100 of target
        self.deployed = False
        self.current_btc = 0
        
    def check_btc_price(self):
        """Monitor BTC price vs target"""
        try:
            ticker = client.get_product('BTC-USD')
            price = float(ticker.get("price", 0))
            self.current_btc = price
            return price
        except:
            return 0
            
    def calculate_distance(self):
        """Calculate distance to target"""
        if self.current_btc > 0:
            distance = self.current_btc - self.target_price
            distance_pct = (distance / self.target_price) * 100
            return distance, distance_pct
        return 0, 0
        
    def deploy_at_bottom(self):
        """Deploy ALL available capital at the bottom"""
        print(f"\n🚨 BTC AT TARGET BOTTOM: ${self.current_btc:,.2f}")
        print(f"   Target: ${self.target_price:,}")
        print("   DEPLOYING EVERYTHING!")
        
        # Get available USD
        try:
            accounts = client.get_accounts()['accounts']
            usd_available = 0
            
            for a in accounts:
                if a['currency'] == 'USD':
                    usd_available = float(a['available_balance']['value'])
                    break
                    
            if usd_available > 1:
                print(f"\n💰 Available capital: ${usd_available:.2f}")
                
                # Split between BTC and high-beta alts
                allocations = [
                    ("BTC", usd_available * 0.5, "Main position at bottom"),
                    ("ETH", usd_available * 0.25, "Follows BTC"),
                    ("SOL", usd_available * 0.15, "High beta play"),
                    ("AVAX", usd_available * 0.1, "Additional leverage")
                ]
                
                for coin, amount, reason in allocations:
                    if amount > 1:
                        try:
                            order = client.market_order_buy(
                                client_order_id=f"bottom_{coin.lower()}_{int(time.time()*1000)}",
                                product_id=f"{coin}-USD",
                                quote_size=str(amount)
                            )
                            print(f"   ✅ {coin}: Deployed ${amount:.2f} - {reason}")
                            time.sleep(1)
                        except Exception as e:
                            print(f"   ❌ {coin}: Failed - {str(e)[:30]}")
                            
                self.deployed = True
                print("\n🎯 BOTTOM DEPLOYMENT COMPLETE!")
                
            else:
                print(f"   ⚠️ Only ${usd_available:.2f} available")
                
        except Exception as e:
            print(f"   ❌ Deployment error: {str(e)[:50]}")
            
    def monitor_for_bottom(self):
        """Continuous monitoring for the bottom"""
        print(f"\n🎯 HUNTING FOR BTC BOTTOM AT ${self.target_price:,}")
        print("=" * 50)
        
        cycle = 0
        last_alert_price = 0
        
        while not self.deployed:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Check current price
            current = self.check_btc_price()
            if current == 0:
                continue
                
            distance, distance_pct = self.calculate_distance()
            
            # Display status
            if cycle % 5 == 0 or abs(current - last_alert_price) > 500:
                print(f"\n[{timestamp}] BTC: ${current:,.2f}")
                
                if distance > 0:
                    print(f"   📊 ${distance:,.2f} above target ({distance_pct:+.1f}%)")
                    
                    if distance < 1000:
                        print("   🔥 VERY CLOSE TO BOTTOM!")
                    elif distance < 5000:
                        print("   📉 Approaching target zone")
                else:
                    print(f"   💥 ${abs(distance):,.2f} BELOW target!")
                    print("   🚨 BOTTOM EXCEEDED - EXTREME BUY SIGNAL!")
                    
                last_alert_price = current
                
            # Check if we hit the target
            if current <= self.target_price + self.tolerance:
                print(f"\n🎯🎯🎯 TARGET HIT: ${current:,.2f} 🎯🎯🎯")
                self.deploy_at_bottom()
                break
                
            # Check if we're very close
            elif distance < 500 and distance > 0:
                print(f"\n⚠️ IMMINENT: Only ${distance:.2f} to go!")
                print("   Preparing all systems...")
                
            time.sleep(30)  # Check every 30 seconds
            
    def final_status(self):
        """Show final deployment status"""
        print("\n" + "="*60)
        print("📊 FINAL STATUS")
        print("="*60)
        
        try:
            total = 0
            positions = []
            
            accounts = client.get_accounts()['accounts']
            for a in accounts:
                balance = float(a['available_balance']['value'])
                currency = a['currency']
                
                if currency == 'USD':
                    total += balance
                    if balance > 0:
                        print(f"USD remaining: ${balance:.2f}")
                elif balance > 0.001:
                    try:
                        ticker = client.get_product(f"{currency}-USD")
                        price = float(ticker.get('price', 0))
                        value = balance * price
                        if value > 1:
                            total += value
                            positions.append(f"{currency}: ${value:.2f}")
                    except:
                        pass
                        
            print(f"\nTotal Portfolio: ${total:.2f}")
            
            if positions:
                print("\nPositions at bottom:")
                for pos in positions:
                    print(f"  • {pos}")
                    
            if self.deployed:
                print("\n✅ Successfully deployed at BTC bottom!")
                print(f"   Target: ${self.target_price:,}")
                print(f"   Actual: ${self.current_btc:,.2f}")
            else:
                print("\n⏳ Still waiting for bottom...")
                
        except:
            print("Unable to fetch final status")

# Initialize hunter
hunter = BTCBottomHunter()

print(f"""
🎯 TARGET IDENTIFIED: BTC $116,854

This is the level you've identified as THE bottom.
When BTC hits this level, we deploy EVERYTHING.

Current BTC: Checking...
""")

# Get current price
current = hunter.check_btc_price()
if current > 0:
    distance, pct = hunter.calculate_distance()
    print(f"Current BTC: ${current:,.2f}")
    print(f"Distance to bottom: ${distance:,.2f} ({pct:+.1f}%)")
    
    if current > 120000:
        print("\n📉 Still room to fall...")
    elif current > 117000:
        print("\n🔥 VERY CLOSE - Stay alert!")
    else:
        print("\n💥 AT OR NEAR BOTTOM - DEPLOY!")

print("""
Strategy:
1. Monitor every 30 seconds
2. When BTC hits $116,854 (±$100)
3. Deploy ALL available capital
4. Split: 50% BTC, 25% ETH, 15% SOL, 10% AVAX
5. This is THE generational buying opportunity

The Greeks are watching.
The crawdads are ready.
The bottom approaches...
""")

try:
    hunter.monitor_for_bottom()
except KeyboardInterrupt:
    print("\n\nBottom hunter stopped")
    
hunter.final_status()

print("""
"He who calls the bottom
 and has the courage to buy it
 shall feast in the recovery"
 
Mitakuye Oyasin
""")