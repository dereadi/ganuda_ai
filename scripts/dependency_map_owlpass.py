#!/usr/bin/env python3
"""Owl Pass Dependency Map — Federation service dependency graph.

Spider: "We need to see the web before we can protect it."
Council vote PROCEED. Longhouse open floor request.

Queries each node's services, builds directed dependency graph,
stores as thermal memory and writes JSON report.
"""
import subprocess
import json
import hashlib
from datetime import datetime

# Known service dependencies (directed: service -> depends_on)
# Format: (node, service) -> [(dep_node, dep_service_or_port, dep_type)]
DEPENDENCY_GRAPH = {
    # --- REDFIN ---
    ("redfin", "llm-gateway.service"): [
        ("redfin", "vllm.service", "inference_backend"),
        ("bluefin", "postgresql:5432", "database"),
        ("bmasass", "mlx-qwen3:8800", "inference_backend"),
        ("bmasass", "mlx-llama:8801", "inference_backend"),
        ("greenfin", "embedding:8003", "rag_search"),
    ],
    ("redfin", "vllm.service"): [
        ("redfin", "gpu:rtx-pro-6000", "hardware"),
    ],
    ("redfin", "sag.service"): [
        ("bluefin", "postgresql:5432", "database"),
        ("redfin", "llm-gateway.service", "api"),
    ],
    ("redfin", "jr-se.service"): [
        ("bluefin", "postgresql:5432", "database"),
        ("redfin", "llm-gateway.service", "api"),
    ],
    ("redfin", "fire-guard.timer"): [
        ("bluefin", "postgresql:5432", "database"),
        ("redfin", "vllm.service", "health_check"),
        ("bluefin", "vlm:8090", "health_check"),
        ("greenfin", "embedding:8003", "health_check"),
        ("owlfin", "caddy:80", "health_check"),
        ("eaglefin", "caddy:80", "health_check"),
        ("bmasass", "mlx-qwen3:8800", "health_check"),
        ("bmasass", "mlx-llama:8801", "health_check"),
    ],
    # --- BLUEFIN ---
    ("bluefin", "postgresql:5432"): [],  # root dependency — nothing above it
    ("bluefin", "vlm-bluefin.service"): [
        ("bluefin", "gpu:rtx-5070", "hardware"),
    ],
    ("bluefin", "vlm-adapter.service"): [
        ("bluefin", "vlm-bluefin.service", "inference_backend"),
    ],
    ("bluefin", "yolo-world.service"): [
        ("bluefin", "gpu:rtx-5070", "hardware"),
    ],
    ("bluefin", "optic-nerve.service"): [
        ("bluefin", "vlm-adapter.service", "vision_api"),
        ("bluefin", "yolo-world.service", "detection_api"),
    ],
    # --- GREENFIN ---
    ("greenfin", "cherokee-embedding.service"): [
        ("greenfin", "gpu:cpu-only", "hardware"),
    ],
    ("greenfin", "openobserve"): [],  # standalone
    # --- DMZ ---
    ("owlfin", "caddy"): [
        ("owlfin", "keepalived", "failover"),
        ("bluefin", "postgresql:5432", "web_content"),
    ],
    ("eaglefin", "caddy"): [
        ("eaglefin", "keepalived", "failover"),
        ("bluefin", "postgresql:5432", "web_content"),
    ],
    # --- BMASASS ---
    ("bmasass", "mlx-qwen3:8800"): [
        ("bmasass", "unified-memory:128gb", "hardware"),
    ],
    ("bmasass", "mlx-llama:8801"): [
        ("bmasass", "unified-memory:128gb", "hardware"),
    ],
}

# Nodes to verify reachability
NODES = {
    "redfin": {"ip": "192.168.132.223", "wg": "10.100.0.1"},
    "bluefin": {"ip": "192.168.132.222", "wg": "10.100.0.2"},
    "greenfin": {"ip": "192.168.132.224", "wg": "10.100.0.3"},
    "owlfin": {"ip": "192.168.132.170", "wg": "10.100.0.5"},
    "eaglefin": {"ip": "192.168.132.84", "wg": "10.100.0.6"},
    "bmasass": {"ip": "100.103.27.106", "wg": None},
}


def check_node_reachable(node_name, config):
    """Ping node, try WireGuard first if available."""
    for label, ip in [("wg", config.get("wg")), ("lan", config.get("ip"))]:
        if not ip:
            continue
        try:
            result = subprocess.run(
                f"ping -c 1 -W 3 {ip}",
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, label, ip
        except subprocess.TimeoutExpired:
            continue
    return False, None, None


def compute_impact(service_key):
    """Find all services that depend on this service (reverse lookup)."""
    dependents = []
    for svc, deps in DEPENDENCY_GRAPH.items():
        for dep_node, dep_svc, dep_type in deps:
            if (dep_node, dep_svc) == service_key or dep_svc == service_key[1]:
                dependents.append({"node": svc[0], "service": svc[1], "dep_type": dep_type})
    return dependents


def main():
    print(f"=== OWL PASS DEPENDENCY MAP ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Phase 1: Node reachability
    print("--- Node Reachability ---")
    node_status = {}
    for node_name, config in NODES.items():
        reachable, via, ip = check_node_reachable(node_name, config)
        node_status[node_name] = {"reachable": reachable, "via": via, "ip": ip}
        status = f"UP ({via} {ip})" if reachable else "UNREACHABLE"
        print(f"  {node_name}: {status}")

    # Phase 2: Dependency graph summary
    print(f"\n--- Dependency Graph ({len(DEPENDENCY_GRAPH)} services) ---")
    root_services = []
    leaf_services = []
    all_deps = set()

    for svc, deps in DEPENDENCY_GRAPH.items():
        if not deps:
            root_services.append(svc)
        all_deps.update((d[0], d[1]) for d in deps)

    for svc in DEPENDENCY_GRAPH:
        if svc not in all_deps:
            leaf_services.append(svc)

    print(f"  Root services (no dependencies): {len(root_services)}")
    for r in root_services:
        print(f"    {r[0]}:{r[1]}")

    print(f"  Leaf services (nothing depends on them): {len(leaf_services)}")
    for l in leaf_services:
        print(f"    {l[0]}:{l[1]}")

    # Phase 3: Critical path analysis (most dependents)
    print(f"\n--- Impact Analysis (services with most dependents) ---")
    impact_scores = {}
    for svc in DEPENDENCY_GRAPH:
        dependents = compute_impact(svc)
        if dependents:
            impact_scores[svc] = dependents

    sorted_impact = sorted(impact_scores.items(), key=lambda x: len(x[1]), reverse=True)
    for svc, dependents in sorted_impact[:10]:
        print(f"  {svc[0]}:{svc[1]} — {len(dependents)} dependent(s)")
        for d in dependents:
            print(f"    <- {d['node']}:{d['service']} ({d['dep_type']})")

    # Phase 4: Single points of failure
    print(f"\n--- Single Points of Failure ---")
    spofs = []
    for svc, dependents in sorted_impact:
        if len(dependents) >= 3:
            spofs.append({"node": svc[0], "service": svc[1], "dependent_count": len(dependents)})
            print(f"  SPOF: {svc[0]}:{svc[1]} ({len(dependents)} dependents)")

    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "node_status": node_status,
        "service_count": len(DEPENDENCY_GRAPH),
        "root_services": [{"node": s[0], "service": s[1]} for s in root_services],
        "leaf_services": [{"node": s[0], "service": s[1]} for s in leaf_services],
        "spofs": spofs,
        "impact_ranking": [
            {"node": s[0], "service": s[1], "dependent_count": len(d)}
            for s, d in sorted_impact[:10]
        ],
        "graph": {
            f"{k[0]}:{k[1]}": [{"node": d[0], "service": d[1], "type": d[2]} for d in v]
            for k, v in DEPENDENCY_GRAPH.items()
        },
    }

    # Write JSON report
    report_path = "/ganuda/reports/dependency_map_owlpass.json"
    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to {report_path}")
    except Exception as e:
        print(f"\n(report write failed: {e})")

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

        content = f"OWL PASS DEPENDENCY MAP: {len(DEPENDENCY_GRAPH)} services mapped. {len(spofs)} SPOFs identified. Nodes: {sum(1 for n in node_status.values() if n['reachable'])}/{len(NODES)} reachable. Run: {datetime.now().isoformat()}"
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

        conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                user="claude", password=secrets.get("CHEROKEE_DB_PASS", ""))
        cur = conn.cursor()
        cur.execute("""INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
            VALUES (%s, 75, false, %s, 'dependency_map', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (content, memory_hash,
             ["dependency_map", "owl_pass", "spider"],
             json.dumps({"spof_count": len(spofs), "service_count": len(DEPENDENCY_GRAPH)})))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  (thermal store failed: {e})")


if __name__ == "__main__":
    main()