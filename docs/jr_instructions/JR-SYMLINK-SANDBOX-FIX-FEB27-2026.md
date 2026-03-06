# Symlink-Aware Path Validation in Executor

**Council Vote**: #d9ca4e7c8c7e43cb (Hawk: BUILD NOW — security patch)
**Long Man Phase**: BUILD
**Priority**: P1 — Security fix
**Assigned**: Software Engineer Jr.

---

## Context

The `validate_path()` method in `search_replace_editor.py` only checks `filepath.startswith()` against allowed/forbidden prefixes. A symlink inside `/ganuda/` pointing to `/etc/shadow` would pass validation. Shanz's Legion sandbox checks BOTH `os.path.abspath()` AND `Path.resolve()` — if either fails, the path is denied.

## Step 1: Add symlink-aware dual resolution to validate_path

File: `/ganuda/jr_executor/search_replace_editor.py`

<<<<<<< SEARCH
    def validate_path(self, filepath: str) -> Tuple[bool, str]:
        """Validate that filepath is allowed for editing."""
        if not os.path.isabs(filepath):
            return False, f"Path must be absolute, got: {filepath}"

        # Check forbidden paths first
        for forbidden in self.forbidden_paths:
            if filepath.startswith(forbidden):
                return False, f"Path is in forbidden area: {forbidden}"

        # Check allowed paths
        path_allowed = any(filepath.startswith(allowed) for allowed in self.allowed_paths)
        if not path_allowed:
            return False, f"Path not in allowed areas: {self.allowed_paths}"

        return True, ""
=======
    def validate_path(self, filepath: str) -> Tuple[bool, str]:
        """Validate that filepath is allowed for editing.

        Uses dual-resolution symlink checking: validates both the literal path
        AND the resolved path (following symlinks). Both must pass.
        Inspired by Legion sandbox.py — denied always wins.
        """
        if not os.path.isabs(filepath):
            return False, f"Path must be absolute, got: {filepath}"

        # Resolve symlinks to get the real target path
        resolved = str(Path(filepath).resolve())

        # Check BOTH literal and resolved paths against forbidden areas
        for forbidden in self.forbidden_paths:
            if filepath.startswith(forbidden):
                return False, f"Path is in forbidden area: {forbidden}"
            if resolved.startswith(forbidden):
                return False, f"Symlink resolves to forbidden area: {resolved} -> {forbidden}"

        # Check BOTH literal and resolved paths against allowed areas
        path_allowed = any(filepath.startswith(allowed) for allowed in self.allowed_paths)
        if not path_allowed:
            return False, f"Path not in allowed areas: {self.allowed_paths}"

        resolved_allowed = any(resolved.startswith(allowed) for allowed in self.allowed_paths)
        if not resolved_allowed:
            return False, f"Symlink resolves outside allowed areas: {resolved}"

        return True, ""
>>>>>>> REPLACE

## Step 2: Ensure Path import exists

File: `/ganuda/jr_executor/search_replace_editor.py`

Verify `from pathlib import Path` is in the imports. If not:

<<<<<<< SEARCH
from typing import Dict, List, Tuple, Any
=======
from pathlib import Path
from typing import Dict, List, Tuple, Any
>>>>>>> REPLACE

## Verification

After applying:
1. Normal paths (`/ganuda/lib/foo.py`) still pass validation
2. A symlink `/ganuda/link -> /etc/shadow` would be REJECTED (resolves outside allowed)
3. A symlink `/ganuda/link -> /ganuda/lib/real.py` would PASS (resolves inside allowed)
4. Forbidden paths are checked on both literal and resolved paths
