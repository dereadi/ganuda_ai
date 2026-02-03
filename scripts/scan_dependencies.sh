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
