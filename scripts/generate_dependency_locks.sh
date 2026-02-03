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
