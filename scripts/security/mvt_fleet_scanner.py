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

HOSTNAME = socket.gethostname().lower().split('.')[0]
RESULTS_DIR = f"/ganuda/security/mvt_results/{HOSTNAME}"

# Known good ports per node (extend as services are added)
KNOWN_PORTS = {
    "redfin": {22, 53, 80, 443, 631, 2019, 3000, 4000, 5432, 5555, 5556,
               8000, 8001, 8002, 8003, 8080, 8081, 8090},
    "bluefin": {22, 5432, 8090, 8091, 8092},
    "greenfin": {22, 5080, 5081, 8003, 9080},
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
            with open(auth_keys, encoding='utf-8', errors='replace') as f:
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