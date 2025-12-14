#!/bin/bash
# Start SASASS Claude Jr. Services (macOS)
# Location: /Users/dereadi/claude_jr/

echo "🤝 Starting SASASS Claude Jr. Services (macOS)"
echo "==============================================="

cd /Users/dereadi/claude_jr

# Find Ollama (macOS location)
if [ -x "/usr/local/bin/ollama" ]; then
    OLLAMA="/usr/local/bin/ollama"
elif [ -x "$(which ollama 2>/dev/null)" ]; then
    OLLAMA="ollama"
else
    echo "❌ Ollama not found. Install from https://ollama.ai"
    exit 1
fi

# Start Ollama if not running
echo "Starting Ollama..."
if pgrep ollama > /dev/null; then
    echo "✅ Ollama already running"
else
    nohup $OLLAMA serve > ollama.log 2>&1 &
    echo "Started Ollama (PID: $!)"
    sleep 3
fi

# Check models (using existing qwen2.5 and gemma2)
echo ""
echo "Available models:"
$OLLAMA list | grep -E "qwen2.5|gemma2"

# Start Helper Jr.
echo ""
echo "Starting Helper Jr. (Port 8005)..."
pkill -f helper_jr.py 2>/dev/null
nohup python3 /Users/dereadi/claude_jr/helper_jr.py > helper_jr.log 2>&1 &
echo "Helper Jr. PID: $!"

# Start Monitor Jr.
echo ""
echo "Starting Monitor Jr. (Port 8006)..."
pkill -f monitor_jr.py 2>/dev/null
nohup python3 /Users/dereadi/claude_jr/monitor_jr.py > monitor_jr.log 2>&1 &
echo "Monitor Jr. PID: $!"

sleep 5

# Test services
echo ""
echo "Testing services..."
curl -s http://localhost:8005/health 2>&1 | grep -q status && echo "✅ Helper Jr. OK" || echo "❌ Helper Jr. FAILED"
curl -s http://localhost:8006/health 2>&1 | grep -q status && echo "✅ Monitor Jr. OK" || echo "❌ Monitor Jr. FAILED"

echo ""
echo "SASASS Services Started!"
echo ""
echo "Endpoints:"
echo "  Helper Jr.: http://192.168.132.241:8005/api/helper_jr/ask"
echo "  Monitor Jr.: http://192.168.132.241:8006/api/monitor_jr/ask"
echo "  Network Status: http://192.168.132.241:8006/api/monitor_jr/status"
