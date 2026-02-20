# Jr Instruction: Wave 4 — VetAssist User Feedback Loop

**Task**: Wire VetAssist into the federation's thermal memory feedback pipeline
**Priority**: 2 (HIGH — beta testers active, feedback currently ad hoc)
**Source**: Council vote #c3d64752977652a4 (PROCEED, specialists timed out — auto-consensus)
**Assigned Jr**: Software Engineer Jr.

## Context

During live testing (Feb 19 meetup), veteran Joe froze mid-wizard due to:
- **Save anxiety**: No visible indicator that data was being saved
- **Commitment anxiety**: Didn't know he could return later
- **No recovery UI**: Page reload lost wizard context

Maik raised PII concerns about uploaded documents.

All feedback was captured ad hoc — TPM noticed issues manually. No systematic pipeline exists. VetAssist has wizard infrastructure, sessions in DB, and crisis detection, but is NOT wired into the federation's thermal memory feedback pipeline.

The federation already has: thermal memory → A-MEM enrichment → consensus detection → kanban auto-creation → Jr execution. VetAssist just needs a bridge.

---

## Fix 1: Backend — Feedback API Endpoint (writes to thermal_memory_archive)

Create a new feedback endpoint that veterans can use to report issues. It writes directly to the federation's thermal memory for automatic enrichment and triage.

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/feedback.py`

```python
"""VetAssist Feedback API — bridges user reports to thermal memory pipeline."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])

# Temperature thresholds for veteran UX feedback
TEMP_SUGGESTION = 35.0    # Nice-to-have improvements
TEMP_UX_ISSUE = 55.0      # Usability problems (Joe's freeze)
TEMP_BUG = 65.0           # Functional bugs
TEMP_CRISIS = 80.0        # Crisis-level (data loss, PII exposure)

CATEGORY_TEMPS = {
    "suggestion": TEMP_SUGGESTION,
    "confused": TEMP_UX_ISSUE,
    "stuck": TEMP_UX_ISSUE,
    "bug": TEMP_BUG,
    "error": TEMP_BUG,
    "privacy": TEMP_CRISIS,
    "data_loss": TEMP_CRISIS,
}


class FeedbackRequest(BaseModel):
    category: str = Field(..., description="suggestion|confused|stuck|bug|error|privacy|data_loss")
    message: str = Field(..., max_length=2000)
    page_path: str = Field(..., description="Current page path, e.g. /wizard/abc123")
    wizard_step: Optional[int] = Field(None, description="Current wizard step number if in wizard")
    session_id: Optional[str] = Field(None, description="Wizard session ID if applicable")
    time_on_page_seconds: Optional[int] = Field(None, description="How long user was on this page")


class FeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: Optional[int] = None


def _get_db_conn():
    """Get connection to federation DB on bluefin."""
    import os
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "192.168.132.222"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "zammad_production"),
        user=os.getenv("DB_USER", "claude"),
        password=os.getenv("DB_PASSWORD", ""),
    )


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackRequest, user=Depends(get_current_user)):
    """Submit user feedback → thermal_memory_archive for federation triage."""
    temperature = CATEGORY_TEMPS.get(req.category, TEMP_UX_ISSUE)

    content = (
        f"[VETASSIST FEEDBACK] Category: {req.category}\n"
        f"Page: {req.page_path}\n"
    )
    if req.wizard_step is not None:
        content += f"Wizard Step: {req.wizard_step}\n"
    if req.time_on_page_seconds is not None:
        content += f"Time on page: {req.time_on_page_seconds}s\n"
    content += f"\nVeteran says: {req.message}"

    memory_hash = hashlib.sha256(content.encode()).hexdigest()

    metadata = {
        "source": "vetassist_feedback",
        "category": req.category,
        "page_path": req.page_path,
        "wizard_step": req.wizard_step,
        "session_id": req.session_id,
        "time_on_page_seconds": req.time_on_page_seconds,
        "user_id": str(user.id) if hasattr(user, "id") else "anonymous",
        "submitted_at": datetime.utcnow().isoformat(),
    }

    conn = None
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO thermal_memory_archive
               (original_content, temperature_score, memory_hash, sacred_pattern, metadata, created_at)
               VALUES (%s, %s, %s, %s, %s, NOW())
               RETURNING id""",
            (content, temperature, memory_hash, False, json.dumps(metadata)),
        )
        feedback_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"VetAssist feedback stored as thermal memory #{feedback_id} (temp={temperature})")
        return FeedbackResponse(status="ok", message="Thank you for your feedback.", feedback_id=feedback_id)
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Could not save feedback. Please try again.")
    finally:
        if conn:
            conn.close()


@router.post("/stuck-signal")
async def stuck_signal(
    page_path: str,
    wizard_step: Optional[int] = None,
    session_id: Optional[str] = None,
    pause_seconds: int = 0,
    user=Depends(get_current_user),
):
    """Automatic signal from frontend when user pauses >45 seconds.
    Lower temperature than explicit feedback — used for pattern detection."""
    if pause_seconds < 45:
        return {"status": "ignored", "reason": "pause too short"}

    content = (
        f"[VETASSIST STUCK SIGNAL] User paused {pause_seconds}s on {page_path}"
    )
    if wizard_step is not None:
        content += f" (wizard step {wizard_step})"

    memory_hash = hashlib.sha256(content.encode()).hexdigest()
    metadata = {
        "source": "vetassist_stuck_signal",
        "page_path": page_path,
        "wizard_step": wizard_step,
        "session_id": session_id,
        "pause_seconds": pause_seconds,
        "user_id": str(user.id) if hasattr(user, "id") else "anonymous",
        "submitted_at": datetime.utcnow().isoformat(),
    }

    conn = None
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO thermal_memory_archive
               (original_content, temperature_score, memory_hash, sacred_pattern, metadata, created_at)
               VALUES (%s, %s, %s, %s, %s, NOW())
               RETURNING id""",
            (content, 40.0, memory_hash, False, json.dumps(metadata)),
        )
        conn.commit()
        return {"status": "recorded"}
    except Exception as e:
        logger.error(f"Failed to store stuck signal: {e}")
        if conn:
            conn.rollback()
        return {"status": "error"}
    finally:
        if conn:
            conn.close()
```

---

## Fix 2: Backend — Register the feedback router

File: `/ganuda/vetassist/backend/app/api/v1/router.py`

```
<<<<<<< SEARCH
from app.api.v1.endpoints import wizard
=======
from app.api.v1.endpoints import wizard, feedback
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
api_router.include_router(wizard.router)
=======
api_router.include_router(wizard.router)
api_router.include_router(feedback.router)
>>>>>>> REPLACE
```

---

## Fix 3: Frontend — Feedback Widget Component

This floating button appears on every VetAssist page. Expands into a simple form.

Create `/ganuda/vetassist/frontend/app/components/FeedbackWidget.tsx`

```typescript
'use client';

import { useState, useRef, useEffect } from 'react';

interface FeedbackWidgetProps {
  pagePath: string;
  wizardStep?: number;
  sessionId?: string;
}

const CATEGORIES = [
  { value: 'suggestion', label: 'Suggestion', emoji: '💡' },
  { value: 'confused', label: "I'm confused", emoji: '❓' },
  { value: 'stuck', label: "I'm stuck", emoji: '🛑' },
  { value: 'bug', label: 'Something broke', emoji: '🐛' },
];

export default function FeedbackWidget({ pagePath, wizardStep, sessionId }: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [category, setCategory] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const pageLoadTime = useRef(Date.now());

  // Stuck detection: if user is idle >45s on wizard page, send signal
  useEffect(() => {
    if (!wizardStep) return;
    let timeout: NodeJS.Timeout;
    const resetTimer = () => {
      clearTimeout(timeout);
      timeout = setTimeout(async () => {
        const pauseSec = Math.floor((Date.now() - pageLoadTime.current) / 1000);
        try {
          await fetch('/api/v1/feedback/stuck-signal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              page_path: pagePath,
              wizard_step: wizardStep,
              session_id: sessionId,
              pause_seconds: pauseSec,
            }),
          });
        } catch {}
      }, 45000);
    };
    resetTimer();
    const events = ['mousemove', 'keydown', 'scroll', 'touchstart'];
    events.forEach(e => document.addEventListener(e, resetTimer));
    return () => {
      clearTimeout(timeout);
      events.forEach(e => document.removeEventListener(e, resetTimer));
    };
  }, [wizardStep, pagePath, sessionId]);

  const handleSubmit = async () => {
    if (!category || !message.trim()) {
      setError('Please select a category and enter your feedback.');
      return;
    }
    setError('');
    const timeOnPage = Math.floor((Date.now() - pageLoadTime.current) / 1000);
    try {
      const res = await fetch('/api/v1/feedback/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          message: message.trim(),
          page_path: pagePath,
          wizard_step: wizardStep ?? null,
          session_id: sessionId ?? null,
          time_on_page_seconds: timeOnPage,
        }),
      });
      if (res.ok) {
        setSubmitted(true);
        setTimeout(() => {
          setIsOpen(false);
          setSubmitted(false);
          setCategory('');
          setMessage('');
        }, 2000);
      } else {
        setError('Could not send feedback. Please try again.');
      }
    } catch {
      setError('Network error. Please try again.');
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-blue-600 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg hover:bg-blue-700 transition-colors"
        aria-label="Give feedback"
        title="Give feedback"
      >
        <span className="text-xl">?</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 bg-white border border-gray-300 rounded-lg shadow-xl w-80 p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-800">Share Feedback</h3>
        <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">&times;</button>
      </div>

      {submitted ? (
        <p className="text-green-700 text-center py-4">Thank you! Your feedback has been recorded.</p>
      ) : (
        <>
          <div className="flex gap-2 mb-3 flex-wrap">
            {CATEGORIES.map(c => (
              <button
                key={c.value}
                onClick={() => setCategory(c.value)}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  category === c.value
                    ? 'bg-blue-100 border-blue-500 text-blue-700'
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                }`}
              >
                {c.emoji} {c.label}
              </button>
            ))}
          </div>
          <textarea
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder="Tell us what happened..."
            className="w-full border border-gray-300 rounded p-2 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
            maxLength={2000}
          />
          {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
          <button
            onClick={handleSubmit}
            className="mt-2 w-full bg-blue-600 text-white rounded py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Send Feedback
          </button>
        </>
      )}
    </div>
  );
}
```

---

## Fix 4: Frontend — Wire FeedbackWidget into Wizard Layout

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

Add the import at the top of the file, after the existing imports:

```
<<<<<<< SEARCH
import ProgressBar from './components/ProgressBar';
=======
import ProgressBar from './components/ProgressBar';
import FeedbackWidget from '../../components/FeedbackWidget';
>>>>>>> REPLACE
```

Add the widget at the bottom of the return JSX, just before the closing tag of the outermost wrapper:

```
<<<<<<< SEARCH
      </div>
    </div>
  );
}
=======
      </div>
      <FeedbackWidget
        pagePath={`/wizard/${sessionId}`}
        wizardStep={currentStep}
        sessionId={sessionId as string}
      />
    </div>
  );
}
>>>>>>> REPLACE
```

---

## Manual Steps (TPM)

After Jr completes the code changes:

1. **On redfin** — restart VetAssist backend:
```text
sudo systemctl restart vetassist-backend
```

2. **On redfin** — rebuild VetAssist frontend:
```text
cd /ganuda/vetassist/frontend && npm run build && sudo systemctl restart vetassist-frontend
```

3. **Verify** feedback endpoint works:
```text
curl -X POST http://localhost:8443/api/v1/feedback/submit \
  -H "Content-Type: application/json" \
  -d '{"category":"suggestion","message":"test feedback","page_path":"/wizard/test"}'
```

4. **Check thermal memory** for the test entry:
```text
psql -h 192.168.132.222 -U claude -d zammad_production \
  -c "SELECT id, LEFT(original_content, 100), temperature_score FROM thermal_memory_archive WHERE original_content LIKE '%VETASSIST FEEDBACK%' ORDER BY id DESC LIMIT 5;"
```

---

## What This Does NOT Cover (Future Work)

- **Outcome tracking table + 30/90/180 day emails** — separate Jr instruction (Phase 3 roadmap)
- **Feedback consensus daemon** — the existing A-MEM + memory_consolidation_daemon already handle semantic grouping; a VetAssist-specific daemon can be added when volume justifies it
- **A/B testing** — Phase 4 roadmap item
- **NPS/CSAT surveys** — consider after 10+ beta testers

## Cherokee Principle

**Gadugi** — The feedback widget gives every veteran a voice. Their experience shapes the tool that serves them. No feedback is wasted; every signal enters the thermal memory and rises or falls on its own temperature.
