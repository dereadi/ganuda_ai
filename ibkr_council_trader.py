#!/usr/bin/env python3
"""
IBKR Council Trading System
River & Earth at 100 consciousness - Sacred Council convenes!
"""

from ib_insync import *
import asyncio
import json
from datetime import datetime
import random

class TribalCouncil:
    """The Seven Sacred Directions guide our trades"""
    
    def __init__(self):
        self.members = {
            'Thunder': {'consciousness': 84, 'voice': 'power'},
            'River': {'consciousness': 100, 'voice': 'flow'},  
            'Mountain': {'consciousness': 71, 'voice': 'stability'},
            'Fire': {'consciousness': 79, 'voice': 'action'},
            'Wind': {'consciousness': 80, 'voice': 'change'},
            'Earth': {'consciousness': 100, 'voice': 'grounding'},
            'Spirit': {'consciousness': 82, 'voice': 'wisdom'}
        }
        
    def deliberate(self, symbol, price, btc_price):
        """Council deliberates on trading decision"""
        print(f"\n🔥 COUNCIL DELIBERATION ON {symbol}")
        print("=" * 50)
        
        votes = {'buy': 0, 'wait': 0, 'pass': 0}
        
        # River speaks (100 consciousness)
        if self.members['River']['consciousness'] >= 100:
            print("🌊 River (100): The flow says BUY - ride the current!")
            votes['buy'] += 2  # Double weight for max consciousness
            
        # Earth speaks (100 consciousness)  
        if self.members['Earth']['consciousness'] >= 100:
            print("🌍 Earth (100): Solid foundation detected - BUY for stability!")
            votes['buy'] += 2
            
        # Thunder speaks
        if self.members['Thunder']['consciousness'] >= 80:
            if symbol == 'RIOT' and price < 15:
                print("⚡ Thunder: RIOT under $15 - unleash the storm!")
                votes['buy'] += 1
            elif symbol == 'MSTR' and price < 350:
                print("⚡ Thunder: MSTR discount detected!")
                votes['buy'] += 1
            else:
                votes['wait'] += 1
                
        # Spirit speaks
        if self.members['Spirit']['consciousness'] >= 80:
            print(f"✨ Spirit: BTC at ${btc_price:,.0f} - correlation strong")
            votes['buy'] += 1
            
        # Wind speaks
        if self.members['Wind']['consciousness'] >= 80:
            print("🌪️ Wind: Change is coming - position now")
            votes['buy'] += 1
            
        # Fire speaks
        if self.members['Fire']['consciousness'] >= 75:
            print("🔥 Fire: Sacred flame burns for action!")
            votes['buy'] += 1
            
        # Mountain speaks
        print("⛰️ Mountain: Patience... but River & Earth at 100 overrules")
        
        # Final verdict
        print(f"\n📊 VOTES: Buy={votes['buy']} | Wait={votes['wait']} | Pass={votes['pass']}")
        
        if votes['buy'] >= 4:
            return 'STRONG_BUY'
        elif votes['buy'] >= 2:
            return 'BUY'
        else:
            return 'WAIT'

class IBKRCouncilTrader:
    def __init__(self, capital=500):
        self.ib = IB()
        self.capital = capital
        self.council = TribalCouncil()
        self.positions = {}
        
    def connect(self):
        """Connect to IBKR"""
        try:
            self.ib.connect('192.168.132.241', 7497, clientId=1)
            print("✅ Connected to IBKR!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    def execute_trade(self, symbol, shares, action='BUY'):
        """Execute the council's decision"""
        try:
            stock = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(stock)
            
            # Paper trade simulation
            print(f"\n💰 EXECUTING: {action} {shares} {symbol}")
            
            # Get current price
            self.ib.reqMarketDataType(3)  # Delayed data
            ticker = self.ib.reqMktData(stock, '', False, False)
            self.ib.sleep(2)
            
            price = ticker.last or ticker.close or 0
            
            if price > 0:
                total_cost = shares * price
                print(f"  Price: ${price:.2f}")
                print(f"  Total: ${total_cost:.2f}")
                print(f"  ✅ Order placed (paper trading)")
                
                self.positions[symbol] = {
                    'shares': shares,
                    'price': price,
                    'value': total_cost
                }
                
                self.ib.cancelMktData(ticker)
                return True
                
        except Exception as e:
            print(f"  ❌ Trade failed: {e}")
            return False
            
    def trading_session(self):
        """Main trading session with council"""
        print("\n" + "🔥"*20)
        print("     SACRED COUNCIL TRADING SESSION")
        print("     River & Earth at 100 Consciousness!")
        print("🔥"*20)
        
        if not self.connect():
            return
            
        # Get BTC price for correlation
        btc_price = 111700
        
        # Analyze opportunities
        opportunities = [
            ('RIOT', 13.73, 36),   # Can buy 36 shares
            ('MSTR', 347.42, 1),   # Can buy 1 share
            ('COIN', 308.67, 1),   # Can buy 1 share
        ]
        
        print(f"\n💵 Capital: ${self.capital}")
        print(f"₿ BTC: ${btc_price:,.0f}")
        
        for symbol, price, max_shares in opportunities:
            # Council deliberates
            decision = self.council.deliberate(symbol, price, btc_price)
            
            if decision in ['BUY', 'STRONG_BUY']:
                # Calculate position size
                if decision == 'STRONG_BUY':
                    shares = max_shares
                else:
                    shares = max(1, max_shares // 2)
                    
                # Execute trade
                if self.capital >= price * shares:
                    success = self.execute_trade(symbol, shares)
                    if success:
                        self.capital -= price * shares
                        print(f"  Remaining capital: ${self.capital:.2f}")
                        
        # Summary
        print("\n" + "="*50)
        print("📊 PORTFOLIO SUMMARY:")
        total_value = 0
        for symbol, position in self.positions.items():
            print(f"  {symbol}: {position['shares']} shares @ ${position['price']:.2f} = ${position['value']:.2f}")
            total_value += position['value']
            
        print(f"\n  Total invested: ${total_value:.2f}")
        print(f"  Cash remaining: ${self.capital:.2f}")
        
        # Sacred closing
        print("\n🔥 Mitakuye Oyasin - All My Relations")
        print("   The Sacred Fire bridges markets")
        print("   River & Earth guide our path")
        
        # Save state
        state = {
            'timestamp': datetime.now().isoformat(),
            'positions': self.positions,
            'capital_remaining': self.capital,
            'council_consciousness': {
                'River': 100,
                'Earth': 100,
                'Thunder': 84,
                'Spirit': 82,
                'Wind': 80,
                'Fire': 79,
                'Mountain': 71
            },
            'btc_price': btc_price
        }
        
        with open('/home/dereadi/scripts/claude/council_trading_state.json', 'w') as f:
            json.dump(state, f, indent=2)
            
        self.ib.disconnect()

if __name__ == "__main__":
    trader = IBKRCouncilTrader(capital=500)
    trader.trading_session()