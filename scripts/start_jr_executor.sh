#!/bin/bash
# Jr Task Executor Startup Script
# Ensures robust, monitored execution with automatic restart
#
# Usage: ./start_jr_executor.sh <agent_id> [node_name]
# Example: ./start_jr_executor.sh "Infrastructure Jr." bluefin
#
# For Seven Generations - Cherokee AI Federation
# January 23, 2026

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GANUDA_DIR="${SCRIPT_DIR%/scripts}"
EXECUTOR_PATH="${GANUDA_DIR}/jr_executor/jr_task_executor.py"
LOG_DIR="/var/log/ganuda"
PYTHON_PATH="/home/dereadi/cherokee_venv/bin/python3"

# Parse arguments
AGENT_ID="${1:-}"
NODE_NAME="${2:-$(hostname -s)}"

if [[ -z "$AGENT_ID" ]]; then
    echo "Usage: $0 <agent_id> [node_name]"
    echo "Example: $0 'Infrastructure Jr.' bluefin"
    exit 1
fi

# Sanitize agent ID for filename
SAFE_AGENT_ID=$(echo "$AGENT_ID" | tr ' ' '_' | tr -cd '[:alnum:]_-')
PID_FILE="/tmp/jr-executor-${SAFE_AGENT_ID}.pid"
LOG_FILE="${LOG_DIR}/jr-executor-${SAFE_AGENT_ID}.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to check if executor is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to stop executor
stop_executor() {
    echo "[$(date)] Stopping executor for ${AGENT_ID}..."
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    # Also kill any orphaned processes
    pkill -f "jr_task_executor.py.*${AGENT_ID}" 2>/dev/null || true
}

# Function to start executor
start_executor() {
    echo "[$(date)] Starting executor for ${AGENT_ID} on ${NODE_NAME}..."

    # Check if already running
    if is_running; then
        echo "[$(date)] Executor already running (PID: $(cat $PID_FILE))"
        return 0
    fi

    # Verify executor script exists
    if [[ ! -f "$EXECUTOR_PATH" ]]; then
        echo "[$(date)] ERROR: Executor not found at $EXECUTOR_PATH"
        exit 1
    fi

    # Verify Python exists
    if [[ ! -x "$PYTHON_PATH" ]]; then
        echo "[$(date)] ERROR: Python not found at $PYTHON_PATH"
        exit 1
    fi

    # Start executor with unbuffered output
    cd "${GANUDA_DIR}/jr_executor"
    nohup "$PYTHON_PATH" -u "$EXECUTOR_PATH" "$AGENT_ID" "$NODE_NAME" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Verify started
    sleep 2
    if is_running; then
        echo "[$(date)] Executor started successfully (PID: $pid)"
        echo "[$(date)] Log file: $LOG_FILE"
        return 0
    else
        echo "[$(date)] ERROR: Executor failed to start"
        cat "$LOG_FILE" | tail -20
        return 1
    fi
}

# Function to restart executor
restart_executor() {
    stop_executor
    sleep 2
    start_executor
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "Executor Status: RUNNING (PID: $pid)"
        echo "Agent ID: $AGENT_ID"
        echo "Node: $NODE_NAME"
        echo "Log: $LOG_FILE"
        echo ""
        echo "Recent log entries:"
        tail -10 "$LOG_FILE" 2>/dev/null || echo "(no log)"
    else
        echo "Executor Status: STOPPED"
    fi
}

# Main command handling
case "${1:-start}" in
    start)
        start_executor
        ;;
    stop)
        stop_executor
        ;;
    restart)
        restart_executor
        ;;
    status)
        show_status
        ;;
    *)
        # First argument is agent ID, start by default
        start_executor
        ;;
esac
