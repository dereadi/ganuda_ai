#!/usr/bin/env python3
"""
Smoke Test — Post-deploy verification for the Cherokee AI Federation.

Reads production_manifest.yaml and verifies every service, port, database,
and sacred file is reachable and healthy. Run after ANY config change.

Ultrathink Gap 6: "We maintain code the way 75% of models do — make the change,
verify the obvious path, miss the downstream breakage."

Usage:
    python3 smoke_test.py              # Full smoke test
    python3 smoke_test.py --quick      # Ports + DB only (30 seconds)
    python3 smoke_test.py --tier 0     # Only tier 0 life support
    python3 smoke_test.py --post-deploy  # Full test + thermalize results
"""

import os
import sys
import yaml
import socket
import argparse
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────
MANIFEST_PATH = "/ganuda/config/production_manifest.yaml"
SECRETS_PATH = "/ganuda/config/secrets.env"

# ── Load secrets ───────────────────────────────────────────────────────
def load_secrets():
    """Load secrets.env into dict."""
    secrets = {}
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    secrets[key.strip()] = val.strip()
    return secrets

# ── Test functions ─────────────────────────────────────────────────────
def check_port(host, port, timeout=5):
    """TCP connect check. Returns (up, latency_ms)."""
    try:
        start = datetime.now()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        latency = (datetime.now() - start).total_seconds() * 1000
        return True, round(latency, 1)
    except Exception:
        return False, None


def check_http(host, port, path="/health", timeout=5):
    """HTTP GET health check. Returns (up, status_code, latency_ms)."""
    try:
        import urllib.request
        start = datetime.now()
        url = f"http://{host}:{port}{path}"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=timeout)
        latency = (datetime.now() - start).total_seconds() * 1000
        return True, resp.status, round(latency, 1)
    except Exception as e:
        return False, None, None


def check_postgres(host, port, dbname, user, password, timeout=5):
    """PostgreSQL connection + SELECT 1. Returns (up, latency_ms)."""
    try:
        import psycopg2
        start = datetime.now()
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname,
            user=user, password=password, connect_timeout=timeout
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        latency = (datetime.now() - start).total_seconds() * 1000
        return True, round(latency, 1)
    except Exception:
        return False, None


def check_sacred_table(host, port, dbname, user, password, table, timeout=5):
    """Verify sacred table exists and has rows."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname,
            user=user, password=password, connect_timeout=timeout
        )
        cur = conn.cursor()
        cur.execute(f"SELECT count(*) FROM {table}")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return True, count
    except Exception as e:
        return False, str(e)


def check_file_exists(path):
    """Verify sacred file exists and is non-empty."""
    p = Path(path)
    if not p.exists():
        return False, "MISSING"
    if p.stat().st_size == 0:
        return False, "EMPTY"
    return True, f"{p.stat().st_size} bytes"


def check_systemd_service(name):
    """Check if systemd service/timer is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5
        )
        status = result.stdout.strip()
        return status == "active", status
    except Exception:
        return False, "error"


# ── Main smoke test ────────────────────────────────────────────────────
def run_smoke_test(manifest, secrets, tier_filter=None, quick=False):
    """Run smoke tests against manifest. Returns (pass_count, fail_count, results)."""
    results = []
    passes = 0
    fails = 0

    def record(category, name, passed, detail=""):
        nonlocal passes, fails
        if passed:
            passes += 1
            status = "PASS"
        else:
            fails += 1
            status = "FAIL"
        results.append({"category": category, "name": name, "status": status, "detail": detail})
        icon = "✓" if passed else "✗"
        print(f"  {icon} [{category}] {name}: {detail}")

    db_host = secrets.get("CHEROKEE_DB_HOST", "10.100.0.2")
    db_port = int(secrets.get("CHEROKEE_DB_PORT", "5432"))
    db_name = secrets.get("CHEROKEE_DB_NAME", "zammad_production")
    db_user = secrets.get("CHEROKEE_DB_USER", "claude")
    db_pass = secrets.get("CHEROKEE_DB_PASS", "")

    # ── Database connectivity ──────────────────────────────────────
    print("\n── Database Connectivity ──")
    for db_key, db_info in manifest.get("databases", {}).items():
        if db_info.get("smoke_test_skip"):
            record("DB", f"{db_key} (ISOLATED)", True, "skipped by design")
            continue
        host = db_info.get("host", db_host)
        port = db_info.get("port", db_port)
        up, latency = check_postgres(host, port, db_name, db_user, db_pass)
        record("DB", f"{db_key} ({host}:{port})", up,
               f"{latency}ms" if up else "UNREACHABLE")

    # ── Sacred tables ──────────────────────────────────────────────
    if not quick:
        print("\n── Sacred Tables ──")
        for table_info in manifest.get("sacred_tables", []):
            table = table_info["table"]
            # Only check tables in the primary DB for now
            if table_info.get("db") in ("zammad_production", "triad_federation"):
                up, count = check_sacred_table(db_host, db_port, db_name, db_user, db_pass, table)
                if up:
                    record("TABLE", table, True, f"{count:,} rows")
                else:
                    # Table might be in triad_federation, try that
                    up2, count2 = check_sacred_table(db_host, db_port, "triad_federation", db_user, db_pass, table)
                    if up2:
                        record("TABLE", table, True, f"{count2:,} rows (triad_federation)")
                    else:
                        record("TABLE", table, False, f"{count}")

    # ── Port checks ────────────────────────────────────────────────
    print("\n── Port Checks ──")
    for node, port_list in manifest.get("ports", {}).items():
        for port_info in port_list:
            port = port_info["port"]
            service = port_info.get("service", "unknown")
            # Determine host
            if node == "redfin":
                host = "127.0.0.1"
            elif node == "bluefin":
                host = db_host  # Uses WireGuard now
            elif node == "bmasass":
                host = "100.103.27.106"
            elif node == "owlfin":
                host = "192.168.132.170"
            elif node == "eaglefin":
                host = "192.168.132.84"
            elif node == "greenfin":
                host = "192.168.132.224"
            elif node == "sasass":
                host = "192.168.132.241"
            elif node == "sasass2":
                host = "192.168.132.242"
            else:
                host = "127.0.0.1"

            up, latency = check_port(host, port)
            record("PORT", f"{node}/{service} ({host}:{port})", up,
                   f"{latency}ms" if up else "UNREACHABLE")

    # ── HTTP health endpoints ──────────────────────────────────────
    print("\n── HTTP Health Endpoints ──")
    health_endpoints = [
        ("redfin", "127.0.0.1", 8000, "/health", "vLLM"),
        ("redfin", "127.0.0.1", 8080, "/health", "LLM Gateway"),
        ("redfin", "127.0.0.1", 8001, "/health", "VetAssist Backend"),
        ("redfin", "127.0.0.1", 9400, "/health", "ConsultationRing"),
    ]
    for node, host, port, path, name in health_endpoints:
        up, status_code, latency = check_http(host, port, path)
        record("HTTP", f"{name} ({host}:{port}{path})", up,
               f"HTTP {status_code}, {latency}ms" if up else "DOWN")

    # ── Sacred files ───────────────────────────────────────────────
    if not quick:
        print("\n── Sacred Files ──")
        for file_info in manifest.get("sacred_files", []):
            path = file_info["path"]
            up, detail = check_file_exists(path)
            record("FILE", path, up, detail)

    # ── Systemd services ───────────────────────────────────────────
    if not quick:
        print("\n── Systemd Services ──")
        for tier_name, tier_services in manifest.get("services", {}).items():
            tier_num = tier_name.split("_")[1] if "_" in tier_name else "?"
            if tier_filter is not None and str(tier_num) != str(tier_filter):
                continue
            for svc in tier_services:
                name = svc["name"]
                up, status = check_systemd_service(name)
                record(f"SVC-T{tier_num}", name, up, status)

    return passes, fails, results


def thermalize_results(passes, fails, results, secrets):
    """Write smoke test results to thermal memory."""
    try:
        import psycopg2
        db_host = secrets.get("CHEROKEE_DB_HOST", "10.100.0.2")
        db_port = int(secrets.get("CHEROKEE_DB_PORT", "5432"))
        db_name = secrets.get("CHEROKEE_DB_NAME", "zammad_production")
        db_user = secrets.get("CHEROKEE_DB_USER", "claude")
        db_pass = secrets.get("CHEROKEE_DB_PASS", "")

        failed_items = [r for r in results if r["status"] == "FAIL"]
        failed_summary = "\n".join(
            f"  FAIL: [{r['category']}] {r['name']} — {r['detail']}"
            for r in failed_items
        ) if failed_items else "  (none)"

        content = (
            f"SMOKE TEST — {datetime.now().strftime('%Y-%m-%d %H:%M')} CT\n"
            f"Result: {passes} PASS, {fails} FAIL\n"
            f"{'ALL CLEAR' if fails == 0 else 'FAILURES DETECTED'}\n\n"
            f"Failures:\n{failed_summary}"
        )

        memory_hash = hashlib.sha256(
            f"smoke_test_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        temp = 50.0 if fails == 0 else min(100.0, 70.0 + fails * 5)

        conn = psycopg2.connect(
            host=db_host, port=db_port, dbname=db_name,
            user=db_user, password=db_pass, connect_timeout=10
        )
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, sacred_pattern,
             current_stage, domain_tag, source_node, tags, memory_type)
            VALUES (%s, %s, %s, false, 'FRESH', 'smoke_test', 'redfin',
                    %s, 'episodic')
            ON CONFLICT (memory_hash) DO NOTHING""",
            (memory_hash, content, temp,
             ['smoke_test', 'post_deploy', 'owl'])
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"\n  Thermalized (temp {temp})")
    except Exception as e:
        print(f"\n  Thermalize failed: {e}")


# ── Entry point ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ganuda Smoke Test")
    parser.add_argument("--quick", action="store_true", help="Ports + DB only")
    parser.add_argument("--tier", type=int, help="Only test specific service tier (0-3)")
    parser.add_argument("--post-deploy", action="store_true", help="Full test + thermalize")
    args = parser.parse_args()

    print(f"═══ GANUDA SMOKE TEST — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ═══")

    if not os.path.exists(MANIFEST_PATH):
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    secrets = load_secrets()

    passes, fails, results = run_smoke_test(
        manifest, secrets,
        tier_filter=args.tier,
        quick=args.quick
    )

    print(f"\n═══ RESULT: {passes} PASS, {fails} FAIL ═══")

    if args.post_deploy:
        thermalize_results(passes, fails, results, secrets)

    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
