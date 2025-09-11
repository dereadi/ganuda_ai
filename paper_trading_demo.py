#!/usr/bin/env python3
"""
Paper Trading Live Demo
Shows the Quantum Crawdads in action!
"""

from quantum_crawdad_paper_trader import QuantumCrawdadPaperTrader
import time

def run_demo():
    # Start paper trader
    trader = QuantumCrawdadPaperTrader()
    
    print('🦞 QUANTUM CRAWDAD PAPER TRADING - LIVE DEMO')
    print('═' * 80)
    print(f'Starting Capital: ${trader.capital:.2f}')
    print(f'Max Position Size: ${trader.max_position_size:.2f}')
    print(f'Stop Loss: {trader.stop_loss_percent}% | Take Profit: {trader.take_profit_percent}%')
    print('═' * 80)
    print('')
    
    # Perform initial market scan
    print('📊 SCANNING LIVE MARKETS...')
    print('─' * 40)
    
    opportunities_found = 0
    
    for symbol in trader.symbols:
        print(f'\nAnalyzing {symbol}...')
        market_data = trader.fetch_market_data(symbol)
        
        if market_data:
            print(f'  Price: ${market_data["price"]:.2f}')
            print(f'  Change: {market_data["change"]:+.2f}%')
            print(f'  Volatility: {market_data["volatility"]:.2f}%')
            
            # Check for trading signals
            signal = trader.analyze_opportunity(market_data)
            
            if signal:
                if signal['confidence'] >= trader.confidence_threshold:
                    print(f'  🎯 SIGNAL DETECTED!')
                    print(f'     Strategy: {signal["strategy"]}')
                    print(f'     Action: {signal["action"]}')
                    print(f'     Confidence: {signal["confidence"]:.0%}')
                    print(f'     Reason: {signal["reason"]}')
                    
                    # Execute paper trade
                    trader.execute_paper_trade(symbol, signal, market_data)
                    opportunities_found += 1
                else:
                    print(f'  📉 Weak signal ({signal["confidence"]:.0%}) - skipping')
    
    print('')
    print('═' * 80)
    print(f'🦞 SCAN COMPLETE')
    print(f'   Opportunities Found: {opportunities_found}')
    print(f'   Trades Executed: {trader.metrics["total_trades"]}')
    print(f'   Capital Remaining: ${trader.capital:.2f}')
    print(f'   Positions Open: {len(trader.positions)}')
    
    if trader.positions:
        print('\n📊 CURRENT POSITIONS:')
        for symbol, pos in trader.positions.items():
            print(f'   {symbol}: ${pos["size"]:.2f} @ ${pos["entry_price"]:.2f} ({pos["strategy"]})')
    
    # Save state
    trader.save_state()
    
    print('')
    print('═' * 80)
    print('💾 State saved to paper_trading_state.json')
    print('')
    print('🔄 Paper trading will continue scanning every 5 minutes.')
    print('   Check paper_trading_state.json for updates.')
    print('   Target: 60% win rate over 24 hours')
    print('')
    print('📈 Watch your crawdads hunt in the volatile waters!')
    print('═' * 80)

if __name__ == "__main__":
    run_demo()