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
