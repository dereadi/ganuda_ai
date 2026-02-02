# JR-SECURITY-PHASE1-CREDENTIAL-ROTATION-FEB02-2026

## Metadata
- **Task ID**: SECURITY-PHASE1-CRED-ROTATION
- **Priority**: P0 (CRITICAL)
- **Assigned To**: DevOps Jr
- **Created**: 2026-02-02
- **Created By**: TPM (Claude Opus 4.5)
- **Estimated Steps**: 6
- **Dependencies**: None
- **Blocks**: SECURITY-PHASE2 (file-by-file migration), SECURITY-PHASE3 (password rotation)

## Problem Statement

The Cherokee AI Federation has the database password `jawaseatlasers2` hardcoded across approximately 1,874 files. The Telegram bot token and LLM Gateway API key are similarly hardcoded in numerous locations. This represents a CRITICAL security vulnerability:

- Any file leak exposes production database credentials
- Credential rotation is currently impossible without touching every file
- No pre-commit guardrails prevent new hardcoded secrets from being committed
- The FreeIPA vault on silverfin exists and a retrieval script lives at `/ganuda/scripts/get-vault-secret.sh`, but nothing uses it

This instruction creates the **infrastructure** for credential migration. It does NOT modify existing files. The actual file-by-file migration will be handled by a series of follow-up instructions.

## CRITICAL EXECUTOR RULES

- NO SEARCH/REPLACE blocks -- the executor cannot process them
- ALL steps use ```bash code blocks only
- Validate current DB access with PGPASSWORD=jawaseatlasers2
- This instruction handles PHASE 1 ONLY: centralized config + pre-commit hook
- Actual password rotation requires admin (human) action

---

## Step 1: Create centralized secrets configuration file

Create `/ganuda/config/secrets.env` with all federation secrets in one place. This file must NEVER be committed to git.

```bash
mkdir -p /ganuda/config

cat > /ganuda/config/secrets.env << 'SECRETS_EOF'
# Cherokee AI Federation - Centralized Secrets Configuration
# Created: 2026-02-02
# WARNING: This file contains production credentials.
# NEVER commit this file to git. It is excluded via .gitignore.
# Permissions MUST remain 600 (owner read/write only).

# ============================================================
# PostgreSQL - Cherokee Main Database (zammad_production)
# ============================================================
CHEROKEE_DB_HOST=192.168.132.222
CHEROKEE_DB_NAME=zammad_production
CHEROKEE_DB_USER=claude
CHEROKEE_DB_PASS=jawaseatlasers2
CHEROKEE_DB_PORT=5432

# ============================================================
# PostgreSQL - VetAssist PII Database
# ============================================================
VETASSIST_DB_HOST=192.168.132.222
VETASSIST_DB_NAME=vetassist_pii
VETASSIST_DB_USER=vetassist_user
VETASSIST_DB_PASS=<TO_BE_SET>
VETASSIST_DB_PORT=5432

# ============================================================
# Telegram Bot
# ============================================================
TELEGRAM_BOT_TOKEN=<TO_BE_SET>

# ============================================================
# LLM Gateway
# ============================================================
LLM_GATEWAY_API_KEY=<TO_BE_SET>
LLM_GATEWAY_URL=http://192.168.132.223:8080
SECRETS_EOF

chmod 600 /ganuda/config/secrets.env

echo "VERIFY: secrets.env created with correct permissions:"
ls -la /ganuda/config/secrets.env
stat -c "%a %U %G" /ganuda/config/secrets.env
```

---

## Step 2: Create Python secrets loader module

Create `/ganuda/lib/secrets_loader.py` -- a thread-safe module that loads secrets with a three-tier fallback: secrets.env file, environment variables, then FreeIPA vault.

```bash
cat > /ganuda/lib/secrets_loader.py << 'LOADER_EOF'
"""
Cherokee AI Federation - Centralized Secrets Loader
====================================================
Created: 2026-02-02
Task: SECURITY-PHASE1-CRED-ROTATION

Three-tier secret resolution:
  1. /ganuda/config/secrets.env (file-based, preferred)
  2. Environment variables (for containerized deployments)
  3. FreeIPA vault via /ganuda/scripts/get-vault-secret.sh (last resort)

Usage:
    from lib.secrets_loader import get_db_config, get_telegram_token, get_llm_api_key

    db = get_db_config()          # Returns dict with host, dbname, user, password, port
    token = get_telegram_token()  # Returns string
    key = get_llm_api_key()       # Returns string

Thread Safety:
    All file reads are protected by threading.Lock. Safe for multi-threaded services.

IMPORTANT: This module NEVER hardcodes passwords. If all three tiers fail,
it raises RuntimeError rather than falling back to a default.
"""

import os
import logging
import subprocess
import threading

logger = logging.getLogger(__name__)

_SECRETS_FILE = "/ganuda/config/secrets.env"
_VAULT_SCRIPT = "/ganuda/scripts/get-vault-secret.sh"

_lock = threading.Lock()
_cache = {}
_cache_loaded = False


def _load_secrets_file():
    """Load secrets from the .env file into the cache. Thread-safe."""
    global _cache, _cache_loaded
    with _lock:
        if _cache_loaded:
            return
        if not os.path.exists(_SECRETS_FILE):
            logger.warning(
                "secrets_loader: %s not found, will use env/vault fallback",
                _SECRETS_FILE,
            )
            _cache_loaded = True
            return
        try:
            with open(_SECRETS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if value and value != "<TO_BE_SET>":
                        _cache[key] = value
            logger.info(
                "secrets_loader: loaded %d secrets from %s",
                len(_cache),
                _SECRETS_FILE,
            )
        except (IOError, OSError) as exc:
            logger.warning(
                "secrets_loader: failed to read %s: %s", _SECRETS_FILE, exc
            )
        _cache_loaded = True


def _get_from_vault(secret_name):
    """Attempt to retrieve a secret from FreeIPA vault via shell script."""
    if not os.path.exists(_VAULT_SCRIPT):
        logger.warning(
            "secrets_loader: vault script %s not found", _VAULT_SCRIPT
        )
        return None
    try:
        result = subprocess.run(
            [_VAULT_SCRIPT, secret_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(
                "secrets_loader: retrieved '%s' from vault", secret_name
            )
            return result.stdout.strip()
        else:
            logger.warning(
                "secrets_loader: vault returned rc=%d for '%s'",
                result.returncode,
                secret_name,
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning(
            "secrets_loader: vault call failed for '%s': %s",
            secret_name,
            exc,
        )
    return None


def get_secret(key):
    """
    Resolve a single secret through the three-tier fallback chain.

    Args:
        key: The secret name (e.g., 'CHEROKEE_DB_PASS')

    Returns:
        The secret value as a string.

    Raises:
        RuntimeError: If the secret cannot be resolved from any tier.
    """
    _load_secrets_file()

    # Tier 1: secrets.env file
    value = _cache.get(key)
    if value:
        return value

    # Tier 2: environment variable
    value = os.environ.get(key)
    if value:
        logger.warning(
            "secrets_loader: '%s' resolved from environment variable (tier 2)",
            key,
        )
        return value

    # Tier 3: FreeIPA vault
    value = _get_from_vault(key)
    if value:
        logger.warning(
            "secrets_loader: '%s' resolved from vault (tier 3)", key
        )
        return value

    raise RuntimeError(
        f"secrets_loader: unable to resolve secret '{key}' from any source. "
        f"Check {_SECRETS_FILE}, environment variables, or vault configuration."
    )


def get_db_config(prefix="CHEROKEE"):
    """
    Return a database configuration dictionary.

    Args:
        prefix: 'CHEROKEE' or 'VETASSIST' to select which database.

    Returns:
        dict with keys: host, dbname, user, password, port
    """
    return {
        "host": get_secret(f"{prefix}_DB_HOST"),
        "dbname": get_secret(f"{prefix}_DB_NAME"),
        "user": get_secret(f"{prefix}_DB_USER"),
        "password": get_secret(f"{prefix}_DB_PASS"),
        "port": int(get_secret(f"{prefix}_DB_PORT")),
    }


def get_telegram_token():
    """Return the Telegram bot token."""
    return get_secret("TELEGRAM_BOT_TOKEN")


def get_llm_api_key():
    """Return the LLM Gateway API key."""
    return get_secret("LLM_GATEWAY_API_KEY")


def get_llm_gateway_url():
    """Return the LLM Gateway base URL."""
    return get_secret("LLM_GATEWAY_URL")


def reload_secrets():
    """
    Force a reload of the secrets file on next access.
    Useful after secrets.env has been updated.
    """
    global _cache, _cache_loaded
    with _lock:
        _cache = {}
        _cache_loaded = False
    logger.info("secrets_loader: cache cleared, will reload on next access")
LOADER_EOF

chmod 644 /ganuda/lib/secrets_loader.py

echo "VERIFY: secrets_loader.py created:"
ls -la /ganuda/lib/secrets_loader.py
python3 -c "import sys; sys.path.insert(0, '/ganuda'); from lib.secrets_loader import get_db_config; print('Import OK')"
```

---

## Step 3: Add .gitignore entries for secrets

Append secret-related patterns to `/ganuda/.gitignore` to prevent accidental commits.

```bash
cat >> /ganuda/.gitignore << 'GITIGNORE_EOF'

# ============================================================
# Secrets - NEVER commit (added 2026-02-02 SECURITY-PHASE1)
# ============================================================
config/secrets.env
config/*.env
*.pem
*.key
secrets/
GITIGNORE_EOF

echo "VERIFY: .gitignore now contains secrets entries:"
grep -n "secrets" /ganuda/.gitignore
grep -n "\.pem" /ganuda/.gitignore
grep -n "\.key" /ganuda/.gitignore
```

---

## Step 4: Install gitleaks pre-commit hook

### Step 4a: Create gitleaks configuration

```bash
cat > /ganuda/.gitleaks.toml << 'GITLEAKS_EOF'
# Gitleaks configuration for Cherokee AI Federation
# Created: 2026-02-02 SECURITY-PHASE1
# Detects hardcoded credentials before they reach the repository.

title = "Cherokee Federation Secret Detection"

[extend]
# Start from default gitleaks rules, then add federation-specific ones

[[rules]]
id = "cherokee-db-password"
description = "Hardcoded database password detected"
regex = '''(?i)(password|passwd|pwd|db_pass)\s*[=:]\s*['"]?[a-zA-Z0-9!@#$%^&*]{8,}['"]?'''
tags = ["password", "database"]

[[rules]]
id = "jawaseatlasers-literal"
description = "Known legacy password 'jawaseatlasers2' detected"
regex = '''jawaseatlasers2'''
tags = ["password", "critical", "legacy"]

[[rules]]
id = "api-key-pattern"
description = "API key pattern detected"
regex = '''(?i)(api[_-]?key|apikey)\s*[=:]\s*['"]?[a-zA-Z0-9_\-]{20,}['"]?'''
tags = ["api-key"]

[[rules]]
id = "bearer-token"
description = "Bearer token detected"
regex = '''(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'''
tags = ["token", "bearer"]

[[rules]]
id = "telegram-bot-token"
description = "Telegram bot token detected"
regex = '''[0-9]{8,10}:[a-zA-Z0-9_-]{35}'''
tags = ["token", "telegram"]

[[rules]]
id = "private-key-header"
description = "Private key file content detected"
regex = '''-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'''
tags = ["private-key"]

[[rules]]
id = "generic-secret-assignment"
description = "Generic secret assignment detected"
regex = '''(?i)(secret|token|credential)\s*[=:]\s*['"]?[a-zA-Z0-9!@#$%^&*_\-]{12,}['"]?'''
tags = ["secret", "generic"]

[allowlist]
description = "Global allowlist"
paths = [
    '''\.gitleaks\.toml$''',
    '''\.gitignore$''',
    '''docs/jr_instructions/.*\.md$''',
    '''docs/kb/.*\.md$''',
]
GITLEAKS_EOF

echo "VERIFY: .gitleaks.toml created:"
ls -la /ganuda/.gitleaks.toml
```

### Step 4b: Create pre-commit hook script

```bash
cat > /ganuda/scripts/pre-commit-gitleaks.sh << 'HOOKSCRIPT_EOF'
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
HOOKSCRIPT_EOF

chmod +x /ganuda/scripts/pre-commit-gitleaks.sh

echo "VERIFY: pre-commit-gitleaks.sh created and executable:"
ls -la /ganuda/scripts/pre-commit-gitleaks.sh
```

### Step 4c: Install the hook into the git repository

```bash
cp /ganuda/scripts/pre-commit-gitleaks.sh /ganuda/.git/hooks/pre-commit
chmod +x /ganuda/.git/hooks/pre-commit

echo "VERIFY: pre-commit hook installed:"
ls -la /ganuda/.git/hooks/pre-commit
```

---

## Step 5: Validation

Run all verification checks to confirm the infrastructure is in place.

```bash
echo "=============================="
echo "SECURITY PHASE 1 VALIDATION"
echo "=============================="
echo ""

PASS=0
FAIL=0

# Check 1: secrets.env exists with 600 permissions
echo -n "[1/5] secrets.env exists with 600 permissions... "
if [ -f /ganuda/config/secrets.env ]; then
    PERMS=$(stat -c "%a" /ganuda/config/secrets.env)
    if [ "${PERMS}" = "600" ]; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (permissions are ${PERMS}, expected 600)"
        FAIL=$((FAIL + 1))
    fi
else
    echo "FAIL (file not found)"
    FAIL=$((FAIL + 1))
fi

# Check 2: secrets_loader.py imports cleanly
echo -n "[2/5] secrets_loader.py imports and returns config... "
IMPORT_RESULT=$(python3 -c "
import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
config = get_db_config('CHEROKEE')
assert config['host'] == '192.168.132.222', f'Bad host: {config[\"host\"]}'
assert config['dbname'] == 'zammad_production', f'Bad dbname: {config[\"dbname\"]}'
assert config['user'] == 'claude', f'Bad user: {config[\"user\"]}'
assert config['password'] == 'jawaseatlasers2', f'Bad password'
assert config['port'] == 5432, f'Bad port: {config[\"port\"]}'
print('OK')
" 2>&1)
if [ "${IMPORT_RESULT}" = "OK" ]; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (${IMPORT_RESULT})"
    FAIL=$((FAIL + 1))
fi

# Check 3: .gitignore has secrets entries
echo -n "[3/5] .gitignore contains secrets entries... "
if grep -q "secrets.env" /ganuda/.gitignore && grep -q "\.pem" /ganuda/.gitignore; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

# Check 4: .gitleaks.toml is valid TOML
echo -n "[4/5] .gitleaks.toml exists and is parseable... "
if [ -f /ganuda/.gitleaks.toml ]; then
    TOML_CHECK=$(python3 -c "
import sys
if sys.version_info >= (3, 11):
    import tomllib
    with open('/ganuda/.gitleaks.toml', 'rb') as f:
        data = tomllib.load(f)
    print('OK')
else:
    # Fallback: just check file exists and has content
    with open('/ganuda/.gitleaks.toml') as f:
        content = f.read()
    if 'rules' in content and 'jawaseatlasers' in content:
        print('OK')
    else:
        print('MISSING_CONTENT')
" 2>&1)
    if [ "${TOML_CHECK}" = "OK" ]; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (${TOML_CHECK})"
        FAIL=$((FAIL + 1))
    fi
else
    echo "FAIL (file not found)"
    FAIL=$((FAIL + 1))
fi

# Check 5: Pre-commit hook is installed and executable
echo -n "[5/5] Pre-commit hook installed and executable... "
if [ -x /ganuda/.git/hooks/pre-commit ]; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=============================="
echo "RESULTS: ${PASS} passed, ${FAIL} failed out of 5 checks"
echo "=============================="

if [ "${FAIL}" -gt 0 ]; then
    echo "STATUS: INCOMPLETE - Fix failures above"
    exit 1
else
    echo "STATUS: PHASE 1 COMPLETE"
    exit 0
fi
```

---

## Step 6: Create migration guide

Create the knowledge base article that explains how downstream files should be updated to use the new secrets loader.

```bash
cat > /ganuda/docs/kb/KB-CREDENTIAL-MIGRATION-GUIDE-FEB02-2026.md << 'KBEOF'
# KB: Credential Migration Guide

## Created: 2026-02-02
## Related Task: SECURITY-PHASE1-CRED-ROTATION
## Status: Active

---

## Overview

The Cherokee AI Federation is migrating away from hardcoded database credentials.
This guide explains how to update existing files to use the centralized secrets loader.

## The Problem

The password `jawaseatlasers2` appears in approximately 1,874 files across the federation codebase.
The Telegram bot token and LLM Gateway API key are similarly hardcoded.

## The Solution

A centralized secrets loader at `/ganuda/lib/secrets_loader.py` provides a three-tier
secret resolution chain:

1. **File-based** (`/ganuda/config/secrets.env`) -- primary, used in production
2. **Environment variables** -- for containerized deployments
3. **FreeIPA vault** (`/ganuda/scripts/get-vault-secret.sh`) -- last resort

## How to Migrate a File

### Database Connections (Most Common)

**Before (hardcoded):**
```python
import psycopg2

conn = psycopg2.connect(
    host='192.168.132.222',
    dbname='zammad_production',
    user='claude',
    password='jawaseatlasers2',
    port=5432
)
```

**After (using secrets loader):**
```python
import psycopg2
from lib.secrets_loader import get_db_config

conn = psycopg2.connect(**get_db_config("CHEROKEE"))
```

### VetAssist Database

```python
from lib.secrets_loader import get_db_config

conn = psycopg2.connect(**get_db_config("VETASSIST"))
```

### Telegram Bot Token

**Before:**
```python
bot = Bot(token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz_123456")
```

**After:**
```python
from lib.secrets_loader import get_telegram_token

bot = Bot(token=get_telegram_token())
```

### LLM Gateway API Key

**Before:**
```python
headers = {"Authorization": "Bearer ck-hardcoded-key-here"}
```

**After:**
```python
from lib.secrets_loader import get_llm_api_key, get_llm_gateway_url

headers = {"Authorization": f"Bearer {get_llm_api_key()}"}
url = get_llm_gateway_url()
```

## Migration Priority Order

Files should be migrated in this order based on risk and impact:

### Priority 1: Active Services (restart required)
These run continuously and are the highest exposure risk:
- `telegram_bot/telegram_chief.py`
- `jr_executor/jr_queue_worker.py`
- `jr_executor/task_executor.py`
- `jr_executor/research_task_executor.py`
- Service daemons under `daemons/`

### Priority 2: Core Libraries
Shared code used by multiple services:
- `lib/jr_llm_reasoner.py`
- `lib/rlm_executor.py`
- `lib/research_client.py`
- `lib/specialist_council.py`
- `lib/hive_mind.py`

### Priority 3: API and Web Services
- `app/` (VetAssist backend endpoints)
- `sag/` (SAG web application)

### Priority 4: Scripts and Utilities
- `scripts/` (operational scripts)
- `jr_executor/jr_cli.py`

### Priority 5: Tests and One-off Files
- Test scripts
- Analysis scripts
- Archive files

## Password Rotation Procedure

Once all active files have been migrated to use secrets_loader, the password can
be rotated:

1. **Generate new password** on the admin workstation
2. **Update PostgreSQL** on 192.168.132.222:
   ```sql
   ALTER USER claude WITH PASSWORD 'new-secure-password-here';
   ALTER USER vetassist_user WITH PASSWORD 'new-vetassist-password-here';
   ```
3. **Update secrets.env** on each federation node:
   ```
   CHEROKEE_DB_PASS=new-secure-password-here
   VETASSIST_DB_PASS=new-vetassist-password-here
   ```
4. **Restart all services** that use the database
5. **Verify connectivity** from each node
6. **Update FreeIPA vault** on silverfin with the new credentials

IMPORTANT: Steps 2-6 must be coordinated and executed within a short maintenance
window. Any file still using the hardcoded password will break after rotation.

## Pre-Commit Hook

A gitleaks-based pre-commit hook now blocks commits that contain hardcoded secrets.
If your commit is blocked:

- Replace the hardcoded credential with a secrets_loader call (see examples above)
- If this is a documentation or instruction file that mentions passwords by name,
  it is allowlisted automatically (docs/jr_instructions/ and docs/kb/ paths)
- Emergency bypass (use sparingly): `git commit --no-verify`

## Verifying Your Migration

After updating a file, verify it works:

```bash
cd /ganuda
python3 -c "
from lib.secrets_loader import get_db_config
import psycopg2
conn = psycopg2.connect(**get_db_config('CHEROKEE'))
cur = conn.cursor()
cur.execute('SELECT 1')
print('Connection OK:', cur.fetchone())
conn.close()
"
```

## Questions

Contact the TPM or DevOps Jr for migration questions. File issues in the kanban
under the SECURITY-PHASE1 tag.
KBEOF

echo "VERIFY: migration guide created:"
ls -la /ganuda/docs/kb/KB-CREDENTIAL-MIGRATION-GUIDE-FEB02-2026.md
wc -l /ganuda/docs/kb/KB-CREDENTIAL-MIGRATION-GUIDE-FEB02-2026.md
```

---

## Scope Boundary

This instruction is COMPLETE after the six steps above. The following are explicitly OUT OF SCOPE and will be handled by follow-up instructions:

- **SECURITY-PHASE2**: File-by-file migration of active services to use secrets_loader (multiple instructions, one per priority tier)
- **SECURITY-PHASE3**: Actual password rotation on PostgreSQL (requires human admin action and a maintenance window)
- **SECURITY-PHASE4**: FreeIPA vault integration and secrets.env elimination (long-term goal)

## Rollback

If any step fails or causes issues:

1. The secrets_loader uses a fallback chain, so existing hardcoded passwords continue to work
2. Remove the pre-commit hook: `rm /ganuda/.git/hooks/pre-commit`
3. The secrets.env file and secrets_loader.py are additive -- they do not modify any existing files

No existing functionality is changed by this instruction.
