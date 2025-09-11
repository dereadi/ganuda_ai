#!/bin/bash

echo "🦞 LAUNCHING QUANTUM CRAWDAD PAPER TRADING"
echo "═══════════════════════════════════════════════════════════════════════════════════"
echo "Starting 24-hour paper trading test with real market data"
echo "Target: 60% win rate with $90 simulated capital"
echo "═══════════════════════════════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment
source quantum_crawdad_env/bin/activate

# Start paper trading
python3 quantum_crawdad_paper_trader.py