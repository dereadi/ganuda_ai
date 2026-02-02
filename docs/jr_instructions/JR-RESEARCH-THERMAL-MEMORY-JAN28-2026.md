# JR Instruction: Research Results to Thermal Memory

**JR ID:** JR-RESEARCH-THERMAL-MEMORY-JAN28-2026
**Priority:** P1
**Assigned To:** Backend Jr.
**Related:** ULTRATHINK-COUNCIL-RESEARCH-INTEGRATION-JAN28-2026
**Depends On:** JR-COUNCIL-RESEARCH-AUTOQUEUE-JAN28-2026

---

## Objective

Store completed ii-researcher results in thermal memory so future Council deliberations can reference past research. Research builds tribal knowledge that compounds over time.

---

## Architecture

```
ii-researcher completes
         │
         ▼
┌─────────────────────────┐
│ research_worker.py      │
│                         │
│ 1. Write JSON file      │
│ 2. Update research_jobs │
│ 3. Notify user          │
│ 4. NEW: Store thermal   │◄── This JR
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ thermal_memory_archive  │
│                         │
│ memory_type:            │
│   'research_result'     │
│                         │
│ temperature: 70° (warm) │
│ decays over time        │
│ heats up when accessed  │
└─────────────────────────┘
         │
         ▼
Future Council queries thermal memory
for relevant past research
```

---

## Implementation

### Step 1: Add Thermal Memory Storage Function

Edit `/ganuda/services/research_worker.py`.

Add import:
```python
import hashlib
```

Add function after `notify_telegram()`:

```python
def store_in_thermal_memory(job_id: str, query: str, answer: str, sources: list):
    """
    Store research result in thermal memory for future Council context.

    Research results start warm (70°) and decay over time.
    Accessed research heats up, unused research cools down.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Extract core question (strip persona prompt)
        core_question = query
        if '---' in query and 'Research Question:' in query:
            core_question = query.split('Research Question:')[-1].strip()

        # Create memory content (truncated for storage)
        memory_content = f"""RESEARCH: {core_question[:200]}

FINDINGS: {answer[:3000]}

SOURCES: {', '.join(s.get('url', s) if isinstance(s, dict) else str(s) for s in sources[:5])}"""

        # Generate memory hash
        memory_hash = hashlib.sha256(f"{job_id}-research".encode()).hexdigest()[:16]

        # Check if already stored (idempotent)
        cur.execute(
            "SELECT 1 FROM thermal_memory_archive WHERE memory_hash = %s",
            (memory_hash,)
        )
        if cur.fetchone():
            logging.info(f"Research {job_id} already in thermal memory")
            cur.close()
            conn.close()
            return

        # Insert into thermal memory
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, memory_type, temperature_score,
             context_tags, source_type, created_at)
            VALUES (%s, %s, 'research_result', 70.0, %s, 'ii-researcher', NOW())
        """, (
            memory_hash,
            memory_content,
            json.dumps({
                'job_id': job_id,
                'question': core_question[:200],
                'source_count': len(sources),
                'answer_length': len(answer)
            })
        ))

        conn.commit()
        cur.close()
        conn.close()

        logging.info(f"Stored research {job_id} in thermal memory (hash: {memory_hash})")

    except Exception as e:
        logging.error(f"Failed to store research in thermal memory: {e}")
```

### Step 2: Call from Job Completion

In `process_job()`, add call after `complete_job()`:

```python
def process_job(job_id, query, max_steps, output_file, callback_type, callback_target):
    """Process a research job."""
    # ... existing code ...

    try:
        from research_client import ResearchClient
        client = ResearchClient(timeout=RESEARCH_TIMEOUT)
        result = client.search(query, max_steps=max_steps)

        if result.error:
            fail_job(job_id, result.error)
            return

        # Write result to file
        # ... existing file write code ...

        complete_job(job_id, output_file, summary)
        logging.info(f"Job {job_id} completed -> {output_file}")

        # NEW: Store in thermal memory for future Council context
        store_in_thermal_memory(job_id, query, result.answer, result.sources)

        # Handle callbacks
        if callback_type == "telegram" and callback_target:
            notify_telegram(callback_target, job_id, summary, output_file)

    except Exception as e:
        fail_job(job_id, str(e))
```

---

## Step 3: Verify Thermal Memory Schema

The `thermal_memory_archive` table should already exist. Verify it has required columns:

```sql
-- Run on bluefin
\d thermal_memory_archive

-- Required columns:
-- memory_hash (unique identifier)
-- original_content (the research content)
-- memory_type (set to 'research_result')
-- temperature_score (starts at 70.0)
-- context_tags (JSON metadata)
-- source_type (set to 'ii-researcher')
-- created_at
```

If `memory_type` column doesn't exist, add it:

```sql
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS memory_type VARCHAR(50) DEFAULT 'general';

CREATE INDEX IF NOT EXISTS idx_thermal_memory_type
ON thermal_memory_archive(memory_type);
```

---

## Testing

### Test 1: Trigger Research and Verify Storage

```bash
# Trigger research via Telegram
/research What is the current status of PostgreSQL 17 features?

# Wait 3-5 minutes, then check thermal memory
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT memory_hash, memory_type, temperature_score, LEFT(original_content, 100)
FROM thermal_memory_archive
WHERE memory_type = 'research_result'
ORDER BY created_at DESC
LIMIT 5;"
```

### Test 2: Verify Idempotency

Run same research twice - should only create one thermal memory entry.

### Test 3: Check Pheromone Decay Compatibility

Verify pheromone decay daemon handles `memory_type = 'research_result'`:

```bash
# Check decay script
grep -i research /ganuda/scripts/pheromone_decay.sh
```

Research memories should decay like other memories (cool by ~1° per day when unused).

---

## Future Enhancement (P2)

In Phase 2, Council will query thermal memory for relevant past research:

```python
# In specialist_council.py
def get_research_context(question: str) -> str:
    """Get relevant past research for Council context."""
    # Extract keywords from question
    # Query thermal_memory_archive WHERE memory_type = 'research_result'
    # Return formatted context for Council prompt
```

This JR focuses only on **storage**. Retrieval is Phase 2.

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/services/research_worker.py` | MODIFY |
| Database: `thermal_memory_archive` | VERIFY/MODIFY |

---

## Rollback

Comment out the `store_in_thermal_memory()` call in `process_job()` if issues occur.

---

FOR SEVEN GENERATIONS
