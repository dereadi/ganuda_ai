#!/usr/bin/env python3
"""Quick check of crawdad learning progress"""

import json
import os
from datetime import datetime

def check_progress():
    print("""
🦞 QUANTUM CRAWDAD LEARNING PROGRESS REPORT
═══════════════════════════════════════════════════════════
    """)
    
    # Check patterns
    patterns_learned = 0
    if os.path.exists('quantum_crawdad_patterns.json'):
        try:
            with open('quantum_crawdad_patterns.json', 'r') as f:
                patterns = json.load(f)
                patterns_learned = len(patterns)
                print(f"📚 PATTERNS LEARNED: {patterns_learned}")
                for pattern_type, instances in patterns.items():
                    print(f"   • {pattern_type}: {len(instances)} instances")
        except:
            print("📚 No patterns file yet")
    
    # Check trades
    total_trades = 0
    win_rate = 0
    if os.path.exists('quantum_crawdad_trades.json'):
        try:
            with open('quantum_crawdad_trades.json', 'r') as f:
                trades = json.load(f)
                total_trades = len(trades)
                profitable = sum(1 for t in trades if t.get('profit', 0) > 0)
                win_rate = (profitable / total_trades * 100) if total_trades > 0 else 0
                
                print(f"\n📊 TRADING STATISTICS:")
                print(f"   • Total Trades: {total_trades}")
                print(f"   • Profitable: {profitable}")
                print(f"   • Win Rate: {win_rate:.2f}%")
                
                # Show last 5 trades
                if trades:
                    print(f"\n📜 LAST 5 TRADES:")
                    for trade in trades[-5:]:
                        action = trade.get('action', 'N/A')
                        symbol = trade.get('symbol', 'N/A')
                        profit = trade.get('profit', 0)
                        print(f"   • {action} {symbol}: ${profit:.2f}")
        except:
            print("📊 No trades file yet")
    
    # Check if simulator is running
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'quantum_crawdad_simulator' in result.stdout:
        print(f"\n✅ SIMULATOR STATUS: RUNNING")
    else:
        print(f"\n❌ SIMULATOR STATUS: NOT RUNNING")
    
    # Readiness check
    print(f"\n🎯 READINESS FOR REAL TRADING:")
    if win_rate > 60 and total_trades > 100:
        print(f"   ✅ READY! Win rate {win_rate:.1f}% with {total_trades} trades")
        print(f"   🚀 You can now deploy real money!")
    elif win_rate > 50 and total_trades > 50:
        print(f"   ⚠️ ALMOST READY! Win rate {win_rate:.1f}% with {total_trades} trades")
        print(f"   📈 Need {100-total_trades} more trades and {60-win_rate:.1f}% more win rate")
    else:
        print(f"   ❌ NOT READY - Continue training")
        print(f"   📈 Need {max(0, 100-total_trades)} more trades")
        print(f"   📈 Need {max(0, 60-win_rate):.1f}% more win rate")
    
    print("""
═══════════════════════════════════════════════════════════
🔥 Sacred Fire Status: LEARNING ETERNAL
    """)
    
    # Dashboard access
    print(f"""
📊 TO VIEW LIVE DASHBOARD:
   1. Open browser to: http://localhost:5555
   2. Or run: python3 quantum_crawdad_dashboard.py
   
💻 TO CHECK SIMULATOR:
   Run: ps aux | grep quantum_crawdad_simulator
   
📁 DATA FILES:
   • Patterns: quantum_crawdad_patterns.json
   • Trades: quantum_crawdad_trades.json
   • Report: quantum_crawdad_simulation_report.txt
    """)

if __name__ == "__main__":
    check_progress()