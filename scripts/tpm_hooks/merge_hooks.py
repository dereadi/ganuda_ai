#!/usr/bin/env python3
"""Idempotent installer — merges TPM hook entries into ~/.claude/settings.json.

Usage:
    python3 /ganuda/scripts/tpm_hooks/merge_hooks.py            # install
    python3 /ganuda/scripts/tpm_hooks/merge_hooks.py --uninstall # remove

Safe to re-run. Backs up settings.json on every mutation.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
HOOK_ID = "ganuda-tpm-hooks"

PYTHON_BIN = "/ganuda/venv/bin/python3"  # stable venv, has psycopg2 etc.

HOOK_CONFIG = {
    "UserPromptSubmit": [{
        "matcher": "",
        "hooks": [{
            "type": "command",
            "command": f"{PYTHON_BIN} {HOOK_DIR}/prompt_inject.py",
            "timeout": 10,
        }],
    }],
    "SessionStart": [{
        "matcher": "",
        "hooks": [{
            "type": "command",
            "command": f"{PYTHON_BIN} {HOOK_DIR}/session_start.py",
            "timeout": 10,
        }],
    }],
    "PreCompact": [{
        "matcher": "",
        "hooks": [{
            "type": "command",
            "command": f"{PYTHON_BIN} {HOOK_DIR}/compact_guard.py",
            "timeout": 10,
        }],
    }],
}


def _load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {}
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)


def _backup(settings):
    if not os.path.exists(SETTINGS_PATH):
        return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{SETTINGS_PATH}.bak_{ts}"
    with open(backup_path, "w") as f:
        json.dump(settings, f, indent=2)
    return backup_path


def _matches_tpm_hook(entry):
    """Identify our entries by command prefix (HOOK_DIR substring)."""
    for h in entry.get("hooks", []):
        cmd = h.get("command", "")
        if HOOK_DIR in cmd:
            return True
    return False


def install():
    settings = _load_settings()
    backup = _backup(settings)
    hooks = settings.setdefault("hooks", {})
    added = 0
    replaced = 0
    for event, entries in HOOK_CONFIG.items():
        existing = hooks.get(event, [])
        # Remove any existing entries that match our prefix (idempotent update)
        remaining = [e for e in existing if not _matches_tpm_hook(e)]
        replaced += len(existing) - len(remaining)
        remaining.extend(entries)
        hooks[event] = remaining
        added += len(entries)

    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Installed {added} hook entries ({replaced} replaced).")
    if backup:
        print(f"Backup: {backup}")
    print(f"Hooks dir: {HOOK_DIR}")
    print(f"Logs will go to: /ganuda/logs/tpm_hooks/")


def uninstall():
    settings = _load_settings()
    if not settings:
        print("No settings.json found — nothing to remove.")
        return
    backup = _backup(settings)
    hooks = settings.get("hooks", {})
    removed = 0
    for event, entries in list(hooks.items()):
        remaining = [e for e in entries if not _matches_tpm_hook(e)]
        removed += len(entries) - len(remaining)
        if remaining:
            hooks[event] = remaining
        else:
            del hooks[event]
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"Removed {removed} TPM hook entries.")
    if backup:
        print(f"Backup: {backup}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.uninstall:
        uninstall()
    else:
        install()


if __name__ == "__main__":
    main()
