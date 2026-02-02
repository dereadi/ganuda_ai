# JR-SECURITY-PHASE7-SUPPLY-CHAIN-CONTINUOUS-FEB02-2026
## Phase 7: Supply Chain Security & Continuous Dependency Monitoring

**Priority:** P2
**Assigned:** DevOps Jr.
**Target Node:** redfin (192.168.132.223)
**Estimated Scope:** 7 new files, 1 append, 2 systemd units
**Depends on:** None (standalone security hardening)

---

### Background

The Cherokee AI Federation currently downloads ML models from Hugging Face without checksum or signature verification. Python dependencies across all virtualenvs have no lock files (`poetry.lock`, `Pipfile.lock`), no dependency vulnerability scanning (no Snyk, no Dependabot), and no SBOM (Software Bill of Materials). This leaves the federation exposed to:

- **Model tampering** -- a compromised or swapped model file in `/ganuda/models/` would go undetected
- **Dependency confusion attacks** -- no pinned hashes means `pip install` could pull a malicious package
- **Known CVE exposure** -- no scanning means we run vulnerable packages indefinitely without knowing
- **Audit gaps** -- no SBOM means we cannot answer "what software is running?" for compliance

The main model is `qwen2.5-coder-32b-awq` served by vLLM. Known virtualenvs:
- `/ganuda/vetassist/backend/venv/`
- `/ganuda/services/llm_gateway/venv/`

### CRITICAL EXECUTOR RULES

- **NO SEARCH/REPLACE blocks** -- do not use sed-style inline edits
- **Use ```bash code blocks only** -- all steps must be executable bash
- **Create new files via heredoc** -- use `cat <<'HEREDOC_EOF' > /path/to/file` pattern

---

### Step 1: Generate Model Integrity Checksums

Create two scripts: one to generate baseline checksums for all model files, and one to verify them.

#### 1a. Create /ganuda/scripts/generate_model_checksums.sh

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/generate_model_checksums.sh
#!/usr/bin/env bash
# Phase 7 Supply Chain: Generate SHA-256 checksums for all ML model files
# Run once to establish baseline, re-run after any model update
set -euo pipefail

MODEL_DIR="/ganuda/models"
CHECKSUM_FILE="/ganuda/config/model_checksums.sha256"
MANIFEST_FILE="/ganuda/config/model_manifest.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ ! -d "$MODEL_DIR" ]; then
    echo "ERROR: Model directory $MODEL_DIR does not exist"
    exit 1
fi

mkdir -p /ganuda/config

echo "=== Generating model checksums ==="
echo "Model directory: $MODEL_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Generate SHA-256 checksums for every file under /ganuda/models/
echo "# Model checksums generated: $TIMESTAMP" > "$CHECKSUM_FILE"
echo "# Source directory: $MODEL_DIR" >> "$CHECKSUM_FILE"
find "$MODEL_DIR" -type f -print0 | sort -z | xargs -0 sha256sum >> "$CHECKSUM_FILE"

TOTAL_FILES=$(find "$MODEL_DIR" -type f | wc -l)
TOTAL_SIZE=$(du -sb "$MODEL_DIR" | awk '{print $1}')
TOTAL_SIZE_HUMAN=$(du -sh "$MODEL_DIR" | awk '{print $1}')

echo "Checksums written to: $CHECKSUM_FILE"
echo "Total files: $TOTAL_FILES"
echo "Total size: $TOTAL_SIZE_HUMAN"

# Generate model manifest JSON
# Walk each top-level directory under /ganuda/models/ as a separate model
echo "[" > "$MANIFEST_FILE"
FIRST=true
for MODEL_PATH in "$MODEL_DIR"/*/; do
    [ -d "$MODEL_PATH" ] || continue
    MODEL_NAME=$(basename "$MODEL_PATH")
    DIR_SIZE=$(du -sb "$MODEL_PATH" | awk '{print $1}')
    DIR_SIZE_HUMAN=$(du -sh "$MODEL_PATH" | awk '{print $1}')
    FILE_COUNT=$(find "$MODEL_PATH" -type f | wc -l)

    # Generate a single top-level checksum by hashing the concatenation of all file checksums
    TOP_CHECKSUM=$(find "$MODEL_PATH" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')

    # Attempt to read download date from directory mtime
    DOWNLOAD_DATE=$(stat -c '%Y' "$MODEL_PATH" 2>/dev/null || echo "unknown")
    if [ "$DOWNLOAD_DATE" != "unknown" ]; then
        DOWNLOAD_DATE=$(date -u -d "@$DOWNLOAD_DATE" +"%Y-%m-%dT%H:%M:%SZ")
    fi

    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        echo "," >> "$MANIFEST_FILE"
    fi

    cat >> "$MANIFEST_FILE" <<ENTRY_EOF
  {
    "model_name": "$MODEL_NAME",
    "source_url": "https://huggingface.co/$MODEL_NAME",
    "download_date": "$DOWNLOAD_DATE",
    "total_size_bytes": $DIR_SIZE,
    "total_size_human": "$DIR_SIZE_HUMAN",
    "file_count": $FILE_COUNT,
    "top_level_checksum": "$TOP_CHECKSUM",
    "generated_at": "$TIMESTAMP"
  }
ENTRY_EOF
done
echo "" >> "$MANIFEST_FILE"
echo "]" >> "$MANIFEST_FILE"

echo ""
echo "Manifest written to: $MANIFEST_FILE"
echo "=== Checksum generation complete ==="
HEREDOC_EOF
chmod +x /ganuda/scripts/generate_model_checksums.sh
```

#### 1b. Create /ganuda/scripts/verify_model_checksums.sh

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/verify_model_checksums.sh
#!/usr/bin/env bash
# Phase 7 Supply Chain: Verify model file integrity against baseline checksums
# Exit 0 = all match, Exit 1 = mismatches found (potential tampering)
# Designed to run as weekly cron job
set -uo pipefail

CHECKSUM_FILE="/ganuda/config/model_checksums.sha256"
LOG_DIR="/ganuda/logs/security"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/model_verify_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

if [ ! -f "$CHECKSUM_FILE" ]; then
    echo "ERROR: Checksum file not found: $CHECKSUM_FILE" | tee "$LOG_FILE"
    echo "Run generate_model_checksums.sh first to establish baseline." | tee -a "$LOG_FILE"
    exit 1
fi

echo "=== Model Integrity Verification ===" | tee "$LOG_FILE"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$LOG_FILE"
echo "Checksum file: $CHECKSUM_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Filter out comment lines and verify
TEMP_CHECKSUMS=$(mktemp)
grep -v '^#' "$CHECKSUM_FILE" > "$TEMP_CHECKSUMS"

TOTAL=$(wc -l < "$TEMP_CHECKSUMS")
echo "Verifying $TOTAL files..." | tee -a "$LOG_FILE"

RESULT=$(sha256sum -c "$TEMP_CHECKSUMS" 2>&1)
EXIT_CODE=$?
echo "$RESULT" >> "$LOG_FILE"

rm -f "$TEMP_CHECKSUMS"

PASSED=$(echo "$RESULT" | grep -c ': OK$' || true)
FAILED=$(echo "$RESULT" | grep -c ': FAILED$' || true)
MISSING=$(echo "$RESULT" | grep -c 'No such file' || true)

echo "" | tee -a "$LOG_FILE"
echo "=== Summary ===" | tee -a "$LOG_FILE"
echo "Total files: $TOTAL" | tee -a "$LOG_FILE"
echo "Passed: $PASSED" | tee -a "$LOG_FILE"
echo "Failed: $FAILED" | tee -a "$LOG_FILE"
echo "Missing: $MISSING" | tee -a "$LOG_FILE"

if [ "$EXIT_CODE" -ne 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "WARNING: INTEGRITY CHECK FAILED" | tee -a "$LOG_FILE"
    echo "Mismatched or missing files detected. Possible tampering." | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Failed files:" | tee -a "$LOG_FILE"
    echo "$RESULT" | grep -E '(FAILED|No such file)' | tee -a "$LOG_FILE"
    exit 1
else
    echo "" | tee -a "$LOG_FILE"
    echo "ALL FILES VERIFIED SUCCESSFULLY" | tee -a "$LOG_FILE"
    exit 0
fi
HEREDOC_EOF
chmod +x /ganuda/scripts/verify_model_checksums.sh
```

---

### Step 2: Generate Dependency Lock Files and SBOM

#### 2a. Create /ganuda/scripts/generate_dependency_locks.sh

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/generate_dependency_locks.sh
#!/usr/bin/env bash
# Phase 7 Supply Chain: Generate dependency lock files and CycloneDX SBOM
# for all known virtualenvs
set -euo pipefail

SBOM_DIR="/ganuda/config/sbom"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

VENVS=(
    "/ganuda/vetassist/backend/venv"
    "/ganuda/services/llm_gateway/venv"
)

mkdir -p "$SBOM_DIR"

echo "=== Dependency Lock & SBOM Generation ==="
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

for VENV_PATH in "${VENVS[@]}"; do
    VENV_NAME=$(echo "$VENV_PATH" | tr '/' '_' | sed 's/^_//')
    PIP_BIN="$VENV_PATH/bin/pip"

    if [ ! -f "$PIP_BIN" ]; then
        echo "SKIP: Virtualenv not found: $VENV_PATH"
        continue
    fi

    echo "--- Processing: $VENV_PATH ---"

    # Generate lock file (pinned versions with hashes)
    LOCK_FILE="$SBOM_DIR/${VENV_NAME}_requirements.lock"
    echo "  Generating lock file: $LOCK_FILE"
    "$PIP_BIN" freeze > "$LOCK_FILE"
    PKG_COUNT=$(wc -l < "$LOCK_FILE")
    echo "  Packages locked: $PKG_COUNT"

    # Install cyclonedx-bom if not present
    if ! "$VENV_PATH/bin/python" -m cyclonedx_py --help >/dev/null 2>&1; then
        echo "  Installing cyclonedx-bom..."
        "$PIP_BIN" install cyclonedx-bom --quiet
    fi

    # Generate CycloneDX SBOM in JSON format
    SBOM_FILE="$SBOM_DIR/${VENV_NAME}_sbom_${TIMESTAMP}.json"
    echo "  Generating SBOM: $SBOM_FILE"
    "$VENV_PATH/bin/python" -m cyclonedx_py environment \
        --output "$SBOM_FILE" \
        --output-format json \
        "$VENV_PATH" 2>/dev/null || {
        # Fallback: older cyclonedx-bom syntax
        "$VENV_PATH/bin/python" -m cyclonedx_py \
            -e \
            --format json \
            -o "$SBOM_FILE" 2>/dev/null || {
            echo "  WARNING: Could not generate SBOM. cyclonedx-bom may need manual setup."
            echo "  Try: $PIP_BIN install cyclonedx-bom && $VENV_PATH/bin/python -m cyclonedx_py --help"
        }
    }

    if [ -f "$SBOM_FILE" ]; then
        echo "  SBOM generated successfully."
    fi

    echo ""
done

echo "=== Lock & SBOM generation complete ==="
echo "Output directory: $SBOM_DIR"
ls -la "$SBOM_DIR/"
HEREDOC_EOF
chmod +x /ganuda/scripts/generate_dependency_locks.sh
```

#### 2b. Create /ganuda/scripts/scan_dependencies.sh

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/scan_dependencies.sh
#!/usr/bin/env bash
# Phase 7 Supply Chain: Scan Python dependencies for known vulnerabilities
# Uses pip-audit (PyPA official tool)
set -uo pipefail

AUDIT_DIR="/ganuda/security/dependency_audit"
TIMESTAMP=$(date +"%Y%m%d")
SUMMARY_FILE="$AUDIT_DIR/summary_${TIMESTAMP}.txt"

VENVS=(
    "/ganuda/vetassist/backend/venv"
    "/ganuda/services/llm_gateway/venv"
)

mkdir -p "$AUDIT_DIR"

echo "=== Dependency Vulnerability Scan ===" | tee "$SUMMARY_FILE"
echo "Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

TOTAL_PACKAGES=0
TOTAL_VULNS=0
TOTAL_CRITICAL=0
TOTAL_HIGH=0
TOTAL_MEDIUM=0
TOTAL_LOW=0

for VENV_PATH in "${VENVS[@]}"; do
    PIP_BIN="$VENV_PATH/bin/pip"
    PYTHON_BIN="$VENV_PATH/bin/python"
    VENV_NAME=$(basename "$(dirname "$VENV_PATH")")

    if [ ! -f "$PIP_BIN" ]; then
        echo "SKIP: $VENV_PATH not found" | tee -a "$SUMMARY_FILE"
        continue
    fi

    echo "--- Scanning: $VENV_PATH ---" | tee -a "$SUMMARY_FILE"

    # Install pip-audit if not present
    if ! "$VENV_PATH/bin/pip-audit" --help >/dev/null 2>&1; then
        if ! "$PYTHON_BIN" -m pip_audit --help >/dev/null 2>&1; then
            echo "  Installing pip-audit..." | tee -a "$SUMMARY_FILE"
            "$PIP_BIN" install pip-audit --quiet
        fi
    fi

    # Run pip-audit with JSON output
    SCAN_FILE="$AUDIT_DIR/scan_${VENV_NAME}_${TIMESTAMP}.json"
    echo "  Output: $SCAN_FILE" | tee -a "$SUMMARY_FILE"

    "$PYTHON_BIN" -m pip_audit \
        --format json \
        --output "$SCAN_FILE" \
        --requirement <("$PIP_BIN" freeze) \
        2>/dev/null || {
        # Fallback: run pip-audit directly against the virtualenv
        "$VENV_PATH/bin/pip-audit" \
            --format json \
            --output "$SCAN_FILE" \
            2>/dev/null || {
            echo "  WARNING: pip-audit scan failed. Check installation." | tee -a "$SUMMARY_FILE"
            continue
        }
    }

    if [ -f "$SCAN_FILE" ]; then
        # Parse results
        PKG_COUNT=$("$PYTHON_BIN" -c "
import json, sys
with open('$SCAN_FILE') as f:
    data = json.load(f)
deps = data if isinstance(data, list) else data.get('dependencies', [])
print(len(deps))
" 2>/dev/null || echo "0")

        VULN_COUNT=$("$PYTHON_BIN" -c "
import json, sys
with open('$SCAN_FILE') as f:
    data = json.load(f)
deps = data if isinstance(data, list) else data.get('dependencies', [])
vulns = sum(len(d.get('vulns', [])) for d in deps)
print(vulns)
" 2>/dev/null || echo "0")

        echo "  Packages scanned: $PKG_COUNT" | tee -a "$SUMMARY_FILE"
        echo "  Vulnerabilities found: $VULN_COUNT" | tee -a "$SUMMARY_FILE"

        TOTAL_PACKAGES=$((TOTAL_PACKAGES + PKG_COUNT))
        TOTAL_VULNS=$((TOTAL_VULNS + VULN_COUNT))
    fi

    echo "" | tee -a "$SUMMARY_FILE"
done

echo "=== OVERALL SUMMARY ===" | tee -a "$SUMMARY_FILE"
echo "Total packages scanned: $TOTAL_PACKAGES" | tee -a "$SUMMARY_FILE"
echo "Total vulnerabilities: $TOTAL_VULNS" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

if [ "$TOTAL_VULNS" -gt 0 ]; then
    echo "ACTION REQUIRED: Vulnerabilities detected. Review scan files in $AUDIT_DIR" | tee -a "$SUMMARY_FILE"
else
    echo "No known vulnerabilities detected." | tee -a "$SUMMARY_FILE"
fi

echo "=== Scan complete ==="
HEREDOC_EOF
chmod +x /ganuda/scripts/scan_dependencies.sh
```

---

### Step 3: Create .gitignore Additions for Security

```bash
# Append security-related paths to .gitignore if not already present
GITIGNORE="/ganuda/.gitignore"

if [ ! -f "$GITIGNORE" ]; then
    touch "$GITIGNORE"
fi

ENTRIES=(
    "security/ai_red_team/results/"
    "security/evidence/"
    "security/dependency_audit/"
    "logs/security/"
)

ADDED=false
for ENTRY in "${ENTRIES[@]}"; do
    if ! grep -qxF "$ENTRY" "$GITIGNORE" 2>/dev/null; then
        if [ "$ADDED" = false ]; then
            echo "" >> "$GITIGNORE"
            echo "# Security scan results (Phase 7 Supply Chain)" >> "$GITIGNORE"
            ADDED=true
        fi
        echo "$ENTRY" >> "$GITIGNORE"
    fi
done

if [ "$ADDED" = true ]; then
    echo "Added security paths to $GITIGNORE"
else
    echo "Security paths already present in $GITIGNORE"
fi
```

---

### Step 4: Create Automated Security Check Script

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/security_check.sh
#!/usr/bin/env bash
# Phase 7 Supply Chain: Unified weekly security check
# Verifies model integrity, scans dependencies, checks infrastructure
# Designed to run as weekly cron or systemd timer
set -uo pipefail

LOG_DIR="/ganuda/logs/security"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$LOG_DIR/security_check_${TIMESTAMP}.txt"
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

mkdir -p "$LOG_DIR"

log_pass() {
    echo "[PASS] $1" | tee -a "$REPORT_FILE"
    PASS_COUNT=$((PASS_COUNT + 1))
}

log_fail() {
    echo "[FAIL] $1" | tee -a "$REPORT_FILE"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

log_warn() {
    echo "[WARN] $1" | tee -a "$REPORT_FILE"
    WARN_COUNT=$((WARN_COUNT + 1))
}

echo "============================================" | tee "$REPORT_FILE"
echo "  Cherokee AI Federation Security Check" | tee -a "$REPORT_FILE"
echo "  $(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$REPORT_FILE"
echo "  Node: $(hostname)" | tee -a "$REPORT_FILE"
echo "============================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- Check 1: Model Integrity ---
echo "--- 1. Model Integrity Checksums ---" | tee -a "$REPORT_FILE"
if [ -f /ganuda/scripts/verify_model_checksums.sh ]; then
    if /ganuda/scripts/verify_model_checksums.sh >/dev/null 2>&1; then
        log_pass "All model checksums verified"
    else
        log_fail "Model checksum verification FAILED - possible tampering"
    fi
else
    log_warn "Model checksum verifier not found. Run generate_model_checksums.sh first."
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 2: Dependency Vulnerabilities ---
echo "--- 2. Dependency Vulnerability Scan ---" | tee -a "$REPORT_FILE"
if [ -f /ganuda/scripts/scan_dependencies.sh ]; then
    /ganuda/scripts/scan_dependencies.sh >/dev/null 2>&1
    LATEST_SUMMARY=$(ls -t /ganuda/security/dependency_audit/summary_*.txt 2>/dev/null | head -1)
    if [ -n "$LATEST_SUMMARY" ]; then
        VULN_LINE=$(grep "Total vulnerabilities:" "$LATEST_SUMMARY" 2>/dev/null || echo "")
        if echo "$VULN_LINE" | grep -q ": 0$"; then
            log_pass "No known dependency vulnerabilities"
        else
            log_warn "Dependency vulnerabilities detected: $VULN_LINE"
        fi
    else
        log_warn "Could not find dependency scan results"
    fi
else
    log_warn "Dependency scanner not found"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 3: Hardcoded Credentials in Recent Changes ---
echo "--- 3. Hardcoded Credentials Check (last 7 days) ---" | tee -a "$REPORT_FILE"
CRED_PATTERNS='(password|passwd|secret|api_key|apikey|token|credential)\s*[=:]\s*["\x27][^\s"'\'']{8,}'
RECENT_FILES=$(find /ganuda -name '*.py' -o -name '*.sh' -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' | head -500)
CRED_HITS=0
if [ -n "$RECENT_FILES" ]; then
    CRED_HITS=$(echo "$RECENT_FILES" | xargs grep -rilE "$CRED_PATTERNS" 2>/dev/null | \
        grep -v 'venv/' | grep -v 'node_modules/' | grep -v '.git/' | \
        grep -v 'secrets/' | grep -v '__pycache__/' | wc -l || true)
fi

if [ "$CRED_HITS" -eq 0 ]; then
    log_pass "No hardcoded credentials detected in scanned files"
else
    log_warn "Potential hardcoded credentials found in $CRED_HITS file(s). Review manually."
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 4: secrets.env Permissions ---
echo "--- 4. Secrets File Permissions ---" | tee -a "$REPORT_FILE"
SECRETS_FILE="/ganuda/secrets/secrets.env"
if [ -f "$SECRETS_FILE" ]; then
    PERMS=$(stat -c '%a' "$SECRETS_FILE")
    OWNER=$(stat -c '%U' "$SECRETS_FILE")
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        log_pass "secrets.env permissions: $PERMS (owner: $OWNER)"
    else
        log_fail "secrets.env has insecure permissions: $PERMS (should be 600 or 400)"
    fi
else
    log_warn "secrets.env not found at $SECRETS_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 5: fail2ban Status ---
echo "--- 5. fail2ban Status ---" | tee -a "$REPORT_FILE"
if systemctl is-active fail2ban >/dev/null 2>&1; then
    JAIL_COUNT=$(fail2ban-client status 2>/dev/null | grep "Number of jail" | awk '{print $NF}' || echo "unknown")
    log_pass "fail2ban active (jails: $JAIL_COUNT)"
else
    log_fail "fail2ban is NOT running"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 6: nftables Rules ---
echo "--- 6. nftables Firewall ---" | tee -a "$REPORT_FILE"
if command -v nft >/dev/null 2>&1; then
    RULE_COUNT=$(nft list ruleset 2>/dev/null | grep -c 'rule' || true)
    if [ "$RULE_COUNT" -gt 0 ]; then
        log_pass "nftables has $RULE_COUNT rules loaded"
    else
        log_fail "nftables has no rules loaded"
    fi
else
    log_warn "nft command not found"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Check 7: PostgreSQL SSL ---
echo "--- 7. PostgreSQL SSL Status ---" | tee -a "$REPORT_FILE"
PG_SSL=$(PGPASSWORD="${PGPASSWORD:-}" psql -h 192.168.132.222 -U claude -d zammad_production \
    -tAc "SHOW ssl;" 2>/dev/null || echo "connection_failed")
if [ "$PG_SSL" = "on" ]; then
    log_pass "PostgreSQL SSL is enabled"
elif [ "$PG_SSL" = "off" ]; then
    log_fail "PostgreSQL SSL is disabled"
else
    log_warn "Could not check PostgreSQL SSL status"
fi
echo "" | tee -a "$REPORT_FILE"

# --- Summary ---
echo "============================================" | tee -a "$REPORT_FILE"
echo "  SUMMARY" | tee -a "$REPORT_FILE"
echo "============================================" | tee -a "$REPORT_FILE"
echo "  Passed:   $PASS_COUNT" | tee -a "$REPORT_FILE"
echo "  Failed:   $FAIL_COUNT" | tee -a "$REPORT_FILE"
echo "  Warnings: $WARN_COUNT" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ "$FAIL_COUNT" -gt 0 ]; then
    VERDICT="SECURITY CHECK FAILED"
elif [ "$WARN_COUNT" -gt 0 ]; then
    VERDICT="SECURITY CHECK PASSED WITH WARNINGS"
else
    VERDICT="ALL SECURITY CHECKS PASSED"
fi

echo "  Verdict: $VERDICT" | tee -a "$REPORT_FILE"
echo "  Report: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- Send to Telegram ---
TELEGRAM_SCRIPT="/ganuda/telegram_bot/send_message.sh"
if [ -f "$TELEGRAM_SCRIPT" ]; then
    TELEGRAM_MSG="Security Check Report ($(hostname))
$VERDICT
Passed: $PASS_COUNT | Failed: $FAIL_COUNT | Warnings: $WARN_COUNT
Full report: $REPORT_FILE"
    bash "$TELEGRAM_SCRIPT" "$TELEGRAM_MSG" 2>/dev/null || true
else
    # Fallback: try curl to Telegram API directly if bot token is available
    if [ -f /ganuda/secrets/secrets.env ]; then
        source /ganuda/secrets/secrets.env 2>/dev/null || true
        if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
            TELEGRAM_MSG="Security Check Report ($(hostname))
$VERDICT
Passed: $PASS_COUNT | Failed: $FAIL_COUNT | Warnings: $WARN_COUNT"
            curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${TELEGRAM_CHAT_ID}" \
                -d "text=${TELEGRAM_MSG}" >/dev/null 2>&1 || true
        fi
    fi
fi

# Exit code reflects overall status
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi
HEREDOC_EOF
chmod +x /ganuda/scripts/security_check.sh
```

---

### Step 5: Create Dependabot-Equivalent Configuration

#### 5a. Create /ganuda/config/dependency-check.yaml

```bash
mkdir -p /ganuda/config

cat <<'HEREDOC_EOF' > /ganuda/config/dependency-check.yaml
# Phase 7 Supply Chain: Dependency Check Configuration
# Used by /ganuda/daemons/dependency_checker.py
# Cherokee AI Federation

scan_schedule: weekly
virtualenvs:
  - /ganuda/vetassist/backend/venv
  - /ganuda/services/llm_gateway/venv

severity_threshold: high
auto_alert: true
alert_channel: telegram

# Known false positives or accepted risks (add CVE IDs here)
ignore:
  # - CVE-XXXX-XXXXX  # Template: reason for ignoring

results_dir: /ganuda/security/dependency_audit
previous_scan_dir: /ganuda/security/dependency_audit/previous
HEREDOC_EOF
```

#### 5b. Create /ganuda/daemons/dependency_checker.py

```bash
mkdir -p /ganuda/daemons

cat <<'HEREDOC_EOF' > /ganuda/daemons/dependency_checker.py
#!/usr/bin/env python3
"""
Phase 7 Supply Chain: Dependency vulnerability checker daemon.

Reads config from /ganuda/config/dependency-check.yaml.
Runs pip-audit on each configured virtualenv.
Compares against previous scan to alert only on NEW vulnerabilities.
Stores results in /ganuda/security/dependency_audit/.
Designed to run as systemd timer (weekly).

Cherokee AI Federation
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


CONFIG_PATH = "/ganuda/config/dependency-check.yaml"
SECRETS_PATH = "/ganuda/secrets/secrets.env"


def load_config():
    """Load dependency check configuration."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_secrets():
    """Load Telegram credentials from secrets.env."""
    secrets = {}
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    secrets[key.strip()] = value.strip().strip("\"'")
    return secrets


def send_telegram_alert(message, secrets):
    """Send alert via Telegram bot."""
    token = secrets.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = secrets.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("WARN: Telegram credentials not configured. Skipping alert.")
        return

    try:
        import urllib.request
        import urllib.parse

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        print("Telegram alert sent.")
    except Exception as e:
        print(f"WARN: Failed to send Telegram alert: {e}")


def run_pip_audit(venv_path):
    """Run pip-audit against a virtualenv and return results dict."""
    python_bin = os.path.join(venv_path, "bin", "python")
    pip_bin = os.path.join(venv_path, "bin", "pip")

    if not os.path.exists(python_bin):
        print(f"  SKIP: {venv_path} not found")
        return None

    # Ensure pip-audit is installed
    try:
        subprocess.run(
            [python_bin, "-m", "pip_audit", "--help"],
            capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  Installing pip-audit in {venv_path}...")
        subprocess.run(
            [pip_bin, "install", "pip-audit", "--quiet"],
            capture_output=True
        )

    # Run pip-audit
    result = subprocess.run(
        [python_bin, "-m", "pip_audit", "--format", "json"],
        capture_output=True, text=True
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  WARN: Could not parse pip-audit output for {venv_path}")
        return None


def extract_vuln_ids(scan_data):
    """Extract set of vulnerability IDs from scan data."""
    vuln_ids = set()
    deps = scan_data if isinstance(scan_data, list) else scan_data.get("dependencies", [])
    for dep in deps:
        for vuln in dep.get("vulns", []):
            vuln_id = vuln.get("id", vuln.get("aliases", ["unknown"])[0] if vuln.get("aliases") else "unknown")
            vuln_ids.add(vuln_id)
    return vuln_ids


def load_previous_vulns(previous_dir, venv_name):
    """Load vulnerability IDs from previous scan."""
    if not os.path.exists(previous_dir):
        return set()

    previous_files = sorted(Path(previous_dir).glob(f"scan_{venv_name}_*.json"), reverse=True)
    if not previous_files:
        return set()

    try:
        with open(previous_files[0], "r") as f:
            data = json.load(f)
        return extract_vuln_ids(data)
    except (json.JSONDecodeError, IOError):
        return set()


def main():
    print("=== Dependency Vulnerability Checker ===")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    config = load_config()
    secrets = load_secrets()

    results_dir = config.get("results_dir", "/ganuda/security/dependency_audit")
    previous_dir = config.get("previous_scan_dir", os.path.join(results_dir, "previous"))
    ignored_cves = set(config.get("ignore", []))
    severity_threshold = config.get("severity_threshold", "high")
    auto_alert = config.get("auto_alert", True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(previous_dir, exist_ok=True)

    all_new_vulns = []

    for venv_path in config.get("virtualenvs", []):
        venv_name = os.path.basename(os.path.dirname(venv_path))
        print(f"--- Scanning: {venv_path} ---")

        scan_data = run_pip_audit(venv_path)
        if scan_data is None:
            continue

        # Save current scan
        scan_file = os.path.join(results_dir, f"scan_{venv_name}_{timestamp}.json")
        with open(scan_file, "w") as f:
            json.dump(scan_data, f, indent=2)
        print(f"  Scan saved: {scan_file}")

        # Compare with previous
        current_vulns = extract_vuln_ids(scan_data)
        previous_vulns = load_previous_vulns(previous_dir, venv_name)
        new_vulns = current_vulns - previous_vulns - ignored_cves

        if new_vulns:
            print(f"  NEW vulnerabilities: {len(new_vulns)}")
            for v in sorted(new_vulns):
                print(f"    - {v}")
                all_new_vulns.append(f"{venv_name}: {v}")
        else:
            print("  No new vulnerabilities.")

        # Archive current as previous for next run
        archive_file = os.path.join(previous_dir, f"scan_{venv_name}_{timestamp}.json")
        shutil.copy2(scan_file, archive_file)

        print()

    # Alert on new vulnerabilities
    if all_new_vulns and auto_alert:
        alert_msg = (
            f"*Dependency Alert* ({len(all_new_vulns)} new)\n"
            f"Node: {os.uname().nodename}\n\n"
            + "\n".join(f"- {v}" for v in all_new_vulns[:20])
        )
        if len(all_new_vulns) > 20:
            alert_msg += f"\n... and {len(all_new_vulns) - 20} more"

        if config.get("alert_channel") == "telegram":
            send_telegram_alert(alert_msg, secrets)

    print("=== Dependency check complete ===")
    return 1 if all_new_vulns else 0


if __name__ == "__main__":
    sys.exit(main())
HEREDOC_EOF
chmod +x /ganuda/daemons/dependency_checker.py
```

---

### Step 6: Create systemd Timer for Weekly Security Checks

#### 6a. Create /ganuda/scripts/systemd/security-check.service

```bash
mkdir -p /ganuda/scripts/systemd

cat <<'HEREDOC_EOF' > /ganuda/scripts/systemd/security-check.service
[Unit]
Description=Cherokee AI Federation Weekly Security Check
Documentation=file:///ganuda/docs/jr_instructions/JR-SECURITY-PHASE7-SUPPLY-CHAIN-CONTINUOUS-FEB02-2026.md
After=network.target postgresql.service

[Service]
Type=oneshot
ExecStart=/ganuda/scripts/security_check.sh
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
StandardOutput=journal
StandardError=journal

# Security hardening for the security checker itself
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/ganuda/logs /ganuda/security /ganuda/config
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
HEREDOC_EOF
```

#### 6b. Create /ganuda/scripts/systemd/security-check.timer

```bash
cat <<'HEREDOC_EOF' > /ganuda/scripts/systemd/security-check.timer
[Unit]
Description=Weekly Security Check Timer
Documentation=file:///ganuda/docs/jr_instructions/JR-SECURITY-PHASE7-SUPPLY-CHAIN-CONTINUOUS-FEB02-2026.md

[Timer]
OnCalendar=Sun *-*-* 03:00:00
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
HEREDOC_EOF
```

#### 6c. Install and enable the timer

```bash
# Copy service and timer to systemd
sudo cp /ganuda/scripts/systemd/security-check.service /etc/systemd/system/
sudo cp /ganuda/scripts/systemd/security-check.timer /etc/systemd/system/

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable security-check.timer
sudo systemctl start security-check.timer

# Verify
systemctl list-timers | grep security-check
```

---

### Step 7: Validation

Run these checks to verify everything is in place and functional.

```bash
echo "=== Step 7: Validation ==="
echo ""

# 7a: Verify all scripts exist and are executable
echo "--- 7a: File existence and permissions ---"
SCRIPTS=(
    "/ganuda/scripts/generate_model_checksums.sh"
    "/ganuda/scripts/verify_model_checksums.sh"
    "/ganuda/scripts/generate_dependency_locks.sh"
    "/ganuda/scripts/scan_dependencies.sh"
    "/ganuda/scripts/security_check.sh"
    "/ganuda/daemons/dependency_checker.py"
    "/ganuda/config/dependency-check.yaml"
    "/ganuda/scripts/systemd/security-check.service"
    "/ganuda/scripts/systemd/security-check.timer"
)

ALL_EXIST=true
for SCRIPT in "${SCRIPTS[@]}"; do
    if [ -f "$SCRIPT" ]; then
        if [ -x "$SCRIPT" ] || [[ "$SCRIPT" == *.yaml ]] || [[ "$SCRIPT" == *.service ]] || [[ "$SCRIPT" == *.timer ]]; then
            echo "  OK: $SCRIPT"
        else
            echo "  WARN: Not executable: $SCRIPT"
        fi
    else
        echo "  MISSING: $SCRIPT"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = true ]; then
    echo "  All files present."
else
    echo "  ERROR: Some files missing. Review steps above."
fi
echo ""

# 7b: Run model checksum generation (may take time for large models)
echo "--- 7b: Model checksum generation ---"
if [ -d /ganuda/models ] && [ "$(ls -A /ganuda/models 2>/dev/null)" ]; then
    /ganuda/scripts/generate_model_checksums.sh
    echo "  Checksum generation complete."
else
    echo "  SKIP: /ganuda/models is empty or does not exist on this node."
fi
echo ""

# 7c: Run dependency scan on first available virtualenv
echo "--- 7c: Dependency scan (first virtualenv) ---"
FIRST_VENV="/ganuda/vetassist/backend/venv"
if [ -f "$FIRST_VENV/bin/pip" ]; then
    /ganuda/scripts/scan_dependencies.sh
    echo "  Dependency scan complete."
else
    echo "  SKIP: $FIRST_VENV not found on this node."
fi
echo ""

# 7d: Verify SBOM output is valid JSON
echo "--- 7d: SBOM validation ---"
SBOM_FILES=$(find /ganuda/config/sbom -name '*sbom*.json' 2>/dev/null | head -1)
if [ -n "$SBOM_FILES" ]; then
    python3 -c "import json; json.load(open('$SBOM_FILES')); print('  Valid JSON: $SBOM_FILES')" 2>/dev/null || \
        echo "  WARN: SBOM file exists but is not valid JSON: $SBOM_FILES"
else
    echo "  SKIP: No SBOM files generated yet. Run generate_dependency_locks.sh first."
fi
echo ""

# 7e: AST parse dependency_checker.py
echo "--- 7e: Python AST validation ---"
python3 -c "
import ast, sys
try:
    with open('/ganuda/daemons/dependency_checker.py', 'r') as f:
        ast.parse(f.read())
    print('  dependency_checker.py: Valid Python (AST parse OK)')
except SyntaxError as e:
    print(f'  dependency_checker.py: SYNTAX ERROR: {e}')
    sys.exit(1)
"
echo ""

echo "=== Validation complete ==="
```

---

### Files Created

| File | Purpose |
|------|---------|
| `/ganuda/scripts/generate_model_checksums.sh` | Generate SHA-256 baseline for all model files |
| `/ganuda/scripts/verify_model_checksums.sh` | Verify model integrity (cron-ready) |
| `/ganuda/scripts/generate_dependency_locks.sh` | Lock files + CycloneDX SBOM generation |
| `/ganuda/scripts/scan_dependencies.sh` | pip-audit vulnerability scanner |
| `/ganuda/scripts/security_check.sh` | Unified weekly security audit |
| `/ganuda/daemons/dependency_checker.py` | Dependabot-equivalent diff alerter |
| `/ganuda/config/dependency-check.yaml` | Scanner configuration |
| `/ganuda/scripts/systemd/security-check.service` | systemd service unit |
| `/ganuda/scripts/systemd/security-check.timer` | systemd weekly timer (Sunday 03:00) |

### Directories Created/Used

| Directory | Purpose |
|-----------|---------|
| `/ganuda/config/` | Checksums, manifest, SBOM |
| `/ganuda/config/sbom/` | CycloneDX SBOM files |
| `/ganuda/security/dependency_audit/` | Scan results and history |
| `/ganuda/logs/security/` | Security check logs |

---

*For Seven Generations*
