"""Chain Protocol ring: dispatch node_onboard.sh across federation nodes.

Node Onboard ring — Associate ring (permanent, not task-scoped).
Runs node_onboard.sh on target nodes, verifies results, thermalizes.

Usage:
    from onboard_dispatch import onboard_user
    results = onboard_user("jsdorn")

Council Vote: NODE-ONBOARD-001
"""

import subprocess
import json
import psycopg2
import hashlib
from datetime import datetime

from lib.secrets_loader import get_db_config

DB_CONFIG = get_db_config()

# Nodes with /ganuda that need onboarding (WireGuard IPs — reliable)
TARGET_NODES = {
    "redfin": "localhost",
    "bluefin": "10.100.0.2",
    "greenfin": "10.100.0.3",
}

ONBOARD_SCRIPT = "/ganuda/scripts/node_onboard.sh"


def preflight_freeipa(username: str) -> dict:
    """Check FreeIPA state for user via greenfin (jump host to silverfin).

    Returns dict with check results. Does NOT fix issues — just reports.
    """
    checks = {
        "user_exists": False,
        "in_ganuda_dev": False,
        "sudo_rule": False,
        "errors": [],
    }

    # Run checks via SSH to greenfin → silverfin
    freeipa_cmds = [
        ("user_exists", f"ssh -o ConnectTimeout=10 10.100.0.3 'ssh silverfin ipa user-show {username} 2>/dev/null'"),
        ("in_ganuda_dev", f"ssh -o ConnectTimeout=10 10.100.0.3 'ssh silverfin ipa group-show ganuda-dev 2>/dev/null' | grep -q {username}"),
    ]

    for check_name, cmd in freeipa_cmds:
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            checks[check_name] = proc.returncode == 0
        except Exception as e:
            checks["errors"].append(f"{check_name}: {str(e)[:100]}")

    return checks


def onboard_user(username: str, nodes: dict = None, skip_preflight: bool = False) -> dict:
    """Dispatch node_onboard.sh to all target nodes for a user.

    Returns dict of {node_name: {status, output, returncode}}.
    """
    targets = nodes or TARGET_NODES
    results = {}

    # FreeIPA pre-flight (optional but recommended)
    preflight = None
    if not skip_preflight:
        try:
            preflight = preflight_freeipa(username)
            if not preflight["user_exists"]:
                return {
                    "username": username,
                    "timestamp": datetime.now().isoformat(),
                    "nodes": {},
                    "all_ok": False,
                    "preflight": preflight,
                    "error": f"User {username} not found in FreeIPA. Create with 'ipa user-add' first.",
                }
        except Exception as e:
            preflight = {"error": str(e), "skipped": True}

    # Dispatch to each node
    for node_name, host in targets.items():
        if host == "localhost":
            cmd = ["sudo", ONBOARD_SCRIPT, username]
        else:
            cmd = [
                "ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", host,
                f"sudo {ONBOARD_SCRIPT} {username}"
            ]

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            results[node_name] = {
                "status": "ok" if proc.returncode == 0 else "error",
                "output": proc.stdout[-500:] if proc.stdout else "",
                "stderr": proc.stderr[-200:] if proc.stderr else "",
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            results[node_name] = {
                "status": "timeout",
                "output": "",
                "returncode": -1,
            }
        except Exception as e:
            results[node_name] = {
                "status": "error",
                "output": str(e),
                "returncode": -1,
            }

    result = {
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "nodes": results,
        "all_ok": all(r["status"] == "ok" for r in results.values()),
    }
    if preflight:
        result["preflight"] = preflight

    # Thermalize
    _thermalize_onboard(result)

    return result


def _thermalize_onboard(result: dict):
    """Store onboard result in thermal memory."""
    username = result["username"]
    node_summary = " | ".join(
        f"{n}: {'ok' if r['status'] == 'ok' else r['status']}"
        for n, r in result["nodes"].items()
    )

    content = (
        f"Chain Protocol onboard: {username}\n"
        f"Nodes: {node_summary}\n"
        f"All OK: {result['all_ok']}\n"
        f"Timestamp: {result['timestamp']}"
    )

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        memory_hash = hashlib.sha256(
            f"onboard-{username}-{result['timestamp']}".encode()
        ).hexdigest()
        cur.execute(
            "INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash, metadata) "
            "VALUES (%s, %s, %s, false, %s, %s)",
            (content, 55, "infrastructure", memory_hash,
             json.dumps({"type": "node_onboard", "username": username,
                         "all_ok": result["all_ok"], "nodes": list(result["nodes"].keys())}))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ONBOARD] Thermalization failed: {e}")
