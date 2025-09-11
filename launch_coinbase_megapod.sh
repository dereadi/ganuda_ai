#!/bin/bash

# Launch Coinbase Quantum Crawdad Megapod

echo "🦀🔥 COINBASE QUANTUM CRAWDAD MEGAPOD LAUNCHER"
echo "=============================================="
echo ""
echo "Make sure you have:"
echo "1. ✅ Coinbase account with $500 deposited"
echo "2. ✅ API key and secret from Coinbase.com"
echo "3. ✅ Identity verified on Coinbase"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Activate virtual environment
source quantum_crawdad_env/bin/activate

# Run the megapod with auto-yes
echo "y" | python3 coinbase_quantum_megapod.py

echo ""
echo "🦀 Megapod terminated. Check logs for results."