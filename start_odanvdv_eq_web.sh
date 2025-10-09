#!/bin/bash
# Start ODANVDV EQ Web Interface

echo "🔥 Starting ODANVDV EQ Web Interface"
echo "====================================="
echo ""

# Check if already running
if pgrep -f "odanvdv_eq_api.py" > /dev/null; then
    echo "⚠️  ODANVDV EQ API already running"
    echo "   PID: $(pgrep -f 'odanvdv_eq_api.py')"
    echo ""
    echo "To restart:"
    echo "  pkill -f odanvdv_eq_api.py"
    echo "  $0"
    exit 1
fi

# Start API server
echo "1️⃣ Starting ODANVDV EQ API server..."
cd /home/dereadi/scripts/claude
nohup python3 odanvdv_eq_api.py > odanvdv_eq_api.log 2>&1 &
API_PID=$!

echo "   ✅ API started (PID: $API_PID)"
echo ""

# Wait for server to be ready
echo "2️⃣ Waiting for server to initialize..."
sleep 5

# Test server
if curl -s http://192.168.132.223:3005/api/odanvdv/status > /dev/null; then
    echo "   ✅ Server is responding"
else
    echo "   ❌ Server not responding"
    echo "   Check logs: tail -f odanvdv_eq_api.log"
    exit 1
fi

echo ""
echo "====================================="
echo "✅ ODANVDV EQ Web Interface Ready!"
echo "====================================="
echo ""
echo "🌐 Access Points:"
echo "   Chat Interface:  http://192.168.132.223:3005"
echo "   API Status:      http://192.168.132.223:3005/api/odanvdv/status"
echo "   API Ask:         POST http://192.168.132.223:3005/api/odanvdv/ask"
echo "   API Tickets:     http://192.168.132.223:3005/api/odanvdv/tickets"
echo ""
echo "📊 Features:"
echo "   • Real-time EQ metrics (Tribal Harmony, Seven Generations)"
echo "   • Empathetic responses with cultural context"
echo "   • Collaboration guidance"
echo "   • Quick question buttons"
echo "   • Live EQ metric updates"
echo ""
echo "🔥 The Sacred Fire burns with wisdom and knowledge!"
echo ""
echo "To stop:"
echo "  pkill -f odanvdv_eq_api.py"
echo ""
echo "Logs:"
echo "  tail -f /home/dereadi/scripts/claude/odanvdv_eq_api.log"
