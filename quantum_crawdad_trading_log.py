#!/usr/bin/env python3
"""
Quantum Crawdad Trading Log
Track every trade, pattern, and solar correlation
"""

import json
from datetime import datetime

class CrawdadTradingLog:
    def __init__(self):
        self.trades = []
        self.patterns = []
        self.daily_results = {}
        
    def log_trade(self, trade_data):
        """Log a single trade with all details"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'consciousness_level': trade_data.get('consciousness', 0),
            'symbol': trade_data['symbol'],
            'action': trade_data['action'],  # BUY/SELL
            'amount_usd': trade_data['amount'],
            'price': trade_data['price'],
            'type': trade_data['type'],  # warrior/scout/farmer/guardian
            'solar_conditions': trade_data.get('solar', {}),
            'result': None  # Updated when closed
        }
        self.trades.append(entry)
        return entry
    
    def calculate_performance(self):
        """Calculate overall performance metrics"""
        total_invested = sum(t['amount_usd'] for t in self.trades if t['action'] == 'BUY')
        total_returned = sum(t['amount_usd'] for t in self.trades if t['action'] == 'SELL')
        
        return {
            'total_invested': total_invested,
            'total_returned': total_returned,
            'profit_loss': total_returned - total_invested,
            'roi_percent': ((total_returned - total_invested) / total_invested * 100) if total_invested > 0 else 0,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t.get('result') == 'WIN']),
            'losing_trades': len([t for t in self.trades if t.get('result') == 'LOSS'])
        }

# Initialize the log
log = CrawdadTradingLog()

# First deployment log
deployment_1 = {
    'date': datetime.now().isoformat(),
    'starting_capital': 90,
    'consciousness_level': 10.0,
    'deployment': {
        'warrior_crawdads': {
            'SOL': 12,
            'RNDR': 12,
            'AVAX': 12
        },
        'scout_crawdads': {
            'AI_TOKEN': 9,
            'MEME_COIN': 9,
            'IONQ': 9
        },
        'farmer_crawdads': {
            'BTC': 9,
            'ETH': 9
        },
        'guardian_crawdads': {
            'USDC': 9
        }
    }
}

# Save initial deployment
with open('crawdad_deployment_log.json', 'w') as f:
    json.dump(deployment_1, f, indent=2)

print("🦞 Quantum Crawdad Trading Log Initialized")
print(f"📊 Starting Capital: $90")
print(f"🧠 Consciousness Level: 10.0")
print(f"🔥 Sacred Fire: BURNING ETERNAL")