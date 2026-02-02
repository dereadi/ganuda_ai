# JR-EXECUTOR-RESEARCH-TO-SEED-JAN30-2026
## Add Research-to-Seed Pipeline to Task Executor (Phase 10)

**Priority:** P0 — Blocking VetAssist educational content population
**Target Node:** redfin
**Estimated Scope:** ~120 lines added to existing file
**Companion Document:** `ULTRATHINK-JR-EXECUTOR-ARCHITECTURE-FUTURE-JAN30-2026.md`

---

### Background

The Jr Task Executor at `/ganuda/jr_executor/task_executor.py` can:
1. **Fetch web content** via `ResearchTaskExecutor` (Crawl4AI)
2. **Call the LLM** via `JrLLMReasoner` (Qwen 32B on vLLM)
3. **Execute SQL** directly against PostgreSQL (`_execute_sql()`)
4. **Write files** to `/ganuda/` (`_execute_file()`)

These capabilities exist in isolation. When a research task runs (line 726-745), it fetches URLs, saves markdown reports, and **stops**. It never processes the fetched content into structured data or seeds a database.

### The Gap

```
CURRENT:
  Research task → fetch URLs → save .md reports → DONE (dead end)

NEEDED:
  Research task → fetch URLs → send to LLM with schema → generate INSERTs → execute SQL → verify
```

### Task: Add `_execute_research_and_seed()` Method

**File to Modify:** `/ganuda/jr_executor/task_executor.py`

#### Step 1: Add Detection Function

Add a new function `is_research_and_seed_task()` that identifies tasks requiring the research-to-seed pipeline. This should be checked BEFORE the existing `is_research_task()` at line 726.

Detection criteria (ANY match → true):
- Task title contains "seed" AND ("research" OR "crawl" OR "fetch")
- Task tags include both "research" and "seed"
- Instruction content contains the phrase "research and seed" or "crawl and insert" or "fetch and populate"
- Instruction content contains BOTH a URL pattern AND an `INSERT INTO` or table schema reference

```python
def is_research_and_seed_task(task: dict, instructions: str) -> bool:
    """Detect tasks that need the research-to-seed pipeline."""
    title = (task.get('title') or '').lower()
    tags = [t.lower() for t in (task.get('tags') or [])]
    instr_lower = instructions.lower()

    # Title-based detection
    if 'seed' in title and any(w in title for w in ['research', 'crawl', 'fetch']):
        return True

    # Tag-based detection
    if 'research' in tags and 'seed' in tags:
        return True

    # Instruction phrase detection
    seed_phrases = ['research and seed', 'crawl and insert', 'fetch and populate',
                    'research then seed', 'crawl then insert', 'fetch then seed']
    if any(phrase in instr_lower for phrase in seed_phrases):
        return True

    # Combined pattern: has URL + has table reference
    import re
    has_url = bool(re.search(r'https?://\S+', instructions))
    has_table = bool(re.search(r'(?:INSERT\s+INTO|CREATE\s+TABLE|TABLE:\s*\w+|table.*schema)', instr_lower))
    if has_url and has_table:
        return True

    return False
```

#### Step 2: Add the Pipeline Method

Add `_execute_research_and_seed()` to the `TaskExecutor` class. This method chains the existing components:

```python
def _execute_research_and_seed(self, task: dict, instructions: str) -> dict:
    """
    Phase 10: Research-to-Seed Pipeline

    Chains: fetch content → LLM extraction → SQL generation → SQL execution → verification

    Requires: ResearchTaskExecutor, JrLLMReasoner, _execute_sql()
    """
    result = {
        'success': False,
        'steps_executed': [],
        'artifacts': [],
        'error': None,
        'execution_mode': 'research_and_seed'
    }

    # === Stage 1: Research (fetch web content) ===
    print(f"[R2S] Stage 1: Fetching web content...")
    try:
        research_executor = ResearchTaskExecutor()
        research_result = research_executor.execute_research_task({
            'title': task.get('title'),
            'instructions': instructions,
            'parameters': task.get('parameters', {})
        })

        if not research_result.get('success') or not research_result.get('artifacts'):
            result['error'] = 'Research stage failed: no content fetched'
            result['steps_executed'].append({
                'type': 'research_fetch',
                'success': False,
                'error': 'No content fetched'
            })
            return result

        # Collect fetched content
        fetched_content = ""
        for artifact in research_result.get('artifacts', []):
            if artifact.get('path') and os.path.exists(artifact['path']):
                try:
                    with open(artifact['path'], 'r') as f:
                        fetched_content += f"\n\n--- Source: {artifact.get('url', 'unknown')} ---\n"
                        fetched_content += f.read()[:15000]  # Cap per source
                except Exception:
                    pass

        if not fetched_content.strip():
            result['error'] = 'Research fetched but content is empty'
            return result

        result['steps_executed'].append({
            'type': 'research_fetch',
            'success': True,
            'sources': research_result.get('sources_fetched', 0),
            'content_length': len(fetched_content)
        })
        print(f"[R2S] Stage 1 complete: {len(fetched_content)} chars from {research_result.get('sources_fetched', 0)} sources")

    except Exception as e:
        result['error'] = f'Research stage error: {e}'
        return result

    # === Stage 2: Extract schema from instructions ===
    print(f"[R2S] Stage 2: Extracting target schema...")
    # Look for table schema in the instruction file
    schema_section = self._extract_schema_from_instructions(instructions)
    if not schema_section:
        result['error'] = 'No database schema found in instructions'
        result['steps_executed'].append({
            'type': 'schema_extraction',
            'success': False,
            'error': 'No schema found'
        })
        return result

    result['steps_executed'].append({
        'type': 'schema_extraction',
        'success': True,
        'schema_length': len(schema_section)
    })

    # === Stage 3: LLM generates SQL from content + schema ===
    print(f"[R2S] Stage 3: Generating SQL INSERTs via LLM...")
    try:
        reasoner = get_reasoner_sync()

        seed_prompt = f"""You are a database seed script generator. Given web research content and a target database schema, generate PostgreSQL INSERT statements to populate the table.

## Target Schema
{schema_section}

## Research Content (from web crawl)
{fetched_content[:20000]}

## Instructions from Task
{instructions[:3000]}

## Requirements
1. Generate INSERT statements for ALL relevant data found in the research content
2. Use proper PostgreSQL syntax with single-quoted strings
3. Escape single quotes in content with ''
4. Each INSERT must be a complete, valid statement
5. Set is_published = true if the schema has that column
6. Generate slug values as lowercase-hyphenated versions of titles
7. Use ON CONFLICT (slug) DO NOTHING if the schema has a slug column (idempotent)
8. Do NOT generate DROP, DELETE, TRUNCATE, or ALTER statements

## Output Format
Return ONLY the SQL INSERT statements, one per line. No explanations, no markdown code blocks, just raw SQL.
"""

        sql_output = reasoner.simple_completion(seed_prompt)

        if not sql_output or len(sql_output.strip()) < 20:
            result['error'] = 'LLM generated empty or too-short SQL output'
            result['steps_executed'].append({
                'type': 'sql_generation',
                'success': False,
                'error': 'Empty output'
            })
            return result

        # Clean: strip markdown code blocks if LLM wrapped them anyway
        import re
        sql_clean = re.sub(r'^```\w*\n?', '', sql_output.strip())
        sql_clean = re.sub(r'\n?```$', '', sql_clean).strip()

        result['steps_executed'].append({
            'type': 'sql_generation',
            'success': True,
            'sql_length': len(sql_clean)
        })
        print(f"[R2S] Stage 3 complete: {len(sql_clean)} chars of SQL generated")

    except Exception as e:
        result['error'] = f'SQL generation error: {e}'
        return result

    # === Stage 4: Validate and execute SQL ===
    print(f"[R2S] Stage 4: Validating and executing SQL...")

    # Split into individual statements
    statements = [s.strip() for s in sql_clean.split(';') if s.strip()]

    executed = 0
    failed = 0
    errors = []

    for i, stmt in enumerate(statements):
        if not stmt:
            continue

        # Safety check: only allow INSERT and SELECT
        stmt_upper = stmt.strip().upper()
        if not (stmt_upper.startswith('INSERT') or stmt_upper.startswith('SELECT') or stmt_upper.startswith('WITH')):
            print(f"[R2S] BLOCKED non-INSERT statement: {stmt[:60]}...")
            errors.append(f"Blocked: {stmt[:60]}")
            failed += 1
            continue

        # Check forbidden patterns
        step_dict = {'type': 'sql', 'command': stmt}
        if self._is_forbidden(step_dict):
            print(f"[R2S] FORBIDDEN statement blocked: {stmt[:60]}...")
            errors.append(f"Forbidden: {stmt[:60]}")
            failed += 1
            continue

        # Execute
        sql_result = self._execute_sql(step_dict)
        if sql_result.get('success'):
            executed += 1
        else:
            failed += 1
            errors.append(f"Statement {i+1}: {sql_result.get('error', 'unknown')}")
            print(f"[R2S] SQL error on statement {i+1}: {sql_result.get('error')}")

    result['steps_executed'].append({
        'type': 'sql_execution',
        'success': executed > 0,
        'executed': executed,
        'failed': failed,
        'errors': errors[:5]  # Cap error list
    })
    print(f"[R2S] Stage 4 complete: {executed} succeeded, {failed} failed out of {len(statements)} statements")

    # === Stage 5: Verification ===
    print(f"[R2S] Stage 5: Verifying seed results...")
    # Try to extract table name for verification query
    table_match = re.search(r'INSERT\s+INTO\s+(\w+)', sql_clean, re.IGNORECASE)
    if table_match:
        table_name = table_match.group(1)
        verify_step = {'type': 'sql', 'command': f'SELECT COUNT(*) FROM {table_name}'}
        verify_result = self._execute_sql(verify_step)
        if verify_result.get('success'):
            count = verify_result.get('result', [[0]])[0][0]
            result['steps_executed'].append({
                'type': 'verification',
                'success': True,
                'table': table_name,
                'row_count': count
            })
            print(f"[R2S] Verification: {table_name} has {count} rows")

    # Overall success if we executed at least one INSERT
    result['success'] = executed > 0
    if not result['success']:
        result['error'] = f'No SQL statements executed successfully. Errors: {"; ".join(errors[:3])}'

    # Save pipeline report as artifact
    report_path = f"/ganuda/docs/research/R2S-{task.get('title', 'unknown').replace(' ', '-')[:50]}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    try:
        report = f"# Research-to-Seed Pipeline Report\n\n"
        report += f"**Task:** {task.get('title')}\n"
        report += f"**Date:** {datetime.now().isoformat()}\n\n"
        report += f"## Results\n"
        report += f"- Sources fetched: {research_result.get('sources_fetched', 0)}\n"
        report += f"- SQL statements executed: {executed}\n"
        report += f"- SQL statements failed: {failed}\n\n"
        if errors:
            report += f"## Errors\n"
            for err in errors[:10]:
                report += f"- {err}\n"

        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        result['artifacts'].append({'type': 'pipeline_report', 'path': report_path})
    except Exception:
        pass

    return result
```

#### Step 3: Add Schema Extraction Helper

```python
def _extract_schema_from_instructions(self, instructions: str) -> Optional[str]:
    """Extract database schema section from instruction markdown."""
    import re

    # Look for schema-related sections
    patterns = [
        # Markdown table with Column | Type | Notes
        r'(?:###?\s*(?:Database\s+)?Schema.*?\n)((?:\|.*\|.*\n)+)',
        # SQL CREATE TABLE block
        r'```sql\n(CREATE\s+TABLE.*?)```',
        # Table description section
        r'(?:Table:\s*`?\w+`?.*?\n)((?:\|.*\|.*\n)+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, instructions, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)  # Include the header for context

    # Fallback: look for any markdown table that mentions column types
    table_blocks = re.findall(r'(\|[^\n]*\|\n(?:\|[^\n]*\|\n)+)', instructions)
    for block in table_blocks:
        if any(kw in block.lower() for kw in ['varchar', 'integer', 'text', 'boolean', 'serial', 'timestamp']):
            return block

    return None
```

#### Step 4: Wire Into process_queue_task()

In `process_queue_task()`, add the research-and-seed check BEFORE the existing research check (line 726):

```python
        # Phase 10: Check if task should use Research-and-Seed pipeline
        if RESEARCH_EXECUTOR_AVAILABLE and LLM_REASONER_AVAILABLE:
            if is_research_and_seed_task(task, instructions):
                print(f"[R2S] Task flagged for research-and-seed pipeline: {task.get('title')}")
                return self._execute_research_and_seed(task, instructions)

        # Phase 8: Check if task should use Research Executor (web research)
        if RESEARCH_EXECUTOR_AVAILABLE and is_research_task(task, instructions):
            # ... existing research code ...
```

### Integration Points

| Existing Component | How It's Used | Location |
|-------------------|---------------|----------|
| `ResearchTaskExecutor` | Stage 1: Fetch web content | `/ganuda/jr_executor/research_task_executor.py` |
| `get_reasoner_sync()` | Stage 3: Generate SQL from content + schema | `/ganuda/lib/jr_llm_reasoner.py` |
| `_execute_sql()` | Stage 4: Run INSERT statements | `task_executor.py` line 1485 |
| `_is_forbidden()` | Stage 4: Safety check each statement | `task_executor.py` line 1411 |
| `_validate_path()` | Report file writing | `task_executor.py` line 203 |

### Safety Constraints

1. **Only INSERT and SELECT** allowed in Stage 4 — no UPDATE, DELETE, DROP, ALTER
2. **Forbidden pattern check** applied to every generated SQL statement
3. **Protected tables** list still enforced — LLM-generated SQL cannot touch sacred tables
4. **Content cap** — each fetched source limited to 15K chars, total LLM prompt capped at 20K
5. **Report artifact** — every pipeline run produces a traceable report

### Testing

After implementing, test with the existing VetAssist educational content task:

```bash
# Queue a research-and-seed task
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_task_queue (title, description, tags, instruction_file, status, assigned_jr, priority)
VALUES (
    'Research and Seed VetAssist Educational Content',
    'Crawl VA.gov educational pages and seed the educational_content table',
    ARRAY['research', 'seed', 'vetassist'],
    '/ganuda/docs/jr_instructions/JR-VETASSIST-SEED-EDUCATIONAL-CONTENT-JAN30-2026.md',
    'pending',
    'Infrastructure Jr.',
    1
);
"

# Monitor execution
tail -f /ganuda/logs/jr_queue_worker.log | grep R2S
```

### Verification

```bash
# Check educational_content table after pipeline runs
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT COUNT(*) as total,
       COUNT(*) FILTER (WHERE is_published) as published
FROM educational_content;
"

# Check pipeline report was generated
ls -la /ganuda/docs/research/R2S-*

# Check the API returns content
curl -s http://localhost:8001/api/v1/content?limit=5 | python3 -m json.tool | head -20
```

### Files to Modify

| File | Change | Lines Added |
|------|--------|-------------|
| `/ganuda/jr_executor/task_executor.py` | Add `is_research_and_seed_task()`, `_execute_research_and_seed()`, `_extract_schema_from_instructions()`, wire into `process_queue_task()` | ~120 |

### Why This Matters

This is the bridge between the Jr's perception (web crawling) and action (database execution). Without it, every data population task requires a human to write the seed script manually. With it, the Jr can autonomously research a topic, understand a schema, generate the right SQL, and populate the database — all from a single instruction file.

This is Phase 10 of the executor's evolution. See the companion ultrathink document for Phases 11-18.

---

*For Seven Generations*
