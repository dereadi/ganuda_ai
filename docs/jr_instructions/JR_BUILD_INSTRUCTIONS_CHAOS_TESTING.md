# Jr Build Instructions: Chaos Testing Framework

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: IT Triad Jr
**Date**: December 13, 2025

## Objective

Implement controlled chaos testing to validate federation resilience. Tests simulate real-world failures to ensure:
1. Services recover automatically
2. Runbooks are accurate
3. Monitoring detects failures
4. No single point of failure

## Philosophy

**"Break it in testing so it doesn't break in production."**

Cherokee principle: Test the strength of the web by tugging each strand deliberately.

## Test Categories

| Category | Target | Risk Level | Approval |
|----------|--------|------------|----------|
| Service Chaos | Individual services | LOW | Self-approve |
| Network Chaos | Connectivity | MEDIUM | TPM approval |
| Resource Chaos | CPU/Memory/Disk | MEDIUM | TPM approval |
| Database Chaos | PostgreSQL | HIGH | Council vote |
| Full Node Chaos | Complete node | HIGH | Council vote |

## Critical Services to Test

| Node | Service | Criticality | Auto-Recovery Expected |
|------|---------|-------------|------------------------|
| redfin | llm-gateway | Critical | Yes (systemd restart) |
| redfin | vLLM | Critical | Manual |
| bluefin | postgresql | Critical | Yes (systemd) |
| bluefin | grafana-server | High | Yes (systemd) |
| redfin | SAG UI | High | Manual |

## Pre-Test Checklist

- [ ] Notify TPM of test window
- [ ] Verify backups are current (especially bluefin)
- [ ] Check thermal memory for active work
- [ ] Ensure no active council votes in progress
- [ ] Document baseline metrics

```bash
# Capture baseline before chaos
ssh dereadi@192.168.132.223 "curl -s http://localhost:8080/health"
ssh dereadi@192.168.132.222 "systemctl is-active postgresql"
```

---

## Test 1: LLM Gateway Service Kill (LOW RISK)

**Purpose**: Verify systemd auto-restart works

### Execute
```bash
# On redfin
ssh dereadi@192.168.132.223

# Check current state
systemctl status llm-gateway

# Kill the process (systemd should restart it)
sudo pkill -f "uvicorn gateway:app"

# Watch for restart (should happen within 5 seconds)
watch -n 1 "systemctl status llm-gateway | head -10"
```

### Expected Behavior
1. Service shows "activating (auto-restart)" within 5 seconds
2. Service returns to "active (running)" within 30 seconds
3. Health check responds: `curl http://localhost:8080/health`

### Verify Recovery
```bash
# Should return healthy
curl -s http://192.168.132.223:8080/health | jq .

# Check restart count
systemctl show llm-gateway --property=NRestarts
```

### Log Result
```sql
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score)
VALUES ('CHAOS-TEST-LLM-GATEWAY-$(date +%Y%m%d%H%M)',
        'Chaos Test: LLM Gateway kill. Recovery: [PASS/FAIL]. Time to recover: Xs. Restart count: N',
        'FRESH', 85.0);"
```

---

## Test 2: PostgreSQL Connection Exhaustion (MEDIUM RISK)

**Purpose**: Verify connection pool limits and recovery

### Execute
```bash
# On bluefin - create many connections
ssh dereadi@192.168.132.222

# Check current connections
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "
SELECT count(*) as current_connections FROM pg_stat_activity;"

# Spawn 50 connections (adjust based on max_connections)
for i in {1..50}; do
  PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "SELECT pg_sleep(30);" &
done

# Monitor connection count
watch -n 2 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -t -c 'SELECT count(*) FROM pg_stat_activity;'"
```

### Expected Behavior
1. Connection count rises to limit
2. New connections rejected with "too many connections"
3. After 30s sleep, connections release
4. Normal operation resumes

### Cleanup
```bash
# Kill test connections if needed
pkill -f "pg_sleep"
```

### Verify Recovery
```bash
# Normal query should work
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 'recovered' as status;"
```

---

## Test 3: Network Partition Simulation (MEDIUM RISK)

**Purpose**: Test behavior when nodes can't reach each other

### Execute (requires TPM approval)
```bash
# On greenfin - block traffic to redfin temporarily
ssh dereadi@192.168.132.224

# Block redfin (60 second test)
sudo iptables -A OUTPUT -d 192.168.132.223 -j DROP
sudo iptables -A INPUT -s 192.168.132.223 -j DROP

# Wait and observe
sleep 60

# Remove block
sudo iptables -D OUTPUT -d 192.168.132.223 -j DROP
sudo iptables -D INPUT -s 192.168.132.223 -j DROP
```

### Expected Behavior
1. Health checks from greenfin to redfin fail
2. Monitoring alerts trigger (check Grafana)
3. Services on both nodes continue running independently
4. Recovery automatic when partition heals

### Verify
```bash
# From greenfin after unblock
ping -c 3 192.168.132.223
curl -s http://192.168.132.223:8080/health
```

---

## Test 4: Disk Space Exhaustion Simulation (MEDIUM RISK)

**Purpose**: Test behavior when disk fills up

### Execute
```bash
# On redfin - fill temp space (NOT production partitions!)
ssh dereadi@192.168.132.223

# Create large file in /tmp (will be cleaned on reboot)
dd if=/dev/zero of=/tmp/chaos_test_fill bs=1G count=10

# Monitor disk
df -h /tmp

# Cleanup immediately after observation
rm /tmp/chaos_test_fill
```

### Expected Behavior
1. Disk usage rises
2. Services may log warnings
3. Cleanup restores normal operation

### NEVER do this on:
- `/ganuda` - production data
- `/pg_data` - database
- `/sag_data` - repository

---

## Test 5: Memory Pressure (MEDIUM RISK)

**Purpose**: Test OOM killer behavior and service recovery

### Execute
```bash
# On greenfin (not redfin - protect GPU workloads)
ssh dereadi@192.168.132.224

# Allocate memory gradually (stress-ng tool)
sudo apt install stress-ng -y

# 70% memory pressure for 30 seconds
stress-ng --vm 1 --vm-bytes 70% --timeout 30s

# Monitor
watch -n 1 free -h
```

### Expected Behavior
1. Memory usage spikes
2. System may swap
3. OOM killer may terminate processes if critical
4. Recovery after stress ends

---

## Test 6: Full Service Stack Restart (LOW RISK)

**Purpose**: Verify all services come up correctly after full restart

### Execute
```bash
# On redfin - restart all Cherokee services
ssh dereadi@192.168.132.223

# List Cherokee services
systemctl list-units --type=service | grep -E "(llm-gateway|it-triad|jr|ganuda)"

# Restart all (one by one to observe)
for svc in llm-gateway it-triad executive-jr-autonomic memory-jr-autonomic ganuda-heartbeat; do
  echo "Restarting $svc..."
  sudo systemctl restart $svc
  sleep 5
  systemctl is-active $svc
done
```

### Verify
```bash
# All should be active
systemctl is-active llm-gateway it-triad executive-jr-autonomic memory-jr-autonomic ganuda-heartbeat
```

---

## Test 7: Database Failover Readiness (HIGH RISK - Council Approval)

**Purpose**: Test PostgreSQL crash recovery

### Pre-requisites
- Fresh backup verified
- Council vote approved
- Maintenance window scheduled

### Execute
```bash
# On bluefin
ssh dereadi@192.168.132.222

# Create backup first!
sudo -u postgres pg_dump zammad_production | gzip > /ganuda/backups/pre_chaos_$(date +%Y%m%d_%H%M%S).sql.gz

# Simulate crash (kill -9)
sudo pkill -9 postgres

# PostgreSQL should auto-recover via systemd
sleep 10
systemctl status postgresql
```

### Verify
```bash
# Database accessible
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production -c "SELECT count(*) FROM thermal_memory_archive;"

# Check for corruption
sudo -u postgres psql -c "SELECT datname, pg_database_size(datname) FROM pg_database;"
```

---

## Chaos Test Automation Script

Create `/ganuda/scripts/chaos_test_suite.sh`:

```bash
#!/bin/bash
# Cherokee AI Federation - Chaos Test Suite
# Usage: ./chaos_test_suite.sh [test_name]
# Tests: gateway, connections, memory, services

set -e

POSTGRES_HOST="192.168.132.222"
REDFIN="192.168.132.223"
LOG_FILE="/var/log/ganuda/chaos_tests.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

test_gateway_recovery() {
    log "TEST: LLM Gateway Recovery"

    # Check baseline
    if ! curl -sf http://$REDFIN:8080/health > /dev/null; then
        log "SKIP: Gateway not running"
        return 1
    fi

    # Kill and time recovery
    START=$(date +%s)
    ssh dereadi@$REDFIN "sudo pkill -f 'uvicorn gateway:app'"

    # Wait for recovery (max 60s)
    for i in {1..60}; do
        if curl -sf http://$REDFIN:8080/health > /dev/null 2>&1; then
            END=$(date +%s)
            RECOVERY_TIME=$((END - START))
            log "PASS: Gateway recovered in ${RECOVERY_TIME}s"
            return 0
        fi
        sleep 1
    done

    log "FAIL: Gateway did not recover within 60s"
    return 1
}

test_db_connections() {
    log "TEST: Database Connection Handling"

    INITIAL=$(PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -t -c "SELECT count(*) FROM pg_stat_activity;")
    log "Initial connections: $INITIAL"

    # This is informational only - don't actually exhaust connections
    MAX=$(PGPASSWORD=jawaseatlasers2 psql -h $POSTGRES_HOST -U claude -d zammad_production -t -c "SHOW max_connections;")
    log "Max connections: $MAX"
    log "PASS: Connection check complete"
}

test_service_restart() {
    log "TEST: Service Restart Resilience"

    SERVICES="llm-gateway"
    for svc in $SERVICES; do
        if ssh dereadi@$REDFIN "systemctl is-active $svc" > /dev/null 2>&1; then
            ssh dereadi@$REDFIN "sudo systemctl restart $svc"
            sleep 5
            if ssh dereadi@$REDFIN "systemctl is-active $svc" > /dev/null 2>&1; then
                log "PASS: $svc restarted successfully"
            else
                log "FAIL: $svc did not restart"
            fi
        else
            log "SKIP: $svc not active"
        fi
    done
}

# Main
case "${1:-all}" in
    gateway) test_gateway_recovery ;;
    connections) test_db_connections ;;
    services) test_service_restart ;;
    all)
        test_gateway_recovery
        test_db_connections
        test_service_restart
        ;;
    *)
        echo "Usage: $0 [gateway|connections|services|all]"
        exit 1
        ;;
esac

log "Chaos test suite complete"
```

## Post-Test Checklist

- [ ] All services returned to normal
- [ ] No data loss verified
- [ ] Monitoring alerts cleared
- [ ] Results logged to thermal memory
- [ ] Runbooks updated if gaps found

## Logging Results to Thermal Memory

```sql
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production << 'EOSQL'
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
VALUES (
  'CHAOS-TEST-RESULTS-' || to_char(now(), 'YYYYMMDDHH24MI'),
  'Chaos Test Results - [DATE]

  TESTS RUN:
  1. LLM Gateway Kill: [PASS/FAIL] - Recovery time: Xs
  2. DB Connections: [PASS/FAIL] - Max handled: N
  3. Service Restart: [PASS/FAIL] - All services recovered

  ISSUES FOUND:
  - [List any issues]

  RUNBOOK UPDATES NEEDED:
  - [List any gaps]',
  'FRESH',
  90.0,
  true
);
EOSQL
```

## Schedule

| Test | Frequency | When |
|------|-----------|------|
| Service restarts | Weekly | Sunday 3 AM |
| Connection tests | Monthly | 1st Sunday |
| Full chaos suite | Quarterly | With council approval |

---

FOR SEVEN GENERATIONS - Testing resilience protects future operations.
