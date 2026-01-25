# JR Instruction: Enhance Jr with Anthropic Harness Patterns + Haiku

**Priority**: P1 - High
**Assigned To**: Software Engineer Jr.
**Created**: January 21, 2026
**Status**: Ready for Execution
**Kanban Task**: SAG-JR-008

## Executive Summary

Enhance the Jr task execution system with:
1. **Claude Haiku integration** for faster, cheaper task execution
2. **Session progress tracking** from Anthropic's long-running agent harness
3. **Feature lists with pass/fail states** for task verification
4. **Jr Progress tab** in SAG dashboard

## Background

The Anthropic harness patterns from their SWE benchmark provide excellent patterns for:
- Long-running agent session management
- Progress tracking with checkpoints
- Feature verification with pass/fail states
- Graceful recovery from failures

Claude Haiku (claude-3-haiku) is significantly faster and cheaper than Opus/Sonnet for:
- Simple code generation tasks
- Document formatting
- Routine analysis
- Quick lookups

## Current Architecture

### Jr Task Executor
- **Location**: `/ganuda/jr_executor/jr_task_executor.py`
- **LLM**: Uses local vLLM (Qwen 32B) via port 8000
- **Models**: Single model, no tiering
- **Progress**: Basic logging, no structured tracking

### What's Missing
- Model tiering (Haiku for simple, Opus for complex)
- Session state persistence
- Feature verification checkpoints
- Dashboard visibility into Jr progress

## Implementation Tasks

### Task 1: Add Haiku Support via Anthropic API

**New File**: `/ganuda/jr_executor/llm_router.py`

```python
"""
LLM Router - Routes tasks to appropriate model based on complexity.

Tier 1 (Haiku): Simple tasks, fast turnaround
- Document formatting
- Simple code snippets
- Lookups and summaries

Tier 2 (Local Qwen): Standard tasks
- Code generation
- Analysis tasks
- Multi-step reasoning

Tier 3 (Opus): Complex tasks
- Architecture decisions
- Security-critical code
- Multi-file refactoring
"""

import os
from enum import Enum
from typing import Optional
import anthropic
import requests

class ModelTier(Enum):
    HAIKU = "haiku"      # Fast, cheap, simple tasks
    LOCAL = "local"       # Local Qwen 32B
    OPUS = "opus"         # Complex, high-stakes

# Anthropic API key from environment or secrets
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Local vLLM endpoint
LOCAL_VLLM_URL = "http://localhost:8000/v1/chat/completions"
LOCAL_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"

# Task complexity indicators
SIMPLE_TASK_KEYWORDS = [
    'format', 'summarize', 'list', 'simple', 'quick',
    'lookup', 'convert', 'basic', 'template'
]

COMPLEX_TASK_KEYWORDS = [
    'architect', 'security', 'refactor', 'multi-file',
    'database schema', 'api design', 'critical'
]


def classify_task_complexity(task: dict) -> ModelTier:
    """
    Classify task complexity to determine model tier.
    """
    title = (task.get('title', '') + ' ' + task.get('instructions', '')).lower()

    # Check for complex indicators
    for keyword in COMPLEX_TASK_KEYWORDS:
        if keyword in title:
            return ModelTier.OPUS

    # Check for simple indicators
    simple_count = sum(1 for kw in SIMPLE_TASK_KEYWORDS if kw in title)
    if simple_count >= 2:
        return ModelTier.HAIKU

    # Default to local model
    return ModelTier.LOCAL


def call_haiku(prompt: str, max_tokens: int = 4096) -> str:
    """Call Claude Haiku via Anthropic API"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def call_local(prompt: str, max_tokens: int = 4096) -> str:
    """Call local vLLM Qwen model"""
    response = requests.post(
        LOCAL_VLLM_URL,
        json={
            "model": LOCAL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=120
    )
    return response.json()['choices'][0]['message']['content']


def call_opus(prompt: str, max_tokens: int = 8192) -> str:
    """Call Claude Opus via Anthropic API"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def route_and_call(task: dict, prompt: str) -> tuple[str, ModelTier]:
    """
    Route task to appropriate model and execute.

    Returns:
        Tuple of (response_text, model_tier_used)
    """
    tier = classify_task_complexity(task)

    if tier == ModelTier.HAIKU:
        return call_haiku(prompt), tier
    elif tier == ModelTier.OPUS:
        return call_opus(prompt), tier
    else:
        return call_local(prompt), tier
```

### Task 2: Session Progress Tracking

**New File**: `/ganuda/jr_executor/session_tracker.py`

```python
"""
Session Tracker - Track Jr task execution progress.

Based on Anthropic harness patterns for long-running agents.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    step_id: str
    name: str
    description: str
    status: StepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TaskSession:
    session_id: str
    task_id: str
    jr_name: str
    model_tier: str
    status: str  # pending, running, completed, failed
    steps: List[ExecutionStep]
    created_at: datetime
    updated_at: datetime
    total_tokens: int = 0


class SessionTracker:
    """
    Tracks Jr task execution sessions with step-by-step progress.
    """

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def create_session(self, task_id: str, jr_name: str, steps: List[str]) -> TaskSession:
        """Create new execution session with defined steps"""
        session = TaskSession(
            session_id=str(uuid.uuid4()),
            task_id=task_id,
            jr_name=jr_name,
            model_tier="pending",
            status="pending",
            steps=[
                ExecutionStep(
                    step_id=str(uuid.uuid4()),
                    name=f"Step {i+1}",
                    description=step,
                    status=StepStatus.PENDING
                )
                for i, step in enumerate(steps)
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._save_session(session)
        return session

    def start_step(self, session: TaskSession, step_index: int) -> None:
        """Mark a step as in progress"""
        session.steps[step_index].status = StepStatus.IN_PROGRESS
        session.steps[step_index].started_at = datetime.now()
        session.updated_at = datetime.now()
        self._save_session(session)

    def complete_step(self, session: TaskSession, step_index: int,
                     passed: bool, output: str = None, error: str = None) -> None:
        """Mark a step as completed (passed or failed)"""
        step = session.steps[step_index]
        step.status = StepStatus.PASSED if passed else StepStatus.FAILED
        step.completed_at = datetime.now()
        step.output = output
        step.error = error
        session.updated_at = datetime.now()
        self._save_session(session)

    def get_progress(self, session: TaskSession) -> dict:
        """Get progress summary"""
        total = len(session.steps)
        passed = sum(1 for s in session.steps if s.status == StepStatus.PASSED)
        failed = sum(1 for s in session.steps if s.status == StepStatus.FAILED)
        pending = sum(1 for s in session.steps if s.status == StepStatus.PENDING)

        return {
            "session_id": session.session_id,
            "total_steps": total,
            "passed": passed,
            "failed": failed,
            "pending": pending,
            "progress_pct": round((passed + failed) / total * 100, 1) if total > 0 else 0,
            "status": session.status
        }

    def _save_session(self, session: TaskSession) -> None:
        """Save session to database"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO jr_execution_sessions
            (session_id, task_id, jr_name, model_tier, status, steps,
             total_tokens, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                status = EXCLUDED.status,
                steps = EXCLUDED.steps,
                total_tokens = EXCLUDED.total_tokens,
                updated_at = EXCLUDED.updated_at
        """, (
            session.session_id,
            session.task_id,
            session.jr_name,
            session.model_tier,
            session.status,
            json.dumps([asdict(s) for s in session.steps], default=str),
            session.total_tokens,
            session.created_at,
            session.updated_at
        ))

        conn.commit()
        cur.close()
        conn.close()
```

### Task 3: Database Schema

**SQL Migration**: `/ganuda/sql/jr_session_tracking.sql`

```sql
-- Jr Execution Sessions Table
CREATE TABLE IF NOT EXISTS jr_execution_sessions (
    session_id UUID PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    jr_name VARCHAR(100) NOT NULL,
    model_tier VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    steps JSONB,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_jr_sessions_status ON jr_execution_sessions(status);
CREATE INDEX IF NOT EXISTS idx_jr_sessions_jr_name ON jr_execution_sessions(jr_name);
CREATE INDEX IF NOT EXISTS idx_jr_sessions_created ON jr_execution_sessions(created_at DESC);

-- View for active sessions
CREATE OR REPLACE VIEW v_jr_active_sessions AS
SELECT
    session_id,
    task_id,
    jr_name,
    model_tier,
    status,
    jsonb_array_length(steps) as total_steps,
    (SELECT COUNT(*) FROM jsonb_array_elements(steps) s WHERE s->>'status' = 'passed') as passed_steps,
    (SELECT COUNT(*) FROM jsonb_array_elements(steps) s WHERE s->>'status' = 'failed') as failed_steps,
    created_at,
    updated_at
FROM jr_execution_sessions
WHERE status IN ('pending', 'running')
ORDER BY created_at DESC;
```

### Task 4: SAG Dashboard Jr Progress Tab

**Add to SAG Interface** - New tab showing:

```
┌─────────────────────────────────────────────────────────────┐
│ Jr Progress Monitor                              [Refresh]  │
├─────────────────────────────────────────────────────────────┤
│ Active Sessions: 3    Completed Today: 12    Failed: 1     │
├─────────────────────────────────────────────────────────────┤
│ Session          │ Jr          │ Model  │ Progress         │
│ ──────────────── │ ─────────── │ ────── │ ──────────────── │
│ abc123...        │ SoftwareEng │ Haiku  │ ████████░░ 80%   │
│   Step 3/4: Generate tests     │ Status: IN_PROGRESS       │
│ ──────────────── │ ─────────── │ ────── │ ──────────────── │
│ def456...        │ DevOps Jr   │ Local  │ ██████████ 100%  │
│   Completed in 45s             │ Status: COMPLETED ✓       │
│ ──────────────── │ ─────────── │ ────── │ ──────────────── │
│ ghi789...        │ Audio Jr    │ Haiku  │ ████░░░░░░ 40%   │
│   Step 2/5: Process audio      │ Status: FAILED ✗          │
│   Error: File not found        │                           │
└─────────────────────────────────────────────────────────────┘
```

**API Endpoints**:

```python
@app.route('/api/jr/sessions')
def get_jr_sessions():
    """Get all active Jr sessions"""
    pass

@app.route('/api/jr/sessions/<session_id>')
def get_session_detail(session_id):
    """Get detailed session with all steps"""
    pass

@app.route('/api/jr/stats')
def get_jr_stats():
    """Get Jr execution statistics"""
    pass
```

## Integration with Existing Code

### Modify jr_task_executor.py

Add to the main execution loop:

```python
from llm_router import route_and_call, classify_task_complexity
from session_tracker import SessionTracker, TaskSession

# Initialize tracker
tracker = SessionTracker(DB_CONFIG)

def execute_task(task: dict) -> dict:
    # Create session with steps
    steps = extract_steps_from_task(task)
    session = tracker.create_session(task['task_id'], self.agent_id, steps)

    # Route to appropriate model
    tier = classify_task_complexity(task)
    session.model_tier = tier.value

    results = []
    for i, step in enumerate(steps):
        tracker.start_step(session, i)
        try:
            # Execute step with routed model
            result = execute_step(step, tier)
            tracker.complete_step(session, i, passed=True, output=result)
            results.append(result)
        except Exception as e:
            tracker.complete_step(session, i, passed=False, error=str(e))
            # Decide whether to continue or abort

    return {"session": session.session_id, "results": results}
```

## Environment Setup

### Anthropic API Key

Add to environment or secrets vault:

```bash
# /ganuda/secrets/anthropic_api_key (or environment variable)
export ANTHROPIC_API_KEY=sk-ant-...
```

## Testing

### Test 1: Model Routing
```python
from llm_router import classify_task_complexity, ModelTier

# Should route to Haiku
task1 = {"title": "Format this simple document", "instructions": "Convert to markdown"}
assert classify_task_complexity(task1) == ModelTier.HAIKU

# Should route to Opus
task2 = {"title": "Architect the security system", "instructions": "Design auth flow"}
assert classify_task_complexity(task2) == ModelTier.OPUS
```

### Test 2: Session Tracking
```python
from session_tracker import SessionTracker

tracker = SessionTracker(DB_CONFIG)
session = tracker.create_session("test-123", "SoftwareEng", ["Step 1", "Step 2"])
tracker.start_step(session, 0)
tracker.complete_step(session, 0, passed=True, output="Done")
progress = tracker.get_progress(session)
assert progress["passed"] == 1
```

## Success Criteria

- [ ] Haiku successfully executes simple tasks (< 2s response)
- [ ] Task routing correctly identifies complexity
- [ ] Session tracking persists to database
- [ ] SAG dashboard shows live Jr progress
- [ ] Failed steps are captured with error details
- [ ] Cost reduction visible (Haiku tasks cheaper)

## Files to Create/Modify

| File | Action |
|------|--------|
| `/ganuda/jr_executor/llm_router.py` | Create |
| `/ganuda/jr_executor/session_tracker.py` | Create |
| `/ganuda/jr_executor/jr_task_executor.py` | Modify |
| `/ganuda/sql/jr_session_tracking.sql` | Create |
| `/ganuda/home/dereadi/sag_unified_interface/templates/jr_progress.html` | Create |
| `/ganuda/home/dereadi/sag_unified_interface/app.py` | Modify |

---

*Cherokee AI Federation - For Seven Generations*
*"Faster execution, smarter routing, better visibility."*
