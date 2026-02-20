#!/usr/bin/env python3
"""Update Pegasus/spyware IOC database from Amnesty International.

Kanban #549 — Pegasus MVT Scans
Downloads latest STIX2 indicators from AmnestyTech/investigations GitHub repo.
Validates format before overwriting existing IOCs.

Usage: python3 /ganuda/scripts/security/ioc_updater.py
"""
import os
import sys
import json
import datetime
import shutil

IOC_DIR = "/ganuda/home/dereadi/security_jr/iocs"
PEGASUS_STIX_PATH = os.path.join(IOC_DIR, "pegasus.stix2")

# Amnesty International's Pegasus investigation IOCs
AMNESTY_RAW_URL = "https://raw.githubusercontent.com/AmnestyTech/investigations/master/2021-07-18_nso/pegasus.stix2"


def update_iocs():
    """Download and validate latest IOC database."""
    print("=" * 60)
    print("IOC DATABASE UPDATE — Cherokee AI Federation")
    print(f"Time: {datetime.datetime.now().isoformat()}")
    print("=" * 60)

    os.makedirs(IOC_DIR, exist_ok=True)

    # Check current state
    print("\n--- Current IOC Database ---")
    if os.path.exists(PEGASUS_STIX_PATH):
        stat = os.stat(PEGASUS_STIX_PATH)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        age_days = (datetime.datetime.now() - mtime).days
        print(f"  File: {PEGASUS_STIX_PATH}")
        print(f"  Size: {stat.st_size:,} bytes")
        print(f"  Last modified: {mtime.isoformat()} ({age_days} days ago)")

        # Parse current indicators
        try:
            with open(PEGASUS_STIX_PATH) as f:
                current = json.load(f)
            current_count = sum(1 for obj in current.get("objects", [])
                                if obj.get("type") == "indicator")
            print(f"  Indicators: {current_count}")
        except Exception:
            current_count = 0
            print(f"  WARNING: Cannot parse current file")

        if age_days < 7:
            print(f"\n  IOCs are {age_days} days old — still fresh")
            print("  Use --force to update anyway")
            if "--force" not in sys.argv:
                return 0
    else:
        print(f"  NO IOC database found at {PEGASUS_STIX_PATH}")
        age_days = 999

    # Download latest
    print("\n--- Downloading Latest IOCs ---")
    print(f"  Source: {AMNESTY_RAW_URL}")

    try:
        import requests
        resp = requests.get(AMNESTY_RAW_URL, timeout=60)
        if resp.status_code != 200:
            print(f"  ERROR: HTTP {resp.status_code}")
            return 1

        # Validate STIX2 format
        try:
            data = resp.json()
        except json.JSONDecodeError:
            print("  ERROR: Response is not valid JSON")
            return 1

        if data.get("type") != "bundle" or "objects" not in data:
            print("  ERROR: Not a valid STIX2 bundle")
            return 1

        new_count = sum(1 for obj in data["objects"] if obj.get("type") == "indicator")
        print(f"  Downloaded: {len(resp.content):,} bytes")
        print(f"  Indicators: {new_count}")

        # Backup existing
        if os.path.exists(PEGASUS_STIX_PATH):
            backup = f"{PEGASUS_STIX_PATH}.bak-{datetime.datetime.now().strftime('%Y%m%d')}"
            shutil.copy2(PEGASUS_STIX_PATH, backup)
            print(f"  Backup: {backup}")

        # Write new file
        with open(PEGASUS_STIX_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Updated: {PEGASUS_STIX_PATH}")
        print(f"  Status: SUCCESS")

    except ImportError:
        print("  ERROR: requests module not available")
        print("  Install: pip install requests")
        return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(update_iocs())