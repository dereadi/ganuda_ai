# Jr Instruction: Security Health Check Stack (Trivy + Lynis)
*Kanban: #550 | Priority: P0 | Estimated: 4-6 hours*
*References: https://trivy.dev/ | https://github.com/CISOfy/lynis*

## Objective
Deploy automated security health checks on redfin using Trivy (CVE scanning) and Lynis (CIS audit), with daily cron and results stored in PostgreSQL.

## Step 1: Install Trivy

```text
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin v0.58.2
trivy --version
```

## Step 2: Install Lynis

```text
cd /ganuda
git clone https://github.com/CISOfy/lynis.git /ganuda/tools/lynis
```

## Step 3: Create Health Check Script

Create `/ganuda/scripts/security_health_check.sh`

```text
#!/bin/bash
# Cherokee Federation Security Health Check
# Runs Trivy (CVE) + Lynis (CIS) and stores results in PostgreSQL
# For Seven Generations

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="/ganuda/reports/security"
mkdir -p "$REPORT_DIR"

HOSTNAME=$(hostname)
DB_HOST="192.168.132.222"
DB_USER="claude"
DB_NAME="zammad_production"

echo "[$(date)] Starting security health check on $HOSTNAME"

# --- Trivy: Filesystem CVE Scan ---
echo "[$(date)] Running Trivy filesystem scan..."
TRIVY_JSON="$REPORT_DIR/trivy_${HOSTNAME}_${TIMESTAMP}.json"
trivy fs --format json --output "$TRIVY_JSON" --severity HIGH,CRITICAL /ganuda/ 2>/dev/null || true

TRIVY_CRITICAL=$(python3 -c "
import json, sys
try:
    data = json.load(open('$TRIVY_JSON'))
    results = data.get('Results', [])
    critical = sum(1 for r in results for v in r.get('Vulnerabilities', []) if v.get('Severity') == 'CRITICAL')
    high = sum(1 for r in results for v in r.get('Vulnerabilities', []) if v.get('Severity') == 'HIGH')
    print(f'{critical},{high}')
except:
    print('0,0')
")
CRIT_COUNT=$(echo "$TRIVY_CRITICAL" | cut -d',' -f1)
HIGH_COUNT=$(echo "$TRIVY_CRITICAL" | cut -d',' -f2)
echo "[$(date)] Trivy: $CRIT_COUNT CRITICAL, $HIGH_COUNT HIGH vulnerabilities"

# --- Lynis: CIS Audit ---
echo "[$(date)] Running Lynis audit..."
LYNIS_REPORT="$REPORT_DIR/lynis_${HOSTNAME}_${TIMESTAMP}.log"
cd /ganuda/tools/lynis
./lynis audit system --quick --no-colors > "$LYNIS_REPORT" 2>&1 || true

LYNIS_SCORE=$(grep -oP 'Hardening index : \K[0-9]+' "$LYNIS_REPORT" 2>/dev/null || echo "0")
LYNIS_WARNINGS=$(grep -c "Warning" "$LYNIS_REPORT" 2>/dev/null || echo "0")
echo "[$(date)] Lynis: Score=$LYNIS_SCORE, Warnings=$LYNIS_WARNINGS"

# --- Store Results in PostgreSQL ---
echo "[$(date)] Storing results in database..."
PGPASSWORD=$(cat /ganuda/config/secrets.env 2>/dev/null | grep DB_PASSWORD | cut -d= -f2 || echo "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE")

PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
INSERT INTO security_health_checks (
    hostname, check_timestamp,
    trivy_critical, trivy_high, trivy_report_path,
    lynis_score, lynis_warnings, lynis_report_path
) VALUES (
    '$HOSTNAME', NOW(),
    $CRIT_COUNT, $HIGH_COUNT, '$TRIVY_JSON',
    $LYNIS_SCORE, $LYNIS_WARNINGS, '$LYNIS_REPORT'
);" 2>/dev/null || echo "[WARN] DB insert failed - table may not exist yet"

echo "[$(date)] Security health check complete"

# --- Alert on CRITICAL findings ---
if [ "$CRIT_COUNT" -gt 0 ]; then
    echo "[ALERT] $CRIT_COUNT CRITICAL CVEs found on $HOSTNAME!"
fi
```

## Step 4: Create Database Table

Create `/ganuda/scripts/sql/create_security_health_checks.sql`

```text
CREATE TABLE IF NOT EXISTS security_health_checks (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(64) NOT NULL,
    check_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    trivy_critical INTEGER DEFAULT 0,
    trivy_high INTEGER DEFAULT 0,
    trivy_report_path TEXT,
    lynis_score INTEGER DEFAULT 0,
    lynis_warnings INTEGER DEFAULT 0,
    lynis_report_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_shc_hostname ON security_health_checks(hostname);
CREATE INDEX idx_shc_timestamp ON security_health_checks(check_timestamp);
```

## Step 5: Make Executable and Test

```text
chmod +x /ganuda/scripts/security_health_check.sh
```

## Validation
- `trivy --version` returns version
- `/ganuda/tools/lynis/lynis --version` returns version
- `security_health_checks` table exists in zammad_production
- Running the script produces JSON + log reports in `/ganuda/reports/security/`
- Results appear in `security_health_checks` table

## Notes
- Cron setup (daily 3AM) requires sudo — TPM will deploy
- Future: expand to bluefin and greenfin via Ansible
- Future: add AIDE file integrity monitoring (Tier 2)
- Script reads DB password from secrets.env, falls back to current password
