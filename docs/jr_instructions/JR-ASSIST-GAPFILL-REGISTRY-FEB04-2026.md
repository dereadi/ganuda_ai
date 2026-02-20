# JR INSTRUCTION: Assist Platform Registry & Generator Gap-Fill

**Task ID:** ASSIST-GAPFILL-REGISTRY
**Priority:** P2 -- Operational tooling (verticals can run without this, but scaling requires it)
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5)
**Date:** 2026-02-04
**Estimated Effort:** 1-2 hours
**Node:** Any (bash 4+ required -- NOT dash/sh)
**Type:** GAP-FILL -- Phase 4 had 0% completion
**Depends On:** ASSIST-GAPFILL-CORE-BACKEND, ASSIST-GAPFILL-SSIDASSIST, ASSIST-GAPFILL-TRIBEASSIST
**Seven Gen Impact:** Every new vertical we add serves a different population left behind by complexity. The generator script means a Jr can scaffold a new vertical in minutes instead of hours. The registry means we know what we have, what works, and what needs attention. Infrastructure that scales is infrastructure that lasts.

---

## Mission Context

Phase 4 (Registry & Generator) had zero percent completion during the initial scaffold execution. None of the three planned files were created: the verticals registry YAML, the new-vertical generator script, and the validation script.

These files provide the operational backbone for the Assist Platform:
- **verticals.yaml**: Single source of truth for all deployed verticals (ports, paths, status)
- **new_vertical.sh**: Generator script that scaffolds a new vertical from template in one command
- **validate_vertical.sh**: Pre-launch validation that catches missing files, broken YAML, and syntax errors before deployment

Without these, every new vertical must be created manually and validated by hand.

**This is a GAP-FILL instruction.** All three files are new. There are no existing files to protect.

---

## Existing Files (DO NOT TOUCH)

Phase 4 had no prior execution. However, the following directories and files from other phases MUST NOT be modified:

| Path | Status |
|---|---|
| `/ganuda/assist/core/` | MANAGED BY ASSIST-GAPFILL-CORE-BACKEND -- do not touch |
| `/ganuda/assist/ssidassist/` | MANAGED BY ASSIST-GAPFILL-SSIDASSIST -- do not touch |
| `/ganuda/assist/tribeassist/` | MANAGED BY ASSIST-GAPFILL-TRIBEASSIST -- do not touch |
| `/ganuda/vetassist/` | PRODUCTION -- do not touch |

---

## Objective

Create 3 files:
1. `/ganuda/assist/verticals.yaml` -- Registry of all Assist verticals
2. `/ganuda/assist/scripts/new_vertical.sh` -- Generator script for new verticals
3. `/ganuda/assist/scripts/validate_vertical.sh` -- Pre-launch validation script

Also ensure the `/ganuda/assist/scripts/` directory exists and scripts are executable.

---

## Prerequisites

- Confirm `/ganuda/assist/` directory exists
- Confirm bash 4+ is available (`bash --version`)
- IMPORTANT: Scripts must use `#!/bin/bash` -- NOT `#!/bin/sh`. Dash does not support `pipefail` or bash arrays, which both scripts require.

---

## Steps

### Step 0: Pre-Flight

```bash
#!/bin/bash
echo "=== Pre-Flight: Verifying Assist directory structure ==="

# Check base directory
if [ -d "/ganuda/assist" ]; then
    echo "[OK] /ganuda/assist exists"
else
    echo "[FAIL] /ganuda/assist does not exist -- something is very wrong"
    exit 1
fi

# Check bash version (need 4+ for arrays and pipefail)
BASH_VER=$(bash --version | head -1)
echo "[INFO] Bash version: $BASH_VER"

# Create scripts directory
mkdir -p /ganuda/assist/scripts
echo "[OK] /ganuda/assist/scripts/ directory ready"

# Check that verticals exist for registry
for v in core ssidassist tribeassist; do
    if [ -d "/ganuda/assist/$v" ]; then
        echo "[OK] /ganuda/assist/$v exists"
    else
        echo "[WARN] /ganuda/assist/$v does not exist yet"
    fi
done

if [ -d "/ganuda/vetassist" ]; then
    echo "[OK] /ganuda/vetassist exists (production)"
else
    echo "[WARN] /ganuda/vetassist does not exist"
fi
```

---

### Step 1: Create `/ganuda/assist/verticals.yaml`

Registry of all Assist verticals. Single source of truth for ports, paths, status, and descriptions. Any automation that needs to discover verticals reads this file.

```yaml
# Assist Platform Vertical Registry
# Updated: 2026-02-04
#
# This file is the single source of truth for all Assist verticals.
# Automation scripts, deployment tools, and monitoring read this file.
#
# Status values:
#   production  - Live, serving users
#   scaffold    - Code exists, not yet deployed
#   planned     - Not yet scaffolded
#
# Port allocation:
#   8000 - vetassist (production)
#   8001 - ssidassist
#   8002 - tribeassist
#   8003+ - future verticals
#
verticals:
  vetassist:
    path: /ganuda/vetassist
    status: production
    port: 8000
    database: zammad_production
    description: "VA disability benefits assistance"

  ssidassist:
    path: /ganuda/assist/ssidassist
    status: scaffold
    port: 8001
    database: zammad_production
    description: "Social Security disability assistance"

  tribeassist:
    path: /ganuda/assist/tribeassist
    status: scaffold
    port: 8002
    database: zammad_production
    description: "Cherokee Nation services assistance"
    language: "bilingual_chr_en"
```

---

### Step 2: Create `/ganuda/assist/scripts/new_vertical.sh`

Generator script for new verticals. Creates the full directory structure and starter files from template. IMPORTANT: Use `#!/bin/bash` -- dash does not support `pipefail` or `${VAR^}` case modification.

```bash
#!/bin/bash
# Generate a new Assist vertical from template
# Usage: ./new_vertical.sh <vertical_name>
#
# Creates the standard directory structure and starter files
# for a new Assist Platform vertical. After running, you get:
#   - backend/ with config, main, services, api stubs
#   - frontend/ directory structure
#   - config/ with council context and crisis patterns
#   - sql/ with schema stub
#
# REQUIRES: bash 4+ (uses ${VAR^} for capitalization)

set -euo pipefail

VERTICAL_NAME="${1:?Usage: $0 <vertical_name>}"
ASSIST_ROOT="/ganuda/assist"
VERTICAL_DIR="${ASSIST_ROOT}/${VERTICAL_NAME}"

if [ -d "$VERTICAL_DIR" ]; then
    echo "ERROR: Directory already exists: $VERTICAL_DIR"
    exit 1
fi

echo "Creating new Assist vertical: $VERTICAL_NAME"

# Create directory structure
mkdir -p "$VERTICAL_DIR"/{backend/{services,api/v1/endpoints},frontend/{app,config/wizards},config,sql}

# Create backend __init__.py
cat > "$VERTICAL_DIR/backend/__init__.py" << PYEOF
"""${VERTICAL_NAME} backend package."""
PYEOF

# Create backend config.py
cat > "$VERTICAL_DIR/backend/config.py" << PYEOF
"""${VERTICAL_NAME} configuration."""
import sys
sys.path.insert(0, '/ganuda/assist')
from core.backend.config import AssistConfig

class ${VERTICAL_NAME^}Config(AssistConfig):
    app_title: str = "${VERTICAL_NAME^}"
    vertical_name: str = "${VERTICAL_NAME}"
    port: int = 8003  # Update port as needed
PYEOF

# Create backend main.py
cat > "$VERTICAL_DIR/backend/main.py" << PYEOF
"""${VERTICAL_NAME} application entry point."""
import sys
sys.path.insert(0, '/ganuda/assist')
from core.backend.base_app import create_assist_app
from .config import ${VERTICAL_NAME^}Config

config = ${VERTICAL_NAME^}Config()
app = create_assist_app(config)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
PYEOF

# Create services __init__.py
cat > "$VERTICAL_DIR/backend/services/__init__.py" << PYEOF
"""${VERTICAL_NAME} services."""
PYEOF

# Create API __init__.py files
touch "$VERTICAL_DIR/backend/api/__init__.py"
touch "$VERTICAL_DIR/backend/api/v1/__init__.py"
touch "$VERTICAL_DIR/backend/api/v1/endpoints/__init__.py"

# Create placeholder config YAMLs
cat > "$VERTICAL_DIR/config/council_context.yaml" << YAMLEOF
domain: "${VERTICAL_NAME}"
specialist_priority:
  turtle: 1.0
  spider: 1.0
  raven: 1.0
  gecko: 1.0
  eagle_eye: 1.0
YAMLEOF

cat > "$VERTICAL_DIR/config/crisis_patterns.yaml" << YAMLEOF
# Crisis patterns for ${VERTICAL_NAME}
# Inherits base patterns from core/config/crisis_patterns.yaml
domain_specific: []
YAMLEOF

# Create SQL schema stub
cat > "$VERTICAL_DIR/sql/${VERTICAL_NAME}_schema.sql" << SQLEOF
-- ${VERTICAL_NAME} Schema
-- Run on bluefin (192.168.132.222) / zammad_production

-- Add vertical-specific tables here
SQLEOF

echo ""
echo "=== Vertical created: $VERTICAL_DIR ==="
find "$VERTICAL_DIR" -type f | sort
echo ""
echo "Next steps:"
echo "  1. Edit backend/config.py with vertical-specific settings"
echo "  2. Add services in backend/services/"
echo "  3. Add API endpoints in backend/api/v1/endpoints/"
echo "  4. Create wizard YAMLs in frontend/config/wizards/"
echo "  5. Add to verticals.yaml"
echo "  6. Run validate_vertical.sh $VERTICAL_NAME"
```

---

### Step 3: Create `/ganuda/assist/scripts/validate_vertical.sh`

Pre-launch validation script. Checks that a vertical has all required files, valid YAML, valid Python syntax, and is registered in the verticals registry. Run this before any deployment.

```bash
#!/bin/bash
# Validate an Assist vertical is ready for launch
# Usage: ./validate_vertical.sh <vertical_name>
#
# Checks:
#   1. Required files exist (config, main, council context, crisis patterns)
#   2. All YAML files parse without errors
#   3. All Python files have valid syntax
#   4. Vertical is registered in verticals.yaml
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed

set -euo pipefail

VERTICAL_NAME="${1:?Usage: $0 <vertical_name>}"
ASSIST_ROOT="/ganuda/assist"
VERTICAL_DIR="${ASSIST_ROOT}/${VERTICAL_NAME}"
ERRORS=0

echo "=== Validating Assist vertical: $VERTICAL_NAME ==="

# Check directory exists
if [ ! -d "$VERTICAL_DIR" ]; then
    echo "[FAIL] Directory not found: $VERTICAL_DIR"
    exit 1
fi

# Check required files
REQUIRED_FILES=(
    "backend/__init__.py"
    "backend/config.py"
    "backend/main.py"
    "config/council_context.yaml"
    "config/crisis_patterns.yaml"
)

echo ""
echo "--- Required files ---"
for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$VERTICAL_DIR/$f" ]; then
        echo "[OK] $f"
    else
        echo "[FAIL] Missing: $f"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check YAML validity
echo ""
echo "--- YAML validation ---"
for yaml_file in "$VERTICAL_DIR"/config/*.yaml; do
    if [ -f "$yaml_file" ]; then
        python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "[OK] YAML valid: $(basename "$yaml_file")"
        else
            echo "[FAIL] YAML invalid: $(basename "$yaml_file")"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# Check Python syntax
echo ""
echo "--- Python syntax ---"
for py_file in $(find "$VERTICAL_DIR" -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*"); do
    python3 -c "import py_compile; py_compile.compile('$py_file', doraise=True)" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[OK] Python valid: $(basename "$py_file")"
    else
        echo "[FAIL] Python invalid: $(basename "$py_file")"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check registered in verticals.yaml
echo ""
echo "--- Registry check ---"
if [ -f "$ASSIST_ROOT/verticals.yaml" ]; then
    if grep -q "$VERTICAL_NAME" "$ASSIST_ROOT/verticals.yaml"; then
        echo "[OK] Registered in verticals.yaml"
    else
        echo "[WARN] Not found in verticals.yaml"
    fi
else
    echo "[WARN] verticals.yaml not found at $ASSIST_ROOT/verticals.yaml"
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "=== VALIDATION PASSED ==="
    exit 0
else
    echo "=== VALIDATION FAILED: $ERRORS error(s) ==="
    exit 1
fi
```

---

### Step 4: Make Scripts Executable

After creating both scripts, make them executable:

```bash
#!/bin/bash
chmod +x /ganuda/assist/scripts/new_vertical.sh
chmod +x /ganuda/assist/scripts/validate_vertical.sh
echo "[OK] Scripts made executable"
ls -la /ganuda/assist/scripts/
```

---

## Verification

After creating all files and setting permissions, run this verification script:

```bash
#!/bin/bash
echo "=== Registry Gap-Fill Verification ==="

PASS=0
FAIL=0

echo "--- Files ---"
for f in "/ganuda/assist/verticals.yaml" "/ganuda/assist/scripts/new_vertical.sh" "/ganuda/assist/scripts/validate_vertical.sh"; do
    if [ -f "$f" ]; then
        echo "[OK] $f ($(wc -l < "$f") lines)"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $f"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Executable check ---"
for f in "/ganuda/assist/scripts/new_vertical.sh" "/ganuda/assist/scripts/validate_vertical.sh"; do
    if [ -x "$f" ]; then
        echo "[OK] $f is executable"
    else
        echo "[FAIL] $f is NOT executable"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- YAML validity ---"
python3 -c "import yaml; yaml.safe_load(open('/ganuda/assist/verticals.yaml'))" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] verticals.yaml is valid YAML"
else
    echo "[FAIL] verticals.yaml is NOT valid YAML"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "--- Shell script syntax ---"
for f in "/ganuda/assist/scripts/new_vertical.sh" "/ganuda/assist/scripts/validate_vertical.sh"; do
    bash -n "$f" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[OK] Syntax valid: $(basename "$f")"
    else
        echo "[FAIL] Syntax error: $(basename "$f")"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Shebang check (must be #!/bin/bash, NOT #!/bin/sh) ---"
for f in "/ganuda/assist/scripts/new_vertical.sh" "/ganuda/assist/scripts/validate_vertical.sh"; do
    SHEBANG=$(head -1 "$f")
    if [ "$SHEBANG" = "#!/bin/bash" ]; then
        echo "[OK] $(basename "$f") uses #!/bin/bash"
    else
        echo "[FAIL] $(basename "$f") has wrong shebang: $SHEBANG"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "--- Registry content check ---"
for v in vetassist ssidassist tribeassist; do
    if grep -q "$v" /ganuda/assist/verticals.yaml; then
        echo "[OK] $v found in registry"
    else
        echo "[FAIL] $v NOT in registry"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -eq 0 ]; then
    echo "GAP-FILL COMPLETE"
else
    echo "GAP-FILL INCOMPLETE -- fix failures above"
fi
```

---

## Deliverables

| # | File | Purpose |
|---|---|---|
| 1 | `verticals.yaml` | Single source of truth for all Assist verticals |
| 2 | `scripts/new_vertical.sh` | Generator script -- scaffold a new vertical in one command |
| 3 | `scripts/validate_vertical.sh` | Pre-launch validation -- catches issues before deployment |

---

## Post-Completion: Smoke Test

After all three gap-fill instructions (SSIDASSIST, TRIBEASSIST, REGISTRY) are complete, run the validation script against both verticals to confirm end-to-end readiness:

```bash
#!/bin/bash
echo "=== Assist Platform Smoke Test ==="
echo ""

/ganuda/assist/scripts/validate_vertical.sh ssidassist
echo ""

/ganuda/assist/scripts/validate_vertical.sh tribeassist
echo ""

echo "=== Smoke test complete ==="
```

---

## Safety Notes

- DO NOT modify anything under `/ganuda/vetassist/` -- that is production.
- DO NOT modify anything under `/ganuda/assist/core/` -- that is managed by ASSIST-GAPFILL-CORE-BACKEND.
- DO NOT modify anything under `/ganuda/assist/ssidassist/` -- that is managed by ASSIST-GAPFILL-SSIDASSIST.
- DO NOT modify anything under `/ganuda/assist/tribeassist/` -- that is managed by ASSIST-GAPFILL-TRIBEASSIST.
- Scripts MUST use `#!/bin/bash` shebang. The `#!/bin/sh` shebang resolves to dash on Debian/Ubuntu, which does not support `pipefail`, bash arrays (`${ARRAY[@]}`), or `${VAR^}` case modification. All three features are used in these scripts.
- The `new_vertical.sh` generator refuses to run if the target directory already exists. This is intentional -- it prevents accidental overwrites of existing verticals.

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04
