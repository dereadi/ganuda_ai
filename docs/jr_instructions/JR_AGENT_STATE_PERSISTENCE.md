# Jr Task: Implement Agent State Persistence

**Ticket:** #1697
**Priority:** P2
**Node:** All nodes
**Created:** December 21, 2025
**Specialist:** Spider (Cultural Integration)

---

## Research Basis

**Source:** [Emergent Collective Memory in Decentralized Multi-Agent AI Systems](https://arxiv.org/abs/2512.10166)

**Key Finding:**
- Individual memory alone = 68.7% performance improvement over baseline
- Environmental traces WITHOUT memory = COMPLETE FAILURE
- "Traces require cognitive infrastructure for interpretation"

**Translation:** Our thermal memory (environmental traces) is necessary but not sufficient. Jrs need their own persistent state to interpret and build upon thermal memory effectively.

---

## Current State

Jrs are **stateless**:
- Each Jr task starts fresh
- No memory of previous tasks
- Relies entirely on thermal memory for context
- Cannot build expertise over time

---

## Proposed Architecture

### Agent State Schema

```sql
-- New table: jr_agent_state
CREATE TABLE jr_agent_state (
    agent_id VARCHAR(64) PRIMARY KEY,
    node_name VARCHAR(32) NOT NULL,
    specialization VARCHAR(64),

    -- Persistent memory
    working_memory JSONB DEFAULT '{}',      -- Current task context
    episodic_memory JSONB DEFAULT '[]',     -- Recent task history (last N tasks)
    semantic_memory JSONB DEFAULT '{}',     -- Learned patterns/preferences

    -- Performance tracking
    tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    specialization_scores JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Index for fast lookups
CREATE INDEX idx_jr_agent_node ON jr_agent_state(node_name);
CREATE INDEX idx_jr_agent_specialization ON jr_agent_state(specialization);
```

### Memory Types

**1. Working Memory** (short-term)
- Current task context
- Variables and intermediate results
- Cleared after task completion, summary retained

**2. Episodic Memory** (medium-term)
- Last 50 tasks performed
- Outcomes and learnings
- Enables "I did something similar before" recall

**3. Semantic Memory** (long-term)
- Learned patterns across tasks
- File locations frequently accessed
- Command sequences that work well
- Error patterns to avoid

---

## Implementation Steps

### Phase 1: Database Schema

```bash
# On bluefin
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production << 'EOF'

CREATE TABLE IF NOT EXISTS jr_agent_state (
    agent_id VARCHAR(64) PRIMARY KEY,
    node_name VARCHAR(32) NOT NULL,
    specialization VARCHAR(64),
    working_memory JSONB DEFAULT '{}',
    episodic_memory JSONB DEFAULT '[]',
    semantic_memory JSONB DEFAULT '{}',
    tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    specialization_scores JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_jr_agent_node ON jr_agent_state(node_name);

EOF
```

### Phase 2: Jr Executor Integration

Modify `/ganuda/jr_executor/` to:

```python
# jr_executor/state_manager.py

import psycopg2
import json
from datetime import datetime

class JrStateManager:
    def __init__(self, agent_id, node_name):
        self.agent_id = agent_id
        self.node_name = node_name
        self.conn = self._connect()
        self._ensure_state_exists()

    def _connect(self):
        return psycopg2.connect(
            host="192.168.132.222",
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )

    def _ensure_state_exists(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_agent_state (agent_id, node_name)
                VALUES (%s, %s)
                ON CONFLICT (agent_id) DO NOTHING
            """, (self.agent_id, self.node_name))
            self.conn.commit()

    def load_state(self):
        """Load agent's persistent state"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT working_memory, episodic_memory, semantic_memory,
                       tasks_completed, specialization_scores
                FROM jr_agent_state WHERE agent_id = %s
            """, (self.agent_id,))
            row = cur.fetchone()
            if row:
                return {
                    "working_memory": row[0],
                    "episodic_memory": row[1],
                    "semantic_memory": row[2],
                    "tasks_completed": row[3],
                    "specialization_scores": row[4]
                }
        return None

    def save_task_outcome(self, task_summary, success, learnings=None):
        """Save task to episodic memory"""
        with self.conn.cursor() as cur:
            # Add to episodic memory (keep last 50)
            cur.execute("""
                UPDATE jr_agent_state
                SET episodic_memory = (
                    SELECT jsonb_agg(elem)
                    FROM (
                        SELECT elem FROM jsonb_array_elements(
                            episodic_memory || %s::jsonb
                        ) elem
                        ORDER BY elem->>'timestamp' DESC
                        LIMIT 50
                    ) sub
                ),
                tasks_completed = tasks_completed + 1,
                success_rate = (success_rate * tasks_completed + %s) / (tasks_completed + 1),
                last_active = NOW()
                WHERE agent_id = %s
            """, (
                json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "summary": task_summary,
                    "success": success,
                    "learnings": learnings
                }),
                1.0 if success else 0.0,
                self.agent_id
            ))
            self.conn.commit()

    def update_semantic_memory(self, key, value):
        """Update long-term learned patterns"""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE jr_agent_state
                SET semantic_memory = semantic_memory || %s::jsonb
                WHERE agent_id = %s
            """, (json.dumps({key: value}), self.agent_id))
            self.conn.commit()

    def get_relevant_episodes(self, keywords, limit=5):
        """Recall relevant past tasks"""
        state = self.load_state()
        if not state:
            return []

        relevant = []
        for episode in state["episodic_memory"]:
            summary = episode.get("summary", "").lower()
            if any(kw.lower() in summary for kw in keywords):
                relevant.append(episode)

        return relevant[:limit]
```

### Phase 3: Integration with Jr Tasks

```python
# In jr task execution flow

from state_manager import JrStateManager

def execute_jr_task(task_id, task_content):
    # Initialize state manager
    agent_id = f"jr-{get_node_name()}-{os.getpid()}"
    state_mgr = JrStateManager(agent_id, get_node_name())

    # Load previous state
    state = state_mgr.load_state()

    # Check for relevant past experience
    keywords = extract_keywords(task_content)
    past_episodes = state_mgr.get_relevant_episodes(keywords)

    if past_episodes:
        # Inject past experience into context
        context = f"Relevant past experience:\n"
        for ep in past_episodes:
            context += f"- {ep['summary']} (success: {ep['success']})\n"
            if ep.get('learnings'):
                context += f"  Learnings: {ep['learnings']}\n"

    # Execute task with enhanced context
    result = do_task(task_content, additional_context=context)

    # Save outcome
    state_mgr.save_task_outcome(
        task_summary=summarize(task_content),
        success=result.success,
        learnings=result.learnings
    )

    return result
```

---

## Interaction with Thermal Memory

The two systems are complementary:

| System | Scope | Persistence | Purpose |
|--------|-------|-------------|---------|
| Thermal Memory | Federation-wide | Permanent (with decay) | Collective knowledge |
| Agent State | Individual agent | Persistent | Individual expertise |

**Flow:**
1. Jr reads thermal memory for collective context
2. Jr checks own episodic memory for relevant past tasks
3. Jr executes task with both contexts
4. Jr saves outcome to own episodic memory
5. If significant, Jr writes to thermal memory (collective)

---

## Success Criteria

1. Jrs can recall relevant past tasks when facing similar work
2. Performance improves over time (measurable via success_rate)
3. Specialization emerges (Jrs become better at certain task types)
4. Reduced redundant work (don't re-solve solved problems)

---

## Verification

```sql
-- Check agent state accumulation
SELECT agent_id, tasks_completed, success_rate,
       jsonb_array_length(episodic_memory) as episodes
FROM jr_agent_state
ORDER BY tasks_completed DESC;

-- See what agents have learned
SELECT agent_id, semantic_memory
FROM jr_agent_state
WHERE semantic_memory != '{}';
```

---

*For Seven Generations - Cherokee AI Federation*
