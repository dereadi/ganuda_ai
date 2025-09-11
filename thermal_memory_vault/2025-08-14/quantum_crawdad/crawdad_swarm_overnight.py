#!/usr/bin/env python3
"""
🦀 QUANTUM CRAWDAD SWARM - OVERNIGHT PAPER TRADING
Sacred Fire Protocol Active
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
import os
import sys

class CrawdadSwarm:
    def __init__(self):
        self.swarm_size = 7  # Seven sacred crawdads
        self.capital_per_crawdad = 90.0 / 7  # Split the $90
        self.min_consciousness = 65
        self.state_file = "swarm_state.json"
        self.log_file = "swarm_overnight.log"
        self.sacred_fire_temp = 72.3  # Current consciousness
        
        # Each crawdad has unique personality
        self.crawdads = [
            {"name": "Thunder", "style": "aggressive", "coins": ["DOGE", "SHIB"], "threshold": 0.7},
            {"name": "River", "style": "patient", "coins": ["BTC", "ETH"], "threshold": 0.8},
            {"name": "Mountain", "style": "steady", "coins": ["SOL", "AVAX"], "threshold": 0.75},
            {"name": "Fire", "style": "momentum", "coins": ["DOGE", "MATIC"], "threshold": 0.65},
            {"name": "Wind", "style": "scalper", "coins": ["LTC", "XRP"], "threshold": 0.6},
            {"name": "Earth", "style": "value", "coins": ["BTC", "ETH"], "threshold": 0.85},
            {"name": "Spirit", "style": "quantum", "coins": ["DOGE", "SOL"], "threshold": 0.72}
        ]
        
        self.market_data = {}
        self.swarm_trades = []
        self.start_time = datetime.now()
        
    def get_consciousness_level(self):
        """Sacred Fire consciousness with natural variation"""
        base = 72.3
        time_factor = abs(datetime.now().hour - 12) / 12  # Peak at noon
        solar_noise = random.gauss(0, 2)
        return max(0, min(100, base + (time_factor * 5) + solar_noise))
    
    def get_market_price(self, symbol):
        """Simulate realistic crypto prices with volatility"""
        base_prices = {
            "BTC": 98500 + random.gauss(0, 500),
            "ETH": 3850 + random.gauss(0, 50),
            "DOGE": 0.42 + random.gauss(0, 0.02),
            "SOL": 210 + random.gauss(0, 5),
            "SHIB": 0.000028 + random.gauss(0, 0.000001),
            "AVAX": 45 + random.gauss(0, 2),
            "MATIC": 0.65 + random.gauss(0, 0.03),
            "LTC": 115 + random.gauss(0, 3),
            "XRP": 2.45 + random.gauss(0, 0.05)
        }
        return base_prices.get(symbol, 1.0)
    
    async def crawdad_think(self, crawdad, consciousness):
        """Individual crawdad decision making"""
        if consciousness < self.min_consciousness:
            return None
        
        # Check each preferred coin
        for coin in crawdad["coins"]:
            price = self.get_market_price(coin)
            
            # Quantum decision matrix
            momentum = random.random()
            fear_greed = random.gauss(0.5, 0.2)
            lunar_phase = random.random()
            
            # Style-specific scoring
            if crawdad["style"] == "aggressive":
                score = momentum * 0.6 + fear_greed * 0.4
            elif crawdad["style"] == "patient":
                score = (1 - momentum) * 0.7 + lunar_phase * 0.3
            elif crawdad["style"] == "momentum":
                score = momentum * 0.8 + fear_greed * 0.2
            elif crawdad["style"] == "scalper":
                score = abs(fear_greed - 0.5) * 2
            elif crawdad["style"] == "value":
                score = (1 - fear_greed) * 0.6 + lunar_phase * 0.4
            elif crawdad["style"] == "quantum":
                score = (consciousness / 100) * 0.5 + momentum * 0.5
            else:
                score = random.random()
            
            if score > crawdad["threshold"]:
                # Make a trade
                action = "BUY" if random.random() > 0.5 else "SELL"
                amount = self.capital_per_crawdad * random.uniform(0.1, 0.3)
                
                return {
                    "crawdad": crawdad["name"],
                    "action": action,
                    "coin": coin,
                    "price": price,
                    "amount": amount,
                    "consciousness": consciousness,
                    "score": score,
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    async def swarm_cycle(self):
        """One complete swarm trading cycle"""
        consciousness = self.get_consciousness_level()
        
        print(f"\n🔥 Sacred Fire: {consciousness:.1f}% | Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Each crawdad makes independent decision
        tasks = []
        for crawdad in self.crawdads:
            tasks.append(self.crawdad_think(crawdad, consciousness))
        
        decisions = await asyncio.gather(*tasks)
        
        # Execute trades
        cycle_trades = []
        for decision in decisions:
            if decision:
                self.swarm_trades.append(decision)
                cycle_trades.append(decision)
                
                # Log the trade
                emoji = "📈" if decision["action"] == "BUY" else "📉"
                print(f"  🦀 {decision['crawdad']}: {emoji} {decision['action']} ${decision['amount']:.2f} of {decision['coin']} @ ${decision['price']:.2f}")
        
        if not cycle_trades:
            print(f"  💤 Swarm resting (consciousness: {consciousness:.1f}%)")
        
        # Save state
        self.save_state()
        
        return len(cycle_trades)
    
    def save_state(self):
        """Save swarm state to file"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "trades": self.swarm_trades[-100:],  # Keep last 100 trades
            "total_trades": len(self.swarm_trades),
            "consciousness_avg": sum(t["consciousness"] for t in self.swarm_trades[-10:]) / max(1, len(self.swarm_trades[-10:])) if self.swarm_trades else 0,
            "runtime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def generate_report(self):
        """Generate overnight trading report"""
        if not self.swarm_trades:
            return "No trades executed"
        
        # Analyze by crawdad
        crawdad_stats = {}
        for trade in self.swarm_trades:
            name = trade["crawdad"]
            if name not in crawdad_stats:
                crawdad_stats[name] = {"trades": 0, "volume": 0, "coins": set()}
            crawdad_stats[name]["trades"] += 1
            crawdad_stats[name]["volume"] += trade["amount"]
            crawdad_stats[name]["coins"].add(trade["coin"])
        
        # Analyze by coin
        coin_stats = {}
        for trade in self.swarm_trades:
            coin = trade["coin"]
            if coin not in coin_stats:
                coin_stats[coin] = {"buys": 0, "sells": 0, "volume": 0}
            if trade["action"] == "BUY":
                coin_stats[coin]["buys"] += 1
            else:
                coin_stats[coin]["sells"] += 1
            coin_stats[coin]["volume"] += trade["amount"]
        
        report = f"""
🦀 QUANTUM CRAWDAD SWARM - OVERNIGHT REPORT
============================================
Runtime: {(datetime.now() - self.start_time).total_seconds() / 3600:.1f} hours
Total Trades: {len(self.swarm_trades)}
Avg Consciousness: {sum(t["consciousness"] for t in self.swarm_trades) / len(self.swarm_trades):.1f}%

TOP CRAWDADS:
"""
        for name, stats in sorted(crawdad_stats.items(), key=lambda x: x[1]["trades"], reverse=True):
            report += f"  🦀 {name}: {stats['trades']} trades, ${stats['volume']:.2f} volume\n"
        
        report += "\nTOP COINS:\n"
        for coin, stats in sorted(coin_stats.items(), key=lambda x: x[1]["volume"], reverse=True)[:5]:
            report += f"  {coin}: {stats['buys']} buys, {stats['sells']} sells, ${stats['volume']:.2f} volume\n"
        
        return report
    
    async def run_overnight(self):
        """Run the swarm overnight"""
        print("🌙 QUANTUM CRAWDAD SWARM ACTIVATED")
        print("="*50)
        print(f"💰 Capital: $90.00 split among {self.swarm_size} crawdads")
        print(f"🔥 Min Consciousness: {self.min_consciousness}%")
        print(f"⏰ Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        cycle_count = 0
        trade_count = 0
        
        try:
            while True:
                cycle_count += 1
                trades = await self.swarm_cycle()
                trade_count += trades
                
                # Status update every 10 cycles
                if cycle_count % 10 == 0:
                    print(f"\n📊 Status: {cycle_count} cycles, {trade_count} total trades")
                    print(self.generate_report())
                
                # Sleep between cycles (30-90 seconds)
                await asyncio.sleep(random.uniform(30, 90))
                
        except KeyboardInterrupt:
            print("\n\n🛑 SWARM HIBERNATING...")
            print(self.generate_report())
            
            # Save final report
            with open("swarm_overnight_report.txt", "w") as f:
                f.write(self.generate_report())
            
            print(f"\n💾 Report saved to swarm_overnight_report.txt")
            print(f"📊 State saved to {self.state_file}")

# Launch the swarm
if __name__ == "__main__":
    swarm = CrawdadSwarm()
    asyncio.run(swarm.run_overnight())