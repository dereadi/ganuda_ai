#!/bin/bash
# Liquidity Guardian Service
# Monitors cash reserves continuously

cd /home/dereadi/scripts/claude

echo "💰 Liquidity Guardian Service Started at $(date)"
echo "Monitoring cash reserves every 5 minutes..."
echo "Target: $250-500 cash at all times"
echo "========================================="

while true; do
    # Run liquidity check
    python3 liquidity_guardian.py >> liquidity_guardian.log 2>&1
    
    # Log timestamp
    echo "[$(date '+%H:%M:%S')] Liquidity check completed" >> liquidity_guardian.log
    
    # Sleep 5 minutes
    sleep 300
done
