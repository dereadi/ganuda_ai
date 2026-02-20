# JR-MOLTBOOK-OUTPUT-FILTER-HARDENING-FEB03-2026

## Harden Output Filter with Proprietary Technology Patterns

| Field          | Value                                          |
|----------------|------------------------------------------------|
| Task ID        | MOLTBOOK-FILTER-HARDEN-001                     |
| Priority       | P1 — Sacred Fire                               |
| Assigned To    | Software Engineer Jr.                          |
| Target Node    | redfin (192.168.132.223)                       |
| Status         | Ready for execution                            |
| Depends On     | Council approval of content sharing policy      |

---

## Context

The current output filter (`/ganuda/services/moltbook_proxy/output_filter.py`) catches infrastructure details (IPs, hostnames, credentials, paths) but does NOT catch proprietary technology names, infrastructure scale details, or exact data volumes. These represent significant OPSEC gaps.

---

## Step 1: Add Proprietary Technology Patterns

```bash
python3 << 'PYEOF'
target = '/ganuda/services/moltbook_proxy/output_filter.py'

with open(target, 'r') as f:
    content = f.read()

# Add new patterns after the existing BLOCKED_PATTERNS list
old_marker = "    # Environment variable patterns\n    re.compile(r'os\\.environ\\['),\n    re.compile(r'PGPASSWORD='),\n]"

new_block = """    # Environment variable patterns
    re.compile(r'os\\.environ\\['),
    re.compile(r'PGPASSWORD='),

    # Proprietary technology names
    re.compile(r'thermal.memor', re.IGNORECASE),
    re.compile(r'fractal.stigmergic', re.IGNORECASE),
    re.compile(r'pheromone.decay', re.IGNORECASE),
    re.compile(r'drift.mitigation', re.IGNORECASE),
    re.compile(r'\\bmagrpo\\b', re.IGNORECASE),
    re.compile(r'sacred.fire.priority', re.IGNORECASE),
    re.compile(r'smart.?extract', re.IGNORECASE),
    re.compile(r'jr.executor', re.IGNORECASE),
    re.compile(r'task.queue.architect', re.IGNORECASE),

    # Infrastructure scale (exact numbers)
    re.compile(r'\\b6.node\\b', re.IGNORECASE),
    re.compile(r'\\b7.specialist\\b', re.IGNORECASE),
    re.compile(r'19,?808', re.IGNORECASE),
    re.compile(r'\\b96.?GB\\b', re.IGNORECASE),
    re.compile(r'\\bblackwell\\b', re.IGNORECASE),

    # Specialist names in architecture context
    re.compile(r'\\b(crawdad|gecko|turtle|eagle.eye|spider|peace.chief|raven)\\b.*\\b(specialist|council|vote)\\b', re.IGNORECASE),

    # Personnel
    re.compile(r'\\bdereadi\\b', re.IGNORECASE),
    re.compile(r'\\bPatoGravy\\b', re.IGNORECASE),
    re.compile(r'\\bDarrell\\b', re.IGNORECASE),
]"""

if old_marker in content:
    content = content.replace(old_marker, new_block)
    with open(target, 'w') as f:
        f.write(content)
    print("SUCCESS: Output filter hardened with proprietary tech patterns")
else:
    print("ERROR: Could not find marker in output_filter.py — manual edit needed")
    exit(1)
PYEOF
```

## Step 2: Add Model Names to SENSITIVE_TERMS

```bash
python3 << 'PYEOF'
target = '/ganuda/services/moltbook_proxy/output_filter.py'

with open(target, 'r') as f:
    content = f.read()

old_terms = """SENSITIVE_TERMS = {
    'psycopg2': 'database library',
    'vllm': 'inference engine',
    'qwen': 'model name',
    'nemotron': 'model name',
}"""

new_terms = """SENSITIVE_TERMS = {
    'psycopg2': 'database library',
    'vllm': 'inference engine',
    'qwen': 'model name',
    'nemotron': 'model name',
    'medgemma': 'model name',
    'blackwell': 'hardware name',
    'systemd': 'infrastructure detail',
    'postgresql': 'database name',
    'grafana': 'monitoring tool',
    'promtail': 'monitoring tool',
    'openobserve': 'monitoring tool',
}"""

if old_terms in content:
    content = content.replace(old_terms, new_terms)
    with open(target, 'w') as f:
        f.write(content)
    print("SUCCESS: SENSITIVE_TERMS expanded")
else:
    print("ERROR: Could not find SENSITIVE_TERMS block — manual edit needed")
    exit(1)
PYEOF
```

## Step 3: Verify

```bash
python3 -c "import ast; ast.parse(open('/ganuda/services/moltbook_proxy/output_filter.py').read())" && echo "SYNTAX OK"
python3 -c "
from output_filter import validate_outbound
# Test proprietary tech detection
tests = [
    ('We use thermal memory systems', False),
    ('Our 6-node cluster runs great', False),
    ('We have 19808 memories', False),
    ('We remember things over time', True),
    ('We run on our own hardware', True),
    ('Crawdad is our security specialist who votes', False),
    ('We make decisions together', True),
]
for text, expected_safe in tests:
    safe, violations = validate_outbound(text)
    status = 'PASS' if safe == expected_safe else 'FAIL'
    print(f'{status}: \"{text[:50]}\" -> safe={safe} (expected {expected_safe})')
"
```

---

## Security Checklist

- [ ] No new external connections
- [ ] All new patterns use re.IGNORECASE
- [ ] Syntax check passes
- [ ] Test cases cover all new patterns
- [ ] Original filter patterns preserved (no deletions)
