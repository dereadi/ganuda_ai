#!/bin/bash
# Cherokee AI Federation - Chaos Test Suite
# Usage: ./chaos_test_suite.sh [test_name]
# Tests: gateway, connections, memory, services, baseline

set -e

POSTGRES_HOST="192.168.132.222"
REDFIN="192.168.132.223"
BLUEFIN="192.168.132.222"
GREENFIN="192.168.132.224"
LOG_FILE="/var/log/ganuda/chaos_tests.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

pass() { log "${GREEN}PASS${NC}: $1"; }
fail() { log "${RED}FAIL${NC}: $1"; }
skip() { log "${YELLOW}SKIP${NC}: $1"; }

# Test 1: Baseline Health Check
test_baseline() {
    log "=== TEST: Baseline Health Check ==="
    
    # LLM Gateway
    if curl -sf http://$REDFIN:8080/health > /dev/null 2>&1; then
        pass "LLM Gateway healthy"
    else
        fail "LLM Gateway not responding"
    fi
    
    # PostgreSQL
    if PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -c "SELECT 1" > /dev/null 2>&1; then
        pass "PostgreSQL connected"
    else
        fail "PostgreSQL not responding"
    fi
    
    # Node reachability
    for node in $REDFIN $BLUEFIN $GREENFIN; do
        if nc -z -w 2 $node 22 > /dev/null 2>&1; then
            pass "Node $node SSH reachable"
        else
            fail "Node $node unSSH reachable"
        fi
    done
}

# Test 2: LLM Gateway Recovery
test_gateway_recovery() {
    log "=== TEST: LLM Gateway Recovery ==="
    
    # Check baseline
    if ! curl -sf http://$REDFIN:8080/health > /dev/null; then
        skip "Gateway not running - cannot test recovery"
        return 1
    fi
    
    log "Killing LLM Gateway process..."
    START=$(date +%s)
    
    # Kill the process
    sudo pkill -f 'uvicorn gateway:app' || true
    
    # Wait for recovery (max 60s)
    for i in {1..60}; do
        if curl -sf http://$REDFIN:8080/health > /dev/null 2>&1; then
            END=$(date +%s)
            RECOVERY_TIME=$((END - START))
            pass "Gateway recovered in ${RECOVERY_TIME} seconds"
            return 0
        fi
        sleep 1
    done
    
    fail "Gateway did not recover within 60s"
    return 1
}

# Test 3: Database Connection Check
test_db_connections() {
    log "=== TEST: Database Connection Handling ==="
    
    INITIAL=$(PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -t -c "SELECT count(*) FROM pg_stat_activity;" | tr -d ' ')
    MAX=$(PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -t -c "SHOW max_connections;" | tr -d ' ')
    
    log "Current connections: $INITIAL / $MAX max"
    
    if [ "$INITIAL" -lt "$MAX" ]; then
        pass "Database has available connections ($INITIAL/$MAX)"
    else
        fail "Database connections at capacity"
    fi
}

# Test 4: Service Restart Resilience
test_service_restart() {
    log "=== TEST: Service Restart Resilience ==="
    
    SERVICES="llm-gateway ganuda-heartbeat"
    
    for svc in $SERVICES; do
        if systemctl is-active $svc > /dev/null 2>&1; then
            log "Restarting $svc..."
            sudo systemctl restart $svc
            sleep 3
            
            if systemctl is-active $svc > /dev/null 2>&1; then
                pass "$svc restarted successfully"
            else
                fail "$svc did not restart"
            fi
        else
            skip "$svc not active on this node"
        fi
    done
}

# Test 5: Thermal Memory Write/Read
test_thermal_memory() {
    log "=== TEST: Thermal Memory Operations ==="
    
    TEST_HASH="CHAOS-VERIFY-$(date +%s)"
    
    # Write
    PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -c "
    INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score)
    VALUES ('$TEST_HASH', 'Chaos test verification entry', 'FRESH', 50.0);" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        pass "Thermal memory write successful"
    else
        fail "Thermal memory write failed"
        return 1
    fi
    
    # Read back
    RESULT=$(PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -t -c "
    SELECT memory_hash FROM thermal_memory_archive WHERE memory_hash = '$TEST_HASH';" | tr -d ' ')
    
    if [ "$RESULT" = "$TEST_HASH" ]; then
        pass "Thermal memory read verified"
    else
        fail "Thermal memory read failed"
    fi
    
    # Cleanup
    PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -c "
    DELETE FROM thermal_memory_archive WHERE memory_hash = '$TEST_HASH';" > /dev/null 2>&1
}

# Test 6: Disk Space Check
test_disk_space() {
    log "=== TEST: Disk Space Availability ==="
    
    # Check critical partitions
    for mount in / /ganuda /sag_data; do
        if [ -d "$mount" ]; then
            USAGE=$(df -h $mount | tail -1 | awk '{print $5}' | tr -d '%')
            if [ "$USAGE" -lt 90 ]; then
                pass "$mount at ${USAGE}% (healthy)"
            elif [ "$USAGE" -lt 95 ]; then
                log "${YELLOW}WARN${NC}: $mount at ${USAGE}% (warning)"
            else
                fail "$mount at ${USAGE}% (critical)"
            fi
        fi
    done
}

# Main execution
main() {
    log "========================================"
    log "Cherokee AI Federation Chaos Test Suite"
    log "========================================"
    
    case "${1:-all}" in
        baseline) test_baseline ;;
        gateway) test_gateway_recovery ;;
        connections) test_db_connections ;;
        services) test_service_restart ;;
        memory) test_thermal_memory ;;
        disk) test_disk_space ;;
        all)
            test_baseline
            test_db_connections
            test_thermal_memory
            test_disk_space
            # Don't auto-run gateway kill in 'all' mode
            log "Note: Run './chaos_test_suite.sh gateway' separately to test gateway recovery"
            ;;
        *)
            echo "Usage: $0 [baseline|gateway|connections|services|memory|disk|all]"
            echo ""
            echo "Tests:"
            echo "  baseline    - Check all services are healthy"
            echo "  gateway     - Kill and verify LLM Gateway auto-recovery"
            echo "  connections - Check database connection availability"
            echo "  services    - Restart and verify service recovery"
            echo "  memory      - Test thermal memory read/write"
            echo "  disk        - Check disk space on critical partitions"
            echo "  all         - Run all safe tests (excludes gateway kill)"
            exit 1
            ;;
    esac
    
    log "========================================"
    log "Chaos test suite complete"
    log "========================================"
}

main "$@"
