#!/bin/bash
# Start SASASS Claude Jr. Services
# Location: /home/dereadi/claude_jr/

echo "🤝 Starting SASASS Claude Jr. Services"
echo "======================================="

cd /home/dereadi/claude_jr

# Start Ollama if not running
echo "Starting Ollama..."
if pgrep ollama > /dev/null; then
    echo "✅ Ollama already running"
else
    nohup ollama serve > ollama.log 2>&1 &
    echo "Started Ollama (PID: $!)"
    sleep 3
fi

# Pull models if needed
echo ""
echo "Checking models..."
ollama list | grep -q "llama3.1:8b" || echo "Pulling llama3.1:8b..." && ollama pull llama3.1:8b
ollama list | grep -q "mistral:7b-instruct" || echo "Pulling mistral:7b-instruct..." && ollama pull mistral:7b-instruct

# Start Helper Jr.
echo ""
echo "Starting Helper Jr. (Port 8005)..."
pkill -f helper_jr.py 2>/dev/null
nohup python3 /home/dereadi/claude_jr/helper_jr.py > helper_jr.log 2>&1 &
echo "Helper Jr. PID: $!"

# Start Monitor Jr.
echo ""
echo "Starting Monitor Jr. (Port 8006)..."
pkill -f monitor_jr.py 2>/dev/null
nohup python3 /home/dereadi/claude_jr/monitor_jr.py > monitor_jr.log 2>&1 &
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
