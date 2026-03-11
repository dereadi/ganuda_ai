# [RECURSIVE] Owl Pass Credential Audit Fix and Scanner - Step 2

**Parent Task**: #1148
**Auto-decomposed**: 2026-03-09T10:53:55.659248
**Original Step Title**: Create cross-node credential audit script

---

### Step 2: Create cross-node credential audit script

Create `/ganuda/scripts/credential_audit_owlpass.py`

```python
#!/usr/bin/env python3
"""Owl Pass Credential Audit — Scan all federation nodes for hardcoded secrets.

Longhouse request (Crawdad). Council vote PROCEED.
Uses FreeIPA SSH to reach all nodes. WireGuard IPs for reliability.
"""
import subprocess
import json
import hashlib
import re
from datetime import datetime

NODES = {
    "redfin": {"ssh": None, "paths": ["/ganuda/"]},
    "bluefin": {"ssh": "dereadi@10.100.0.2", "paths": ["/ganuda/"]},
    "greenfin": {"ssh": "dereadi@10.100.0.3", "paths": ["/ganuda/"]},
    "owlfin": {"ssh": "dereadi@10.100.0.5", "paths": ["/etc/caddy/"]},
    "eaglefin": {"ssh": "dereadi@10.100.0.6", "paths": ["/etc/caddy/"]},
}

PATTERNS = [
    r'password\s*=\s*["\'][^"\']{8,}["\']',
    r'PASSWORD\s*=\s*["\'][^"\']{8,}["\']',
    r'api_key\s*=\s*["\'][^"\']{8,}["\']',
    r'API_KEY\s*=\s*["\'][^"\']{8,}["\']',
    r'secret\s*=\s*["\'][^"\']{8,}["\']',
    r'token\s*=\s*["\'][^"\']{8,}["\']',
]

IGNORE_PATTERNS = [
    r'secrets\.env',
    r'\.example',
    r'CLAUDE\.md',
    r'MEMORY\.md',
    r'__pycache__',
    r'\.git/',
    r'node_modules/',
    r'\.next/',
]

EXTENSIONS = "py,js,ts,yaml,yml,json,conf,cfg,ini,toml,sh,env"


def scan_node(node_name, config):
    """Scan a single node for hardcoded credentials."""
    findings = []
    ssh_prefix = config["ssh"]

    for search_path in config["paths"]:
        for pattern in PATTERNS:
            if ssh_prefix:
                cmd = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {ssh_prefix} \"grep -rnI --include='*.py' --include='*.js' --include='*.yaml' --include='*.yml' --include='*.json' --include='*.conf' --include='*.sh' -E '{pattern}' {search_path} 2>/dev/null\" 2>/dev/null"
            else:
                cmd = f"grep -rnI --include='*.py' --include='*.js' --include='*.yaml' --include='*.yml' --include='*.json' --include='*.conf' --include='*.sh' -E '{pattern}' {search_path} 2>/dev/null"

            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    if any(re.search(ignore, line) for ignore in IGNORE_PATTERNS):
                        continue
                    findings.append({"node": node_name, "match": line[:200]})
            except subprocess.TimeoutExpired:
                findings.append({"node": node_name, "match": f"TIMEOUT scanning {search_path}"})

    return findings


def main():
    print(f"=== OWL PASS CREDENTIAL AUDIT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    all_findings = []
    for node_name, config in NODES.items():
        print(f"Scanning {node_name}...")
        findings = scan_node(node_name, config)
        all_findings.extend(findings)
        print(f"  {len(findings)} potential finding(s)")

    print()
    print(f"=== TOTAL: {len(all_findings)} FINDINGS ===")
    for f in all_findings:
        print(f"  [{f['node']}] {f['match']}")

    # Store results in thermal memory
    if all_findings:
        try:
            import psycopg2
            secrets_file = {}
            with open("/ganuda/config/secrets.env") as sf:
                for line in sf:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        secrets_file[k.strip()] = v.strip()

            content = f"OWL PASS CREDENTIAL AUDIT: {len(all_findings)} finding(s) across {len(NODES)} nodes. Nodes scanned: {', '.join(NODES.keys())}. Run: {datetime.now().isoformat()}"
            memory_hash = hashlib.sha256(content.encode()).hexdigest()

            conn = psycopg2.connect(host="192.168.132.222", port=5432, dbname="zammad_production",
                                    user="claude", password=secrets_file.get("CHEROKEE_DB_PASS", ""))
            cur = conn.cursor()
            cur.execute("""INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
                VALUES (%s, 70, false, %s, 'security', %s, %s::jsonb)
                ON CONFLICT (memory_hash) DO NOTHING""",
                (content, memory_hash,
                 ["credential_audit", "owl_pass", "crawdad"],
                 json.dumps({"findings_count": len(all_findings), "nodes_scanned": list(NODES.keys())})))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"  (thermal store failed: {e})")


if __name__ == "__main__":
    main()
```

## Acceptance Criteria
- Hardcoded password in redfin VetAssist main.py replaced with env var lookup
- Credential audit script scans all 5 Linux nodes via FreeIPA SSH (WireGuard IPs)
- Findings stored in thermal memory
- Script is reusable (can be wired to a timer later)
- No credentials are printed in full — matches truncated to 200 chars
