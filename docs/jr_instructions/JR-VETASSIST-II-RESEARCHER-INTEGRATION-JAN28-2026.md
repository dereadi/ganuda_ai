# JR Instruction: VetAssist ii-researcher Integration

**JR ID:** JR-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026
**Priority:** P1
**Assigned To:** VetAssist Jr.
**Related:** JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026

---

## Objective

Connect VetAssist dashboard to ii-researcher async pattern. Research results should appear in the user's dashboard under "AI Research" table.

---

## Current State

| Component | Current | Target |
|-----------|---------|--------|
| research.py | Uses `jr_work_queue` table | Use `research_jobs` table |
| dashboard.py | `research_history: []` (disabled) | Query `research_jobs` for veteran |
| Research worker | Writes to file only | Also link to veteran_id |

---

## Database Changes

Add veteran_id to research_jobs table:

```sql
-- Run on bluefin (192.168.132.222) in zammad_production

ALTER TABLE research_jobs ADD COLUMN IF NOT EXISTS veteran_id VARCHAR(100);
CREATE INDEX IF NOT EXISTS idx_research_jobs_veteran ON research_jobs(veteran_id);
```

---

## Backend Changes

### File: `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`

Replace `jr_work_queue` with `research_jobs` integration:

```python
"""
VetAssist Deep Research Endpoint
Uses ii-researcher async pattern
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from psycopg2.extras import RealDictCursor
import requests

from app.core.database_config import get_db_connection

router = APIRouter()

LLM_GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"


class ResearchRequest(BaseModel):
    veteran_id: str = Field(..., description="Veteran ID for dashboard linking")
    session_id: str = Field(..., description="Chat session ID")
    question: str = Field(..., description="The veteran's question")
    condition: Optional[str] = Field(None, description="Related medical condition")


@router.post("/trigger")
def trigger_research(request: ResearchRequest):
    """Queue research via ii-researcher async pattern."""
    try:
        # Queue via LLM Gateway
        response = requests.post(
            f"{LLM_GATEWAY_URL}/v1/research/async",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "query": f"{request.question} {request.condition or ''}".strip(),
                "max_steps": 5
            },
            timeout=10
        )

        if response.status_code != 200:
            raise HTTPException(500, f"Research queue failed: {response.text}")

        data = response.json()
        job_id = data.get("job_id")

        # Link job to veteran for dashboard
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE research_jobs
                SET requester_type = 'vetassist',
                    requester_id = %s,
                    callback_type = 'dashboard'
                WHERE job_id = %s
            """, (request.veteran_id, job_id))

            # Also store veteran_id directly if column exists
            try:
                cur.execute("""
                    UPDATE research_jobs SET veteran_id = %s WHERE job_id = %s
                """, (request.veteran_id, job_id))
            except:
                pass  # Column may not exist yet

            conn.commit()
        conn.close()

        return {
            "status": "research_queued",
            "job_id": job_id,
            "message": "Deep research started. Check your dashboard in 3-5 minutes.",
            "estimated_time": "3-5 minutes"
        }

    except requests.RequestException as e:
        raise HTTPException(500, f"Gateway connection error: {str(e)}")


@router.get("/results/{veteran_id}")
def get_research_results(veteran_id: str):
    """Get completed research for veteran's dashboard."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    job_id,
                    query as question,
                    status,
                    result_summary as summary,
                    output_file,
                    created_at,
                    completed_at
                FROM research_jobs
                WHERE requester_id = %s
                AND requester_type = 'vetassist'
                ORDER BY created_at DESC
                LIMIT 10
            """, (veteran_id,))
            results = cur.fetchall()
        conn.close()

        return {
            "veteran_id": veteran_id,
            "research_count": len(results),
            "results": [
                {
                    "job_id": r['job_id'],
                    "question": r['question'],
                    "status": r['status'],
                    "summary": r['summary'],
                    "output_file": r['output_file'],
                    "created_at": r['created_at'].isoformat() if r['created_at'] else None,
                    "completed_at": r['completed_at'].isoformat() if r['completed_at'] else None
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/status/{job_id}")
def get_research_status(job_id: str):
    """Check status of specific research job."""
    try:
        response = requests.get(
            f"{LLM_GATEWAY_URL}/v1/research/status/{job_id}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        return response.json()
    except Exception as e:
        raise HTTPException(500, str(e))
```

### File: `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

Re-enable research_history query (around line 60):

```python
# Get research history from research_jobs table
research_history = []
try:
    cur.execute("""
        SELECT
            job_id,
            query as question,
            status,
            result_summary as summary,
            created_at,
            completed_at
        FROM research_jobs
        WHERE requester_id = %s
        AND requester_type = 'vetassist'
        ORDER BY created_at DESC
        LIMIT 5
    """, (veteran_id,))
    research_rows = cur.fetchall()
    research_history = [
        {
            "job_id": r['job_id'],
            "question": r['question'],
            "status": r['status'],
            "summary": r['summary'],
            "created_at": r['created_at'].isoformat() if r['created_at'] else None,
            "completed_at": r['completed_at'].isoformat() if r['completed_at'] else None
        }
        for r in research_rows
    ]
except Exception:
    conn.rollback()

# Then in the return:
return {
    ...
    "research_history": research_history,
    ...
}
```

---

## Frontend Changes

### File: `/ganuda/vetassist/frontend/src/app/dashboard/page.tsx`

Add AI Research table component:

```tsx
{/* AI Research Section */}
<div className="bg-white rounded-lg shadow p-6">
  <h2 className="text-xl font-semibold mb-4">AI Research</h2>
  {dashboardData.research_history?.length > 0 ? (
    <table className="w-full">
      <thead>
        <tr className="text-left text-gray-500 border-b">
          <th className="pb-2">Question</th>
          <th className="pb-2">Status</th>
          <th className="pb-2">Date</th>
        </tr>
      </thead>
      <tbody>
        {dashboardData.research_history.map((r) => (
          <tr key={r.job_id} className="border-b">
            <td className="py-2">{r.question?.substring(0, 50)}...</td>
            <td className="py-2">
              <span className={`px-2 py-1 rounded text-sm ${
                r.status === 'completed' ? 'bg-green-100 text-green-800' :
                r.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {r.status}
              </span>
            </td>
            <td className="py-2 text-gray-500">
              {new Date(r.created_at).toLocaleDateString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  ) : (
    <p className="text-gray-500">No research history yet. Use the chat to ask questions!</p>
  )}
</div>
```

---

## Data Flow

```
User asks question in VetAssist chat
         │
         ▼
/api/v1/research/trigger
         │
         ▼
LLM Gateway /v1/research/async
         │
         ▼
research_jobs table (with veteran_id)
         │
         ▼
research-worker processes job
         │
         ▼
Writes to /ganuda/research/completed/{job_id}.json
Updates research_jobs status = 'completed'
         │
         ▼
Dashboard polls /api/v1/research/results/{veteran_id}
         │
         ▼
AI Research table shows results
```

---

## Testing

1. Login to VetAssist as test veteran
2. Go to chat, ask "What is the VA rating for tinnitus?"
3. Check dashboard - should show "running" status
4. Wait 3-5 minutes
5. Refresh dashboard - should show "completed" with summary

---

## Database Connection Note

VetAssist connects to bluefin (192.168.132.222) where `research_jobs` table lives. Ensure `database_config.py` uses correct connection.

---

FOR SEVEN GENERATIONS
