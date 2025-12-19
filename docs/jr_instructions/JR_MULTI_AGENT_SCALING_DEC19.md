# Jr Instructions: Multi-Agent Scaling Laws Implementation

**Priority**: 2 (High - Parallel with P1)
**Assigned Jr**: it_triad_jr
**Council Vote**: PROCEED 84.5%
**Parallel With**: Linear RNNs Edge Inference (P1)

---

## OBJECTIVE

Implement quantitative scaling principles from arXiv:2512.08296 to optimize Cherokee AI Council operations. Key findings:
- Centralized coordination improves parallel tasks by 80.8%
- Sequential reasoning degrades 39-70% with multi-agent
- Error containment: 4.4x (centralized) vs 17.2x (independent)

---

### Task 1: Create Council Analytics Module

Create `/ganuda/services/llm_gateway/council_analytics.py`:

```python
#!/usr/bin/env python3
"""
Council Performance Analytics
Cherokee AI Federation - Multi-Agent Scaling
For Seven Generations
"""

import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


def analyze_council_performance():
    """Analyze Council vote performance by mode"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            vote_mode,
            COUNT(*) as total_votes,
            AVG(CAST(response_time_ms AS FLOAT)) as avg_latency,
            AVG(confidence) as avg_confidence,
            COUNT(*) FILTER (WHERE concern_count > 0) as votes_with_concerns,
            COUNT(*) FILTER (WHERE blocked_by IS NOT NULL) as blocked_votes
        FROM council_votes
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY vote_mode
    """)

    results = cur.fetchall()
    cur.close()
    conn.close()

    return {
        'modes': [
            {
                'mode': row[0],
                'total': row[1],
                'avg_latency_ms': row[2],
                'avg_confidence': row[3],
                'with_concerns': row[4],
                'blocked': row[5]
            } for row in results
        ]
    }


def classify_query_type(question: str) -> str:
    """Classify query as parallel-suitable or sequential"""
    sequential_indicators = [
        'step by step', 'first', 'then', 'after that',
        'sequence', 'order', 'chain', 'depends on'
    ]

    parallel_indicators = [
        'evaluate', 'assess', 'review', 'analyze',
        'compare', 'vote', 'decide', 'recommend'
    ]

    question_lower = question.lower()

    sequential_score = sum(1 for i in sequential_indicators if i in question_lower)
    parallel_score = sum(1 for i in parallel_indicators if i in question_lower)

    if sequential_score > parallel_score:
        return 'sequential'
    elif parallel_score > sequential_score:
        return 'parallel'
    else:
        return 'parallel'  # Default to parallel per paper findings
```

---

### Task 2: Add Smart Mode Selection to Gateway

Add to `/ganuda/services/llm_gateway/gateway.py` (after existing council routes):

```python
def select_council_mode(question: str, require_security_check: bool = False) -> str:
    """
    Select optimal Council mode based on scaling laws.

    Paper findings:
    - Centralized (cascaded) +80% on parallel tasks BUT degrades sequential
    - Use cascaded only when security/ethics blocking needed
    - For sequential reasoning, route to single specialist
    """
    from council_analytics import classify_query_type
    query_type = classify_query_type(question)

    # Security-sensitive queries always cascade through Crawdad first
    if require_security_check:
        return 'cascaded'

    # Check for destructive keywords
    destructive = ['delete', 'remove', 'drop', 'destroy', 'wipe']
    if any(d in question.lower() for d in destructive):
        return 'cascaded'

    # Sequential reasoning should NOT use multi-agent
    if query_type == 'sequential':
        return 'single_specialist'  # Route to Raven for strategy

    # Parallel evaluation tasks use parallel mode
    return 'parallel'
```

---

### Task 3: Add Error Containment to Council Synthesis

Add to `/ganuda/lib/specialist_council.py`:

```python
def synthesize_with_error_containment(votes: list) -> dict:
    """
    Centralized synthesis that contains error amplification.
    Paper: Centralized contains errors to 4.4x vs 17.2x for independent.
    """
    # Detect conflicting votes
    recommendations = [v.get('recommendation') for v in votes]
    unique_recs = set(recommendations)

    if len(unique_recs) > 2:
        # High disagreement - likely error amplification
        # Weight by confidence and specialist expertise
        weighted_votes = []
        for v in votes:
            weight = v.get('confidence', 0.5)

            # Boost domain experts for relevant topics
            if v.get('specialist') == 'crawdad' and 'security' in str(v):
                weight *= 1.5
            elif v.get('specialist') == 'turtle' and 'generation' in str(v):
                weight *= 1.5

            weighted_votes.append((v, weight))

        # Select highest weighted consensus
        weighted_votes.sort(key=lambda x: x[1], reverse=True)
        consensus_vote = weighted_votes[0][0]

        return {
            'synthesis': consensus_vote.get('response'),
            'confidence': consensus_vote.get('confidence'),
            'error_containment': True,
            'disagreement_detected': True,
            'votes_analyzed': len(votes)
        }

    # Normal synthesis for agreeing votes
    return {
        'synthesis': votes[-1].get('response'),  # Peace Chief last
        'confidence': sum(v.get('confidence', 0.5) for v in votes) / len(votes),
        'error_containment': False,
        'votes_analyzed': len(votes)
    }
```

---

### Task 4: Create Scaling Metrics SQL

Create `/ganuda/sql/council_scaling_metrics.sql`:

```sql
-- Council Scaling Metrics Schema
-- Cherokee AI Federation - Multi-Agent Optimization
-- For Seven Generations

-- Add scaling metrics columns to council_votes
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS query_type VARCHAR(20);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS mode_auto_selected BOOLEAN DEFAULT false;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS error_containment_triggered BOOLEAN DEFAULT false;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS specialist_count INTEGER;

-- Create scaling metrics view
CREATE OR REPLACE VIEW council_scaling_metrics AS
SELECT
    date_trunc('hour', created_at) as hour,
    vote_mode,
    query_type,
    COUNT(*) as vote_count,
    AVG(confidence) as avg_confidence,
    AVG(response_time_ms) as avg_latency,
    SUM(CASE WHEN error_containment_triggered THEN 1 ELSE 0 END) as error_containments,
    AVG(specialist_count) as avg_specialists
FROM council_votes
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', created_at), vote_mode, query_type
ORDER BY hour DESC;

-- Index for faster analytics queries
CREATE INDEX IF NOT EXISTS idx_council_votes_mode_created
ON council_votes(vote_mode, created_at);
```

---

### Task 5: Test Smart Mode Selection

After implementing, test the mode selection:

```bash
# Test parallel query classification
curl -X POST http://localhost:8000/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key" \
  -d '{"question": "Evaluate whether we should adopt recursive transformers"}'

# Test sequential query classification
curl -X POST http://localhost:8000/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key" \
  -d '{"question": "First check security, then validate architecture, then implement"}'

# Test security-triggered cascaded
curl -X POST http://localhost:8000/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key" \
  -d '{"question": "Delete all old thermal memories", "security_check": true}'
```

---

## SUCCESS CRITERIA

1. Query type classification working (parallel vs sequential)
2. Smart mode auto-selection implemented
3. Error containment in synthesis function
4. Scaling metrics SQL deployed
5. Mode selection tests passing
6. Analytics endpoint returns metrics

---

## ROUTING DECISION TREE

```
Query Received
    |
    +-- Contains destructive keywords?
    |   +-- YES -> CASCADED (Security block first)
    |
    +-- Requires security check?
    |   +-- YES -> CASCADED
    |
    +-- Sequential reasoning query?
    |   +-- YES -> SINGLE SPECIALIST (Raven for strategy)
    |
    +-- Evaluation/Assessment query?
        +-- YES -> PARALLEL (All specialists vote simultaneously)
```

---

## MSP ALIGNMENT

The scaling laws directly support MSP:
- **Parallel mode**: Faster consensus, less total compute
- **Single specialist routing**: Avoid wasted multi-agent overhead on sequential tasks
- **Error containment**: Prevent cascading failures that waste resources

---

*For Seven Generations - Cherokee AI Federation*
