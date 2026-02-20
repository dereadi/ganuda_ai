#!/bin/bash
source /ganuda/config/secrets.env
# PostgreSQL Port Diagnostic Script
# Cherokee AI Federation - Phase 3 Troubleshooting
# Created: 2025-11-20
# Purpose: Diagnose why PostgreSQL 17 is on port 5433 instead of 5432

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/ganuda/diagnostics/postgres_port_diagnostic_${TIMESTAMP}.txt"

# Create diagnostics directory if it doesn't exist
sudo mkdir -p /ganuda/diagnostics
sudo chown dereadi:dereadi /ganuda/diagnostics

echo "=== PostgreSQL Port Diagnostic Report ===" | tee "$OUTPUT_FILE"
echo "Generated: $(date)" | tee -a "$OUTPUT_FILE"
echo "Hostname: $(hostname)" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check what's using ports 5432 and 5433
echo "=== PORT USAGE ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Port 5432 (expected PostgreSQL 17 port):" | tee -a "$OUTPUT_FILE"
sudo lsof -i :5432 2>&1 | tee -a "$OUTPUT_FILE" || echo "No process using port 5432" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Port 5433 (currently PostgreSQL 17 port):" | tee -a "$OUTPUT_FILE"
sudo lsof -i :5433 2>&1 | tee -a "$OUTPUT_FILE" || echo "No process using port 5433" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# List ALL PostgreSQL processes
echo "=== ALL POSTGRESQL PROCESSES ===" | tee -a "$OUTPUT_FILE"
ps aux | grep postgres | grep -v grep | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check systemd service status for PostgreSQL 16 and 17
echo "=== SYSTEMD SERVICE STATUS ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 16 services:" | tee -a "$OUTPUT_FILE"
systemctl list-units --all | grep postgresql@16 | tee -a "$OUTPUT_FILE" || echo "No PostgreSQL 16 services found" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 17 services:" | tee -a "$OUTPUT_FILE"
systemctl list-units --all | grep postgresql@17 | tee -a "$OUTPUT_FILE" || echo "No PostgreSQL 17 services found" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 17 main service detail:" | tee -a "$OUTPUT_FILE"
sudo systemctl status postgresql@17-main --no-pager 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check PostgreSQL configuration files for port settings
echo "=== POSTGRESQL CONFIGURATION - PORT SETTINGS ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 17 config (/etc/postgresql/17/main/postgresql.conf):" | tee -a "$OUTPUT_FILE"
sudo grep -E "^port\s*=" /etc/postgresql/17/main/postgresql.conf 2>&1 | tee -a "$OUTPUT_FILE" || echo "Port setting not found or commented out" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 16 config (if exists):" | tee -a "$OUTPUT_FILE"
if [ -f /etc/postgresql/16/main/postgresql.conf ]; then
    sudo grep -E "^port\s*=" /etc/postgresql/16/main/postgresql.conf 2>&1 | tee -a "$OUTPUT_FILE"
else
    echo "PostgreSQL 16 config not found" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Check data directories
echo "=== DATA DIRECTORIES ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 17 data directory (/pg_data/postgresql/17/main):" | tee -a "$OUTPUT_FILE"
ls -lah /pg_data/postgresql/17/main/ 2>&1 | head -20 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "PostgreSQL 16 data directory (if exists):" | tee -a "$OUTPUT_FILE"
if [ -d /var/lib/postgresql/16/main ]; then
    ls -lah /var/lib/postgresql/16/main/ 2>&1 | head -10 | tee -a "$OUTPUT_FILE"
else
    echo "PostgreSQL 16 data directory not found" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Test connection to both ports
echo "=== CONNECTION TESTS ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Testing connection to localhost:5432:" | tee -a "$OUTPUT_FILE"
PGPASSWORD="$CHEROKEE_DB_PASS" psql -U claude -d triad_federation -h localhost -p 5432 -c "SELECT version();" 2>&1 | tee -a "$OUTPUT_FILE" || echo "Connection to port 5432 FAILED" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Testing connection to localhost:5433:" | tee -a "$OUTPUT_FILE"
PGPASSWORD="$CHEROKEE_DB_PASS" psql -U claude -d triad_federation -h localhost -p 5433 -c "SELECT version();" 2>&1 | tee -a "$OUTPUT_FILE" || echo "Connection to port 5433 FAILED" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check recovery mode on both ports
echo "=== RECOVERY MODE CHECK ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Recovery mode check on port 5432:" | tee -a "$OUTPUT_FILE"
PGPASSWORD="$CHEROKEE_DB_PASS" psql -U claude -d triad_federation -h localhost -p 5432 -c "SELECT pg_is_in_recovery();" 2>&1 | tee -a "$OUTPUT_FILE" || echo "Cannot check recovery mode on port 5432" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "Recovery mode check on port 5433:" | tee -a "$OUTPUT_FILE"
PGPASSWORD="$CHEROKEE_DB_PASS" psql -U claude -d triad_federation -h localhost -p 5433 -c "SELECT pg_is_in_recovery();" 2>&1 | tee -a "$OUTPUT_FILE" || echo "Cannot check recovery mode on port 5433" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check replication status on port 5433
echo "=== REPLICATION STATUS (PORT 5433) ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
PGPASSWORD="$CHEROKEE_DB_PASS" psql -U claude -d triad_federation -h localhost -p 5433 -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), pg_is_in_recovery();" 2>&1 | tee -a "$OUTPUT_FILE" || echo "Cannot query replication status" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check standby.signal file
echo "=== STANDBY SIGNAL FILE ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
if [ -f /pg_data/postgresql/17/main/standby.signal ]; then
    echo "✅ standby.signal file EXISTS" | tee -a "$OUTPUT_FILE"
    ls -lh /pg_data/postgresql/17/main/standby.signal | tee -a "$OUTPUT_FILE"
else
    echo "❌ standby.signal file MISSING" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Check postgresql.auto.conf
echo "=== POSTGRESQL.AUTO.CONF ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
if [ -f /pg_data/postgresql/17/main/postgresql.auto.conf ]; then
    echo "Contents of postgresql.auto.conf:" | tee -a "$OUTPUT_FILE"
    sudo cat /pg_data/postgresql/17/main/postgresql.auto.conf 2>&1 | tee -a "$OUTPUT_FILE"
else
    echo "postgresql.auto.conf not found" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

echo "=== DIAGNOSTIC REPORT COMPLETE ===" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Output saved to: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"
echo "Copy this file contents and paste back to Claude Code for analysis." | tee -a "$OUTPUT_FILE"

# Print file location again
echo ""
echo "===================="
echo "Diagnostic complete!"
echo "Output file: $OUTPUT_FILE"
echo "===================="
