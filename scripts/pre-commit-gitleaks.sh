#!/usr/bin/env bash
# Cherokee AI Federation - Pre-commit Secret Detection Hook
# Created: 2026-02-02 SECURITY-PHASE1
#
# This hook scans staged files for hardcoded secrets before allowing a commit.
# It uses gitleaks if installed, otherwise falls back to basic regex checks.

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

REPO_ROOT="$(git rev-parse --show-toplevel)"
GITLEAKS_CONFIG="${REPO_ROOT}/.gitleaks.toml"

echo -e "${YELLOW}[SECRET SCAN] Checking staged files for hardcoded credentials...${NC}"

# Try gitleaks first
if command -v gitleaks &> /dev/null; then
    if ! gitleaks protect --staged --config="${GITLEAKS_CONFIG}" --verbose 2>&1; then
        echo ""
        echo -e "${RED}============================================================${NC}"
        echo -e "${RED}  COMMIT BLOCKED: Hardcoded secrets detected in staged files${NC}"
        echo -e "${RED}============================================================${NC}"
        echo ""
        echo -e "  Use ${YELLOW}from lib.secrets_loader import get_db_config${NC}"
        echo -e "  instead of hardcoding passwords."
        echo ""
        echo -e "  See: ${YELLOW}/ganuda/docs/kb/KB-CREDENTIAL-MIGRATION-GUIDE-FEB02-2026.md${NC}"
        echo ""
        echo -e "  To bypass (emergency only): ${YELLOW}git commit --no-verify${NC}"
        echo ""
        exit 1
    fi
else
    # Fallback: basic regex scan on staged files
    echo -e "${YELLOW}[SECRET SCAN] gitleaks not found, using basic regex scan...${NC}"

    STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
    if [ -z "${STAGED_FILES}" ]; then
        echo -e "${GREEN}[SECRET SCAN] No staged files to check.${NC}"
        exit 0
    fi

    FOUND_SECRETS=0

    while IFS= read -r file; do
        # Skip binary files, images, and allowlisted paths
        case "${file}" in
            *.png|*.jpg|*.jpeg|*.gif|*.ico|*.woff|*.ttf|*.pyc|*.so)
                continue
                ;;
            .gitleaks.toml|.gitignore|docs/jr_instructions/*|docs/kb/*)
                continue
                ;;
        esac

        # Check staged content (not working tree)
        CONTENT=$(git show ":${file}" 2>/dev/null || true)
        if [ -z "${CONTENT}" ]; then
            continue
        fi

        # Check for the known legacy password
        if echo "${CONTENT}" | grep -q "jawaseatlasers2"; then
            echo -e "${RED}  FOUND: Legacy password in ${file}${NC}"
            FOUND_SECRETS=1
        fi

        # Check for password assignments (not comments or docs)
        if echo "${CONTENT}" | grep -Pq "(?i)(password|passwd|db_pass)\s*[=:]\s*['\"][a-zA-Z0-9!@#\$%^&*]{8,}['\"]"; then
            echo -e "${RED}  FOUND: Hardcoded password in ${file}${NC}"
            FOUND_SECRETS=1
        fi

        # Check for private keys
        if echo "${CONTENT}" | grep -q "BEGIN.*PRIVATE KEY"; then
            echo -e "${RED}  FOUND: Private key in ${file}${NC}"
            FOUND_SECRETS=1
        fi

        # Check for Telegram bot tokens
        if echo "${CONTENT}" | grep -Pq "[0-9]{8,10}:[a-zA-Z0-9_-]{35}"; then
            echo -e "${RED}  FOUND: Telegram bot token in ${file}${NC}"
            FOUND_SECRETS=1
        fi

    done <<< "${STAGED_FILES}"

    if [ "${FOUND_SECRETS}" -eq 1 ]; then
        echo ""
        echo -e "${RED}============================================================${NC}"
        echo -e "${RED}  COMMIT BLOCKED: Hardcoded secrets detected in staged files${NC}"
        echo -e "${RED}============================================================${NC}"
        echo ""
        echo -e "  Use ${YELLOW}from lib.secrets_loader import get_db_config${NC}"
        echo -e "  instead of hardcoding passwords."
        echo ""
        echo -e "  See: ${YELLOW}/ganuda/docs/kb/KB-CREDENTIAL-MIGRATION-GUIDE-FEB02-2026.md${NC}"
        echo ""
        echo -e "  To bypass (emergency only): ${YELLOW}git commit --no-verify${NC}"
        echo ""
        exit 1
    fi
fi

echo -e "${GREEN}[SECRET SCAN] No hardcoded secrets detected. Commit allowed.${NC}"
exit 0
