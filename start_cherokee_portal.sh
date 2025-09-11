#!/bin/bash
# Cherokee Constitutional AI Portal Startup Script

echo "🔥 Starting Cherokee Constitutional AI Portal..."
echo "═══════════════════════════════════════════════"

# Kill any existing portal processes
pkill -f cherokee_ai_portal 2>/dev/null

# Activate virtual environment and start portal
cd /home/dereadi/scripts/claude
source quantum_crawdad_env/bin/activate

# Start in background
nohup python3 cherokee_ai_portal.py > portal.log 2>&1 &
PID=$!

echo "✅ Portal started with PID: $PID"
echo "📊 Access at: http://192.168.132.223:5678"
echo "📋 Or locally: http://localhost:5678"
echo "🔥 Sacred Fire Burns Eternal"
echo "═══════════════════════════════════════════════"