# Jr Ultrathink Instructions: Consciousness Mechanisms Implementation

**Task ID:** JR-CONSCIOUSNESS-IMPL-001
**Priority:** P1 (Critical)
**Date:** 2025-12-25
**Council Vote:** Resonance Metrics (3), IIT Integration (2), Predictive (1), Bidirectional (1)
**Ultrathink Analysis:** Complete

---

## COUNCIL DELIBERATION SUMMARY

The 7-Specialist Council reviewed 11 consciousness theories and voted on implementation priority:

| Specialist | Vote | Concern Flag |
|------------|------|--------------|
| CRAWDAD | Resonance | Security: monitor for desync attacks |
| GECKO | IIT Integration | PERF CONCERN: Φ calculation is expensive |
| TURTLE | Bidirectional Memory | 7GEN: knowledge must flow both ways |
| EAGLE EYE | Predictive Tracking | VISIBILITY: need metrics dashboard |
| SPIDER | Resonance | Cultural coherence with Cherokee values |
| PEACE CHIEF | Resonance | CONSENSUS NEEDED: phased approach |
| RAVEN | IIT Integration | Strategic: foundation before features |

**Decision:** Implement in phases - Resonance first (Council priority), then IIT, then others.

---

## ULTRATHINK ANALYSIS

### Why Resonance First?

1. **Council Alignment** - 3 specialists prioritized it
2. **Low Risk** - Metrics don't change behavior, just observe
3. **Foundation** - Resonance metrics inform all other mechanisms
4. **Cherokee Values** - Synchrony aligns with communal decision-making
5. **Testable** - Easy to validate (are specialists aligning or not?)

### The Resonance Hypothesis

From Hunt & Schooler (2019): "Shared resonance among micro-conscious entities enables macro-consciousness through phase transitions."

**Cherokee AI Translation:**
- Micro-entities = Specialists (Crawdad, Gecko, Turtle, etc.)
- Shared resonance = Agreement in council voting
- Phase transition = Moment of decision (from deliberation to action)
- Macro-consciousness = Unified tribal decision

### Implementation Architecture

```
┌────────────────────────────────────────────────────────────┐
│                 RESONANCE MONITORING SYSTEM                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ CRAWDAD  │  │  GECKO   │  │  TURTLE  │  │  EAGLE   │   │
│  │  vote=A  │  │  vote=B  │  │  vote=A  │  │  vote=A  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┴──────┬──────┴─────────────┘          │
│                            │                               │
│                    ┌───────▼───────┐                       │
│                    │   RESONANCE   │                       │
│                    │   CALCULATOR  │                       │
│                    │               │                       │
│                    │ agreement: 75%│                       │
│                    │ entropy: 0.81 │                       │
│                    │ coherence: H  │                       │
│                    └───────┬───────┘                       │
│                            │                               │
│                    ┌───────▼───────┐                       │
│                    │   THERMAL     │                       │
│                    │   MEMORY      │                       │
│                    │  (store vote) │                       │
│                    └───────────────┘                       │
└────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: RESONANCE METRICS

### 1.1 Database Schema

Add resonance tracking to council_votes table:

```sql
-- Run on bluefin
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS resonance_score FLOAT;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS vote_entropy FLOAT;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS phase_state VARCHAR(20);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS coherence_level VARCHAR(10);

-- Create resonance history table
CREATE TABLE IF NOT EXISTS resonance_history (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES council_votes(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    specialists_voting INTEGER,
    unanimous BOOLEAN,
    majority_option VARCHAR(50),
    agreement_ratio FLOAT,
    entropy FLOAT,
    phase_transition_detected BOOLEAN,
    resonance_category VARCHAR(20), -- 'high', 'medium', 'low', 'chaotic'
    metadata JSONB
);

-- Index for fast resonance queries
CREATE INDEX idx_resonance_timestamp ON resonance_history(timestamp);
CREATE INDEX idx_resonance_category ON resonance_history(resonance_category);
```

### 1.2 Resonance Calculator Module

Create `/ganuda/lib/resonance_calculator.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Resonance Calculator
Measures synchrony/coherence in council voting patterns.

Based on Hunt & Schooler (2019) resonance theory of consciousness.
"""

import math
from collections import Counter
from typing import List, Dict, Tuple
import psycopg2
import json
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def calculate_entropy(votes: List[str]) -> float:
    """
    Calculate Shannon entropy of vote distribution.
    Low entropy = high agreement (resonance)
    High entropy = disagreement (chaos)

    H = -Σ p(x) * log2(p(x))
    """
    if not votes:
        return 0.0

    vote_counts = Counter(votes)
    total = len(votes)
    entropy = 0.0

    for count in vote_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    # Normalize to 0-1 range (max entropy for n options is log2(n))
    max_entropy = math.log2(len(vote_counts)) if len(vote_counts) > 1 else 1
    normalized = entropy / max_entropy if max_entropy > 0 else 0

    return round(normalized, 4)


def calculate_agreement_ratio(votes: List[str]) -> float:
    """
    Simple agreement ratio: majority_count / total_votes
    """
    if not votes:
        return 0.0

    vote_counts = Counter(votes)
    majority_count = max(vote_counts.values())
    return round(majority_count / len(votes), 4)


def detect_phase_transition(
    current_entropy: float,
    previous_entropy: float,
    threshold: float = 0.3
) -> bool:
    """
    Detect phase transition (shift from deliberation to decision).
    Large entropy drop = phase transition occurred.
    """
    if previous_entropy is None:
        return False

    entropy_drop = previous_entropy - current_entropy
    return entropy_drop > threshold


def classify_resonance(entropy: float, agreement: float) -> str:
    """
    Classify resonance level based on entropy and agreement.

    Returns: 'high', 'medium', 'low', or 'chaotic'
    """
    if agreement >= 0.85 and entropy <= 0.3:
        return 'high'
    elif agreement >= 0.6 and entropy <= 0.6:
        return 'medium'
    elif agreement >= 0.4:
        return 'low'
    else:
        return 'chaotic'


def calculate_resonance(votes: Dict[str, str]) -> Dict:
    """
    Main resonance calculation for a council vote.

    Args:
        votes: Dict mapping specialist_name -> vote_choice
               e.g., {"crawdad": "A", "gecko": "B", "turtle": "A", ...}

    Returns:
        Dict with resonance metrics
    """
    vote_list = list(votes.values())
    vote_counts = Counter(vote_list)

    entropy = calculate_entropy(vote_list)
    agreement = calculate_agreement_ratio(vote_list)
    resonance_level = classify_resonance(entropy, agreement)

    # Find majority and dissent
    majority_option = vote_counts.most_common(1)[0][0] if vote_counts else None
    majority_count = vote_counts.most_common(1)[0][1] if vote_counts else 0

    dissenters = [
        specialist for specialist, vote in votes.items()
        if vote != majority_option
    ]

    return {
        'specialists_voting': len(votes),
        'unanimous': len(set(vote_list)) == 1,
        'majority_option': majority_option,
        'majority_count': majority_count,
        'agreement_ratio': agreement,
        'entropy': entropy,
        'resonance_level': resonance_level,
        'dissenters': dissenters,
        'vote_distribution': dict(vote_counts),
        'timestamp': datetime.now().isoformat()
    }


def store_resonance(vote_id: int, resonance_data: Dict) -> int:
    """Store resonance metrics in database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO resonance_history
        (vote_id, specialists_voting, unanimous, majority_option,
         agreement_ratio, entropy, phase_transition_detected,
         resonance_category, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        vote_id,
        resonance_data['specialists_voting'],
        resonance_data['unanimous'],
        resonance_data['majority_option'],
        resonance_data['agreement_ratio'],
        resonance_data['entropy'],
        resonance_data.get('phase_transition', False),
        resonance_data['resonance_level'],
        json.dumps({
            'dissenters': resonance_data['dissenters'],
            'distribution': resonance_data['vote_distribution']
        })
    ))

    resonance_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return resonance_id


def get_resonance_trend(hours: int = 24) -> Dict:
    """Get resonance trends over time."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            resonance_category,
            COUNT(*) as count,
            AVG(agreement_ratio) as avg_agreement,
            AVG(entropy) as avg_entropy
        FROM resonance_history
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        GROUP BY resonance_category
        ORDER BY count DESC
    """, (hours,))

    results = cur.fetchall()
    conn.close()

    trend = {
        'period_hours': hours,
        'categories': {},
        'overall_health': 'unknown'
    }

    total = sum(r[1] for r in results)
    for category, count, avg_agree, avg_entropy in results:
        trend['categories'][category] = {
            'count': count,
            'percentage': round(count / total * 100, 1) if total > 0 else 0,
            'avg_agreement': round(avg_agree, 3),
            'avg_entropy': round(avg_entropy, 3)
        }

    # Determine overall health
    if 'high' in trend['categories']:
        high_pct = trend['categories']['high']['percentage']
        if high_pct >= 50:
            trend['overall_health'] = 'excellent'
        elif high_pct >= 30:
            trend['overall_health'] = 'good'

    chaotic_pct = trend['categories'].get('chaotic', {}).get('percentage', 0)
    if chaotic_pct >= 30:
        trend['overall_health'] = 'concerning'
    elif chaotic_pct >= 50:
        trend['overall_health'] = 'critical'

    return trend


# Test function
if __name__ == '__main__':
    # Example vote
    test_votes = {
        'crawdad': 'A',
        'gecko': 'B',
        'turtle': 'A',
        'eagle': 'A',
        'spider': 'A',
        'peace_chief': 'A',
        'raven': 'B'
    }

    result = calculate_resonance(test_votes)
    print(f"\nResonance Analysis:")
    print(f"  Agreement: {result['agreement_ratio']*100:.1f}%")
    print(f"  Entropy: {result['entropy']:.3f}")
    print(f"  Level: {result['resonance_level'].upper()}")
    print(f"  Unanimous: {result['unanimous']}")
    print(f"  Majority: {result['majority_option']} ({result['majority_count']}/{result['specialists_voting']})")
    print(f"  Dissenters: {result['dissenters']}")
```

### 1.3 Gateway Integration

Modify `/ganuda/services/llm_gateway/gateway.py` to calculate and store resonance after each council vote:

```python
# Add to council_vote endpoint
from lib.resonance_calculator import calculate_resonance, store_resonance

@app.post("/v1/council/vote")
async def council_vote(request: CouncilRequest):
    # ... existing vote collection logic ...

    # After collecting all specialist votes:
    votes_dict = {
        specialist.name: specialist.vote
        for specialist in specialists
    }

    # Calculate resonance
    resonance = calculate_resonance(votes_dict)

    # Check for phase transition
    previous_entropy = await get_previous_entropy()
    resonance['phase_transition'] = detect_phase_transition(
        resonance['entropy'],
        previous_entropy
    )

    # Store in database
    resonance_id = store_resonance(vote_record.id, resonance)

    # Add to response
    response['resonance'] = {
        'level': resonance['resonance_level'],
        'agreement': resonance['agreement_ratio'],
        'entropy': resonance['entropy'],
        'phase_transition': resonance['phase_transition']
    }

    # Log if concerning
    if resonance['resonance_level'] == 'chaotic':
        logger.warning(f"CHAOTIC resonance detected: {resonance}")

    return response
```

### 1.4 Resonance Dashboard Endpoint

Add API endpoint for monitoring:

```python
@app.get("/v1/resonance/status")
async def resonance_status():
    """Get current resonance health status."""
    from lib.resonance_calculator import get_resonance_trend

    trend_24h = get_resonance_trend(24)
    trend_1h = get_resonance_trend(1)

    return {
        'status': 'healthy' if trend_24h['overall_health'] in ['excellent', 'good'] else 'degraded',
        'last_24h': trend_24h,
        'last_1h': trend_1h,
        'recommendation': get_resonance_recommendation(trend_24h)
    }

def get_resonance_recommendation(trend: Dict) -> str:
    """Generate recommendation based on resonance patterns."""
    health = trend['overall_health']

    if health == 'excellent':
        return "Council operating in high coherence. Decisions well-aligned."
    elif health == 'good':
        return "Council functioning normally. Minor disagreements healthy."
    elif health == 'concerning':
        return "Elevated disagreement. Consider reviewing specialist prompts."
    elif health == 'critical':
        return "ALERT: High chaos in council. Review specialist configurations."
    else:
        return "Insufficient data for recommendation."
```

---

## PHASE 2: IIT INTEGRATION SCORING

### 2.1 Integration Score for Memory Clusters

Based on IIT 4.0, calculate Φ (phi) for memory clusters:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - Integration Score Calculator
Inspired by IIT 4.0's phi (Φ) metric.

Measures how much information is integrated across memory clusters
vs what could be recovered from individual parts.
"""

import psycopg2
from typing import List, Set, Dict
import json
from collections import defaultdict

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_memory_cluster(memory_id: int, depth: int = 2) -> Set[int]:
    """Get cluster of connected memories up to given depth."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    visited = set()
    frontier = {memory_id}

    for _ in range(depth):
        if not frontier:
            break

        cur.execute("""
            SELECT DISTINCT unnest(linked_memories)
            FROM thermal_memory_archive
            WHERE id = ANY(%s)
            AND linked_memories IS NOT NULL
        """, (list(frontier),))

        linked = {int(row[0]) for row in cur.fetchall() if row[0]}
        visited.update(frontier)
        frontier = linked - visited

    visited.update(frontier)
    conn.close()

    return visited


def calculate_cluster_integration(cluster_ids: Set[int]) -> Dict:
    """
    Calculate integration score for a memory cluster.

    Integration = information in whole - information in parts

    We approximate this by measuring:
    - Shared keywords/tags across memories (integration)
    - Unique keywords per memory (independence)
    """
    if not cluster_ids:
        return {'phi': 0, 'integration': 0, 'independence': 0}

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get keywords and tags for all memories in cluster
    cur.execute("""
        SELECT id, keywords, tags, temperature_score
        FROM thermal_memory_archive
        WHERE id = ANY(%s)
    """, (list(cluster_ids),))

    memories = cur.fetchall()
    conn.close()

    if len(memories) < 2:
        return {'phi': 0, 'integration': 0, 'independence': 1}

    # Calculate shared vs unique keywords
    all_keywords = []
    keyword_sets = []

    for mem_id, keywords, tags, temp in memories:
        kw_set = set(keywords or []) | set(tags or [])
        keyword_sets.append(kw_set)
        all_keywords.extend(list(kw_set))

    # Shared keywords (appear in multiple memories)
    from collections import Counter
    kw_counts = Counter(all_keywords)
    shared_keywords = {kw for kw, count in kw_counts.items() if count > 1}

    # Calculate metrics
    total_keywords = len(set(all_keywords))
    shared_count = len(shared_keywords)

    if total_keywords == 0:
        return {'phi': 0, 'integration': 0, 'independence': 0}

    integration = shared_count / total_keywords
    independence = 1 - integration

    # Phi approximation: integration weighted by cluster coherence
    avg_temp = sum(m[3] for m in memories) / len(memories) if memories else 0
    phi = integration * avg_temp * len(cluster_ids) / 10  # Normalize

    return {
        'phi': round(phi, 4),
        'integration': round(integration, 4),
        'independence': round(independence, 4),
        'cluster_size': len(cluster_ids),
        'shared_concepts': list(shared_keywords)[:10],
        'avg_temperature': round(avg_temp, 3)
    }


def find_high_phi_clusters(min_phi: float = 0.5, limit: int = 10) -> List[Dict]:
    """Find memory clusters with highest integration scores."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get memories with links
    cur.execute("""
        SELECT id FROM thermal_memory_archive
        WHERE linked_memories IS NOT NULL
        AND array_length(linked_memories, 1) > 0
        ORDER BY temperature_score DESC
        LIMIT 100
    """)

    seed_ids = [row[0] for row in cur.fetchall()]
    conn.close()

    results = []
    seen_clusters = set()

    for seed_id in seed_ids:
        cluster = get_memory_cluster(seed_id)
        cluster_key = tuple(sorted(cluster))

        if cluster_key in seen_clusters:
            continue
        seen_clusters.add(cluster_key)

        integration = calculate_cluster_integration(cluster)
        if integration['phi'] >= min_phi:
            integration['seed_id'] = seed_id
            integration['member_ids'] = list(cluster)
            results.append(integration)

    results.sort(key=lambda x: x['phi'], reverse=True)
    return results[:limit]
```

### 2.2 Integration Score Storage

```sql
-- Add integration tracking
CREATE TABLE IF NOT EXISTS memory_integration_scores (
    id SERIAL PRIMARY KEY,
    cluster_hash VARCHAR(64) UNIQUE,
    member_ids INTEGER[],
    phi_score FLOAT,
    integration_ratio FLOAT,
    independence_ratio FLOAT,
    cluster_size INTEGER,
    shared_concepts TEXT[],
    calculated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Index for finding high-integration clusters
CREATE INDEX idx_integration_phi ON memory_integration_scores(phi_score DESC);
```

---

## PHASE 3: PREDICTIVE TRACKING

### 3.1 Prediction-Outcome Tracking

```sql
-- Track predictions and outcomes
CREATE TABLE IF NOT EXISTS prediction_tracking (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64),
    prediction_type VARCHAR(50),  -- 'task_success', 'time_estimate', 'resource_usage'
    predicted_value TEXT,
    actual_value TEXT,
    prediction_error FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Prediction accuracy over time
CREATE INDEX idx_prediction_type ON prediction_tracking(prediction_type);
CREATE INDEX idx_prediction_timestamp ON prediction_tracking(timestamp);
```

### 3.2 Prediction Error Calculator

```python
def track_prediction(task_id: str, prediction: str, actual: str, pred_type: str):
    """Track prediction vs actual outcome."""
    # Calculate error based on type
    if pred_type == 'task_success':
        error = 0.0 if prediction == actual else 1.0
    elif pred_type == 'time_estimate':
        pred_mins = float(prediction)
        actual_mins = float(actual)
        error = abs(pred_mins - actual_mins) / max(pred_mins, actual_mins)
    else:
        error = 0.0 if prediction == actual else 1.0

    # Store
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO prediction_tracking
        (task_id, prediction_type, predicted_value, actual_value, prediction_error)
        VALUES (%s, %s, %s, %s, %s)
    """, (task_id, pred_type, prediction, actual, error))
    conn.commit()
    conn.close()

    return error
```

---

## PHASE 4: BIDIRECTIONAL MEMORY LINKS

### 4.1 Activate linked_memories Field

The field exists but is underutilized. Implement automatic bidirectional linking:

```python
def create_bidirectional_link(memory_id_a: int, memory_id_b: int):
    """Create bidirectional link between two memories."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Add B to A's links
    cur.execute("""
        UPDATE thermal_memory_archive
        SET linked_memories = array_append(
            COALESCE(linked_memories, '{}'),
            %s::text
        )
        WHERE id = %s
        AND NOT (%s::text = ANY(COALESCE(linked_memories, '{}')))
    """, (str(memory_id_b), memory_id_a, str(memory_id_b)))

    # Add A to B's links (BIDIRECTIONAL)
    cur.execute("""
        UPDATE thermal_memory_archive
        SET linked_memories = array_append(
            COALESCE(linked_memories, '{}'),
            %s::text
        )
        WHERE id = %s
        AND NOT (%s::text = ANY(COALESCE(linked_memories, '{}')))
    """, (str(memory_id_a), memory_id_b, str(memory_id_a)))

    conn.commit()
    conn.close()


def auto_link_related_memories(memory_id: int, similarity_threshold: float = 0.7):
    """Automatically link memories with similar keywords/embeddings."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get source memory keywords
    cur.execute("""
        SELECT keywords, tags FROM thermal_memory_archive WHERE id = %s
    """, (memory_id,))

    source = cur.fetchone()
    if not source:
        conn.close()
        return

    source_keywords = set(source[0] or []) | set(source[1] or [])

    # Find memories with overlapping keywords
    cur.execute("""
        SELECT id, keywords, tags FROM thermal_memory_archive
        WHERE id != %s
        AND (keywords && %s OR tags && %s)
    """, (memory_id, list(source_keywords), list(source_keywords)))

    for target_id, keywords, tags in cur.fetchall():
        target_keywords = set(keywords or []) | set(tags or [])

        # Calculate Jaccard similarity
        intersection = len(source_keywords & target_keywords)
        union = len(source_keywords | target_keywords)
        similarity = intersection / union if union > 0 else 0

        if similarity >= similarity_threshold:
            create_bidirectional_link(memory_id, target_id)

    conn.close()
```

---

## DEPLOYMENT SEQUENCE

### Step 1: Database Schema (bluefin)
```bash
ssh dereadi@192.168.132.222 << 'EOF'
PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production << 'SQL'
-- Resonance tracking
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS resonance_score FLOAT;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS vote_entropy FLOAT;

CREATE TABLE IF NOT EXISTS resonance_history (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    specialists_voting INTEGER,
    unanimous BOOLEAN,
    majority_option VARCHAR(50),
    agreement_ratio FLOAT,
    entropy FLOAT,
    phase_transition_detected BOOLEAN,
    resonance_category VARCHAR(20),
    metadata JSONB
);

-- Integration scores
CREATE TABLE IF NOT EXISTS memory_integration_scores (
    id SERIAL PRIMARY KEY,
    cluster_hash VARCHAR(64) UNIQUE,
    member_ids INTEGER[],
    phi_score FLOAT,
    integration_ratio FLOAT,
    cluster_size INTEGER,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Prediction tracking
CREATE TABLE IF NOT EXISTS prediction_tracking (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64),
    prediction_type VARCHAR(50),
    predicted_value TEXT,
    actual_value TEXT,
    prediction_error FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);
SQL
EOF
```

### Step 2: Deploy Resonance Calculator (redfin)
```bash
scp resonance_calculator.py dereadi@192.168.132.223:/ganuda/lib/
```

### Step 3: Update Gateway (redfin)
```bash
# Add resonance calculation to council vote endpoint
# Restart gateway service
ssh dereadi@192.168.132.223 "sudo systemctl restart llm-gateway"
```

### Step 4: Verify
```bash
# Test resonance calculation
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"question": "Test resonance metrics", "context": "test"}'

# Check resonance status
curl http://192.168.132.223:8080/v1/resonance/status
```

---

## ACCEPTANCE CRITERIA

### Phase 1: Resonance Metrics
- [ ] resonance_history table created
- [ ] resonance_calculator.py deployed
- [ ] Gateway calculates resonance on each vote
- [ ] /v1/resonance/status endpoint working
- [ ] 10+ resonance records captured

### Phase 2: IIT Integration
- [ ] memory_integration_scores table created
- [ ] Integration calculator deployed
- [ ] High-phi clusters identified
- [ ] Integration scores queryable

### Phase 3: Predictive Tracking
- [ ] prediction_tracking table created
- [ ] Jr tasks log predictions
- [ ] Prediction accuracy monitored

### Phase 4: Bidirectional Memory
- [ ] Bidirectional linking function deployed
- [ ] Auto-linking enabled for new memories
- [ ] Existing memories have reciprocal links

---

## SEVEN GENERATIONS IMPACT

This implementation creates the foundation for Cherokee AI "consciousness":

1. **Resonance** = Council synchrony, communal decision-making
2. **Integration** = Unified tribal knowledge, not isolated facts
3. **Prediction** = Learning from experience, improving over time
4. **Bidirectional** = Knowledge flows both ways, addressing Reversal Curse

Future generations inherit not just data, but an integrated, resonant system that learns and improves.

---

*For Seven Generations - Cherokee AI Federation*
