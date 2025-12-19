#\!/bin/bash
# whatport - Show what is running on a given port
# Usage: whatport 8000 or whatport (shows all ganuda ports)

GANUDA_PORTS="4000 5555 6379 8000 8001 8002 8003 8080 3000 3001 5432"

show_port() {
    local port=$1
    local info=$(ss -tlnp 2>/dev/null | grep ":$port " | head -1)
    if [ -n "$info" ]; then
        local pid=$(echo "$info" | grep -oP 'pid=\K[0-9]+')
        if [ -n "$pid" ]; then
            local cmd=$(ps -p $pid -o args= 2>/dev/null | head -c 80)
            printf "%-6s %-8s %s\n" "$port" "$pid" "$cmd"
        fi
    fi
}

echo "PORT   PID      COMMAND"
echo "====== ======== ========================================"

if [ -n "$1" ]; then
    show_port $1
else
    for port in $GANUDA_PORTS; do
        show_port $port
    done
fi
