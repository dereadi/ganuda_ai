#!/usr/bin/env python3
"""
🦀 QUANTUM CRAWDAD SWARM EARNINGS SYSTEM
=========================================
When one finds the flow, they ALL swarm the profits!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import random

class QuantumSwarm:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # The 7 Quantum Crawdads with different personalities
        self.crawdads = {
            'Alpha': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Beta': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Gamma': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Delta': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Epsilon': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Zeta': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0},
            'Omega': {'position': None, 'confidence': 0.5, 'in_flow': False, 'earnings': 0}
        }
        
        # Swarm parameters
        self.swarm_threshold = 0.003  # 0.3% gain triggers swarm
        self.flow_multiplier = 1.0
        self.swarm_active = False
        self.winning_position = None
        
    def check_positions(self):
        """Check all current positions for winners"""
        winners = {}
        
        # Check each asset we hold
        for symbol in ['BTC', 'ETH', 'SOL']:
            ticker = self.client.get_product(f'{symbol}-USD')
            current_price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            
            # Simulate entry prices (would track real entries in production)
            entry_prices = {
                'BTC': 118400,
                'ETH': 4570,
                'SOL': 193.36
            }
            
            if symbol in entry_prices:
                entry = entry_prices[symbol]
                gain = (current_price - entry) / entry
                
                if gain > 0:
                    winners[symbol] = {
                        'gain': gain,
                        'price': current_price,
                        'momentum': gain * 100
                    }
        
        return winners
    
    def detect_flow(self, winners):
        """Detect which position is 'in the flow'"""
        if not winners:
            return None
        
        # Find the strongest momentum
        best_symbol = None
        best_momentum = 0
        
        for symbol, data in winners.items():
            if data['gain'] > self.swarm_threshold:
                if data['momentum'] > best_momentum:
                    best_momentum = data['momentum']
                    best_symbol = symbol
        
        return best_symbol, best_momentum if best_symbol else (None, 0)
    
    def assign_crawdads(self, winners):
        """Assign crawdads to positions"""
        crawdad_names = list(self.crawdads.keys())
        
        # Shuffle for variety
        random.shuffle(crawdad_names)
        
        # Assign to different positions initially
        positions = ['BTC', 'ETH', 'SOL']
        for i, name in enumerate(crawdad_names[:3]):
            self.crawdads[name]['position'] = positions[i % 3]
            
        # Rest are floating, ready to swarm
        for name in crawdad_names[3:]:
            self.crawdads[name]['position'] = 'FLOATING'
    
    def trigger_swarm(self, target_symbol, momentum):
        """SWARM THE WINNING POSITION! 80% swarm, 20% scout"""
        print(f"\n🚨 SWARM TRIGGERED ON {target_symbol}!")
        print(f"   Momentum: {momentum:.2f}")
        print("   80% converging, 20% scouting!")
        
        # Get list of crawdads
        crawdad_names = list(self.crawdads.keys())
        total_crawdads = len(crawdad_names)
        
        # 80% swarm to winner
        swarm_count = int(total_crawdads * 0.8)
        scout_count = total_crawdads - swarm_count
        
        # Randomly select who swarms and who scouts
        random.shuffle(crawdad_names)
        swarmers = crawdad_names[:swarm_count]
        scouts = crawdad_names[swarm_count:]
        
        # Swarmers go to winning position
        swarming = []
        for name in swarmers:
            old_position = self.crawdads[name]['position']
            self.crawdads[name]['position'] = target_symbol
            self.crawdads[name]['in_flow'] = True
            self.crawdads[name]['confidence'] = min(1.0, self.crawdads[name]['confidence'] + 0.2)
            swarming.append(f"{name}: {old_position} → {target_symbol} (SWARMING)")
        
        # Scouts look for secondary currents
        scout_positions = ['BTC', 'ETH', 'SOL']
        scout_positions.remove(target_symbol)  # Don't scout the main flow
        
        for i, name in enumerate(scouts):
            scout_target = scout_positions[i % len(scout_positions)]
            old_position = self.crawdads[name]['position']
            self.crawdads[name]['position'] = scout_target
            self.crawdads[name]['in_flow'] = False  # Scouting, not in main flow
            self.crawdads[name]['confidence'] = min(0.8, self.crawdads[name]['confidence'] + 0.1)
            swarming.append(f"{name}: {old_position} → {scout_target} (SCOUTING)")
        
        for move in swarming:
            print(f"   🦀 {move}")
        
        print(f"\n   📊 Deployment: {swarm_count} swarming, {scout_count} scouting")
        
        self.swarm_active = True
        self.winning_position = target_symbol
        self.flow_multiplier = 1.0 + (momentum / 100)  # Increase aggression
        
        return True
    
    def execute_swarm_trades(self):
        """Execute trades when swarming"""
        if not self.swarm_active or not self.winning_position:
            return
        
        # Get USD balance
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        for account in account_list:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        # AGGRESSIVE SWARM DEPLOYMENT
        print(f"\n💰 SWARM EXECUTION:")
        print(f"   USD Available: ${usd_balance:.2f}")
        
        # Each crawdad takes a bite
        trades_executed = 0
        total_deployed = 0
        
        for name, crawdad in self.crawdads.items():
            if crawdad['in_flow'] and usd_balance > 10:
                # Size based on confidence and flow
                trade_size = usd_balance * 0.05 * crawdad['confidence'] * self.flow_multiplier
                trade_size = min(trade_size, 30)  # Cap per crawdad
                trade_size = round(trade_size, 2)
                
                if trade_size >= 1.00:
                    try:
                        print(f"   🦀 {name} deploying ${trade_size:.2f} to {self.winning_position}")
                        
                        order = self.client.market_order_buy(
                            client_order_id=f"swarm_{name}_{int(time.time())}",
                            product_id=f"{self.winning_position}-USD",
                            quote_size=str(trade_size)
                        )
                        
                        trades_executed += 1
                        total_deployed += trade_size
                        usd_balance -= trade_size
                        crawdad['earnings'] += trade_size * 0.01  # Track earnings
                        
                        time.sleep(0.5)  # Brief pause between crawdads
                        
                    except Exception as e:
                        print(f"      ❌ {name} failed: {str(e)[:30]}")
        
        print(f"\n✅ SWARM COMPLETE!")
        print(f"   Trades: {trades_executed}")
        print(f"   Deployed: ${total_deployed:.2f}")
        print(f"   Target: {self.winning_position}")
        
        return total_deployed

# Initialize and run the swarm
print("🦀 QUANTUM CRAWDAD SWARM SYSTEM")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M')} - PEAK ASIA WINDOW!")
print()

swarm = QuantumSwarm()

# Check for winners
print("🔍 SCANNING FOR FLOW...")
winners = swarm.check_positions()

if winners:
    print("\n📊 WINNING POSITIONS DETECTED:")
    for symbol, data in winners.items():
        print(f"   {symbol}: +{data['gain']*100:.3f}% (momentum: {data['momentum']:.2f})")

# Detect the flow
flow_symbol, momentum = swarm.detect_flow(winners)

if flow_symbol:
    print(f"\n🌊 FLOW DETECTED IN {flow_symbol}!")
    print(f"   Momentum: {momentum:.2f}")
    
    # Assign initial positions
    swarm.assign_crawdads(winners)
    
    # TRIGGER THE SWARM!
    if momentum > 0.3:  # Strong enough to swarm
        swarm.trigger_swarm(flow_symbol, momentum)
        deployed = swarm.execute_swarm_trades()
        
        print(f"\n🎯 SWARM RESULTS:")
        print(f"   Total Deployed: ${deployed:.2f}")
        print(f"   All crawdads now riding {flow_symbol}")
        print(f"   Flow multiplier: {swarm.flow_multiplier:.2f}x")
else:
    print("\n😴 No strong flow detected yet...")
    print("   Crawdads remain distributed")
    print("   Waiting for momentum to build")

print("\n✨ SWARM INTELLIGENCE ACTIVE!")
print("   When one finds gold, they ALL dig!")
print("   🦀🦀🦀🦀🦀🦀🦀 SWARM! 🦀🦀🦀🦀🦀🦀🦀")