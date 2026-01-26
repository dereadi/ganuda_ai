# Ultrathink: Jr Graduated Priority Orchestrator

**Date:** 2026-01-25
**Council Vote:** PROCEED WITH CAUTION (70% confidence)
**Author:** TPM Claude

---

## Problem Statement

Jr workers (Software Engineer, Research, Infrastructure) currently have no systemd management. They're started manually and die when sessions end, causing:
1. Tasks stuck in pending state
2. Manual intervention required to restart workers
3. No resource coordination between concurrent workers
4. Multiple duplicate workers causing race conditions

---

## Proposed Solution: Graduated Priority Queue Orchestrator

### Core Concept

A single daemon manages all Jr workers with dynamic resource allocation following a **halving priority pattern**:

```
Position 1: 50% of LLM inference capacity
Position 2: 25%
Position 3: 12.5%
Position 4: 6.25%
...and so on
```

When a task completes, all lower-priority tasks **promote upward**:

```
Before:                    After Task A completes:
  Task A: 50% ─────────►   Task B: 50% (promoted)
  Task B: 25%              Task C: 25% (promoted)
  Task C: 12.5%            Task D: 12.5% (promoted)
  Task D: 6.25%            [empty slot]
```

### Council Guidance

1. **Per-task priority** (not per-Jr-type) - A Research Jr task can have higher priority than a Software Engineer Jr task
2. **Token bucket rate limiting** - Each task gets a token bucket sized to its priority percentage
3. **DoS protection** - Prevent runaway tasks from consuming all resources

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    systemd service                          │
│                 jr-orchestrator.service                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   JrOrchestrator Daemon                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Priority Queue Manager                  │   │
│  │  - Tracks active tasks across all workers           │   │
│  │  - Assigns priority slots (50%, 25%, 12.5%...)     │   │
│  │  - Handles promotion on completion                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Token Bucket Controller                 │   │
│  │  - Rate limits LLM API calls per worker             │   │
│  │  - Refills buckets based on priority percentage     │   │
│  │  - Prevents any single task from monopolizing       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Worker Process Manager                  │   │
│  │  - Spawns/monitors worker subprocesses              │   │
│  │  - Handles worker crashes (restart with backoff)    │   │
│  │  - IPC for priority updates                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ SE Jr.  │   │Research │   │ Infra   │   │IT Triad │
    │ Worker  │   │   Jr.   │   │   Jr.   │   │   Jr.   │
    └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

### Token Bucket Implementation

```python
class GraduatedTokenBucket:
    """
    Token bucket that refills based on priority position.

    Position 1 (50%): 100 tokens/minute
    Position 2 (25%): 50 tokens/minute
    Position 3 (12.5%): 25 tokens/minute
    ...
    """

    BASE_RATE = 100  # tokens per minute for position 1

    def __init__(self, position: int):
        self.position = position
        self.tokens = 0
        self.max_tokens = self._calculate_max()
        self.refill_rate = self._calculate_rate()

    def _calculate_rate(self) -> float:
        # 50%, 25%, 12.5%, 6.25%...
        return self.BASE_RATE * (0.5 ** (self.position - 1))

    def _calculate_max(self) -> int:
        # Burst capacity proportional to rate
        return int(self._calculate_rate() * 2)

    def try_consume(self, tokens: int = 1) -> bool:
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def promote(self, new_position: int):
        """Called when higher-priority task completes."""
        self.position = new_position
        self.refill_rate = self._calculate_rate()
        self.max_tokens = self._calculate_max()
```

### Priority Promotion Logic

```python
class PriorityQueueManager:
    """Manages task priorities with automatic promotion."""

    def __init__(self):
        self.active_tasks: List[TaskSlot] = []

    def add_task(self, task_id: str, worker_name: str) -> int:
        """Add task to queue, returns assigned position."""
        position = len(self.active_tasks) + 1
        slot = TaskSlot(task_id, worker_name, position)
        self.active_tasks.append(slot)
        return position

    def complete_task(self, task_id: str) -> List[Promotion]:
        """Remove task and promote all below it."""
        promotions = []

        # Find and remove the completed task
        completed_idx = None
        for i, slot in enumerate(self.active_tasks):
            if slot.task_id == task_id:
                completed_idx = i
                break

        if completed_idx is not None:
            self.active_tasks.pop(completed_idx)

            # Promote everyone below
            for i in range(completed_idx, len(self.active_tasks)):
                old_pos = self.active_tasks[i].position
                new_pos = i + 1  # Positions are 1-indexed
                self.active_tasks[i].position = new_pos
                promotions.append(Promotion(
                    task_id=self.active_tasks[i].task_id,
                    old_position=old_pos,
                    new_position=new_pos
                ))

        return promotions
```

### Urgent Task Handling (Queue Jumping)

For urgent tasks (sacred_fire_priority > 8):

```python
def insert_urgent(self, task_id: str, worker_name: str) -> List[Promotion]:
    """Insert urgent task at position 1, demote all others."""
    demotions = []

    # Demote all existing tasks
    for slot in self.active_tasks:
        old_pos = slot.position
        slot.position += 1
        demotions.append(Demotion(slot.task_id, old_pos, slot.position))

    # Insert at position 1
    self.active_tasks.insert(0, TaskSlot(task_id, worker_name, 1))

    return demotions
```

---

## Database Schema Addition

```sql
-- Track active task priorities
CREATE TABLE jr_task_priorities (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES jr_work_queue(id),
    worker_name VARCHAR(100),
    priority_position INTEGER NOT NULL,
    token_bucket_tokens FLOAT DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),

    UNIQUE(task_id)
);

-- Index for quick position lookups
CREATE INDEX idx_priority_position ON jr_task_priorities(priority_position);
```

---

## Systemd Service

```ini
[Unit]
Description=Cherokee AI Jr Orchestrator - Graduated Priority Queue
After=network.target postgresql.service vllm-cherokee.service
Wants=vllm-cherokee.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_orchestrator.py
Restart=always
RestartSec=30
StandardOutput=append:/ganuda/logs/jr_orchestrator.log
StandardError=append:/ganuda/logs/jr_orchestrator.log
SyslogIdentifier=jr-orchestrator

[Install]
WantedBy=multi-user.target
```

---

## Implementation Plan

### Phase 1: Core Orchestrator (P0)
- [ ] Create `jr_orchestrator.py` with process management
- [ ] Implement token bucket rate limiting
- [ ] Create systemd service file
- [ ] Database schema for priority tracking

### Phase 2: Priority Management (P1)
- [ ] Implement graduated priority queue
- [ ] Add promotion/demotion logic
- [ ] IPC mechanism for priority updates to workers
- [ ] Urgent task queue-jumping

### Phase 3: Monitoring & Safety (P1)
- [ ] Heartbeat monitoring for stuck workers
- [ ] Automatic restart with exponential backoff
- [ ] Resource abuse detection (DoS protection)
- [ ] Grafana dashboard for queue visualization

---

## Success Criteria

1. Single systemd service manages all Jr workers
2. Tasks complete in priority order (50% → 25% → 12.5%)
3. Completions trigger automatic promotion
4. No manual intervention needed for 24/7 operation
5. Urgent tasks can jump the queue
6. No resource thrashing or starvation

---

## For Seven Generations

A well-orchestrated workforce serves the people continuously. Each Jr contributes according to need, promotes when others complete, and the work flows like water - always finding its level.
