# Jr Build Instructions: IoT Scheduled Scans

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: IT Triad Jr
**Date**: December 13, 2025

## Objective

Set up scheduled IoT device discovery scans on greenfin to:
1. Automatically discover new devices on both networks
2. Update device status in the `iot_devices` database table
3. Alert on new or unauthorized devices
4. Maintain accurate device inventory

## Network Topology

greenfin has two network interfaces:
```
eno1:      192.168.132.224 (Federation network)
wlp195s0:  10.0.0.118      (IoT network via WiFi bridge)
```

## Pre-requisites Verified

- [x] arp-scan installed on greenfin
- [x] nmap installed on greenfin
- [x] `iot_devices` table exists on bluefin (47 devices)
- [x] greenfin can reach both networks

## Step 1: Create Scanner Script

Create `/ganuda/scripts/iot_scan.sh` on greenfin:

```bash
#!/bin/bash
# Cherokee AI Federation - IoT Network Scanner
# Runs on greenfin, updates iot_devices table on bluefin
# Usage: /ganuda/scripts/iot_scan.sh [discovery|service|full]

set -e

SCAN_TYPE="${1:-discovery}"
LOG_FILE="/var/log/ganuda/iot_scan.log"
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_NAME="zammad_production"
export PGPASSWORD="jawaseatlasers2"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Ensure log directory exists
mkdir -p /var/log/ganuda

log "Starting IoT scan: $SCAN_TYPE"

# --- Scan Federation Network (192.168.132.x) ---
log "Scanning federation network (192.168.132.0/24)..."
FEDERATION_DEVICES=$(sudo arp-scan -I eno1 192.168.132.0/24 2>/dev/null | grep -E '^[0-9]+\.' | awk '{print $1}' | sort -u)

for ip in $FEDERATION_DEVICES; do
    mac=$(sudo arp-scan -I eno1 $ip/32 2>/dev/null | grep -E '^[0-9]+\.' | awk '{print $2}' | head -1)
    if [ -n "$mac" ]; then
        log "Found: $ip ($mac)"
        psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -q -c "
            INSERT INTO iot_devices (ip_address, mac_address, status, last_seen, first_seen)
            VALUES ('$ip', '$mac', 'active', now(), now())
            ON CONFLICT (mac_address) DO UPDATE SET
                ip_address = EXCLUDED.ip_address,
                status = 'active',
                last_seen = now();"
    fi
done

# --- Scan IoT Network (10.0.0.x) ---
log "Scanning IoT network (10.0.0.0/24)..."
IOT_DEVICES=$(sudo arp-scan -I wlp195s0 10.0.0.0/24 2>/dev/null | grep -E '^[0-9]+\.' | awk '{print $1}' | sort -u)

for ip in $IOT_DEVICES; do
    mac=$(sudo arp-scan -I wlp195s0 $ip/32 2>/dev/null | grep -E '^[0-9]+\.' | awk '{print $2}' | head -1)
    vendor=$(sudo arp-scan -I wlp195s0 $ip/32 2>/dev/null | grep -E '^[0-9]+\.' | awk '{print $3" "$4" "$5}' | head -1)
    if [ -n "$mac" ]; then
        log "Found: $ip ($mac) - $vendor"
        psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -q -c "
            INSERT INTO iot_devices (ip_address, mac_address, vendor, status, last_seen, first_seen)
            VALUES ('$ip', '$mac', '$vendor', 'active', now(), now())
            ON CONFLICT (mac_address) DO UPDATE SET
                ip_address = EXCLUDED.ip_address,
                vendor = COALESCE(NULLIF('$vendor', ''), iot_devices.vendor),
                status = 'active',
                last_seen = now();"
    fi
done

# --- Mark stale devices as inactive ---
log "Marking devices not seen in 24 hours as inactive..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -q -c "
    UPDATE iot_devices SET status = 'inactive'
    WHERE last_seen < now() - interval '24 hours' AND status = 'active';"

# --- Service scan if requested ---
if [ "$SCAN_TYPE" = "service" ] || [ "$SCAN_TYPE" = "full" ]; then
    log "Running service discovery scan with nmap..."
    for ip in $IOT_DEVICES; do
        log "Scanning services on $ip..."
        services=$(sudo nmap -sV --top-ports 20 "$ip" 2>/dev/null | grep "open" | tr '\n' ';')
        if [ -n "$services" ]; then
            # Escape single quotes for SQL
            services_escaped=$(echo "$services" | sed "s/'/''/g")
            psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -q -c "
                UPDATE iot_devices SET open_services = '$services_escaped'
                WHERE ip_address = '$ip';"
        fi
    done
fi

# --- Report Summary ---
ACTIVE=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM iot_devices WHERE status = 'active';")
INACTIVE=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM iot_devices WHERE status = 'inactive';")
log "Scan complete. Active: $ACTIVE, Inactive: $INACTIVE"

# --- Check for new unauthorized devices ---
NEW_UNAUTHORIZED=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "
    SELECT count(*) FROM iot_devices
    WHERE is_authorized IS NULL
    AND first_seen > now() - interval '1 hour';")

if [ "$NEW_UNAUTHORIZED" -gt 0 ]; then
    log "ALERT: $NEW_UNAUTHORIZED new unauthorized device(s) detected!"
    # Could integrate with telegram bot here
fi

log "IoT scan completed successfully"
```

## Step 2: Deploy Script

```bash
ssh dereadi@192.168.132.224

# Create script
sudo mkdir -p /ganuda/scripts
sudo vim /ganuda/scripts/iot_scan.sh
# [paste content above]

# Make executable
sudo chmod +x /ganuda/scripts/iot_scan.sh

# Create log directory
sudo mkdir -p /var/log/ganuda
sudo chown dereadi:dereadi /var/log/ganuda

# Test run
sudo /ganuda/scripts/iot_scan.sh discovery
```

## Step 3: Set Up Cron Jobs

```bash
ssh dereadi@192.168.132.224

# Edit root crontab (needed for arp-scan sudo)
sudo crontab -e
```

Add these entries:

```cron
# Cherokee AI IoT Network Scanning
# Discovery scan every hour at minute 15
15 * * * * /ganuda/scripts/iot_scan.sh discovery >> /var/log/ganuda/iot_scan.log 2>&1

# Service scan daily at 3:33 AM (sacred timing)
33 3 * * * /ganuda/scripts/iot_scan.sh service >> /var/log/ganuda/iot_scan.log 2>&1
```

## Step 4: Verify Cron is Active

```bash
# Check crontab
sudo crontab -l

# Verify cron service
systemctl status cron

# Watch for next run
tail -f /var/log/ganuda/iot_scan.log
```

## Step 5: Register in Tribe Config Registry

```sql
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production << 'EOSQL'
INSERT INTO tribe_config_registry (
    config_name, config_type, description, hostname,
    file_path, schedule_cron, status_command, health_check_command,
    manages, owner, criticality, tags
) VALUES (
    'iot-scan-hourly', 'cron', 'Hourly IoT device discovery scan',
    'greenfin', '/ganuda/scripts/iot_scan.sh',
    '15 * * * *', 'sudo crontab -l | grep iot_scan',
    'tail -1 /var/log/ganuda/iot_scan.log | grep -q "completed successfully"',
    ARRAY['iot_devices'], 'tribe', 'medium',
    ARRAY['iot', 'discovery', 'cron', 'scheduled']
), (
    'iot-scan-daily-service', 'cron', 'Daily IoT service discovery scan',
    'greenfin', '/ganuda/scripts/iot_scan.sh',
    '33 3 * * *', 'sudo crontab -l | grep "iot_scan.sh service"',
    'grep "service" /var/log/ganuda/iot_scan.log | tail -1',
    ARRAY['iot_devices'], 'tribe', 'medium',
    ARRAY['iot', 'discovery', 'cron', 'nmap', 'services']
)
ON CONFLICT (config_name) DO UPDATE SET
    schedule_cron = EXCLUDED.schedule_cron,
    description = EXCLUDED.description;
EOSQL
```

## Verification Checklist

- [ ] `/ganuda/scripts/iot_scan.sh` created on greenfin
- [ ] Script is executable
- [ ] `/var/log/ganuda` directory exists
- [ ] Test run completes successfully
- [ ] Hourly cron job added (15 * * * *)
- [ ] Daily service scan cron job added (33 3 * * *)
- [ ] Cron jobs registered in Tribe Config Registry
- [ ] Log rotation configured (optional)

## Monitoring

```bash
# Check last scan results
tail -50 /var/log/ganuda/iot_scan.log

# Check device counts
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
    SELECT status, count(*) FROM iot_devices GROUP BY status;"

# Check for unauthorized devices
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
    SELECT ip_address, mac_address, vendor, first_seen
    FROM iot_devices WHERE is_authorized IS NULL ORDER BY first_seen DESC LIMIT 10;"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| arp-scan fails | Check interface name: `ip addr show` |
| Database connection fails | Verify PGPASSWORD and host connectivity |
| Cron not running | Check `systemctl status cron` |
| Permission denied | Run with sudo or check file permissions |

---

FOR SEVEN GENERATIONS - Continuous monitoring protects the network.
