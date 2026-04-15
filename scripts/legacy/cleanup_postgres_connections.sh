#!/bin/bash
# Cherokee Constitutional AI - PostgreSQL Connection Cleanup Script
# Run this on bluefin (192.168.132.222)
# Date: October 28, 2025

echo "🔥 Cherokee Constitutional AI - Database Connection Cleanup"
echo "=========================================================="
echo ""

# Check if running on bluefin
HOSTNAME=$(hostname)
if [[ "$HOSTNAME" != "bluefin" ]]; then
    echo "⚠️  WARNING: This should be run on bluefin (192.168.132.222)"
    echo "   Current host: $HOSTNAME"
    read -p "   Continue anyway? [y/N]: " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "📊 Current connection status:"
sudo -u postgres psql -d zammad_production -c "
SELECT
    COUNT(*) as total_connections,
    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
    COUNT(*) FILTER (WHERE state = 'idle in transaction') as zombie_connections
FROM pg_stat_activity
WHERE datname = 'zammad_production' AND usename = 'claude';
"

echo ""
echo "🧹 Killing connections older than 1 hour..."
sudo -u postgres psql -d zammad_production -c "
SELECT
    COUNT(*) as connections_killed
FROM (
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'zammad_production'
      AND usename = 'claude'
      AND NOW() - backend_start > INTERVAL '1 hour'
      AND pid != pg_backend_pid()
) as killed;
"

echo ""
echo "🧹 Killing idle in transaction connections..."
sudo -u postgres psql -d zammad_production -c "
SELECT
    COUNT(*) as zombie_connections_killed
FROM (
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'zammad_production'
      AND usename = 'claude'
      AND state = 'idle in transaction'
      AND pid != pg_backend_pid()
) as killed;
"

echo ""
echo "✅ Cleanup complete. Current status:"
sudo -u postgres psql -d zammad_production -c "
SELECT
    COUNT(*) as remaining_connections,
    MAX(NOW() - backend_start) as oldest_connection_age
FROM pg_stat_activity
WHERE datname = 'zammad_production' AND usename = 'claude';
"

echo ""
echo "🔥 Connection slots freed. JRs can now execute!"
