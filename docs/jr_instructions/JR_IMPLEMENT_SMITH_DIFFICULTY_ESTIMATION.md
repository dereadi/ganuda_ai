# Jr Task: Implement SMITH-Inspired Difficulty Re-Estimation for Task Bidding

**Task ID:** task-smith-difficulty-001
**Priority:** P2 (Council Voted)
**Node:** redfin (Jr executor), bluefin (database)
**Created:** December 22, 2025
**Research Basis:** arXiv:2512.11303 - SMITH: Unifying Dynamic Tool Creation and Cross-Task Experience Sharing
**Council Vote:** f0d882b6d8ed0162 (79.5% confidence)

---

## Executive Summary

The SMITH paper (arXiv:2512.11303) achieves **81.8% accuracy on GAIA benchmark** through hierarchical memory organization:

- **Procedural Memory**: Executable patterns
- **Semantic Memory**: Knowledge organization
- **Episodic Memory**: Task-specific experiences

Key innovation: **Difficulty re-estimation** based on historical task performance. When allocating tasks, SMITH estimates difficulty using past execution data, improving task-agent matching.

Our Jr task bidding system currently uses static capability scores. This task adds **dynamic difficulty estimation** based on episodic memory of past tasks.

---

## Current Jr Task Bidding System

### How It Works Now

```
1. Task announced to jr_task_announcements
2. Jr agents calculate bid scores:
   - capability_score (static, 0-1)
   - node_load_factor (dynamic, based on uptime)
   - specialization_match (static, keyword matching)
3. Highest composite_score wins
4. Task assigned via jr_task_bids
```

### What's Missing

- **No historical difficulty awareness**: A Jr that failed similar tasks still bids high
- **No time estimation**: No prediction of how long tasks will take
- **No cross-Jr learning**: One Jr's failure doesn't inform others

---

## SMITH-Inspired Improvements

### New Bidding Formula

```
composite_score = (
    capability_score * 0.3 +
    difficulty_match_score * 0.3 +  # NEW
    historical_success_rate * 0.2 + # NEW
    (1 - node_load_factor) * 0.2
)
```

Where:
- **difficulty_match_score**: How well Jr's past performance matches this difficulty level
- **historical_success_rate**: Jr's success rate on similar task types

---

## Implementation Plan

### Phase 1: Create Task Completion Tracking

#### 1.1 New Table: jr_task_completions

```sql
-- On bluefin (zammad_production)

CREATE TABLE IF NOT EXISTS jr_task_completions (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(128) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    task_type VARCHAR(64),           -- 'code_review', 'deployment', 'research', etc.
    task_keywords TEXT[],            -- Keywords extracted from task description

    -- Timing metrics
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Outcome metrics
    outcome VARCHAR(32) NOT NULL,    -- 'success', 'partial', 'failure', 'timeout'
    outcome_score FLOAT,             -- 0.0 to 1.0
    error_type VARCHAR(64),          -- If failed, what kind of error

    -- Difficulty metrics (retrospective)
    estimated_difficulty FLOAT,      -- What we thought (0-1)
    actual_difficulty FLOAT,         -- What it turned out to be (0-1)

    -- Context
    node_name VARCHAR(32),
    node_load_at_start FLOAT,
    memories_used TEXT[],            -- Memory hashes that helped

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_completions_agent ON jr_task_completions(agent_id);
CREATE INDEX idx_task_completions_type ON jr_task_completions(task_type);
CREATE INDEX idx_task_completions_outcome ON jr_task_completions(outcome);
CREATE INDEX idx_task_completions_time ON jr_task_completions(completed_at);
```

#### 1.2 Task Type Classification Function

```sql
CREATE OR REPLACE FUNCTION classify_task_type(task_description TEXT)
RETURNS VARCHAR(64) AS $$
BEGIN
    -- Classify based on keywords
    IF task_description ILIKE '%deploy%' OR task_description ILIKE '%install%' THEN
        RETURN 'deployment';
    ELSIF task_description ILIKE '%review%' OR task_description ILIKE '%audit%' THEN
        RETURN 'code_review';
    ELSIF task_description ILIKE '%research%' OR task_description ILIKE '%investigate%' THEN
        RETURN 'research';
    ELSIF task_description ILIKE '%fix%' OR task_description ILIKE '%bug%' OR task_description ILIKE '%error%' THEN
        RETURN 'bugfix';
    ELSIF task_description ILIKE '%test%' OR task_description ILIKE '%verify%' THEN
        RETURN 'testing';
    ELSIF task_description ILIKE '%document%' OR task_description ILIKE '%write%' THEN
        RETURN 'documentation';
    ELSIF task_description ILIKE '%optimize%' OR task_description ILIKE '%performance%' THEN
        RETURN 'optimization';
    ELSIF task_description ILIKE '%integrate%' OR task_description ILIKE '%connect%' THEN
        RETURN 'integration';
    ELSE
        RETURN 'general';
    END IF;
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 2: Difficulty Estimation Functions

#### 2.1 Calculate Historical Difficulty for Task Type

```sql
CREATE OR REPLACE FUNCTION estimate_task_difficulty(
    p_task_type VARCHAR(64),
    p_keywords TEXT[] DEFAULT NULL
) RETURNS TABLE (
    estimated_difficulty FLOAT,
    avg_duration_seconds INTEGER,
    success_rate FLOAT,
    sample_size INTEGER,
    confidence VARCHAR(16)
) AS $$
DECLARE
    sample_count INTEGER;
BEGIN
    -- Get historical stats for this task type
    SELECT
        COALESCE(AVG(actual_difficulty), 0.5),
        COALESCE(AVG(duration_seconds), 300)::INTEGER,
        COALESCE(
            SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END)::FLOAT /
            NULLIF(COUNT(*), 0),
            0.5
        ),
        COUNT(*)
    INTO
        estimated_difficulty,
        avg_duration_seconds,
        success_rate,
        sample_size
    FROM jr_task_completions
    WHERE task_type = p_task_type
      AND completed_at > NOW() - INTERVAL '30 days';

    -- Adjust confidence based on sample size
    IF sample_size >= 20 THEN
        confidence := 'high';
    ELSIF sample_size >= 5 THEN
        confidence := 'medium';
    ELSE
        confidence := 'low';
        -- Default to moderate difficulty if insufficient data
        estimated_difficulty := 0.5;
    END IF;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

#### 2.2 Calculate Agent's Difficulty Match Score

```sql
CREATE OR REPLACE FUNCTION agent_difficulty_match(
    p_agent_id VARCHAR(64),
    p_task_type VARCHAR(64),
    p_estimated_difficulty FLOAT
) RETURNS FLOAT AS $$
DECLARE
    agent_sweet_spot FLOAT;
    match_score FLOAT;
BEGIN
    -- Find the difficulty level where this agent performs best
    SELECT
        AVG(actual_difficulty) FILTER (WHERE outcome = 'success')
    INTO agent_sweet_spot
    FROM jr_task_completions
    WHERE agent_id = p_agent_id
      AND task_type = p_task_type
      AND completed_at > NOW() - INTERVAL '30 days';

    -- Default to 0.5 if no history
    IF agent_sweet_spot IS NULL THEN
        agent_sweet_spot := 0.5;
    END IF;

    -- Calculate match score (1.0 = perfect match, 0.0 = worst match)
    -- Gaussian-like falloff from sweet spot
    match_score := EXP(-2 * POWER(p_estimated_difficulty - agent_sweet_spot, 2));

    RETURN match_score;
END;
$$ LANGUAGE plpgsql;
```

#### 2.3 Calculate Agent's Historical Success Rate

```sql
CREATE OR REPLACE FUNCTION agent_success_rate(
    p_agent_id VARCHAR(64),
    p_task_type VARCHAR(64) DEFAULT NULL
) RETURNS FLOAT AS $$
DECLARE
    rate FLOAT;
BEGIN
    SELECT
        COALESCE(
            SUM(CASE WHEN outcome = 'success' THEN 1.0
                     WHEN outcome = 'partial' THEN 0.5
                     ELSE 0.0 END) / NULLIF(COUNT(*), 0),
            0.5  -- Default for new agents
        )
    INTO rate
    FROM jr_task_completions
    WHERE agent_id = p_agent_id
      AND (p_task_type IS NULL OR task_type = p_task_type)
      AND completed_at > NOW() - INTERVAL '30 days';

    RETURN rate;
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 3: Enhanced Bid Scoring

#### 3.1 New Composite Score Function

```sql
CREATE OR REPLACE FUNCTION calculate_enhanced_bid_score(
    p_agent_id VARCHAR(64),
    p_task_description TEXT,
    p_capability_score FLOAT,
    p_node_load FLOAT
) RETURNS TABLE (
    composite_score FLOAT,
    capability_component FLOAT,
    difficulty_match_component FLOAT,
    success_rate_component FLOAT,
    load_component FLOAT,
    estimated_difficulty FLOAT,
    estimated_duration_seconds INTEGER
) AS $$
DECLARE
    v_task_type VARCHAR(64);
    v_difficulty FLOAT;
    v_duration INTEGER;
    v_confidence VARCHAR(16);
    v_difficulty_match FLOAT;
    v_success_rate FLOAT;
BEGIN
    -- Classify the task
    v_task_type := classify_task_type(p_task_description);

    -- Get difficulty estimate
    SELECT ed.estimated_difficulty, ed.avg_duration_seconds, ed.confidence
    INTO v_difficulty, v_duration, v_confidence
    FROM estimate_task_difficulty(v_task_type) ed;

    -- Get agent's difficulty match
    v_difficulty_match := agent_difficulty_match(p_agent_id, v_task_type, v_difficulty);

    -- Get agent's success rate
    v_success_rate := agent_success_rate(p_agent_id, v_task_type);

    -- Calculate components
    capability_component := p_capability_score * 0.3;
    difficulty_match_component := v_difficulty_match * 0.3;
    success_rate_component := v_success_rate * 0.2;
    load_component := (1.0 - LEAST(p_node_load, 1.0)) * 0.2;

    -- Final score
    composite_score := capability_component +
                       difficulty_match_component +
                       success_rate_component +
                       load_component;

    estimated_difficulty := v_difficulty;
    estimated_duration_seconds := v_duration;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
```

---

### Phase 4: Update Jr Executor

#### 4.1 Modify Bid Calculation in Jr Executor

Update `/ganuda/jr_executor/jr_executor.py` on redfin:

```python
# Add to jr_executor.py

def calculate_bid_score(self, task: dict) -> dict:
    """
    Calculate enhanced bid score using SMITH difficulty estimation
    Based on arXiv:2512.11303
    """
    conn = self.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get enhanced score from database function
    cur.execute("""
        SELECT * FROM calculate_enhanced_bid_score(%s, %s, %s, %s)
    """, (
        self.agent_id,
        task['description'],
        self.capability_score,
        self.get_node_load()
    ))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return {
        'composite_score': result['composite_score'],
        'breakdown': {
            'capability': result['capability_component'],
            'difficulty_match': result['difficulty_match_component'],
            'success_rate': result['success_rate_component'],
            'load': result['load_component']
        },
        'estimates': {
            'difficulty': result['estimated_difficulty'],
            'duration_seconds': result['estimated_duration_seconds']
        }
    }


def record_task_completion(self, task_id: str, outcome: str,
                           duration_seconds: int, error_type: str = None):
    """
    Record task completion for future difficulty estimation
    """
    conn = self.get_db_connection()
    cur = conn.cursor()

    # Calculate actual difficulty based on duration and outcome
    expected_duration = self.last_task_estimate.get('duration_seconds', 300)
    duration_ratio = duration_seconds / expected_duration

    if outcome == 'success':
        actual_difficulty = min(1.0, duration_ratio * 0.5)
    elif outcome == 'partial':
        actual_difficulty = min(1.0, duration_ratio * 0.7)
    else:
        actual_difficulty = min(1.0, duration_ratio * 0.9)

    cur.execute("""
        INSERT INTO jr_task_completions (
            task_id, agent_id, task_type, started_at, completed_at,
            duration_seconds, outcome, estimated_difficulty, actual_difficulty,
            node_name, node_load_at_start, error_type
        ) VALUES (
            %s, %s, classify_task_type(%s), %s, NOW(),
            %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        task_id,
        self.agent_id,
        self.current_task['description'],
        self.task_started_at,
        duration_seconds,
        outcome,
        self.last_task_estimate.get('difficulty', 0.5),
        actual_difficulty,
        self.node_name,
        self.load_at_start,
        error_type
    ))

    conn.commit()
    cur.close()
    conn.close()
```

---

### Phase 5: Cross-Jr Learning (Semantic Memory)

#### 5.1 Share Learnings Across Jrs

```sql
-- Create view for cross-Jr learning insights
CREATE OR REPLACE VIEW task_difficulty_insights AS
SELECT
    task_type,
    COUNT(*) as total_attempts,
    AVG(actual_difficulty) as avg_difficulty,
    STDDEV(actual_difficulty) as difficulty_variance,
    AVG(duration_seconds) as avg_duration,
    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,

    -- Best performing agents for this task type
    (SELECT ARRAY_AGG(agent_id ORDER BY success_rate DESC)
     FROM (
         SELECT agent_id,
                SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
         FROM jr_task_completions tc2
         WHERE tc2.task_type = tc.task_type
         GROUP BY agent_id
         HAVING COUNT(*) >= 3
         LIMIT 3
     ) top_agents
    ) as top_agents,

    -- Common failure patterns
    MODE() WITHIN GROUP (ORDER BY error_type) as most_common_error

FROM jr_task_completions tc
WHERE completed_at > NOW() - INTERVAL '30 days'
GROUP BY task_type;
```

#### 5.2 Inject Insights into Jr Context

```python
def get_task_insights(self, task_type: str) -> dict:
    """
    Get cross-Jr learning insights for a task type
    Implements SMITH semantic memory sharing
    """
    conn = self.get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM task_difficulty_insights
        WHERE task_type = %s
    """, (task_type,))

    insight = cur.fetchone()
    cur.close()
    conn.close()

    if insight:
        return {
            'task_type': task_type,
            'avg_difficulty': insight['avg_difficulty'],
            'success_rate': insight['success_rate'],
            'avg_duration_minutes': insight['avg_duration'] / 60,
            'top_agents': insight['top_agents'],
            'common_pitfall': insight['most_common_error'],
            'recommendation': self._generate_recommendation(insight)
        }
    return None
```

---

## Testing

### Test 1: Verify Task Classification

```sql
SELECT classify_task_type('Deploy the Django admin to redfin');
-- Expected: 'deployment'

SELECT classify_task_type('Fix the bug in thermal memory query');
-- Expected: 'bugfix'

SELECT classify_task_type('Research arXiv papers on multi-agent systems');
-- Expected: 'research'
```

### Test 2: Simulate Task History

```sql
-- Insert sample task completions
INSERT INTO jr_task_completions
    (task_id, agent_id, task_type, duration_seconds, outcome, actual_difficulty, node_name)
VALUES
    ('task-001', 'jr-redfin-gecko', 'deployment', 300, 'success', 0.4, 'redfin'),
    ('task-002', 'jr-redfin-gecko', 'deployment', 600, 'success', 0.6, 'redfin'),
    ('task-003', 'jr-sasass-spider', 'deployment', 900, 'failure', 0.8, 'sasass'),
    ('task-004', 'jr-redfin-gecko', 'bugfix', 450, 'success', 0.5, 'redfin'),
    ('task-005', 'jr-sasass-spider', 'bugfix', 1200, 'partial', 0.7, 'sasass');
```

### Test 3: Verify Enhanced Bid Scoring

```sql
SELECT * FROM calculate_enhanced_bid_score(
    'jr-redfin-gecko',
    'Deploy the new T5 service to greenfin',
    0.85,  -- capability
    0.3    -- node load
);
```

---

## Success Criteria

1. ✅ jr_task_completions table tracking all task outcomes
2. ✅ classify_task_type() correctly categorizes tasks
3. ✅ estimate_task_difficulty() returns historical estimates
4. ✅ Enhanced bid scores favor agents with good track records
5. ✅ Cross-Jr learning insights available
6. ✅ Jr executor records completions and uses enhanced scoring

---

## Expected Outcomes

Based on SMITH paper results (81.8% on GAIA), we expect:

- **15-20% improvement** in task completion rates
- **Better task-agent matching** based on historical performance
- **Reduced failures** by avoiding mismatched difficulty assignments
- **Faster convergence** to optimal Jr for each task type

---

## References

- arXiv:2512.11303 - SMITH: Unifying Dynamic Tool Creation and Cross-Task Experience Sharing
- Council Vote: f0d882b6d8ed0162 (79.5% confidence)
- Existing: jr_task_announcements, jr_task_bids tables

---

*For Seven Generations - Cherokee AI Federation*
