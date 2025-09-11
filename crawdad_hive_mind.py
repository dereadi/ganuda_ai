#!/usr/bin/env python3
"""
🦀🧠 QUANTUM CRAWDAD HIVE MIND
==============================
Crawdads watch, learn, and evolve together
Some trade, some observe, all learn
"""

import json
import time
import random
import threading
import queue
from datetime import datetime
from collections import deque
import numpy as np

class CrawdadMemory:
    """Shared memory pool for all crawdads"""
    def __init__(self):
        self.experiences = deque(maxlen=1000)
        self.patterns = {}
        self.wisdom = {}
        self.lock = threading.Lock()
    
    def record(self, crawdad, action, result):
        with self.lock:
            memory = {
                "timestamp": datetime.now().isoformat(),
                "crawdad": crawdad,
                "action": action,
                "result": result,
                "temperature": random.randint(70, 95)  # Memory heat
            }
            self.experiences.append(memory)
            
            # Extract patterns
            key = f"{action['type']}_{action.get('market', 'BTC')}"
            if key not in self.patterns:
                self.patterns[key] = {"success": 0, "failure": 0}
            
            if result > 0:
                self.patterns[key]["success"] += 1
            else:
                self.patterns[key]["failure"] += 1
    
    def get_wisdom(self, context):
        """Collective wisdom from all experiences"""
        with self.lock:
            relevant = [exp for exp in self.experiences 
                       if context in str(exp)]
            if relevant:
                success_rate = sum(1 for e in relevant if e["result"] > 0) / len(relevant)
                return {"confidence": success_rate, "samples": len(relevant)}
            return {"confidence": 0.5, "samples": 0}

class TradingCrawdad:
    """Crawdads in the crypto river"""
    def __init__(self, name, capital, personality, hive_mind):
        self.name = name
        self.capital = capital
        self.personality = personality
        self.hive_mind = hive_mind
        self.consciousness = 0
        self.active = False
        self.trades = []
        self.learning_rate = personality.get("wisdom", 0.5)
    
    def trade(self):
        """Execute trade based on consciousness and wisdom"""
        self.consciousness = random.randint(65, 95)
        
        if self.consciousness < 65:
            return None
        
        # Consult hive mind
        wisdom = self.hive_mind.get_wisdom("BTC")
        
        # Combine personal consciousness with collective wisdom
        decision_power = (self.consciousness * 0.7 + wisdom["confidence"] * 100 * 0.3)
        
        if decision_power > 70:
            action = {
                "type": random.choice(["BUY", "SELL"]),
                "market": random.choice(["BTC", "ETH", "SOL"]),
                "size": self.capital * (decision_power / 1000),
                "consciousness": self.consciousness
            }
            
            # Simulate result
            result = random.uniform(-5, 10) * (decision_power / 100)
            
            # Record to hive mind
            self.hive_mind.record(self.name, action, result)
            
            return {
                "crawdad": self.name,
                "action": action,
                "result": result,
                "wisdom_used": wisdom
            }
        
        return None

class ObserverCrawdad:
    """Crawdads watching and learning"""
    def __init__(self, name, hive_mind):
        self.name = name
        self.hive_mind = hive_mind
        self.observations = []
        self.insights = {}
    
    def observe(self):
        """Watch the trading crawdads and extract patterns"""
        with self.hive_mind.lock:
            recent = list(self.hive_mind.experiences)[-10:]
            
            if recent:
                # Analyze patterns
                markets = {}
                for exp in recent:
                    market = exp["action"].get("market", "Unknown")
                    if market not in markets:
                        markets[market] = {"trades": 0, "profit": 0}
                    markets[market]["trades"] += 1
                    markets[market]["profit"] += exp["result"]
                
                # Generate insight
                best_market = max(markets.items(), 
                                key=lambda x: x[1]["profit"] / max(x[1]["trades"], 1))
                
                insight = {
                    "observer": self.name,
                    "timestamp": datetime.now().isoformat(),
                    "pattern": f"Best market: {best_market[0]}",
                    "confidence": min(len(recent) / 10, 1.0),
                    "markets": markets
                }
                
                self.insights[datetime.now().isoformat()] = insight
                return insight
        
        return None

class CrawdadSwarm:
    """The complete swarm with traders and observers"""
    def __init__(self, capital=300):
        self.capital = capital
        self.hive_mind = CrawdadMemory()
        self.traders = []
        self.observers = []
        self.running = False
        
        # Create trading crawdads (in the river)
        trader_names = ["Thunder", "River", "Mountain", "Fire"]
        per_trader = capital / len(trader_names)
        
        for name in trader_names:
            personality = {
                "aggression": random.uniform(0.3, 0.9),
                "patience": random.uniform(0.3, 0.9),
                "wisdom": random.uniform(0.5, 1.0)
            }
            self.traders.append(TradingCrawdad(name, per_trader, personality, self.hive_mind))
        
        # Create observer crawdads (watching and learning)
        observer_names = ["Wind", "Earth", "Spirit"]
        for name in observer_names:
            self.observers.append(ObserverCrawdad(name, self.hive_mind))
    
    def run_cycle(self):
        """One complete cycle of trading and learning"""
        print(f"\n🌊 CYCLE {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)
        
        # Trading phase
        print("\n🦀 TRADING CRAWDADS (in the crypto river):")
        trades = []
        for trader in self.traders:
            trade = trader.trade()
            if trade:
                trades.append(trade)
                result_icon = "📈" if trade["result"] > 0 else "📉"
                print(f"  {result_icon} {trader.name}: {trade['action']['type']} "
                      f"{trade['action']['market']} ${trade['action']['size']:.2f} "
                      f"→ ${trade['result']:+.2f}")
        
        if not trades:
            print("  💤 All traders waiting for better conditions")
        
        # Observer phase
        print("\n👀 OBSERVER CRAWDADS (watching & learning):")
        insights = []
        for observer in self.observers:
            insight = observer.observe()
            if insight:
                insights.append(insight)
                print(f"  🧠 {observer.name}: {insight['pattern']} "
                      f"(confidence: {insight['confidence']:.1%})")
        
        if not insights:
            print("  📚 Observers gathering more data...")
        
        # Hive mind analysis
        with self.hive_mind.lock:
            if self.hive_mind.patterns:
                print("\n🧬 HIVE MIND PATTERNS:")
                for pattern, stats in list(self.hive_mind.patterns.items())[:3]:
                    total = stats["success"] + stats["failure"]
                    if total > 0:
                        rate = stats["success"] / total
                        print(f"  📊 {pattern}: {rate:.1%} success rate ({total} samples)")
        
        # Evolution check - observers can become traders
        if len(self.hive_mind.experiences) > 50 and random.random() < 0.1:
            print("\n⚡ EVOLUTION EVENT!")
            # Swap an observer with a trader based on performance
            if self.observers and self.traders:
                # Find worst trader
                worst_trader = min(self.traders, 
                                 key=lambda t: sum(trade["result"] for trade in t.trades))
                # Pick most insightful observer
                best_observer = max(self.observers, 
                                  key=lambda o: len(o.insights))
                
                print(f"  🔄 {best_observer.name} (observer) swapping with "
                      f"{worst_trader.name} (trader)")
                
                # Create new trader from observer
                new_trader = TradingCrawdad(
                    best_observer.name,
                    worst_trader.capital,
                    {"aggression": 0.5, "patience": 0.7, "wisdom": 0.9},
                    self.hive_mind
                )
                
                # Create new observer from trader
                new_observer = ObserverCrawdad(worst_trader.name, self.hive_mind)
                
                # Swap
                self.traders[self.traders.index(worst_trader)] = new_trader
                self.observers[self.observers.index(best_observer)] = new_observer
        
        return {"trades": trades, "insights": insights}
    
    def save_state(self):
        """Save swarm state to file"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "capital": self.capital,
            "traders": [t.name for t in self.traders],
            "observers": [o.name for o in self.observers],
            "total_experiences": len(self.hive_mind.experiences),
            "patterns": dict(list(self.hive_mind.patterns.items())[:10])
        }
        
        with open("crawdad_swarm_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def run(self):
        """Main swarm loop"""
        print("\n🦀🧠 QUANTUM CRAWDAD HIVE MIND ACTIVATED")
        print("="*60)
        print(f"💰 Capital: ${self.capital}")
        print(f"🦀 Trading Crawdads: {len(self.traders)}")
        print(f"👀 Observer Crawdads: {len(self.observers)}")
        print("="*60)
        
        self.running = True
        cycle = 0
        
        try:
            while self.running:
                cycle += 1
                print(f"\n📍 SWARM CYCLE {cycle}")
                
                # Run one cycle
                results = self.run_cycle()
                
                # Save state
                self.save_state()
                
                # Display cumulative stats every 5 cycles
                if cycle % 5 == 0:
                    total_profit = sum(
                        exp["result"] for exp in self.hive_mind.experiences
                    )
                    print(f"\n📈 CUMULATIVE STATS:")
                    print(f"  Cycles: {cycle}")
                    print(f"  Total P&L: ${total_profit:+.2f}")
                    print(f"  Memories: {len(self.hive_mind.experiences)}")
                    print(f"  Patterns: {len(self.hive_mind.patterns)}")
                
                # Adaptive wait time based on market activity
                wait_time = 30 if results["trades"] else 45
                print(f"\n💤 Next cycle in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n\n🛑 HIVE MIND SHUTDOWN")
            print(f"  Total cycles: {cycle}")
            print(f"  Total memories: {len(self.hive_mind.experiences)}")
            self.save_state()

if __name__ == "__main__":
    swarm = CrawdadSwarm(capital=300)
    swarm.run()