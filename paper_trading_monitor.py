#!/usr/bin/env python3
"""
Paper Trading Monitor - Watch the Crawdads Hunt!
Real-time monitoring of paper trading performance
"""

import json
import time
from datetime import datetime
import os

def load_state():
    """Load current paper trading state"""
    try:
        with open('paper_trading_state.json', 'r') as f:
            return json.load(f)
    except:
        return None

def display_monitor():
    """Display real-time trading monitor"""
    print("\033[2J\033[H")  # Clear screen
    
    print("""
🦞 QUANTUM CRAWDAD PAPER TRADING MONITOR
═══════════════════════════════════════════════════════════════════════════════════
Real-time monitoring of paper trading performance
Press Ctrl+C to exit
═══════════════════════════════════════════════════════════════════════════════════
    """)
    
    while True:
        state = load_state()
        
        if state:
            # Display metrics
            metrics = state.get('metrics', {})
            
            print(f"\n⏰ Last Update: {state.get('timestamp', 'Unknown')}")
            print(f"💰 Capital: ${state.get('capital', 90):.2f}")
            
            print(f"\n📊 PERFORMANCE METRICS:")
            print(f"   Total Trades: {metrics.get('total_trades', 0)}")
            print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
            print(f"   P&L: ${metrics.get('total_pnl', 0):.2f}")
            print(f"   Best Trade: ${metrics.get('best_trade', 0):.2f}")
            print(f"   Worst Trade: ${metrics.get('worst_trade', 0):.2f}")
            
            # Display positions
            positions = state.get('positions', {})
            if positions:
                print(f"\n📈 OPEN POSITIONS ({len(positions)}):")
                for symbol, pos in positions.items():
                    print(f"   {symbol}: ${pos.get('size', 0):.2f} @ ${pos.get('entry_price', 0):.2f}")
            else:
                print(f"\n📈 No open positions - Waiting for opportunities...")
            
            # Display recent trades
            trades = state.get('trades', [])
            if trades:
                print(f"\n🔄 RECENT TRADES:")
                for trade in trades[-5:]:  # Last 5 trades
                    action = trade.get('action', '')
                    symbol = trade.get('symbol', '')
                    if action == 'SELL' and 'pnl' in trade:
                        pnl = trade['pnl']
                        pnl_pct = trade.get('pnl_pct', 0)
                        emoji = '✅' if pnl > 0 else '❌'
                        print(f"   {emoji} {action} {symbol}: ${pnl:.2f} ({pnl_pct:.1f}%)")
                    else:
                        price = trade.get('price', 0)
                        size = trade.get('size', 0)
                        print(f"   🦞 {action} {symbol}: ${size:.2f} @ ${price:.2f}")
            
            # Check win rate
            win_rate = metrics.get('win_rate', 0)
            if win_rate >= 60:
                print(f"\n🎯 TARGET ACHIEVED! Win rate: {win_rate:.1f}%")
            else:
                print(f"\n⏳ Progress to target: {win_rate:.1f}% / 60%")
        
        else:
            print("\n⚠️ Waiting for paper trading data...")
        
        print("\n" + "─" * 80)
        print("Refreshing every 30 seconds...")
        
        time.sleep(30)
        print("\033[2J\033[H")  # Clear screen for next update

if __name__ == "__main__":
    try:
        display_monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped. Paper trading continues in background!")
        print("Check paper_trading_state.json for updates.")