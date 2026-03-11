#!/usr/bin/env python3
"""Owl Pass Chaos Test — Controlled service failure simulation.

Coyote: "Smooth sailing often means we're not pushing the boundaries enough."
Coyote amendment: Test the watchdog too.

SAFETY: This script STOPS and RESTARTS services. Run during maintenance windows only.
Uses FreeIPA sudo for all service operations.
"""
import subprocess
import time
import json
import hashlib
from datetime import datetime

# Services to test (node, service_name, check_method)
# check_method: 'local' = systemctl on redfin, 'ssh' = via WireGuard
TEST_TARGETS = [
    {"node": "redfin", "service": "llm-gateway.service", "ssh": None, "description": "LLM Gateway"},
    {"node": "redfin", "service": "vllm.service", "ssh": None, "description": "vLLM Inference"},
    {"node": "redfin", "service": "sag.service", "ssh": None, "description": "SAG Control Room"},
]

# Fire Guard cycle is 2 minutes — wait 150s to ensure at least one cycle
DETECTION_WAIT_SECONDS = 150
RECOVERY_WAIT_SECONDS = 30


def run_cmd(cmd, timeout=30):
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"


def check_fire_guard_detected(service_name):
    """Check if Fire Guard's latest results include an alert for this service."""
    import psycopg2
    try:
        secrets = {}
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    secrets[k.strip()] = v.strip()

        conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                user="claude", password=secrets.get("CHEROKEE_DB_PASS", ""))
        cur = conn.cursor()
        cur.execute("""SELECT original_content FROM thermal_memory_archive
            WHERE domain_tag = 'fire_guard' AND temperature_score > 50
            ORDER BY id DESC LIMIT 5""")
        for row in cur.fetchall():
            if service_name.replace(".service", "") in row[0].lower():
                cur.close()
                conn.close()
                return True
        cur.close()
        conn.close()
    except Exception:
        pass
    return False


def test_service(target):
    """Stop a service, wait for Fire Guard to detect, restart, verify recovery."""
    result = {
        "node": target["node"],
        "service": target["service"],
        "description": target["description"],
        "timestamp": datetime.now().isoformat(),
    }

    ssh = target.get("ssh")
    svc = target["service"]

    # Verify service is running first
    if ssh:
        cmd_status = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'sudo systemctl is-active {svc}'"
    else:
        cmd_status = f"sudo systemctl is-active {svc}"

    ok, stdout, _ = run_cmd(cmd_status)
    if stdout.strip() != "active":
        result["skipped"] = f"Service not active (status: {stdout.strip()})"
        return result

    # STOP the service
    print(f"  [STOP] {target['description']} on {target['node']}...")
    if ssh:
        cmd_stop = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'sudo systemctl stop {svc}'"
    else:
        cmd_stop = f"sudo systemctl stop {svc}"

    ok, _, err = run_cmd(cmd_stop)
    result["stop_success"] = ok

    # Wait for Fire Guard detection cycle
    print(f"  [WAIT] {DETECTION_WAIT_SECONDS}s for Fire Guard detection...")
    time.sleep(DETECTION_WAIT_SECONDS)

    # Check if Fire Guard detected the failure
    detected = check_fire_guard_detected(svc)
    result["fire_guard_detected"] = detected
    print(f"  [CHECK] Fire Guard detected: {detected}")

    # RESTART the service
    print(f"  [START] Restarting {target['description']}...")
    if ssh:
        cmd_start = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh} 'sudo systemctl start {svc}'"
    else:
        cmd_start = f"sudo systemctl start {svc}"

    ok, _, err = run_cmd(cmd_start)
    result["restart_success"] = ok

    # Wait for recovery
    time.sleep(RECOVERY_WAIT_SECONDS)

    # Verify recovery
    ok, stdout, _ = run_cmd(cmd_status)
    result["recovered"] = stdout.strip() == "active"
    print(f"  [VERIFY] Recovered: {result['recovered']}")

    return result


def main():
    print(f"=== OWL PASS CHAOS TEST ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Targets: {len(TEST_TARGETS)} services")
    print(f"Detection wait: {DETECTION_WAIT_SECONDS}s per service")
    print(f"WARNING: This will temporarily stop services. Run during maintenance only.")
    print()

    results = []
    for target in TEST_TARGETS:
        print(f"\n--- Testing: {target['description']} ({target['service']}) ---")
        result = test_service(target)
        results.append(result)

    # Summary
    print(f"\n=== CHAOS TEST RESULTS ===")
    detected_count = sum(1 for r in results if r.get("fire_guard_detected"))
    recovered_count = sum(1 for r in results if r.get("recovered"))
    skipped_count = sum(1 for r in results if r.get("skipped"))

    for r in results:
        if r.get("skipped"):
            print(f"  SKIP  {r['description']}: {r['skipped']}")
        else:
            det = "DETECTED" if r.get("fire_guard_detected") else "MISSED"
            rec = "RECOVERED" if r.get("recovered") else "FAILED"
            print(f"  {det}/{rec}  {r['description']}")

    print(f"\nDetection rate: {detected_count}/{len(results) - skipped_count}")
    print(f"Recovery rate: {recovered_count}/{len(results) - skipped_count}")

    # Store in thermal memory
    try:
        import psycopg2
        secrets = {}
        with open("/ganuda/config/secrets.env") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    secrets[k.strip()] = v.strip()

        content = f"OWL PASS CHAOS TEST: {len(TEST_TARGETS)} services tested. Detection rate: {detected_count}/{len(results)-skipped_count}. Recovery rate: {recovered_count}/{len(results)-skipped_count}. Run: {datetime.now().isoformat()}"
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

        conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                user="claude", password=secrets.get("CHEROKEE_DB_PASS", ""))
        cur = conn.cursor()
        cur.execute("""INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
            VALUES (%s, 80, false, %s, 'chaos_test', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (content, memory_hash,
             ["chaos_test", "owl_pass", "coyote", "fire_guard"],
             json.dumps({"results": results, "detection_rate": f"{detected_count}/{len(results)-skipped_count}"})))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  (thermal store failed: {e})")


if __name__ == "__main__":
    main()