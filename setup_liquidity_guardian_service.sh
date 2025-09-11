#!/bin/bash
# Setup Liquidity Guardian as a background service

echo "💰 Setting up Liquidity Guardian Service"
echo "========================================"

# Create the monitoring script
cat > /home/dereadi/scripts/claude/liquidity_guardian_service.sh << 'EOF'
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
EOF

chmod +x liquidity_guardian_service.sh

echo "✅ Service script created"
echo ""
echo "Starting Liquidity Guardian..."

# Kill any existing guardian
pkill -f liquidity_guardian_service.sh 2>/dev/null

# Start new guardian
nohup ./liquidity_guardian_service.sh > liquidity_guardian.log 2>&1 &
GUARDIAN_PID=$!

echo "✅ LIQUIDITY GUARDIAN ACTIVE!"
echo "================================"
echo "PID: $GUARDIAN_PID"
echo "Log: liquidity_guardian.log"
echo ""
echo "📋 PROTECTION ACTIVE:"
echo "  • Min Cash: $250 (emergency threshold)"
echo "  • Ideal: $500 (optimal trading)"
echo "  • Max: $1000 (deploy excess)"
echo ""
echo "Monitor: tail -f liquidity_guardian.log"
echo "Stop: kill $GUARDIAN_PID"
echo ""
echo "🔥 Never miss an opportunity again!"