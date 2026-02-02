# JR Instruction: RLM Protected Paths Configuration

**JR ID:** JR-RLM-001
**Priority:** P0 (CRITICAL)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** 31653da1507b46ec
**Assigned To:** Software Engineer Jr.
**Effort:** Low

## Problem Statement

The RLM executor previously destroyed critical frontend files by overwriting them with broken stubs. Critical application files need protection from automated modification.

## Required Implementation

### 1. Protected Paths Configuration

CREATE: `/ganuda/config/rlm_protected_paths.yaml`

```yaml
# RLM Protected Paths Configuration
# Council Approved: 2026-01-27 (Vote 31653da1507b46ec)
#
# Files matching these patterns CANNOT be modified by RLM executor.
# This is a BLACKLIST - these specific paths are protected.

version: "1.0"

# Protection mode: blacklist (these cannot be modified) or whitelist (only these can)
mode: blacklist

# Protected path patterns (glob syntax)
protected_patterns:
  # VetAssist Frontend Core
  - "/ganuda/vetassist/frontend/app/**/page.tsx"
  - "/ganuda/vetassist/frontend/app/**/layout.tsx"
  - "/ganuda/vetassist/frontend/app/**/components/*.tsx"
  - "/ganuda/vetassist/frontend/package.json"
  - "/ganuda/vetassist/frontend/next.config.*"

  # VetAssist Backend Core
  - "/ganuda/vetassist/backend/app/core/*.py"
  - "/ganuda/vetassist/backend/app/main.py"
  - "/ganuda/vetassist/backend/.env"

  # SAG Core
  - "/ganuda/sag/app.py"
  - "/ganuda/sag/config/*.py"

  # Federation Core
  - "/ganuda/lib/specialist_council.py"
  - "/ganuda/lib/rlm_executor.py"  # Self-protection
  - "/ganuda/config/*.yaml"

  # System files
  - "/ganuda/**/__init__.py"
  - "/ganuda/**/requirements.txt"
  - "/ganuda/**/pyproject.toml"

# Paths that CAN be modified (override protection)
# Use sparingly - these are exceptions to protected patterns
allowed_overrides: []

# Notify on attempted modification of protected files
notify_on_block: true
notification_channel: "telegram"  # telegram, slack, or log_only
```

### 2. Modify RLM Executor

MODIFY: `/ganuda/lib/rlm_executor.py`

Add at top of file after imports:

```python
import yaml
import fnmatch
from pathlib import Path

# Load protected paths configuration
PROTECTED_PATHS_CONFIG = Path('/ganuda/config/rlm_protected_paths.yaml')
_protected_patterns = []

def load_protected_paths():
    """Load protected paths from config file."""
    global _protected_patterns
    if PROTECTED_PATHS_CONFIG.exists():
        with open(PROTECTED_PATHS_CONFIG) as f:
            config = yaml.safe_load(f)
            _protected_patterns = config.get('protected_patterns', [])
            logger.info(f"[RLM] Loaded {len(_protected_patterns)} protected path patterns")
    else:
        logger.warning("[RLM] No protected paths config found - using defaults")
        _protected_patterns = [
            "/ganuda/vetassist/frontend/app/**/page.tsx",
            "/ganuda/vetassist/frontend/app/**/layout.tsx",
            "/ganuda/lib/*.py",
        ]
    return _protected_patterns

def is_path_protected(file_path: str) -> bool:
    """Check if a path matches any protected pattern."""
    if not _protected_patterns:
        load_protected_paths()

    for pattern in _protected_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False
```

Add in `_write_files_from_response()` method, BEFORE the existing path security checks (around line 333):

```python
                # P0 SAFEGUARD: Check protected paths FIRST
                if is_path_protected(file_path):
                    self.logger.error(
                        f"[RLM] BLOCKED modification of protected file: {file_path}"
                    )
                    artifacts.append({
                        'type': 'file_blocked',
                        'path': file_path,
                        'reason': 'Protected path - modification not allowed',
                        'blocked_by': 'protected_paths'
                    })
                    continue
```

## Verification

```bash
# 1. Verify config file exists
cat /ganuda/config/rlm_protected_paths.yaml | head -20

# 2. Test protection check
python3 << 'EOF'
import sys
sys.path.insert(0, '/ganuda')
from lib.rlm_executor import is_path_protected, load_protected_paths

load_protected_paths()

test_paths = [
    "/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx",
    "/ganuda/vetassist/backend/app/core/config.py",
    "/ganuda/vetassist/backend/app/services/new_service.py",  # Should be allowed
    "/ganuda/lib/specialist_council.py",
]

print("Protection status:")
for p in test_paths:
    status = "🔒 PROTECTED" if is_path_protected(p) else "✓ Allowed"
    print(f"  {status}: {p}")
EOF
```

## Dependencies

- PyYAML (should be installed)
- fnmatch (stdlib)

---

FOR SEVEN GENERATIONS
