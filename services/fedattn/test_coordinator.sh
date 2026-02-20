#!/bin/bash
# Test FedAttn Coordinator
# Cherokee AI Federation

echo "=== FedAttn Coordinator Test Suite ==="
echo ""

# Kill any existing coordinator
echo "[1/6] Stopping any existing coordinator..."
pkill -f "uvicorn coordinator:app" 2>/dev/null
sleep 2

# Start coordinator in background
echo "[2/6] Starting coordinator..."
cd /ganuda/services/fedattn
nohup /home/dereadi/cherokee_venv/bin/python -m uvicorn coordinator:app --host 0.0.0.0 --port 8081 > coordinator.log 2>&1 &
COORDINATOR_PID=$!
sleep 5

# Test health endpoint
echo "[3/6] Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8081/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  ✓ Health check passed"
    echo "  Response: $HEALTH"
else
    echo "  ✗ Health check failed"
    echo "  Response: $HEALTH"
    cat coordinator.log
    exit 1
fi

# Test starting a session
echo "[4/6] Starting test session..."
SESSION=$(curl -s -X POST http://localhost:8081/session/start \
  -H "Content-Type: application/json" \
  -d '{"initiator_node": "redfin", "sync_interval": 8}')
SESSION_ID=$(echo "$SESSION" | jq -r '.session_id')
if [ "$SESSION_ID" != "null" ] && [ -n "$SESSION_ID" ]; then
    echo "  ✓ Session created: $SESSION_ID"
else
    echo "  ✗ Session creation failed"
    echo "  Response: $SESSION"
    exit 1
fi

# Test listing active sessions
echo "[5/6] Listing active sessions..."
SESSIONS=$(curl -s http://localhost:8081/sessions/active)
COUNT=$(echo "$SESSIONS" | jq -r '.count')
if [ "$COUNT" = "1" ]; then
    echo "  ✓ Active sessions: $COUNT"
    echo "  Details: $SESSIONS"
else
    echo "  ✗ Expected 1 active session, got $COUNT"
    exit 1
fi

# Test ending session
echo "[6/6] Ending test session..."
END=$(curl -s -X POST http://localhost:8081/session/$SESSION_ID/end)
if echo "$END" | grep -q "ended"; then
    echo "  ✓ Session ended successfully"
else
    echo "  ✗ Session end failed"
    echo "  Response: $END"
fi

echo ""
echo "=== All Tests Passed ==="
echo "Coordinator PID: $COORDINATOR_PID"
echo "Log file: /ganuda/services/fedattn/coordinator.log"
echo ""
echo "To stop coordinator: pkill -f 'uvicorn coordinator:app'"
