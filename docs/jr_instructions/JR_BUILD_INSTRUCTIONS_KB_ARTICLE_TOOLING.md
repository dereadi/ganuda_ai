# Jr Build Instructions: KB Article Tooling

**Task ID:** JR-KB-TOOLING-001
**Priority:** High
**Assigned Specialist:** Spider (Cultural Integration)
**Date:** 2025-12-25

---

## Context

The Cherokee AI Federation has 1,157 memories in thermal_memory_archive but **ZERO** tagged as `kb_article`. We're accumulating tribal knowledge but not capturing it in a reusable, searchable format. This means we keep solving the same problems repeatedly.

## Objective

Build tooling and workflow so that learnings are automatically or semi-automatically converted to KB articles in thermal memory.

---

## Requirements

### 1. KB Article Schema

Create a standardized KB article structure in thermal_memory_archive:

```sql
-- Tags array must include 'kb_article'
-- Metadata jsonb should include:
{
  "kb_type": "bug_fix" | "how_to" | "architecture" | "troubleshooting" | "lesson_learned",
  "kb_id": "KB-YYYY-NNNN",  -- e.g., KB-2025-0001
  "symptoms": ["list", "of", "symptoms"],
  "root_cause": "description",
  "resolution": "what fixed it",
  "prevention": "how to prevent in future",
  "related_kb": ["KB-2025-0002"],
  "affected_nodes": ["redfin", "bluefin"],
  "created_by": "jr_name or tpm"
}
```

### 2. KB Article Creation Script

Create `/ganuda/scripts/create_kb_article.py` on redfin:

```python
#!/usr/bin/env python3
"""
Create a new KB article in thermal memory.

Usage:
  python create_kb_article.py --type bug_fix \
    --title "False task completion in Jr queue" \
    --symptoms "Tasks marked complete in seconds" \
    --root_cause "Competing it_triad_cli.py daemon" \
    --resolution "Killed competing daemons, consolidated to single worker" \
    --prevention "Check for competing workers before deploying new daemons"
"""

import argparse
import psycopg2
import hashlib
import json
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def generate_kb_id():
    """Generate next KB ID: KB-YYYY-NNNN"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    year = datetime.now().year
    cur.execute("""
        SELECT COUNT(*) FROM thermal_memory_archive
        WHERE 'kb_article' = ANY(tags)
        AND metadata->>'kb_id' LIKE %s
    """, (f'KB-{year}-%',))
    count = cur.fetchone()[0]
    conn.close()
    return f"KB-{year}-{count+1:04d}"

def create_kb_article(args):
    kb_id = generate_kb_id()

    content = f"""# {args.title}

**KB ID:** {kb_id}
**Type:** {args.type}
**Created:** {datetime.now().isoformat()}

## Symptoms
{args.symptoms}

## Root Cause
{args.root_cause}

## Resolution
{args.resolution}

## Prevention
{args.prevention}
"""

    metadata = {
        "kb_type": args.type,
        "kb_id": kb_id,
        "symptoms": args.symptoms.split(',') if ',' in args.symptoms else [args.symptoms],
        "root_cause": args.root_cause,
        "resolution": args.resolution,
        "prevention": args.prevention,
        "affected_nodes": args.nodes.split(',') if args.nodes else [],
        "created_by": args.author or "jr"
    }

    memory_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, current_stage, temperature_score,
         created_at, tags, metadata, keywords)
        VALUES (%s, %s, 'hot', 0.9, NOW(),
                ARRAY['kb_article', %s], %s, %s)
        RETURNING id
    """, (
        memory_hash,
        content,
        args.type,
        json.dumps(metadata),
        args.title.lower().split()
    ))
    article_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    print(f"Created KB article: {kb_id} (ID: {article_id})")
    return kb_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create KB article')
    parser.add_argument('--type', required=True,
                        choices=['bug_fix', 'how_to', 'architecture', 'troubleshooting', 'lesson_learned'])
    parser.add_argument('--title', required=True)
    parser.add_argument('--symptoms', required=True)
    parser.add_argument('--root_cause', required=True)
    parser.add_argument('--resolution', required=True)
    parser.add_argument('--prevention', default='')
    parser.add_argument('--nodes', default='')
    parser.add_argument('--author', default='jr')

    args = parser.parse_args()
    create_kb_article(args)
```

### 3. KB Search Script

Create `/ganuda/scripts/search_kb.py`:

```python
#!/usr/bin/env python3
"""
Search KB articles by symptoms or keywords.

Usage:
  python search_kb.py "task completion"
  python search_kb.py --symptoms "tasks marked complete"
"""

import argparse
import psycopg2
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def search_kb(query, symptoms_only=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    if symptoms_only:
        cur.execute("""
            SELECT metadata->>'kb_id',
                   metadata->>'kb_type',
                   original_content,
                   temperature_score
            FROM thermal_memory_archive
            WHERE 'kb_article' = ANY(tags)
            AND (
                metadata->>'symptoms' ILIKE %s
                OR metadata->>'root_cause' ILIKE %s
            )
            ORDER BY temperature_score DESC
            LIMIT 10
        """, (f'%{query}%', f'%{query}%'))
    else:
        cur.execute("""
            SELECT metadata->>'kb_id',
                   metadata->>'kb_type',
                   original_content,
                   temperature_score
            FROM thermal_memory_archive
            WHERE 'kb_article' = ANY(tags)
            AND original_content ILIKE %s
            ORDER BY temperature_score DESC
            LIMIT 10
        """, (f'%{query}%',))

    results = cur.fetchall()
    conn.close()

    for kb_id, kb_type, content, score in results:
        print(f"\n{'='*60}")
        print(f"[{kb_id}] ({kb_type}) - Score: {score:.2f}")
        print('='*60)
        # Print first 500 chars of content
        print(content[:500] + '...' if len(content) > 500 else content)

    if not results:
        print("No KB articles found matching query.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search KB articles')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--symptoms', action='store_true',
                        help='Search only in symptoms and root cause')

    args = parser.parse_args()
    search_kb(args.query, args.symptoms)
```

### 4. Automatic KB Creation Hook

Create `/ganuda/lib/kb_auto_creator.py` that listens for:
- Tasks with `error` or `fix` tags in thermal_memory
- Jr completions that include "resolved", "fixed", "solution"

This should propose KB articles to the TPM for approval before creating.

---

## Acceptance Criteria

1. [ ] `create_kb_article.py` script deployed to `/ganuda/scripts/`
2. [ ] `search_kb.py` script deployed to `/ganuda/scripts/`
3. [ ] At least 3 KB articles created from recent bug fixes:
   - False task completion daemon conflict
   - TaskExecutor wrong database config
   - Hive Mind column name mismatches
4. [ ] Scripts tested and working
5. [ ] Entry added to thermal memory documenting the KB tooling itself

---

## Dependencies

- Python 3.x with psycopg2
- PostgreSQL access to bluefin

## Estimated Complexity

Medium - mostly SQL and Python scripting, existing patterns to follow.

---

*For Seven Generations*
