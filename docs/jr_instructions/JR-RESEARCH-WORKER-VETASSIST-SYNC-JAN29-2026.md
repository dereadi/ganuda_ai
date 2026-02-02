# JR Instruction: Research Worker VetAssist Sync

**JR ID:** JR-RESEARCH-WORKER-VETASSIST-SYNC-JAN29-2026
**Priority:** P1
**Assigned To:** Backend Jr.
**Related:** JR-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026

---

## Objective

When research_worker completes a VetAssist research job, also populate the `vetassist_research_results` table so the dashboard can display research history.

---

## Problem

Currently:
1. VetAssist triggers research → `research_jobs` table
2. research_worker processes job → writes to `/ganuda/research/completed/*.json`
3. Dashboard queries `vetassist_research_results` → **Empty** (never populated)

The worker handles Telegram callbacks but not VetAssist.

---

## Solution

Add VetAssist callback handling in research_worker.py.

### Edit `/ganuda/services/research_worker.py`

**Step 1: Add notify_vetassist function after notify_telegram (around line 245):**

```python
def notify_vetassist(job_id: str, query: str, answer: str, sources: list, requester_id: str):
    """Populate vetassist_research_results table for dashboard."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO vetassist_research_results
                (veteran_id, job_id, question, answer, sources, completed_at, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (job_id) DO UPDATE SET
                answer = EXCLUDED.answer,
                sources = EXCLUDED.sources,
                completed_at = NOW()
        """, (
            requester_id,  # veteran_id
            job_id,
            query,
            answer,
            json.dumps(sources) if sources else '[]'
        ))

        conn.commit()
        cur.close()
        conn.close()

        logging.info(f"Synced research {job_id} to vetassist_research_results for veteran {requester_id}")

    except Exception as e:
        logging.error(f"Failed to sync to vetassist_research_results: {e}")
```

**Step 2: Update claim_job to also fetch requester_type and requester_id:**

Find the SELECT in claim_job (around line 56):

```python
# Current
RETURNING job_id, query, max_steps, output_file, callback_type, callback_target
```

Change to:

```python
# New - add requester fields
RETURNING job_id, query, max_steps, output_file, callback_type, callback_target, requester_type, requester_id
```

**Step 3: Update process_job signature and call:**

Find process_job definition (around line 161):

```python
# Current
def process_job(job_id, query, max_steps, output_file, callback_type, callback_target):

# New
def process_job(job_id, query, max_steps, output_file, callback_type, callback_target, requester_type, requester_id):
```

**Step 4: Add VetAssist callback in process_job (after Telegram callback, around line 203):**

```python
        # Handle callbacks
        if callback_type == "telegram" and callback_target:
            notify_telegram(callback_target, job_id, summary, output_file)

        # VetAssist sync - populate dashboard table
        if requester_type == "vetassist" and requester_id:
            notify_vetassist(job_id, query, result.answer, result.sources, requester_id)
```

**Step 5: Update the caller in main loop to pass new fields:**

Find where process_job is called (in the main while loop):

```python
# Current (approximate)
process_job(job_id, query, max_steps, output_file, callback_type, callback_target)

# New
process_job(job_id, query, max_steps, output_file, callback_type, callback_target, requester_type, requester_id)
```

---

## Database Prep

Ensure `vetassist_research_results` has unique constraint on job_id:

```sql
-- Run on bluefin (192.168.132.222)
ALTER TABLE vetassist_research_results
ADD CONSTRAINT vetassist_research_results_job_id_key UNIQUE (job_id);
```

---

## Testing

1. Trigger research from VetAssist chat:
   ```
   POST /api/v1/research/trigger
   {
     "veteran_id": "test-vet-123",
     "session_id": "test-session",
     "question": "What is the rating for sleep apnea?"
   }
   ```

2. Wait for completion (3-5 min)

3. Check database:
   ```sql
   SELECT * FROM vetassist_research_results
   WHERE veteran_id = 'test-vet-123'
   ORDER BY created_at DESC LIMIT 1;
   ```

4. Check VetAssist dashboard - should show research in AI Research table

---

## Files to Modify

| File | Action |
|------|--------|
| `/ganuda/services/research_worker.py` | Add notify_vetassist, update claim_job SELECT, update process_job |

---

## Service Restart

```bash
sudo systemctl restart research-worker
```

---

FOR SEVEN GENERATIONS
