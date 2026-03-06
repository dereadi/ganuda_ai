# Jr Instruction: VetAssist Feedback Widget — Create New Files (v2, Part 1 of 2)

**Task ID:** FEEDBACK-CREATE-v2
**Kanban:** #1854
**Priority:** 5
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create the backend endpoint and frontend component for the VetAssist feedback system. This is Part 1 (Create new files only). Part 2 wires them into existing code.

Per KB-EXECUTOR-MIXED-STEP-TYPES-SKIP-BUG: Create and SEARCH/REPLACE blocks must be in separate instructions.

---

## Step 1: Create feedback endpoint

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/feedback.py`

```python
"""
VetAssist Feedback Endpoint — Cherokee AI Federation
Stores user feedback and bridges to thermal memory for learning.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import hashlib

router = APIRouter(prefix="/feedback", tags=["feedback"])

# DB connection (same pattern as wizard.py)
import os
import sys
sys.path.insert(0, '/ganuda/lib')
from secrets_loader import get_db_config


def get_db_conn():
    return psycopg2.connect(**get_db_config())


class FeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    page: str = Field(..., description="Which page: wizard, chat, calculator, knowledge")
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    comment: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, description="bug, feature, praise, confusion")


class FeedbackResponse(BaseModel):
    id: int
    received: bool = True
    message: str = "Thank you for your feedback"


@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(data: FeedbackRequest):
    """Submit user feedback. Stored in DB and bridged to thermal memory."""
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Store in vetassist_feedback table
            cur.execute("""
                INSERT INTO vetassist_feedback
                    (session_id, page, rating, comment, category, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (data.session_id, data.page, data.rating, data.comment, data.category))
            row = cur.fetchone()
            feedback_id = row['id']

            # Bridge to thermal memory for federation learning
            if data.rating <= 2 or data.comment:
                content = f"VETASSIST FEEDBACK ({data.page}): Rating {data.rating}/5"
                if data.comment:
                    content += f" — {data.comment[:500]}"
                memory_hash = hashlib.sha256(
                    f"feedback-{feedback_id}-{datetime.now().isoformat()}".encode()
                ).hexdigest()
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                        (original_content, temperature_score, metadata,
                         source_node, memory_type, memory_hash, created_at)
                    VALUES (%s, %s, %s, 'redfin', 'episodic', %s, NOW())
                """, (
                    content[:2000],
                    70.0 if data.rating <= 2 else 50.0,
                    json.dumps({
                        "type": "user_feedback",
                        "page": data.page,
                        "rating": data.rating,
                        "category": data.category,
                        "feedback_id": feedback_id
                    }),
                    memory_hash
                ))

            conn.commit()
        conn.close()
        return FeedbackResponse(id=feedback_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 2: Create feedback table migration

Create `/ganuda/vetassist/backend/migrations/004_create_feedback_table.sql`

```sql
-- VetAssist Feedback Table
-- Stores user feedback for product improvement and thermal memory bridge

CREATE TABLE IF NOT EXISTS vetassist_feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    page VARCHAR(50) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vetassist_feedback_page ON vetassist_feedback (page);
CREATE INDEX IF NOT EXISTS idx_vetassist_feedback_rating ON vetassist_feedback (rating);
```

---

## Step 3: Create FeedbackWidget component

Create `/ganuda/vetassist/frontend/app/components/FeedbackWidget.tsx`

```typescript
"use client";

import { useState } from "react";
import { MessageSquare, Star, X, Send, Loader2 } from "lucide-react";

interface FeedbackWidgetProps {
  page: string;
  sessionId?: string;
}

export default function FeedbackWidget({ page, sessionId }: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

  const submit = async () => {
    if (rating === 0) return;
    setSubmitting(true);
    try {
      await fetch(`${apiUrl}/feedback/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          page,
          rating,
          comment: comment || null,
          category,
        }),
      });
      setSubmitted(true);
      setTimeout(() => {
        setIsOpen(false);
        setSubmitted(false);
        setRating(0);
        setComment("");
        setCategory(null);
      }, 2000);
    } catch {
      // Silently fail — feedback is non-critical
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white rounded-full p-3 shadow-lg hover:bg-blue-700 transition-colors z-50"
        title="Give feedback"
      >
        <MessageSquare className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 bg-white rounded-lg shadow-xl border border-gray-200 p-4 w-80 z-50">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-medium text-gray-900 text-sm">How is this working for you?</h3>
        <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
          <X className="h-4 w-4" />
        </button>
      </div>

      {submitted ? (
        <p className="text-green-600 text-sm text-center py-4">Thank you for your feedback!</p>
      ) : (
        <>
          <div className="flex gap-1 justify-center mb-3">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                onClick={() => setRating(n)}
                onMouseEnter={() => setHoverRating(n)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-1"
              >
                <Star
                  className={`h-6 w-6 ${
                    n <= (hoverRating || rating)
                      ? "fill-yellow-400 text-yellow-400"
                      : "text-gray-300"
                  }`}
                />
              </button>
            ))}
          </div>

          <div className="flex gap-1 flex-wrap mb-3">
            {["bug", "confusion", "feature", "praise"].map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(category === cat ? null : cat)}
                className={`text-xs px-2 py-1 rounded-full border ${
                  category === cat
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-500 hover:border-gray-300"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell us more (optional)"
            className="w-full text-sm border border-gray-200 rounded-md p-2 mb-3 resize-none"
            rows={2}
            maxLength={2000}
          />

          <button
            onClick={submit}
            disabled={rating === 0 || submitting}
            className={`w-full flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium text-white ${
              rating === 0 || submitting ? "bg-gray-300" : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Send Feedback
          </button>
        </>
      )}
    </div>
  );
}
```

---

## Verification

```text
ls -la /ganuda/vetassist/backend/app/api/v1/endpoints/feedback.py
ls -la /ganuda/vetassist/frontend/app/components/FeedbackWidget.tsx
ls -la /ganuda/vetassist/backend/migrations/004_create_feedback_table.sql
```

## What NOT to Change

- Do NOT modify any existing files in this instruction
- Do NOT add router registration yet (Part 2)
- Do NOT add FeedbackWidget to wizard page yet (Part 2)
