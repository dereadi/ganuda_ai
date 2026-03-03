# JR Instruction: VetAssist Frontend Deploy Script

**Task ID**: VETASSIST-DEPLOY-SCRIPT
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

Next.js with `output: 'standalone'` does NOT copy `.next/static` or `public` into the standalone directory. Every `npm run build` produces a standalone server that cannot serve its own CSS, JS, or fonts. This caused a production outage on March 2, 2026 — the page rendered with no styling.

We need a deploy script that automates the full build-copy-restart cycle so the static asset step can never be skipped.

## Step 1: Create the deploy script

Create `/ganuda/vetassist/frontend/deploy.sh`

```python
#!/bin/bash
# VetAssist Frontend Deploy Script
# Automates: build → copy static assets → restart service
#
# Why this exists: Next.js standalone mode does NOT include .next/static
# or public/ in the standalone output. Without this copy step, the
# frontend serves HTML that references CSS/JS hashes it can't find.
# Incident: 2026-03-02 — garbled page, no styling.
#
# Usage: ./deploy.sh
# Requires: FreeIPA sudo (systemctl restart vetassist-frontend)

set -euo pipefail

FRONTEND_DIR="/ganuda/vetassist/frontend"
STANDALONE_DIR="${FRONTEND_DIR}/.next/standalone"

echo "=== VetAssist Frontend Deploy ==="
echo "Started: $(date)"

# Step 1: Build
echo "[1/4] Building Next.js..."
cd "$FRONTEND_DIR"
npm run build

# Step 2: Verify standalone output exists
if [ ! -f "${STANDALONE_DIR}/server.js" ]; then
    echo "ERROR: standalone/server.js not found. Build may have failed."
    exit 1
fi

# Step 3: Copy static assets (THE CRITICAL STEP)
echo "[2/4] Copying .next/static into standalone..."
rm -rf "${STANDALONE_DIR}/.next/static"
cp -r "${FRONTEND_DIR}/.next/static" "${STANDALONE_DIR}/.next/static"

if [ -d "${FRONTEND_DIR}/public" ]; then
    echo "[3/4] Copying public/ into standalone..."
    rm -rf "${STANDALONE_DIR}/public"
    cp -r "${FRONTEND_DIR}/public" "${STANDALONE_DIR}/public"
else
    echo "[3/4] No public/ directory — skipping"
fi

# Step 4: Restart service
echo "[4/4] Restarting vetassist-frontend..."
sudo systemctl restart vetassist-frontend

# Verify
sleep 2
CSS_FILE=$(find "${STANDALONE_DIR}/.next/static/css" -name "*.css" -print -quit 2>/dev/null)
if [ -n "$CSS_FILE" ]; then
    CSS_BASENAME=$(basename "$CSS_FILE")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/_next/static/css/${CSS_BASENAME}")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "VERIFIED: CSS serving correctly (HTTP ${HTTP_CODE})"
    else
        echo "WARNING: CSS returned HTTP ${HTTP_CODE} — check service logs"
    fi
else
    echo "WARNING: No CSS files found in standalone static dir"
fi

echo "=== Deploy complete: $(date) ==="
```

## Verification

1. `chmod +x /ganuda/vetassist/frontend/deploy.sh`
2. Run `./deploy.sh` — should complete all 4 steps and print "VERIFIED: CSS serving correctly"
3. Visit `https://vetassist.ganuda.us/` — should render with full styling

## Files Created

- `/ganuda/vetassist/frontend/deploy.sh`
