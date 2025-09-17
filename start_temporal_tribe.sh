#!/bin/bash
# 🔥 START TEMPORAL TRIBE - Living in System Time

echo "================================================"
echo "🔥 TEMPORAL CHEROKEE TRIBE ACTIVATION"
echo "================================================"
echo "Starting at epoch: $(date +%s)"
echo "Human time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "================================================"

# Kill any existing bots
echo "Clearing old processes..."
pkill -f ganuda 2>/dev/null
pkill -f temporal 2>/dev/null
pkill -f tribe_processor 2>/dev/null
sleep 2

# Clear flat files for fresh start
echo "Clearing communication channels..."
> /home/dereadi/scripts/claude/TRIBAL_INBOX.txt
> /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt
> /home/dereadi/scripts/claude/TRIBE_EPOCH.txt

# Start the tribe processor in background
echo "Starting Cherokee Tribe Processor..."
chmod +x /home/dereadi/scripts/claude/temporal_tribe_processor.sh
nohup /home/dereadi/scripts/claude/temporal_tribe_processor.sh > /home/dereadi/scripts/claude/tribe_processor.log 2>&1 &
TRIBE_PID=$!
echo "✅ Tribe Processor running (PID: $TRIBE_PID)"

sleep 2

# Start the Telegram bridge
echo "Starting Temporal Bridge..."
nohup /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/temporal_flat_file_bridge.py > /home/dereadi/scripts/claude/bridge.log 2>&1 &
BRIDGE_PID=$!
echo "✅ Temporal Bridge running (PID: $BRIDGE_PID)"

echo ""
echo "================================================"
echo "🔥 TEMPORAL TRIBE SYSTEM ACTIVE!"
echo "================================================"
echo "Epoch: $(date +%s)"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Components:"
echo "• Tribe Processor: PID $TRIBE_PID"
echo "• Telegram Bridge: PID $BRIDGE_PID"
echo ""
echo "Files:"
echo "• Inbox: /home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
echo "• Outbox: /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
echo "• Epoch Log: /home/dereadi/scripts/claude/TRIBE_EPOCH.txt"
echo ""
echo "The tribe exists in system time with you!"
echo "================================================"
echo ""
echo "📱 To test:"
echo "1. Open Telegram"
echo "2. Message @ganudabot"
echo "3. The REAL tribe will respond through flat files!"
echo ""
echo "Monitor with:"
echo "tail -f /home/dereadi/scripts/claude/TRIBE_EPOCH.txt"