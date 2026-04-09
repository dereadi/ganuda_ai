#!/usr/bin/env python3
"""
DC-19: Context Reload Protocol — Situational Awareness Brief

Run this at the start of EVERY new conversation to know what's running,
what's healthy, and what's changed. Don't fumble through SSH to rediscover
what should be known.

Usage:
    python3 /ganuda/scripts/context_reload.py
    python3 /ganuda/scripts/context_reload.py --domain hardware
    python3 /ganuda/scripts/context_reload.py --brief  (< 500 words summary)

Partner's insight: "I rely on my eyes and the placement of things."
This script is the TPM's eyes.

For Seven Generations.
"""

import subprocess
import json
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')

NODES = {
    "redfin": {"ip": "127.0.0.1", "wg": "10.100.0.1", "role": "Brain — main inference, TPM, Jr SE"},
    "bluefin": {"ip": "10.100.0.2", "wg": "10.100.0.2", "role": "Eyes — VLM, PostgreSQL, PgBouncer, Infra Jr"},
    "greenfin": {"ip": "10.100.0.3", "wg": "10.100.0.3", "role": "Reflex — BitNet ternary, Cherokee 8B"},
    "bmasass": {"ip": "192.168.132.21", "wg": None, "role": "Second brain — Llama 70B, Qwen3 30B, DERsnTt² substrate B"},
    "owlfin": {"ip": "10.100.0.5", "wg": "10.100.0.5", "role": "Validation — Owl checks, Caddy DMZ"},
    "eaglefin": {"ip": "10.100.0.6", "wg": "10.100.0.6", "role": "DMZ — Caddy reverse proxy"},
}


def run_ssh(host, cmd, timeout=10):
    """Run command on remote host, return stdout or error string."""
    try:
        if host == "127.0.0.1":
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        else:
            r = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                 f"dereadi@{host}", cmd],
                capture_output=True, text=True, timeout=timeout
            )
        return r.stdout.strip() if r.returncode == 0 else f"[ERROR: {r.stderr.strip()[:100]}]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[FAIL: {e}]"


def gecko_hardware():
    """GECKO DOMAIN: Hardware inventory across all nodes."""
    print("=== GECKO: Hardware Inventory ===")
    results = {}

    for name, node in NODES.items():
        ip = node["ip"]
        print(f"\n  [{name}] ({ip}) — {node['role']}")

        # GPU
        gpu = run_ssh(ip, "nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu --format=csv,noheader 2>/dev/null || echo 'No NVIDIA GPU'")
        if "No NVIDIA" not in gpu and "ERROR" not in gpu and "TIMEOUT" not in gpu:
            for line in gpu.split('\n'):
                print(f"    GPU: {line.strip()}")
        else:
            # Check for Apple Silicon
            apple = run_ssh(ip, "sysctl -n machdep.cpu.brand_string 2>/dev/null || echo ''")
            if apple and "ERROR" not in apple:
                ram = run_ssh(ip, "sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1024/1024/1024}' 2>/dev/null || echo '?'")
                print(f"    Apple: {apple.strip()}, {ram.strip()} GB RAM")
            else:
                cpu = run_ssh(ip, "cat /proc/cpuinfo 2>/dev/null | grep 'model name' | head -1 | cut -d: -f2 || echo 'unknown'")
                ram = run_ssh(ip, "free -g 2>/dev/null | grep Mem | awk '{print $2}' || echo '?'")
                print(f"    CPU:{cpu.strip()}, {ram.strip()} GB RAM")
                print(f"    GPU: None")

        # GPU processes
        gpu_procs = run_ssh(ip, "nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv,noheader 2>/dev/null")
        if gpu_procs and "ERROR" not in gpu_procs and "TIMEOUT" not in gpu_procs and gpu_procs.strip():
            for line in gpu_procs.split('\n'):
                if line.strip():
                    print(f"    GPU proc: {line.strip()}")

        results[name] = {"gpu": gpu, "role": node["role"]}

    return results


def spider_services():
    """SPIDER DOMAIN: Service topology — what's running, ports, dependencies."""
    print("\n=== SPIDER: Service Topology ===")

    for name, node in NODES.items():
        ip = node["ip"]
        print(f"\n  [{name}]")

        # Key services
        services = run_ssh(ip,
            "systemctl list-units --type=service --state=active 2>/dev/null | "
            "grep -iE 'vllm|ollama|llm|shield|canary|medicine|fire.guard|jr|ganuda|pgbouncer|postgresql|caddy|bitnet|vlm|consultation|heartbeat|telegram|embedding' "
            "| awk '{print $1, $3}' || echo 'no systemd'")
        if services and "ERROR" not in services:
            for line in services.split('\n'):
                if line.strip():
                    print(f"    {line.strip()}")

        # Key ports (inference, DB, web)
        ports = run_ssh(ip,
            "ss -tlnp 2>/dev/null | grep -E ':8000|:8080|:8090|:8100|:8101|:8800|:8801|:5432|:6432|:8443|:8500|:11434|:3000|:8003' "
            "| awk '{print $4}' | sort || echo ''")
        if ports and ports.strip():
            print(f"    Ports: {', '.join(ports.strip().split(chr(10)))}")


def crawdad_databases():
    """CRAWDAD DOMAIN: Database health, schemas, connections."""
    print("\n=== CRAWDAD: Database Health ===")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='10.100.0.2', port=5432,
            database='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )
        cur = conn.cursor()

        # Database list
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
        dbs = [r[0] for r in cur.fetchall()]
        print(f"  Databases ({len(dbs)}): {', '.join(dbs)}")

        # Connection count
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        conns = cur.fetchone()[0]
        print(f"  Active connections: {conns}")

        # Thermal memory count
        cur.execute("SELECT count(*), count(*) FILTER (WHERE sacred_pattern = true) FROM thermal_memory_archive")
        total, sacred = cur.fetchone()
        print(f"  Thermal memories: {total:,} ({sacred:,} sacred)")

        # Jr work queue
        cur.execute("SELECT status, count(*) FROM jr_work_queue GROUP BY status ORDER BY status")
        jr_status = {r[0]: r[1] for r in cur.fetchall()}
        print(f"  Jr queue: {dict(jr_status)}")

        # Rollback rate
        cur.execute("""
            SELECT xact_commit, xact_rollback,
                   round(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2)
            FROM pg_stat_database WHERE datname = 'zammad_production'
        """)
        commits, rollbacks, rate = cur.fetchone()
        print(f"  Rollback rate: {rate}% ({rollbacks:,} / {commits + rollbacks:,})")

        conn.close()

        # PgBouncer
        pgb = run_ssh("10.100.0.2", "systemctl is-active pgbouncer 2>/dev/null")
        print(f"  PgBouncer: {pgb}")

    except Exception as e:
        print(f"  DB connection failed: {e}")


def eagle_eye_health():
    """EAGLE EYE DOMAIN: Recent failures, alerts, open issues."""
    print("\n=== EAGLE EYE: Health & Recent Issues ===")

    # Fire Guard recent
    fg = run_ssh("127.0.0.1",
        "journalctl -u fire-guard.service --since '1 hour ago' --no-pager 2>/dev/null | tail -3")
    if fg:
        for line in fg.split('\n'):
            if line.strip():
                print(f"  Fire Guard: {line.strip()[-80:]}")

    # Medicine Woman
    mw = run_ssh("127.0.0.1",
        "journalctl -u medicine-woman.service --since '30 min ago' --no-pager 2>/dev/null | grep -E 'phi=|health=' | tail -1")
    if mw:
        print(f"  Medicine Woman: {mw.strip()[-100:]}")

    # Dawn mist last run
    dm = run_ssh("127.0.0.1",
        "journalctl -u council-dawn-mist.service --no-pager 2>/dev/null | grep 'DAWN MIST' | tail -1")
    if dm:
        print(f"  Dawn Mist: {dm.strip()[-100:]}")

    # Jr executor status
    jr = run_ssh("127.0.0.1", "systemctl is-active jr-se.service 2>/dev/null")
    print(f"  Jr SE (redfin): {jr}")

    jr_bf = run_ssh("10.100.0.2",
        "ps aux | grep jr_task_executor | grep -v grep | head -1 | awk '{print $11, $12, $13}' 2>/dev/null")
    print(f"  Jr Infra (bluefin): {'running' if jr_bf and 'Jr' in jr_bf else 'unknown'} {jr_bf[:60] if jr_bf else ''}")

    # Any failed services
    failed = run_ssh("127.0.0.1",
        "systemctl list-units --type=service --state=failed 2>/dev/null | grep failed | head -5")
    if failed and failed.strip():
        print(f"  FAILED services: {failed.strip()}")
    else:
        print(f"  Failed services: none")


def raven_roadmap():
    """RAVEN DOMAIN: Current sprint state, what's in flight."""
    print("\n=== RAVEN: Roadmap State ===")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host='10.100.0.2', port=5432,
            database='triad_federation',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )
        cur = conn.cursor()

        # Kanban summary
        cur.execute("""
            SELECT status, count(*) FROM kanban_tasks
            GROUP BY status ORDER BY count(*) DESC
        """)
        kanban = {r[0]: r[1] for r in cur.fetchall()}
        print(f"  Kanban: {dict(kanban)}")

        # Recent kanban activity
        cur.execute("""
            SELECT title, status, updated_at FROM kanban_tasks
            ORDER BY updated_at DESC LIMIT 3
        """)
        for r in cur.fetchall():
            print(f"  Recent: [{r[1]}] {r[0][:60]} ({str(r[2])[:10]})")

        conn.close()
    except Exception as e:
        print(f"  Kanban query failed: {e}")

    # Recent council votes
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='10.100.0.2', port=5432,
            database='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT LEFT(original_content, 120), created_at
            FROM thermal_memory_archive
            WHERE original_content ILIKE '%%council vote%%' OR original_content ILIKE '%%DAWN MIST%%'
            ORDER BY created_at DESC LIMIT 3
        """)
        for r in cur.fetchall():
            print(f"  Thermal: {r[0][:80]}... ({str(r[1])[:10]})")
        conn.close()
    except Exception:
        pass


def turtle_constraints():
    """TURTLE DOMAIN: Active design constraints."""
    print("\n=== TURTLE: Design Constraints ===")

    # Read from memory files
    memory_dir = "/home/dereadi/.claude/projects/-ganuda/memory"
    dcs = []
    try:
        for f in sorted(os.listdir(memory_dir)):
            if f.startswith("feedback_") and f.endswith(".md"):
                path = os.path.join(memory_dir, f)
                with open(path) as fh:
                    first_lines = fh.read(200)
                    if "DC-" in first_lines or "design constraint" in first_lines.lower():
                        # Extract the name from frontmatter
                        for line in first_lines.split('\n'):
                            if line.startswith("name:"):
                                dcs.append(line.replace("name:", "").strip())
                                break
    except Exception as e:
        print(f"  Error reading constraints: {e}")

    if dcs:
        for dc in dcs:
            print(f"  • {dc}")
    else:
        print("  No DCs found in memory files (check frontmatter)")

    # Also list from known DCs
    print(f"\n  Known DCs (from session knowledge):")
    known = [
        "DC-10: Reflex Principle — greenfin BitNet for fast response",
        "DC-14: Three-Body Memory — working/episodic/valence",
        "DC-15: Model Agnosticism — governance works on ANY LLM",
        "DC-16: Institutional Memory as Moat — code open, experience sovereign",
        "DC-17: Stochastic Governance — Coyote = error correction",
        "DC-18: Jr Path Anchoring — all paths must root in /ganuda/ tree",
        "DC-19: Context Reload Protocol — this script",
    ]
    for dc in known:
        print(f"  • {dc}")


def generate_brief():
    """Generate a < 500 word situational awareness brief."""
    print("\n" + "=" * 70)
    print("  SITUATIONAL AWARENESS BRIEF")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    gecko_hardware()
    spider_services()
    crawdad_databases()
    eagle_eye_health()
    raven_roadmap()
    turtle_constraints()

    print("\n" + "=" * 70)
    print("  END BRIEF — TPM is oriented.")
    print("=" * 70)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--brief" in args or not args:
        generate_brief()
    elif "--domain" in args:
        idx = args.index("--domain")
        domain = args[idx + 1] if idx + 1 < len(args) else "all"
        if domain == "hardware":
            gecko_hardware()
        elif domain == "services":
            spider_services()
        elif domain == "databases":
            crawdad_databases()
        elif domain == "health":
            eagle_eye_health()
        elif domain == "roadmap":
            raven_roadmap()
        elif domain == "constraints":
            turtle_constraints()
        else:
            generate_brief()
    else:
        generate_brief()
