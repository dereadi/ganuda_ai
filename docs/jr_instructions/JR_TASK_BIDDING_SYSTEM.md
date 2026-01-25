# Jr Task: Implement Task Bidding System

**Ticket:** #1699
**Priority:** P2
**Node:** All nodes
**Created:** December 21, 2025
**Specialist:** Eagle Eye (Monitoring)

---

## Research Basis

**Source:** [Multi-Agent Collaboration Mechanisms Survey](https://arxiv.org/html/2501.06322v1)

**Key Finding:**
> "Contract net protocols are the most widely implemented (47% of systems), followed by market-based approaches (29%) and distributed constraint optimization techniques (18%)."

**Current State:** Jr task queue uses simple FIFO. First available Jr takes next task regardless of:
- Jr's past experience with similar tasks
- Node's current workload
- Capability match

---

## Proposed Architecture

### Bidding Schema

```sql
-- Task announcements
CREATE TABLE IF NOT EXISTS jr_task_announcements (
    task_id VARCHAR(64) PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    task_content TEXT NOT NULL,
    required_capabilities TEXT[],
    preferred_node VARCHAR(32),
    priority INTEGER DEFAULT 5,
    deadline TIMESTAMP,
    announced_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(16) DEFAULT 'open',  -- open, bidding, assigned, completed
    assigned_to VARCHAR(64),
    winning_bid_id INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Jr bids on tasks
CREATE TABLE IF NOT EXISTS jr_task_bids (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES jr_task_announcements(task_id),
    agent_id VARCHAR(64) NOT NULL,
    node_name VARCHAR(32) NOT NULL,

    -- Bid details
    capability_score FLOAT,       -- How well Jr matches task requirements
    experience_score FLOAT,       -- Past success with similar tasks
    load_score FLOAT,             -- Current availability (higher = more available)
    confidence FLOAT,             -- Jr's confidence in completing task

    -- Calculated
    composite_score FLOAT,

    bid_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Index for bid selection
CREATE INDEX idx_bids_task ON jr_task_bids(task_id);
CREATE INDEX idx_bids_score ON jr_task_bids(composite_score DESC);
```

### Bid Scoring Formula

```python
def calculate_composite_score(bid: dict) -> float:
    """
    Calculate composite bid score.

    Weights:
    - capability_score: 40% (can Jr do this?)
    - experience_score: 30% (has Jr done this before?)
    - load_score: 20% (is Jr available?)
    - confidence: 10% (does Jr think it can?)
    """
    weights = {
        'capability': 0.40,
        'experience': 0.30,
        'load': 0.20,
        'confidence': 0.10
    }

    score = (
        weights['capability'] * bid['capability_score'] +
        weights['experience'] * bid['experience_score'] +
        weights['load'] * bid['load_score'] +
        weights['confidence'] * bid['confidence']
    )

    # Bonus for preferred node
    if bid.get('is_preferred_node'):
        score *= 1.1

    # Penalty for recent failures on similar tasks
    if bid.get('recent_failures', 0) > 2:
        score *= 0.8

    return min(1.0, score)
```

---

## Implementation

### Phase 1: Task Announcement

```python
# /ganuda/lib/task_bidding.py

class TaskAnnouncer:
    def __init__(self):
        self.conn = get_db_connection()

    def announce_task(self, task_id: str, task_type: str, content: str,
                      capabilities: list = None, preferred_node: str = None,
                      priority: int = 5, deadline: datetime = None):
        """Announce a new task for bidding"""

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_task_announcements
                (task_id, task_type, task_content, required_capabilities,
                 preferred_node, priority, deadline, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'open')
            """, (task_id, task_type, content, capabilities,
                  preferred_node, priority, deadline))
            self.conn.commit()

        # Broadcast to all nodes
        self._broadcast_announcement(task_id)

        # Start bidding window
        return task_id

    def _broadcast_announcement(self, task_id: str):
        """Notify all nodes of new task"""
        # Could use pub/sub, webhook, or polling
        pass

    def close_bidding(self, task_id: str) -> dict:
        """Close bidding and select winner"""

        with self.conn.cursor() as cur:
            # Get best bid
            cur.execute("""
                SELECT id, agent_id, node_name, composite_score
                FROM jr_task_bids
                WHERE task_id = %s
                ORDER BY composite_score DESC
                LIMIT 1
            """, (task_id,))
            winner = cur.fetchone()

            if not winner:
                return {"error": "No bids received"}

            bid_id, agent_id, node_name, score = winner

            # Assign task
            cur.execute("""
                UPDATE jr_task_announcements
                SET status = 'assigned',
                    assigned_to = %s,
                    winning_bid_id = %s
                WHERE task_id = %s
            """, (agent_id, bid_id, task_id))

            self.conn.commit()

        return {
            "task_id": task_id,
            "assigned_to": agent_id,
            "node": node_name,
            "score": score
        }
```

### Phase 2: Jr Bidding Agent

```python
class JrBidder:
    """Each Jr runs this to bid on announced tasks"""

    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        self.conn = get_db_connection()
        self.state_mgr = JrStateManager(agent_id, node_name)

    def get_open_tasks(self):
        """Get tasks available for bidding"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT task_id, task_type, task_content,
                       required_capabilities, preferred_node, priority
                FROM jr_task_announcements
                WHERE status = 'open'
                ORDER BY priority DESC, announced_at ASC
            """)
            return cur.fetchall()

    def calculate_bid(self, task: tuple) -> dict:
        """Calculate bid for a task"""
        task_id, task_type, content, required_caps, preferred_node, priority = task

        # Capability score
        capability_score = self._calculate_capability_score(required_caps)

        # Experience score (from agent state)
        experience_score = self._calculate_experience_score(task_type, content)

        # Load score (inverse of current workload)
        load_score = self._calculate_load_score()

        # Confidence (can use LLM to self-assess)
        confidence = self._calculate_confidence(content)

        bid = {
            'task_id': task_id,
            'agent_id': self.agent_id,
            'node_name': self.node_name,
            'capability_score': capability_score,
            'experience_score': experience_score,
            'load_score': load_score,
            'confidence': confidence,
            'is_preferred_node': self.node_name == preferred_node
        }

        bid['composite_score'] = calculate_composite_score(bid)

        return bid

    def _calculate_capability_score(self, required_caps: list) -> float:
        """How well does this Jr match required capabilities"""
        if not required_caps:
            return 0.8  # No requirements = assume capable

        # Get Jr's known capabilities from state
        state = self.state_mgr.load_state()
        jr_caps = state.get('specialization_scores', {})

        if not jr_caps:
            return 0.5  # Unknown capabilities

        matches = sum(1 for cap in required_caps if cap in jr_caps)
        return matches / len(required_caps)

    def _calculate_experience_score(self, task_type: str, content: str) -> float:
        """Has this Jr done similar tasks before?"""
        keywords = extract_keywords(content)
        past_episodes = self.state_mgr.get_relevant_episodes(keywords, limit=10)

        if not past_episodes:
            return 0.3  # No experience

        # Calculate success rate on similar tasks
        successes = sum(1 for ep in past_episodes if ep.get('success'))
        return successes / len(past_episodes)

    def _calculate_load_score(self) -> float:
        """How available is this Jr? (1.0 = fully available)"""
        # Check current task queue for this node
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM jr_task_announcements
                WHERE assigned_to = %s AND status = 'assigned'
            """, (self.agent_id,))
            current_tasks = cur.fetchone()[0]

        # Assume max 5 concurrent tasks
        return max(0.1, 1.0 - (current_tasks / 5.0))

    def _calculate_confidence(self, content: str) -> float:
        """Jr's confidence in completing task"""
        # Could query local LLM for self-assessment
        # For now, use heuristic
        content_len = len(content)
        if content_len < 500:
            return 0.9  # Short task = high confidence
        elif content_len < 2000:
            return 0.7
        else:
            return 0.5  # Long/complex task = lower confidence

    def submit_bid(self, bid: dict):
        """Submit bid to database"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_task_bids
                (task_id, agent_id, node_name, capability_score,
                 experience_score, load_score, confidence, composite_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bid['task_id'], bid['agent_id'], bid['node_name'],
                bid['capability_score'], bid['experience_score'],
                bid['load_score'], bid['confidence'], bid['composite_score']
            ))
            self.conn.commit()
```

### Phase 3: Bidding Coordinator

```python
class BiddingCoordinator:
    """Orchestrates the bidding process"""

    def __init__(self):
        self.conn = get_db_connection()
        self.announcer = TaskAnnouncer()
        self.bidding_window_seconds = 5  # Time to collect bids

    async def submit_task(self, task_type: str, content: str, **kwargs) -> dict:
        """Submit a new task and get it assigned via bidding"""

        task_id = generate_task_id()

        # Analyze task to determine requirements
        required_caps = self._analyze_required_capabilities(task_type, content)
        preferred_node = self._determine_preferred_node(task_type)

        # Announce task
        self.announcer.announce_task(
            task_id=task_id,
            task_type=task_type,
            content=content,
            capabilities=required_caps,
            preferred_node=preferred_node,
            **kwargs
        )

        # Wait for bids
        await asyncio.sleep(self.bidding_window_seconds)

        # Close bidding and assign
        result = self.announcer.close_bidding(task_id)

        if 'error' in result:
            # No bids - assign to any available Jr
            result = self._fallback_assignment(task_id)

        return result

    def _analyze_required_capabilities(self, task_type: str, content: str) -> list:
        """Determine what capabilities are needed"""
        caps = []

        # Basic heuristics
        if 'database' in content.lower() or 'sql' in content.lower():
            caps.append('database')
        if 'python' in content.lower() or 'code' in content.lower():
            caps.append('coding')
        if 'security' in content.lower():
            caps.append('security')
        if 'test' in content.lower():
            caps.append('testing')
        if 'document' in content.lower():
            caps.append('documentation')

        return caps or None

    def _determine_preferred_node(self, task_type: str) -> str:
        """Determine best node for task type"""
        node_preferences = {
            'gpu_inference': 'redfin',
            'database': 'bluefin',
            'monitoring': 'greenfin',
            'edge_development': 'sasass',
            'planning': 'tpm'
        }
        return node_preferences.get(task_type)
```

### Phase 4: Integration

Replace existing FIFO queue with bidding system:

```python
# Old way
def enqueue_jr_task(content):
    insert_into_queue(content)
    # First available Jr picks it up

# New way
async def submit_jr_task(task_type, content, priority=5):
    coordinator = BiddingCoordinator()
    result = await coordinator.submit_task(task_type, content, priority=priority)

    if 'error' not in result:
        log_assignment(result)
        return result['task_id']
    else:
        raise TaskAssignmentError(result['error'])
```

---

## Monitoring

```sql
-- Bid success rates by agent
SELECT
    agent_id,
    COUNT(*) as total_bids,
    COUNT(*) FILTER (WHERE task_id IN (
        SELECT task_id FROM jr_task_announcements WHERE assigned_to = jr_task_bids.agent_id
    )) as winning_bids,
    AVG(composite_score) as avg_score
FROM jr_task_bids
GROUP BY agent_id
ORDER BY winning_bids DESC;

-- Task assignment distribution by node
SELECT
    node_name,
    COUNT(*) as tasks_assigned
FROM jr_task_announcements
JOIN jr_task_bids ON jr_task_announcements.winning_bid_id = jr_task_bids.id
WHERE jr_task_announcements.status IN ('assigned', 'completed')
GROUP BY node_name;

-- Average bidding competition
SELECT
    AVG(bid_count) as avg_bids_per_task
FROM (
    SELECT task_id, COUNT(*) as bid_count
    FROM jr_task_bids
    GROUP BY task_id
) sub;
```

---

## Success Criteria

1. Tasks assigned based on capability match, not just availability
2. Experienced Jrs get similar tasks (specialization emerges)
3. Load distributed across nodes
4. Assignment latency < 10 seconds
5. Higher task success rate compared to FIFO baseline

---

*For Seven Generations - Cherokee AI Federation*
