# Jr Instruction: Pegasus MVT Fleet Scan — Automated Security Scanning

**Kanban**: #549 (Pegasus MVT Scans)
**Sacred Fire Priority**: 95
**Story Points**: 3
**River Cycle**: RC-2026-02A
**Long Man Step**: BUILD

## Context

Phase 1 security work (Nov 2025) established MVT (Mobile Verification Toolkit) and a Linux security baseline scanner. Current state:

| Component | Status | Location |
|-----------|--------|----------|
| MVT venv | INSTALLED | `/ganuda/home/dereadi/security_jr/spoke_security_phase1/mvt_venv/` |
| Pegasus IOCs | PRESENT (Nov 2025) | `/ganuda/home/dereadi/security_jr/iocs/pegasus.stix2` |
| Redfin scan | VERIFIED CLEAN | Nov 9, 2025 |
| Bluefin scan | NOT DONE | — |
| Greenfin scan | NOT DONE | — |
| Fleet automation | NOT BUILT | — |
| Results in DB | NO | — |

We need a fleet-wide security scanner that checks each Linux node for compromise indicators (suspicious processes, network connections, crontabs, SSH keys, persistence mechanisms) and stores results in the security_health_checks table.

## Steps

### Step 1: Create Fleet Security Scanner

Create `/ganuda/scripts/security/mvt_fleet_scanner.py`

```python
#!/usr/bin/env python3
"""Fleet-wide security scan for Cherokee AI Federation Linux nodes.

Kanban #549 — Pegasus MVT Scans
Scans the LOCAL node for compromise indicators using process, network,
crontab, SSH key, and persistence mechanism checks. Stores results
in the security_health_checks database table.

Usage: CHEROKEE_DB_PASS=xxx python3 /ganuda/scripts/security/mvt_fleet_scanner.py
"""
import os
import sys
import json
import subprocess
import datetime
import socket

HOSTNAME = socket.gethostname().lower()
RESULTS_DIR = f"/ganuda/security/mvt_results/{HOSTNAME}"

# Known good ports per node (extend as services are added)
KNOWN_PORTS = {
    "redfin": {22, 80, 443, 3001, 4000, 5555, 8000, 8080, 9090},
    "bluefin": {22, 3000, 5432, 8090, 8091, 8092, 9090},
    "greenfin": {22, 3128, 8003, 9080, 9090},
}

# Suspicious process name patterns
SUSPICIOUS_PROCESS_PATTERNS = [
    "pegasus", "chrysaor", "trident", "lawful_intercept",
    "cellebrite", "graykey", "nsxpc", "bridgehead",
    "cryptominer", "xmrig", "coinhive", "c2_beacon",
]

# Suspicious cron/rc patterns
SUSPICIOUS_SCRIPT_PATTERNS = [
    "curl.*|.*sh", "wget.*|.*sh", "base64 -d", "eval $(",
    "python -c.*import", "/dev/tcp/", "nc -e", "ncat -e",
    "socat.*exec", "perl.*socket",
]

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
}


def run_cmd(cmd, timeout=15):
    """Run command, return stdout or empty string on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def scan_processes():
    """Check for suspicious processes."""
    findings = []
    output = run_cmd(["ps", "aux"])
    for line in output.split("\n"):
        lower = line.lower()
        for pattern in SUSPICIOUS_PROCESS_PATTERNS:
            if pattern in lower:
                findings.append({
                    "type": "suspicious_process",
                    "severity": "CRITICAL",
                    "detail": line.strip()[:200],
                    "pattern": pattern,
                })
    return findings


def scan_network():
    """Check for unknown listening ports."""
    findings = []
    known = KNOWN_PORTS.get(HOSTNAME, set())
    output = run_cmd(["ss", "-tulnp"])
    for line in output.split("\n")[1:]:
        if "LISTEN" not in line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        addr = parts[4]
        try:
            port = int(addr.rsplit(":", 1)[-1])
        except (ValueError, IndexError):
            continue
        if port not in known and port > 1024:
            findings.append({
                "type": "unknown_listener",
                "severity": "HIGH",
                "detail": line.strip()[:200],
                "port": port,
            })
    return findings


def scan_crontabs():
    """Check for suspicious crontab entries."""
    findings = []

    # User crontab
    output = run_cmd(["crontab", "-l"])
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for pattern in SUSPICIOUS_SCRIPT_PATTERNS:
            if pattern.split(".*")[0] in line:
                findings.append({
                    "type": "suspicious_cron",
                    "severity": "CRITICAL",
                    "detail": line[:200],
                    "pattern": pattern,
                })

    # System cron directories
    for cron_dir in ["/etc/cron.d", "/etc/cron.daily", "/etc/cron.hourly"]:
        if not os.path.isdir(cron_dir):
            continue
        for fname in os.listdir(cron_dir):
            fpath = os.path.join(cron_dir, fname)
            try:
                with open(fpath) as f:
                    content = f.read()
                for pattern in SUSPICIOUS_SCRIPT_PATTERNS:
                    key = pattern.split(".*")[0]
                    if key in content:
                        findings.append({
                            "type": "suspicious_cron_file",
                            "severity": "HIGH",
                            "detail": f"{fpath}: contains '{key}'",
                        })
            except (PermissionError, IsADirectoryError, OSError):
                pass

    return findings


def scan_ssh_keys():
    """Check authorized_keys for unexpected entries."""
    findings = []
    auth_keys = os.path.expanduser("~/.ssh/authorized_keys")
    if os.path.exists(auth_keys):
        try:
            with open(auth_keys) as f:
                keys = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            if len(keys) > 10:
                findings.append({
                    "type": "excessive_ssh_keys",
                    "severity": "HIGH",
                    "detail": f"{len(keys)} authorized SSH keys (review recommended)",
                })
            # Check for keys with suspicious comments
            for key in keys:
                parts = key.split()
                if len(parts) >= 3:
                    comment = " ".join(parts[2:]).lower()
                    suspicious_comments = ["temp", "test", "backdoor", "hack", "anon"]
                    for sc in suspicious_comments:
                        if sc in comment:
                            findings.append({
                                "type": "suspicious_ssh_key",
                                "severity": "CRITICAL",
                                "detail": f"Key with suspicious comment: {comment[:100]}",
                            })
        except PermissionError:
            pass
    return findings


def scan_persistence():
    """Check for unusual persistence mechanisms."""
    findings = []

    # User systemd services
    user_svc_dir = os.path.expanduser("~/.config/systemd/user/")
    if os.path.isdir(user_svc_dir):
        for fname in os.listdir(user_svc_dir):
            if not fname.endswith(".service"):
                continue
            fpath = os.path.join(user_svc_dir, fname)
            try:
                with open(fpath) as f:
                    content = f.read()
                for pattern in SUSPICIOUS_SCRIPT_PATTERNS:
                    key = pattern.split(".*")[0]
                    if key in content:
                        findings.append({
                            "type": "suspicious_user_service",
                            "severity": "CRITICAL",
                            "detail": f"{fpath}: contains '{key}'",
                        })
            except (PermissionError, OSError):
                pass

    # Shell RC files
    for rcfile in ["~/.bashrc", "~/.profile", "~/.bash_profile", "~/.zshrc"]:
        rcpath = os.path.expanduser(rcfile)
        if not os.path.exists(rcpath):
            continue
        try:
            with open(rcpath) as f:
                content = f.read()
            for pattern in SUSPICIOUS_SCRIPT_PATTERNS:
                key = pattern.split(".*")[0]
                if key in content:
                    findings.append({
                        "type": "suspicious_rc_file",
                        "severity": "HIGH",
                        "detail": f"{rcpath}: contains '{key}'",
                    })
        except PermissionError:
            pass

    return findings


def store_results(findings, scan_time):
    """Store scan results in the security_health_checks database table."""
    if not DB_CONFIG["password"]:
        print("  SKIP: No CHEROKEE_DB_PASS set, cannot store in DB")
        return

    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        severity = "INFO"
        if any(f.get("severity") == "HIGH" for f in findings):
            severity = "HIGH"
        if any(f.get("severity") == "CRITICAL" for f in findings):
            severity = "CRITICAL"

        cur.execute("""
            INSERT INTO security_health_checks
            (node_name, scan_type, findings_json, scan_timestamp, severity)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            HOSTNAME,
            'mvt_fleet_scan',
            json.dumps({"findings": findings, "total": len(findings)}),
            scan_time,
            severity,
        ))
        conn.commit()
        conn.close()
        print(f"  Results stored in security_health_checks (severity={severity})")
    except ImportError:
        print("  SKIP: psycopg2 not available")
    except Exception as e:
        print(f"  WARNING: DB store failed: {e}")


def scan():
    """Run the full node security scan."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    scan_time = datetime.datetime.now().isoformat()

    print("=" * 60)
    print(f"SECURITY SCAN — {HOSTNAME}")
    print(f"Cherokee AI Federation — {scan_time}")
    print("=" * 60)

    all_findings = []
    checks = [
        ("Processes", scan_processes),
        ("Network listeners", scan_network),
        ("Crontabs", scan_crontabs),
        ("SSH keys", scan_ssh_keys),
        ("Persistence mechanisms", scan_persistence),
    ]

    for i, (name, func) in enumerate(checks, 1):
        print(f"\n[{i}/{len(checks)}] Scanning {name}...")
        findings = func()
        all_findings.extend(findings)
        if findings:
            for f in findings:
                sev = f.get("severity", "INFO")
                print(f"  [{sev}] {f.get('type', 'unknown')}: {f.get('detail', '')[:80]}")
        else:
            print(f"  Clean")

    # Save results to file
    results = {
        "hostname": HOSTNAME,
        "scan_time": scan_time,
        "findings": all_findings,
        "total_findings": len(all_findings),
        "status": "CLEAN" if not all_findings else "REVIEW_NEEDED",
    }

    ts = scan_time.replace(":", "-").replace(".", "-")
    results_file = os.path.join(RESULTS_DIR, f"scan_{ts}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved: {results_file}")

    # Store in database
    store_results(all_findings, scan_time)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    critical = sum(1 for f in all_findings if f.get("severity") == "CRITICAL")
    high = sum(1 for f in all_findings if f.get("severity") == "HIGH")

    if critical:
        print(f"  CRITICAL findings: {critical}")
    if high:
        print(f"  HIGH findings:     {high}")
    if not all_findings:
        print(f"  NODE CLEAN: No suspicious indicators found on {HOSTNAME}")
    else:
        print(f"  TOTAL findings:    {len(all_findings)} — REVIEW NEEDED")

    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(scan())
```

### Step 2: Create IOC Database Updater

Create `/ganuda/scripts/security/ioc_updater.py`

```python
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
```

## Verification

Run the fleet scanner on the current node:

```text
CHEROKEE_DB_PASS=<password> python3 /ganuda/scripts/security/mvt_fleet_scanner.py
```

Check IOC database age:

```text
python3 /ganuda/scripts/security/ioc_updater.py
```

Force-update IOCs:

```text
python3 /ganuda/scripts/security/ioc_updater.py --force
```

Verify results stored in database:

```text
PGPASSWORD=<password> psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT node_name, scan_type, severity, scan_timestamp FROM security_health_checks WHERE scan_type='mvt_fleet_scan' ORDER BY scan_timestamp DESC LIMIT 5"
```

## What This Does NOT Cover

- iOS/Android device scanning via MVT proper (requires macOS host + USB device connection)
- Suricata IDS rules deployment (rules exist at `/ganuda/home/dereadi/security_jr/whitehat_suricata_rules.rules`)
- Automated daily scanning via systemd timer (timer exists at `~/.config/systemd/user/security-whitehat-scanner.timer`)
- Network-level scanning with nmap (existing script at `/ganuda/home/dereadi/security_jr/whitehat_network_scan.py`)
- Scanning non-Linux nodes (sasass, sasass2, bmasass — different approach needed)
