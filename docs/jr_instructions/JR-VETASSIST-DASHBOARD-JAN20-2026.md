# Jr Instruction: VetAssist Veteran Dashboard

**Priority**: 3 of 3
**Council Audit**: 3b690ed593a16433
**Estimated Complexity**: Medium
**Parent ULTRATHINK**: ULTRATHINK-VETASSIST-SPRINT2-JAN20-2026.md

## Objective

Build a veteran dashboard to view, resume, and manage claim wizard sessions.

## Prerequisites

- Authentication integration (Priority 1) completed
- PDF export (Priority 2) completed
- VetAssist frontend and backend running

## Tasks

### Task 1: Dashboard API Endpoints

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Import auth dependency
from .auth import get_current_user

class ClaimSummary(BaseModel):
    session_id: str
    wizard_type: str
    form_name: str
    status: str
    current_step: int
    total_steps: int
    created_at: datetime
    updated_at: Optional[datetime]
    conditions_count: int = 0
    files_count: int = 0

class DashboardStats(BaseModel):
    total_claims: int
    active_claims: int
    completed_claims: int
    total_conditions: int
    total_files: int

@router.get("/claims", response_model=List[ClaimSummary])
def list_user_claims(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """
    List all wizard sessions for the authenticated user.

    Query params:
    - status: Filter by status (in_progress, completed, abandoned)
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT
                    s.session_id,
                    s.wizard_type,
                    s.status,
                    s.current_step,
                    s.answers,
                    s.created_at,
                    s.updated_at,
                    (SELECT COUNT(*) FROM vetassist_wizard_files f
                     WHERE f.session_id = s.session_id AND NOT f.deleted) as files_count
                FROM vetassist_wizard_sessions s
                WHERE s.veteran_id = %s
            """
            params = [user_id]

            if status:
                query += " AND s.status = %s"
                params.append(status)

            query += " ORDER BY s.updated_at DESC NULLS LAST, s.created_at DESC"

            cur.execute(query, params)
            sessions = cur.fetchall()

        claims = []
        for s in sessions:
            form = WIZARD_FORMS.get(s['wizard_type'], {})
            answers = s['answers'] if isinstance(s['answers'], dict) else json.loads(s['answers'] or '{}')

            # Count conditions from answers
            conditions = answers.get('conditions', [])
            conditions_count = len(conditions) if isinstance(conditions, list) else 0

            claims.append(ClaimSummary(
                session_id=s['session_id'],
                wizard_type=s['wizard_type'],
                form_name=form.get('name', s['wizard_type']),
                status=s['status'],
                current_step=s['current_step'],
                total_steps=len(form.get('steps', [])),
                created_at=s['created_at'],
                updated_at=s['updated_at'],
                conditions_count=conditions_count,
                files_count=s['files_count'] or 0
            ))

        return claims
    finally:
        conn.close()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(user_id: str = Depends(get_current_user)):
    """Get aggregate statistics for user's claims"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total_claims,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as active_claims,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_claims
                FROM vetassist_wizard_sessions
                WHERE veteran_id = %s
            """, (user_id,))
            stats = cur.fetchone()

            cur.execute("""
                SELECT COUNT(*) as total_files
                FROM vetassist_wizard_files f
                JOIN vetassist_wizard_sessions s ON f.session_id = s.session_id
                WHERE s.veteran_id = %s AND NOT f.deleted
            """, (user_id,))
            files = cur.fetchone()

        return DashboardStats(
            total_claims=stats['total_claims'],
            active_claims=stats['active_claims'],
            completed_claims=stats['completed_claims'],
            total_conditions=0,  # Calculate from answers
            total_files=files['total_files'] or 0
        )
    finally:
        conn.close()


@router.delete("/claims/{session_id}", status_code=204)
def delete_claim(session_id: str, user_id: str = Depends(get_current_user)):
    """Delete a wizard session (soft delete)"""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute("""
                SELECT veteran_id FROM vetassist_wizard_sessions
                WHERE session_id = %s
            """, (session_id,))
            session = cur.fetchone()

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            if session[0] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            # Soft delete
            cur.execute("""
                UPDATE vetassist_wizard_sessions
                SET status = 'deleted', updated_at = NOW()
                WHERE session_id = %s
            """, (session_id,))
            conn.commit()
    finally:
        conn.close()
```

### Task 2: Register Dashboard Router

In `/ganuda/vetassist/backend/app/api/v1/__init__.py`:

```python
from .endpoints import dashboard
api_router.include_router(dashboard.router)
```

### Task 3: Frontend Dashboard Page

Replace/enhance `/ganuda/vetassist/frontend/app/dashboard/page.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  FileText, Plus, Clock, CheckCircle, Trash2,
  Download, ChevronRight, AlertCircle, Loader2
} from 'lucide-react';

interface Claim {
  session_id: string;
  wizard_type: string;
  form_name: string;
  status: string;
  current_step: number;
  total_steps: number;
  created_at: string;
  updated_at: string;
  conditions_count: number;
  files_count: number;
}

interface Stats {
  total_claims: number;
  active_claims: number;
  completed_claims: number;
  total_files: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

  useEffect(() => {
    loadDashboard();
  }, [filter]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [claimsRes, statsRes] = await Promise.all([
        fetch(`${apiUrl}/dashboard/claims${filter !== 'all' ? `?status=${filter}` : ''}`),
        fetch(`${apiUrl}/dashboard/stats`)
      ]);

      if (claimsRes.ok) setClaims(await claimsRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteClaim = async (sessionId: string) => {
    if (!confirm('Delete this claim? This cannot be undone.')) return;

    try {
      const res = await fetch(`${apiUrl}/dashboard/claims/${sessionId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setClaims(claims.filter(c => c.session_id !== sessionId));
      }
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const downloadPDF = async (sessionId: string, wizardType: string) => {
    const res = await fetch(`${apiUrl}/wizard/${sessionId}/export/pdf`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `VA${wizardType}_${sessionId.slice(0, 8)}.pdf`;
    a.click();
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Claims</h1>
            <p className="text-gray-600">Manage your VA disability claims</p>
          </div>
          <Link
            href="/wizard"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-5 w-5" />
            New Claim
          </Link>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <p className="text-sm text-gray-500">Total Claims</p>
              <p className="text-2xl font-bold">{stats.total_claims}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <p className="text-sm text-gray-500">In Progress</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.active_claims}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-green-600">{stats.completed_claims}</p>
            </div>
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <p className="text-sm text-gray-500">Documents</p>
              <p className="text-2xl font-bold">{stats.total_files}</p>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'in_progress', 'completed'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {f === 'all' ? 'All Claims' : f === 'in_progress' ? 'In Progress' : 'Completed'}
            </button>
          ))}
        </div>

        {/* Claims List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : claims.length === 0 ? (
          <div className="bg-white rounded-lg border p-12 text-center">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No claims yet</h3>
            <p className="text-gray-500 mb-4">Start your first VA disability claim</p>
            <Link
              href="/wizard"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              <Plus className="h-5 w-5" /> Start New Claim
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {claims.map(claim => (
              <div
                key={claim.session_id}
                className="bg-white rounded-lg border p-4 hover:shadow-md transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      claim.status === 'completed' ? 'bg-green-100' : 'bg-yellow-100'
                    }`}>
                      {claim.status === 'completed'
                        ? <CheckCircle className="h-6 w-6 text-green-600" />
                        : <Clock className="h-6 w-6 text-yellow-600" />
                      }
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{claim.form_name}</h3>
                      <p className="text-sm text-gray-500">
                        {claim.status === 'completed'
                          ? `Completed ${formatDate(claim.updated_at || claim.created_at)}`
                          : `Step ${claim.current_step} of ${claim.total_steps}`
                        }
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {claim.status === 'completed' ? (
                      <button
                        onClick={() => downloadPDF(claim.session_id, claim.wizard_type)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="Download PDF"
                      >
                        <Download className="h-5 w-5" />
                      </button>
                    ) : (
                      <Link
                        href={`/wizard/${claim.session_id}`}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        Continue <ChevronRight className="h-4 w-4" />
                      </Link>
                    )}
                    <button
                      onClick={() => deleteClaim(claim.session_id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded"
                      title="Delete"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Progress bar for in-progress claims */}
                {claim.status !== 'completed' && (
                  <div className="mt-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full"
                        style={{ width: `${(claim.current_step / claim.total_steps) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### Task 4: Update Wizard to Associate with User

Modify wizard session creation to use authenticated user's ID:

```python
# In wizard.py start_wizard()
@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_wizard(request: WizardStartRequest, user_id: str = Depends(get_current_user)):
    # Use user_id from auth instead of request.veteran_id
    ...
```

### Task 5: Add Navigation to Dashboard

Update the main layout or navbar to include dashboard link for authenticated users.

## Validation

1. Login as user
2. Create 2-3 wizard sessions (some complete, some in progress)
3. Visit /dashboard
4. Verify stats display correctly
5. Test filter tabs
6. Test continue button on in-progress claims
7. Test download button on completed claims
8. Test delete functionality

## Files to Create/Modify

- `backend/app/api/v1/endpoints/dashboard.py` (NEW)
- `backend/app/api/v1/__init__.py` (MODIFY)
- `frontend/app/dashboard/page.tsx` (REPLACE)
- `backend/app/api/v1/endpoints/wizard.py` (MODIFY - use auth user)

## Report Back

When complete, update Jr work queue with:
- Screenshots of dashboard
- Test results
- Any UX improvements suggested
