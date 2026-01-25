# Jr Instructions: HiveMind DAG-Shapley Contribution Tracking

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Source**: arXiv:2512.06432
**Ultrathink**: ULTRATHINK-HIVEMIND-DEC20-2025.md

---

## OBJECTIVE

Implement contribution tracking for the 7-Specialist Council using DAG-Shapley algorithm principles from the HiveMind paper. This enables dynamic prompt refinement based on which specialists add unique value.

---

### Task 1: Create Contribution Tracker

Create `/ganuda/services/llm_gateway/contribution_tracker.py`:

```python
#!/usr/bin/env python3
"""
Specialist Contribution Tracker
Based on HiveMind DAG-Shapley (arXiv:2512.06432)
Cherokee AI Federation - For Seven Generations
"""

import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

SPECIALISTS = [
    'gecko', 'crawdad', 'turtle', 'spider',
    'eagle_eye', 'raven', 'peace_chief'
]


class SpecialistContribution:
    """Track individual specialist contribution metrics."""

    def __init__(self, specialist_name: str):
        self.specialist = specialist_name
        self.votes_cast = 0
        self.votes_aligned_with_final = 0
        self.unique_concerns_raised = 0
        self.concerns_validated = 0
        self.shapley_value = 0.0

    def to_dict(self) -> dict:
        alignment_rate = (
            self.votes_aligned_with_final / max(self.votes_cast, 1)
        )
        concern_validity = (
            self.concerns_validated / max(self.unique_concerns_raised, 1)
        )
        return {
            'specialist': self.specialist,
            'votes_cast': self.votes_cast,
            'alignment_rate': round(alignment_rate, 3),
            'unique_concerns': self.unique_concerns_raised,
            'concern_validity': round(concern_validity, 3),
            'shapley_value': round(self.shapley_value, 3)
        }


def get_db():
    return psycopg2.connect(**DB_CONFIG)


def record_vote(audit_hash: str, specialist: str, vote: str,
                concern_flag: bool, final_decision: str):
    """Record a specialist's vote for contribution tracking."""
    conn = get_db()
    cur = conn.cursor()

    aligned = (vote == final_decision)

    cur.execute("""
        INSERT INTO specialist_contributions
        (audit_hash, specialist, vote, concern_flag, aligned_with_final, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (audit_hash, specialist) DO UPDATE SET
            vote = EXCLUDED.vote,
            concern_flag = EXCLUDED.concern_flag,
            aligned_with_final = EXCLUDED.aligned_with_final
    """, (audit_hash, specialist, vote, concern_flag, aligned))

    conn.commit()
    cur.close()
    conn.close()


def calculate_shapley_values(days: int = 30) -> Dict[str, float]:
    """
    Calculate simplified Shapley values for each specialist.

    Shapley value approximation based on:
    1. Unique concern contribution (flagged issues that were validated)
    2. Vote alignment with final decision
    3. Marginal contribution to decision quality
    """
    conn = get_db()
    cur = conn.cursor()

    cutoff = datetime.now() - timedelta(days=days)

    # Get contribution stats per specialist
    cur.execute("""
        SELECT
            specialist,
            COUNT(*) as votes,
            SUM(CASE WHEN aligned_with_final THEN 1 ELSE 0 END) as aligned,
            SUM(CASE WHEN concern_flag THEN 1 ELSE 0 END) as concerns
        FROM specialist_contributions
        WHERE created_at > %s
        GROUP BY specialist
    """, (cutoff,))

    stats = {row[0]: {
        'votes': row[1],
        'aligned': row[2],
        'concerns': row[3]
    } for row in cur.fetchall()}

    cur.close()
    conn.close()

    # Calculate Shapley approximation
    shapley = {}
    total_votes = sum(s['votes'] for s in stats.values()) or 1

    for specialist in SPECIALISTS:
        s = stats.get(specialist, {'votes': 0, 'aligned': 0, 'concerns': 0})

        # Unique contribution score
        alignment = s['aligned'] / max(s['votes'], 1)
        concern_rate = s['concerns'] / max(s['votes'], 1)

        # Shapley approximation: value = alignment + concern_novelty
        # Higher concern rate = more unique value (if concerns are valid)
        shapley[specialist] = round(alignment * 0.7 + concern_rate * 0.3, 3)

    return shapley


def get_contribution_report() -> dict:
    """Generate full contribution report for all specialists."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            specialist,
            COUNT(*) as votes,
            SUM(CASE WHEN aligned_with_final THEN 1 ELSE 0 END) as aligned,
            SUM(CASE WHEN concern_flag THEN 1 ELSE 0 END) as concerns,
            AVG(CASE WHEN aligned_with_final THEN 1.0 ELSE 0.0 END) as align_rate
        FROM specialist_contributions
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY specialist
        ORDER BY align_rate DESC
    """)

    specialists = []
    for row in cur.fetchall():
        specialists.append({
            'specialist': row[0],
            'votes': row[1],
            'aligned': row[2],
            'concerns': row[3],
            'alignment_rate': round(row[4] or 0, 3)
        })

    shapley = calculate_shapley_values()

    cur.close()
    conn.close()

    return {
        'generated_at': datetime.now().isoformat(),
        'period_days': 30,
        'specialists': specialists,
        'shapley_values': shapley,
        'top_contributors': sorted(shapley.items(), key=lambda x: x[1], reverse=True)[:3]
    }


if __name__ == '__main__':
    report = get_contribution_report()
    print(json.dumps(report, indent=2))
```

---

### Task 2: Create Database Schema

Create `/ganuda/sql/specialist_contributions.sql`:

```sql
-- Specialist Contribution Tracking Schema
-- Based on HiveMind DAG-Shapley

CREATE TABLE IF NOT EXISTS specialist_contributions (
    id SERIAL PRIMARY KEY,
    audit_hash VARCHAR(32) NOT NULL,
    specialist VARCHAR(32) NOT NULL,
    vote VARCHAR(32),
    concern_flag BOOLEAN DEFAULT FALSE,
    aligned_with_final BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(audit_hash, specialist)
);

CREATE INDEX idx_spec_contrib_specialist ON specialist_contributions(specialist);
CREATE INDEX idx_spec_contrib_created ON specialist_contributions(created_at);

-- View for quick stats
CREATE OR REPLACE VIEW specialist_stats AS
SELECT
    specialist,
    COUNT(*) as total_votes,
    SUM(CASE WHEN aligned_with_final THEN 1 ELSE 0 END) as aligned_votes,
    SUM(CASE WHEN concern_flag THEN 1 ELSE 0 END) as concerns_raised,
    ROUND(AVG(CASE WHEN aligned_with_final THEN 1.0 ELSE 0.0 END)::numeric, 3) as alignment_rate
FROM specialist_contributions
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY specialist;
```

---

### Task 3: Integrate with Gateway

Add to `/ganuda/services/llm_gateway/gateway.py` in the council_vote function:

```python
# After collecting all specialist votes:
from contribution_tracker import record_vote

# Record each specialist's contribution
for specialist, response in specialist_responses.items():
    record_vote(
        audit_hash=audit_hash,
        specialist=specialist,
        vote=response.get('vote', 'unknown'),
        concern_flag=response.get('has_concern', False),
        final_decision=final_decision
    )
```

---

## SUCCESS CRITERIA

1. specialist_contributions table created
2. contribution_tracker.py runs without errors
3. Votes are recorded after each council decision
4. Shapley values calculated for all 7 specialists
5. get_contribution_report() returns valid JSON

---

*For Seven Generations - Cherokee AI Federation*
