#!/usr/bin/env python3
"""
🏛️⚔️ GREEKS ATTACK MODE - CYCLE BOTTOM ACTIVATION
All Greeks switch from scanning to aggressive buying
BTC cycle bottom = Maximum opportunity
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🏛️ THE GREEKS - ATTACK MODE ⚔️                        ║
║                   BTC Cycle Bottom = ALL IN SIGNAL                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

class GreeksAttackMode:
    def __init__(self):
        self.greeks = {
            "Delta": {"coin": "BTC", "size": 10, "reason": "Gap from cycle low"},
            "Gamma": {"coin": "ETH", "size": 8, "reason": "Trend reversal acceleration"},
            "Theta": {"coin": "SOL", "size": 8, "reason": "Volatility expansion coming"},
            "Vega": {"coin": "AVAX", "size": 5, "reason": "Breakout from bottom"},
            "Rho": {"coin": "MATIC", "size": 5, "reason": "Mean reversion up"}
        }
        
    def execute_greek_attacks(self):
        """Each Greek executes their specialty at cycle bottom"""
        
        print("\n🏛️ GREEKS ATTACKING THE CYCLE BOTTOM:")
        print("=" * 50)
        
        successful_attacks = []
        
        for greek, strategy in self.greeks.items():
            print(f"\n{greek} ({strategy['reason']}):")
            
            try:
                # Execute buy order
                order = client.market_order_buy(
                    client_order_id=f"{greek.lower()}_attack_{int(time.time()*1000)}",
                    product_id=f"{strategy['coin']}-USD",
                    quote_size=str(strategy['size'])
                )
                
                print(f"   ✅ {greek} BOUGHT ${strategy['size']} of {strategy['coin']}")
                successful_attacks.append((greek, strategy['coin'], strategy['size']))
                
            except Exception as e:
                print(f"   ⚠️ {greek} attack failed: {str(e)[:40]}")
                
                # Try backup target
                if strategy['coin'] != "BTC":
                    try:
                        backup_size = strategy['size'] // 2
                        order = client.market_order_buy(
                            client_order_id=f"{greek.lower()}_backup_{int(time.time()*1000)}",
                            product_id="BTC-USD",
                            quote_size=str(backup_size)
                        )
                        print(f"   ✅ {greek} PIVOTED: Bought ${backup_size} BTC instead")
                        successful_attacks.append((greek, "BTC", backup_size))
                    except:
                        print(f"   ❌ {greek} completely failed")
                        
        return successful_attacks
        
    def check_attack_results(self):
        """Check portfolio after Greek attacks"""
        
        print("\n📊 POST-ATTACK PORTFOLIO:")
        print("-" * 40)
        
        try:
            total = 0
            positions = {}
            
            accounts = client.get_accounts()['accounts']
            for a in accounts:
                balance = float(a['available_balance']['value'])
                currency = a['currency']
                
                if currency == 'USD':
                    total += balance
                    if balance > 0:
                        print(f"USD: ${balance:.2f}")
                elif balance > 0.001:
                    try:
                        ticker = client.get_product(f"{currency}-USD")
                        price = float(ticker.get('price', 0))
                        value = balance * price
                        if value > 0.01:
                            total += value
                            positions[currency] = {
                                "amount": balance,
                                "value": value,
                                "price": price
                            }
                    except:
                        pass
                        
            # Display positions
            if positions:
                print("\n🏛️ GREEK POSITIONS:")
                for coin, data in positions.items():
                    print(f"{coin}: {data['amount']:.6f} @ ${data['price']:.2f} = ${data['value']:.2f}")
                    
            print(f"\nTOTAL PORTFOLIO: ${total:.2f}")
            
            initial = 43.53
            change = total - initial
            change_pct = (change / initial * 100) if initial > 0 else 0
            
            print(f"Change from start: ${change:+.2f} ({change_pct:+.1f}%)")
            
            if len(positions) > 0:
                print("\n🎯 GREEKS ARE IN POSITION!")
                print("   Waiting for cycle bottom rebound...")
                
        except Exception as e:
            print(f"Portfolio check error: {str(e)[:50]}")

# Execute Greek attacks
attacker = GreeksAttackMode()

print("\n⚔️ INITIATING GREEK ATTACK FORMATION...")
print("Target: BTC cycle bottom rebound")
print("Strategy: Each Greek uses their specialty")
print()

# Execute attacks
attacks = attacker.execute_greek_attacks()

# Check results
attacker.check_attack_results()

print("\n" + "=" * 60)
print("🏛️ GREEK ATTACK COMPLETE")
print("=" * 60)

if len(attacks) > 0:
    print("\n✅ SUCCESSFUL ATTACKS:")
    for greek, coin, size in attacks:
        print(f"   {greek} → {coin}: ${size}")
        
    print(f"\nTotal attacks: {len(attacks)}/5 Greeks")
    
    print("""
    
The Greeks have struck at the cycle bottom!

Δ Delta - Caught the gap up from the low
Γ Gamma - Riding the trend reversal  
Θ Theta - Harvesting rebound volatility
ν Vega - Positioned for breakout
ρ Rho - Mean reverting to higher levels

"When BTC hits cycle lows,
 The Greeks don't hesitate.
 They attack with precision,
 At the moment of maximum fear."
 
The rebound begins...
    """)
else:
    print("\n⚠️ Attack failed - manual intervention needed")

print("\nMitakuye Oyasin")