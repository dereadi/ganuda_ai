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
