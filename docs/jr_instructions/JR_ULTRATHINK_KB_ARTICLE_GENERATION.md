# Jr Ultrathink Instructions: KB Article Generation Sprint

**Task ID:** JR-KB-GENERATE-001
**Priority:** High (P2)
**Assigned Specialist:** Spider (Cultural Integration)
**Date:** 2025-12-25
**Ultrathink Analysis:** Complete

---

## ULTRATHINK ANALYSIS

### Problem Statement

The Cherokee AI Federation has accumulated significant tribal knowledge through bug fixes, architectural decisions, and operational learnings. However:

- **1,175 thermal memories** exist but only **1 KB article**
- Bug fixes are solved, then forgotten - we solve the same problems repeatedly
- Operational knowledge exists only in conversation transcripts
- New Jrs have no searchable knowledge base to consult

### Knowledge Loss Quantification

Scanning thermal memory for the past 30 days reveals these undocumented learnings:

| Issue | Resolution | KB Article Status |
|-------|------------|-------------------|
| Grafana false alerts on bluefin | Moved to remote check on redfin | KB-2025-0001 (exists) |
| TaskExecutor wrong database config | Fixed DB_HOST config | NOT DOCUMENTED |
| Hive Mind column name mismatches | Schema alignment | NOT DOCUMENTED |
| Competing it_triad_cli daemons | Killed duplicates, single worker | NOT DOCUMENTED |
| SSH key authentication failures | pg_hba.conf TCP config | NOT DOCUMENTED |
| vLLM OOM on large context | Reduced max_model_len | NOT DOCUMENTED |
| Gateway 502 errors | Increased timeout, retry logic | NOT DOCUMENTED |

**Estimated knowledge loss: 85%+ of operational learnings are not captured as KB articles.**

### Seven Generations Impact

**Without KB articles:**
- Each Jr rediscovers problems independently
- Time wasted on solved problems
- Inconsistent solutions applied
- Tribal knowledge dies with context windows

**With KB articles:**
- Searchable before asking for help
- Consistent resolution patterns
- Accelerated onboarding
- Knowledge compounds across generations

### KB Article Categories

| Type | Purpose | Priority |
|------|---------|----------|
| `bug_fix` | Document error → root cause → fix | HIGH |
| `how_to` | Step-by-step operational procedures | HIGH |
| `architecture` | Design decisions and rationale | MEDIUM |
| `troubleshooting` | Diagnostic trees for common issues | HIGH |
| `lesson_learned` | Post-incident analysis | MEDIUM |

---

## EXECUTION PLAN

### Phase 1: Mine Thermal Memory for KB Candidates

Query thermal memory for potential KB articles:

```sql
-- Find memories with error/fix patterns
SELECT id, created_at, LEFT(original_content, 200) as preview,
       keywords, tags
FROM thermal_memory_archive
WHERE (
    original_content ILIKE '%error%'
    OR original_content ILIKE '%fixed%'
    OR original_content ILIKE '%resolved%'
    OR original_content ILIKE '%root cause%'
    OR original_content ILIKE '%solution%'
)
AND 'kb_article' != ALL(COALESCE(tags, '{}'))
AND created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at DESC
LIMIT 50;
```

### Phase 2: Create Priority KB Articles

#### KB-2025-0002: TaskExecutor Database Configuration

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type bug_fix \
  --title "TaskExecutor Connecting to Wrong Database" \
  --symptoms "Tasks failing silently,Jr completions not recorded,Database connection errors to localhost" \
  --root_cause "TaskExecutor was configured with DB_HOST=localhost instead of 192.168.132.222 (bluefin). The executor ran on redfin but PostgreSQL lives on bluefin." \
  --resolution "Updated environment variable DB_HOST=192.168.132.222 in systemd unit file and restarted service. Verified with: psql -h 192.168.132.222 -U claude -d zammad_production -c 'SELECT 1'" \
  --prevention "Always use explicit IP addresses for database connections. Add DB_HOST to ansible templates. Include connection test in deployment playbook." \
  --nodes redfin \
  --author jr_spider
```

#### KB-2025-0003: Competing Daemon Processes

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type bug_fix \
  --title "Multiple Competing Daemon Instances Causing Race Conditions" \
  --symptoms "Tasks marked complete in seconds without work,Duplicate task processing,Database lock contention,it_triad_cli.py spawning multiple times" \
  --root_cause "Multiple mechanisms were starting the daemon: systemd service, cron job, and manual invocation. Each instance picked up tasks and marked them complete, causing race conditions." \
  --resolution "1. Killed all running instances: pkill -f it_triad_cli.py. 2. Disabled cron job. 3. Ensured only systemd manages the service. 4. Added PID file check to prevent duplicate starts." \
  --prevention "Use systemd as ONLY daemon manager. Add Type=simple with PIDFile. Include 'pgrep -f daemon_name && exit 1' guard in scripts. Document in runbook." \
  --nodes redfin \
  --author jr_spider
```

#### KB-2025-0004: PostgreSQL Peer Authentication vs MD5

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type troubleshooting \
  --title "PostgreSQL Peer Authentication Failed for User Claude" \
  --symptoms "psql: FATAL: Peer authentication failed for user claude,Connection works from remote but not local,Socket connection rejected" \
  --root_cause "pg_hba.conf uses 'peer' authentication for local socket connections but 'md5' for TCP. When connecting via socket (/var/run/postgresql/.s.PGSQL.5432), peer auth checks Unix username. When connecting via TCP (-h 127.0.0.1), md5 password auth is used." \
  --resolution "For local connections, always specify -h 127.0.0.1 or -h localhost to force TCP connection with md5 auth. Example: PGPASSWORD=xxx psql -h 127.0.0.1 -U claude -d zammad_production" \
  --prevention "Document in runbook: always use -h flag for psql. Add alias: alias psql-claude='PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production'" \
  --nodes bluefin \
  --author jr_spider
```

#### KB-2025-0005: vLLM Out of Memory on Large Contexts

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type bug_fix \
  --title "vLLM CUDA Out of Memory on Extended Context Requests" \
  --symptoms "CUDA OOM errors,vLLM service crash,Gateway 502 errors after long conversations,GPU memory at 100%" \
  --root_cause "max_model_len was set too high for available VRAM. Nemotron-9B with 96GB VRAM can handle ~32K context but was configured for 64K. Long conversations exhausted KV cache." \
  --resolution "Reduced max_model_len to 32768 in vLLM startup command. Added --gpu-memory-utilization 0.9 to leave headroom. Implemented context window tracking in gateway to warn before OOM." \
  --prevention "Calculate max context: VRAM_GB * 1000 / model_params_B * 0.7 = rough max tokens. Monitor GPU memory via nvidia-smi. Add gateway-level context limits." \
  --nodes redfin \
  --author jr_spider
```

#### KB-2025-0006: Hive Mind Schema Column Mismatches

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type bug_fix \
  --title "Hive Mind Bidding Column Name Mismatches" \
  --symptoms "column task_id does not exist errors,Jr bids not recorded,Bidding daemon crashes on INSERT" \
  --root_cause "Python code referenced task_id but table column was named announcement_id. Schema evolved but code referenced old column names. Also: priority vs bid_priority, node_id vs agent_id mismatches." \
  --resolution "Aligned Python code to match actual schema: SELECT column_name FROM information_schema.columns WHERE table_name = 'jr_task_announcements'. Updated all column references in hive_mind_bidding.py." \
  --prevention "Always query schema before writing INSERT/SELECT. Create schema documentation. Use SQLAlchemy ORM to catch mismatches at startup. Add schema validation in CI." \
  --nodes redfin,bluefin \
  --author jr_spider
```

#### KB-2025-0007: Gateway Timeout and Retry Configuration

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type how_to \
  --title "Configuring LLM Gateway Timeouts for Long-Running Requests" \
  --symptoms "502 Bad Gateway on complex queries,Council votes timing out,Long reasoning chains failing" \
  --root_cause "Default httpx timeout of 30 seconds insufficient for complex multi-specialist council deliberations that can take 60-90 seconds." \
  --resolution "Updated gateway.py: httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)). Added retry logic with exponential backoff. Implemented streaming for long responses." \
  --prevention "Set timeouts based on p99 response times. Add monitoring for request duration. Implement circuit breaker for vLLM failures. Log slow requests for optimization." \
  --nodes redfin \
  --author jr_spider
```

### Phase 3: Create Operational How-To Articles

#### KB-2025-0008: Adding a New Node to the Federation

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type how_to \
  --title "Adding a New Node to the Cherokee AI Federation" \
  --symptoms "Need to add new hardware,Expanding compute capacity,Onboarding new device" \
  --root_cause "Standard operational procedure" \
  --resolution "1. Assign IP in 192.168.132.x range. 2. Create dereadi user with sudo. 3. Copy SSH public key. 4. Add to ansible inventory. 5. Run base_system.yml playbook. 6. Register in CMDB. 7. Add to monitoring. 8. Document in FEDERATION_NODE_MAP.md" \
  --prevention "Keep ansible inventory current. Document all nodes in CMDB. Update monitoring dashboards." \
  --nodes all \
  --author jr_spider
```

#### KB-2025-0009: Thermal Memory Search Patterns

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type how_to \
  --title "Effective Thermal Memory Search Patterns" \
  --symptoms "Need to find relevant memories,Context retrieval for Jr tasks,Knowledge lookup" \
  --root_cause "Operational knowledge" \
  --resolution "Key queries: 1. By recency: ORDER BY created_at DESC. 2. By temperature: ORDER BY temperature_score DESC. 3. By keywords: WHERE keywords && ARRAY['term']. 4. By tags: WHERE 'tag' = ANY(tags). 5. Full text: WHERE original_content ILIKE '%term%'. 6. By metadata: WHERE metadata->>'key' = 'value'" \
  --prevention "Use tags consistently. Keep keywords array populated. Update temperature scores on access." \
  --nodes bluefin \
  --author jr_spider
```

### Phase 4: Create Architecture Decision Records

#### KB-2025-0010: Why Thermal Memory Over Traditional Vector DB

```bash
python3 /ganuda/scripts/create_kb_article.py \
  --type architecture \
  --title "Architecture Decision: Thermal Memory vs Traditional Vector Database" \
  --symptoms "Why not use Pinecone/Weaviate/Chroma? Why PostgreSQL with pgvector?" \
  --root_cause "Architectural decision record" \
  --resolution "Decision: PostgreSQL with thermal decay over specialized vector DB. Rationale: 1. Single database reduces operational complexity. 2. Thermal decay (temperature_score) models human memory forgetting curve. 3. Stigmergic patterns require mutable scores, not just similarity. 4. ACID transactions for council votes. 5. Already running Zammad on PostgreSQL. Trade-offs: Slightly slower vector search, but benefits outweigh for our use case." \
  --prevention "Document all architectural decisions as ADRs. Review annually. Consider migration paths." \
  --nodes bluefin \
  --author jr_spider
```

---

## AUTOMATED KB ARTICLE DETECTION

Create `/ganuda/lib/kb_candidate_detector.py`:

```python
#!/usr/bin/env python3
"""
Scan thermal memory for potential KB article candidates.
Identifies error patterns, fix patterns, and learning moments.
"""

import psycopg2
import json
import re
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Patterns that suggest KB-worthy content
KB_PATTERNS = [
    (r'error.*fixed', 'bug_fix'),
    (r'root cause.*was', 'bug_fix'),
    (r'solution.*implemented', 'bug_fix'),
    (r'resolved by', 'bug_fix'),
    (r'how to', 'how_to'),
    (r'step \d+', 'how_to'),
    (r'procedure for', 'how_to'),
    (r'decided to use', 'architecture'),
    (r'chose.*because', 'architecture'),
    (r'lesson learned', 'lesson_learned'),
    (r'next time.*should', 'lesson_learned'),
    (r'troubleshoot', 'troubleshooting'),
    (r'diagnose', 'troubleshooting'),
]

def find_kb_candidates(days_back=7):
    """Find memories that should become KB articles."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get recent memories not already tagged as KB
    cur.execute("""
        SELECT id, original_content, tags, created_at
        FROM thermal_memory_archive
        WHERE created_at >= NOW() - INTERVAL '%s days'
        AND 'kb_article' != ALL(COALESCE(tags, '{}'))
        ORDER BY created_at DESC
    """, (days_back,))

    candidates = []
    for id, content, tags, created_at in cur.fetchall():
        content_lower = content.lower()
        for pattern, kb_type in KB_PATTERNS:
            if re.search(pattern, content_lower):
                candidates.append({
                    'memory_id': id,
                    'suggested_type': kb_type,
                    'pattern_matched': pattern,
                    'preview': content[:300],
                    'created_at': str(created_at)
                })
                break  # One match per memory

    conn.close()
    return candidates

def main():
    candidates = find_kb_candidates(days_back=30)

    print(f"\n{'='*60}")
    print(f"KB Article Candidates Found: {len(candidates)}")
    print('='*60)

    for c in candidates:
        print(f"\n[Memory #{c['memory_id']}] Type: {c['suggested_type']}")
        print(f"Pattern: {c['pattern_matched']}")
        print(f"Preview: {c['preview'][:200]}...")
        print('-'*40)

    # Output JSON for automated processing
    with open('/ganuda/logs/kb_candidates.json', 'w') as f:
        json.dump(candidates, f, indent=2)
    print(f"\nFull list saved to /ganuda/logs/kb_candidates.json")

if __name__ == '__main__':
    main()
```

---

## VALIDATION STEPS

```bash
# 1. Verify KB articles created
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production -c \"SELECT metadata->>'kb_id', metadata->>'kb_type', LEFT(original_content, 60) FROM thermal_memory_archive WHERE 'kb_article' = ANY(tags) ORDER BY metadata->>'kb_id';\""

# 2. Test search functionality
ssh dereadi@192.168.132.222 "cd /ganuda/scripts && python3 search_kb.py 'database'"

# 3. Run candidate detector
ssh dereadi@192.168.132.222 "cd /ganuda/lib && python3 kb_candidate_detector.py"
```

---

## ACCEPTANCE CRITERIA

1. [ ] KB-2025-0002 through KB-2025-0010 created (9 new articles)
2. [ ] Total KB article count >= 10
3. [ ] `kb_candidate_detector.py` deployed and tested
4. [ ] Search functionality verified working
5. [ ] At least one `bug_fix`, `how_to`, and `architecture` article exists
6. [ ] Articles reference affected nodes correctly
7. [ ] All articles have proper symptoms/root_cause/resolution structure

---

## DEPENDENCIES

- `create_kb_article.py` already deployed (verified working)
- `search_kb.py` already deployed
- PostgreSQL access to bluefin

---

## ESTIMATED COMPLEXITY

Medium - Mostly executing create_kb_article.py with proper parameters. Candidate detector is new code.

---

*For Seven Generations - Cherokee AI Federation*
