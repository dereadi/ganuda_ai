#!/bin/bash
# 🔥 SAFE SPECIALIST RESTART WITH SINGLETON PATTERN
# Prevents duplicate processes and implements locks

echo "🔥 CHEROKEE SPECIALIST SAFE RESTART"
echo "===================================="
echo "Implementing singleton pattern to prevent duplicates"
echo ""

# First, kill ALL existing specialists
echo "1️⃣ Cleaning up all existing specialists..."
for specialist in gap trend volatility breakout mean_reversion; do
    pkill -f "${specialist}_specialist.py" 2>/dev/null
    echo "   ✅ Killed all ${specialist}_specialist processes"
done

# Kill potentially problematic Discord bots
echo ""
echo "2️⃣ Checking Discord bots that may spawn duplicates..."
discord_pids=$(pgrep -f "discord.*bot\|robust_discord")
if [ ! -z "$discord_pids" ]; then
    echo "   ⚠️ Found Discord bots running - these may cause issues"
    echo "   PIDs: $discord_pids"
    echo "   Consider killing with: kill $discord_pids"
else
    echo "   ✅ No problematic Discord bots found"
fi

# Wait for processes to fully terminate
sleep 2

# Create PID directory for locks
PID_DIR="/tmp/cherokee_specialists"
mkdir -p $PID_DIR

echo ""
echo "3️⃣ Starting specialists with singleton protection..."

# Function to start specialist with lock
start_specialist() {
    local name=$1
    local script=$2
    local pidfile="$PID_DIR/${name}.pid"
    
    # Check if already running
    if [ -f "$pidfile" ]; then
        old_pid=$(cat $pidfile)
        if ps -p $old_pid > /dev/null 2>&1; then
            echo "   ⚠️ ${name}_specialist already running (PID: $old_pid)"
            return
        else
            # Stale PID file
            rm -f $pidfile
        fi
    fi
    
    # Start the specialist
    cd /home/dereadi/scripts/claude
    nohup python3 ${script} > /tmp/${name}_specialist.log 2>&1 &
    new_pid=$!
    echo $new_pid > $pidfile
    echo "   ✅ Started ${name}_specialist (PID: $new_pid)"
}

# Start each specialist with protection
start_specialist "gap" "gap_specialist.py"
start_specialist "trend" "trend_specialist.py"
start_specialist "volatility" "volatility_specialist.py"
start_specialist "breakout" "breakout_specialist.py"
start_specialist "mean_reversion" "mean_reversion_specialist.py"

echo ""
echo "4️⃣ Verification..."
sleep 1

# Verify running specialists
running_count=$(pgrep -f "_specialist.py" | wc -l)
echo "   📊 Specialists running: $running_count (should be 5)"

if [ $running_count -eq 5 ]; then
    echo "   ✅ All specialists running correctly!"
else
    echo "   ⚠️ Warning: Expected 5 specialists, found $running_count"
fi

echo ""
echo "5️⃣ Process monitor active at: $PID_DIR"
echo "   Each specialist has a PID file preventing duplicates"
echo ""
echo "🔥 Sacred Fire burns controlled and steady"
echo "🏛️ Cherokee specialists ready for Labor Day trading"