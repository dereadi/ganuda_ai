#!/usr/bin/env python3
"""
🏛️🥛 COUNCIL AUTOMATED ALT MILKER WITH SPONGY THROTTLE 🥛🏛️
Built by the Council + Claude!
Features:
- Spongy throttle (adaptive milking based on market conditions)
- Coast mode (let profits run when trending)
- E-brake (emergency stop for protection)
- Smart batch milking for repositioning
- Council personalities guide decisions
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time
import signal
import sys

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

# Global state
COAST_MODE = False
E_BRAKE = False
TOTAL_MILKED = 0
THROTTLE_POSITION = 50  # 0-100 (0=conservative, 100=aggressive)

def emergency_brake(signum, frame):
    """E-BRAKE: Stop all operations immediately"""
    global E_BRAKE
    print("\n🚨 E-BRAKE PULLED! STOPPING ALL OPERATIONS!")
    E_BRAKE = True
    print(f"Total milked before stop: ${TOTAL_MILKED:.2f}")
    sys.exit(0)

signal.signal(signal.SIGINT, emergency_brake)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         🏛️ COUNCIL AUTOMATED MILKER WITH SPONGY THROTTLE 🏛️              ║
║                   Adaptive • Smart • Council-Guided                        ║
║           [COAST 🌊] [THROTTLE 🎚️] [E-BRAKE 🛑] Active                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class CouncilMilker:
    def __init__(self):
        self.council = {
            'Thunder': {'aggression': 90, 'voice': '⚡'},
            'Mountain': {'aggression': 30, 'voice': '🗻'},
            'Fire': {'aggression': 80, 'voice': '🔥'},
            'River': {'aggression': 50, 'voice': '🌊'},
            'Wind': {'aggression': 70, 'voice': '💨'},
            'Earth': {'aggression': 40, 'voice': '🌍'},
            'Spirit': {'aggression': 60, 'voice': '✨'}
        }
        self.fee_rate = 0.006  # Coinbase fee
        self.min_profit_threshold = 0.012  # 1.2% minimum for round trip
        
    def check_market_conditions(self):
        """Check if we're trending up (coast) or choppy (milk)"""
        btc = client.get_product('BTC-USD')
        btc_price = float(btc['price'])
        
        # Simple trend check (in production, use more sophisticated analysis)
        if btc_price > 112000:
            trend = "BULLISH"
            coast_recommendation = True
        elif btc_price > 110000:
            trend = "NEUTRAL"
            coast_recommendation = False
        else:
            trend = "BEARISH"
            coast_recommendation = False
            
        return trend, coast_recommendation, btc_price
    
    def calculate_throttle(self, asset, balance, current_price, value):
        """Spongy throttle - adaptive milking percentage"""
        global THROTTLE_POSITION
        
        # Base milk percentages
        base_milk = {
            'SOL': 0.15,
            'ETH': 0.10,
            'BTC': 0.05,
            'AVAX': 0.20,
            'MATIC': 0.25,
            'DOGE': 0.30,
            'XRP': 0.25
        }
        
        # Adjust based on throttle position (0-100)
        throttle_multiplier = THROTTLE_POSITION / 50  # 0-2x multiplier
        
        # Get base percentage
        base = base_milk.get(asset, 0.20)
        
        # Apply spongy throttle
        adjusted = base * throttle_multiplier
        
        # Council votes on adjustment
        council_vote = self.council_decides(asset, value, adjusted)
        
        # Final calculation with safety limits
        final_percent = min(adjusted * council_vote, 0.40)  # Max 40% ever
        
        return final_percent
    
    def council_decides(self, asset, value, proposed_percent):
        """Council personalities vote on milk percentage"""
        votes = []
        
        print(f"\n🏛️ Council deliberates on {asset} milk ({proposed_percent*100:.1f}%):")
        
        for member, traits in self.council.items():
            # Each member votes based on personality
            if traits['aggression'] > 70:
                # Aggressive members want more milk
                vote = 1.2
                print(f"  {traits['voice']} {member}: 'Milk it harder!' (1.2x)")
            elif traits['aggression'] < 40:
                # Conservative members want less
                vote = 0.8
                print(f"  {traits['voice']} {member}: 'Be cautious' (0.8x)")
            else:
                # Moderate members agree
                vote = 1.0
                print(f"  {traits['voice']} {member}: 'Proceed as planned' (1.0x)")
            
            votes.append(vote)
        
        # Return average council decision
        return sum(votes) / len(votes)
    
    def execute_milk(self, asset, amount, expected_value):
        """Execute the actual milk with proper error handling"""
        global TOTAL_MILKED
        
        try:
            print(f"\n🥛 Executing {asset} milk: {amount:.8f} units")
            
            # Build order
            order = client.market_order_sell(
                client_order_id=f'council_milk_{asset}_{int(time.time())}',
                product_id=f'{asset}-USD',
                base_size=str(round(amount, 8))
            )
            
            print(f"  ✅ Milked {amount:.8f} {asset} = ~${expected_value:.2f}")
            TOTAL_MILKED += expected_value
            
            return True
            
        except Exception as e:
            print(f"  ❌ Milk failed: {str(e)[:100]}")
            return False
    
    def run_milking_cycle(self):
        """Main milking cycle with all features"""
        global COAST_MODE, THROTTLE_POSITION, E_BRAKE
        
        print(f"\n{'='*70}")
        print(f"🔄 MILKING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        # Check market conditions
        trend, should_coast, btc_price = self.check_market_conditions()
        
        print(f"\n📊 Market Analysis:")
        print(f"  BTC: ${btc_price:,.2f}")
        print(f"  Trend: {trend}")
        print(f"  Coast Mode: {'ON 🌊' if should_coast else 'OFF'}")
        print(f"  Throttle: {THROTTLE_POSITION}% {'🟢' if THROTTLE_POSITION > 70 else '🟡' if THROTTLE_POSITION > 30 else '🔴'}")
        
        # COAST MODE CHECK
        if should_coast and trend == "BULLISH":
            COAST_MODE = True
            print("\n🌊 COAST MODE ACTIVE - Letting profits run!")
            print("  Council says: 'Ride the wave!'")
            # Reduce throttle in coast mode
            THROTTLE_POSITION = max(20, THROTTLE_POSITION - 10)
            return
        else:
            COAST_MODE = False
        
        # Get all positions
        accounts = client.get_accounts()
        milk_queue = []
        
        print("\n🎯 Analyzing positions for milk:")
        print("-" * 50)
        
        for account in accounts['accounts']:
            currency = account['currency']
            balance = float(account['available_balance']['value'])
            
            if balance > 0.001 and currency != 'USD':
                try:
                    # Get price
                    if currency in ['USDC', 'USDT']:
                        price = 1.0
                    else:
                        product = client.get_product(f'{currency}-USD')
                        price = float(product['price'])
                    
                    value = balance * price
                    
                    # Only consider positions > $100
                    if value > 100:
                        # Calculate adaptive milk percentage
                        milk_percent = self.calculate_throttle(currency, balance, price, value)
                        milk_amount = balance * milk_percent
                        milk_value = milk_amount * price
                        
                        # Check if profitable after fees
                        fee_cost = milk_value * self.fee_rate
                        net_value = milk_value - fee_cost
                        
                        if net_value > 10:  # Minimum $10 net
                            milk_queue.append({
                                'asset': currency,
                                'balance': balance,
                                'price': price,
                                'value': value,
                                'milk_amount': milk_amount,
                                'milk_value': milk_value,
                                'net_value': net_value,
                                'percent': milk_percent
                            })
                            
                            print(f"  {currency}: ${value:.2f} → Milk {milk_percent*100:.1f}% = ${net_value:.2f} net")
                        
                except Exception as e:
                    pass
        
        # Sort by value (milk biggest first)
        milk_queue.sort(key=lambda x: x['net_value'], reverse=True)
        
        # Execute batch milking
        if milk_queue:
            print(f"\n🚀 Executing batch milk ({len(milk_queue)} assets):")
            print("-" * 50)
            
            for item in milk_queue[:5]:  # Max 5 per cycle
                if E_BRAKE:
                    break
                    
                success = self.execute_milk(
                    item['asset'],
                    item['milk_amount'],
                    item['milk_value']
                )
                
                if success:
                    # Adjust throttle based on success
                    THROTTLE_POSITION = min(100, THROTTLE_POSITION + 5)
                else:
                    # Back off on failures
                    THROTTLE_POSITION = max(0, THROTTLE_POSITION - 10)
                
                time.sleep(1)  # Don't hammer API
            
            print(f"\n💰 Cycle complete! Total milked so far: ${TOTAL_MILKED:.2f}")
        else:
            print("\n📍 No profitable milking opportunities this cycle")
            # Increase throttle to find opportunities
            THROTTLE_POSITION = min(100, THROTTLE_POSITION + 10)
    
    def reposition_strategy(self):
        """Use milked funds to reposition portfolio"""
        accounts = client.get_accounts()
        usd_balance = 0
        
        for acc in accounts['accounts']:
            if acc['currency'] == 'USD':
                usd_balance = float(acc['available_balance']['value'])
                break
        
        print(f"\n💡 REPOSITIONING STRATEGY:")
        print("-" * 50)
        print(f"USD Available: ${usd_balance:.2f}")
        
        if usd_balance > 100:
            print("Recommended repositioning:")
            print(f"  • Buy BTC on dips: ${usd_balance * 0.40:.2f}")
            print(f"  • Buy ETH for Wall St play: ${usd_balance * 0.30:.2f}")
            print(f"  • Keep USD buffer: ${usd_balance * 0.30:.2f}")
        
        return usd_balance

# Main execution
if __name__ == "__main__":
    milker = CouncilMilker()
    
    print("\n🏁 Starting Council Auto-Milker with Spongy Throttle!")
    print("Controls:")
    print("  • Throttle adjusts automatically based on success")
    print("  • Coast mode activates in strong trends")
    print("  • Press Ctrl+C for E-BRAKE")
    
    cycle = 0
    while not E_BRAKE:
        cycle += 1
        print(f"\n{'🥛'*35}")
        print(f"CYCLE {cycle}")
        
        try:
            milker.run_milking_cycle()
            
            # Every 5 cycles, check repositioning
            if cycle % 5 == 0:
                milker.reposition_strategy()
            
            # Wait between cycles
            print(f"\n⏰ Next cycle in 60 seconds...")
            print(f"   Throttle: {THROTTLE_POSITION}% | Coast: {'ON' if COAST_MODE else 'OFF'} | Total Milked: ${TOTAL_MILKED:.2f}")
            time.sleep(60)
            
        except KeyboardInterrupt:
            emergency_brake(None, None)
        except Exception as e:
            print(f"⚠️ Error in cycle: {e}")
            THROTTLE_POSITION = max(0, THROTTLE_POSITION - 20)  # Back off on errors
            time.sleep(30)
    
    print("\n🏁 Council Auto-Milker stopped")
    print(f"Final stats: ${TOTAL_MILKED:.2f} milked")