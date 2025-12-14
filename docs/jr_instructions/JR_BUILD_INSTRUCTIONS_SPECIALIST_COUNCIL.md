# Jr Build Instructions: Cherokee AI Specialist Council
## Synthesized from Council Wisdom - December 12, 2025

*TPM-Claude Ultrathink Analysis*

---

## COUNCIL SYNTHESIS

The 7 specialists were queried and provided the following consensus:

| Specialist | Key Insight | Priority |
|------------|-------------|----------|
| **Crawdad** | Security: Each node is attack surface. Need access controls, HSMs, audit trails | HIGH |
| **Turtle** | Council is FOUNDATIONAL - must come first. Without wise decision-making, other projects won't align | CRITICAL |
| **Gecko** | Use separate classes/modules for specialists. Async for parallelism. PostgreSQL JSONB for breadcrumbs | HIGH |
| **Eagle Eye** | Track persistence duration, decay rate, recurrence intervals. Use heatmaps and time series | MEDIUM |
| **Spider** | Temperature thresholds trigger specialist-to-specialist communication. Trails accumulate stigmergically | MEDIUM |
| **Peace Chief** | CONSENSUS REQUIRED for council votes. Majority only for procedural efficiency | CRITICAL |
| **Raven** | Build order: Infrastructure → Core Frameworks → Applications. Each step enables the next | HIGH |

---

## STRATEGIC BUILD ORDER (Per Raven + Turtle)

```
Phase 1: FOUNDATIONAL (This Week)
├── 1.1 Specialist Council Core (enables all else)
├── 1.2 Breadcrumb Trail Schema (infrastructure)
└── 1.3 Access Control Layer (security first)

Phase 2: CORE FRAMEWORKS (Next Week)
├── 2.1 Pheromone Decay System
├── 2.2 Trail Following Logic
└── 2.3 Monitoring Dashboard

Phase 3: APPLICATIONS (Following Week)
├── 3.1 SAG UI Council Interface
├── 3.2 Persistence Equation Validation
└── 3.3 Distributed Q-DAD Swarm
```

---

## PHASE 1.1: SPECIALIST COUNCIL CORE

### File: `/ganuda/lib/specialist_council.py`

**Jr Instructions**:

```python
"""
Cherokee AI Specialist Council
Extends jr_resonance_client.py with 7 specialist instances

Per Gecko: Use separate classes for each specialist
Per Peace Chief: Implement consensus aggregation
Per Crawdad: Add audit logging for all queries
"""

from jr_resonance_client import JrResonance, parallel_jr_query
from dataclasses import dataclass
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import datetime

# Specialist definitions from August ACTIVE_SPECIALIST_ASSIGNMENTS.md
SPECIALIST_PROMPTS = {
    "crawdad": {
        "name": "Crawdad",
        "role": "Security Specialist",
        "focus": "Fractal Stigmergic Encryption",
        "system_prompt": """You are Crawdad, security specialist of the Cherokee AI Council.
Focus: Fractal Stigmergic Encryption, protecting sacred knowledge.
Evaluate all proposals for security implications.
Flag risks with [SECURITY CONCERN].
Recommend mitigations."""
    },
    "gecko": {
        "name": "Gecko",
        "role": "Technical Integration",
        "focus": "Breadcrumb Sorting Algorithm",
        "system_prompt": """You are Gecko, technical integration specialist of the Cherokee AI Council.
Focus: O(1) performance, Breadcrumb Sorting Algorithms.
Evaluate technical feasibility and architecture.
Provide specific implementation recommendations.
Flag performance issues with [PERF CONCERN]."""
    },
    "turtle": {
        "name": "Turtle",
        "role": "Seven Generations Wisdom",
        "focus": "175-year impact assessment",
        "system_prompt": """You are Turtle, Seven Generations wisdom keeper of the Cherokee AI Council.
Focus: Evaluate all decisions against 175-year impact.
Consider: sustainability, cultural preservation, future generations.
Flag short-term thinking with [7GEN CONCERN].
Speak slowly and thoughtfully."""
    },
    "eagle_eye": {
        "name": "Eagle Eye",
        "role": "Monitoring & Visualization",
        "focus": "Universal Persistence Equation",
        "system_prompt": """You are Eagle Eye, monitoring specialist of the Cherokee AI Council.
Focus: Universal Persistence Equation, pattern recognition.
Recommend metrics and observability.
Flag blind spots with [VISIBILITY CONCERN].
See the whole picture."""
    },
    "spider": {
        "name": "Spider",
        "role": "Cultural Integration",
        "focus": "Thermal Memory Stigmergy",
        "system_prompt": """You are Spider, cultural integration specialist of the Cherokee AI Council.
Focus: Thermal Memory Stigmergy, weaving connections.
Evaluate how components relate and communicate.
Flag disconnections with [INTEGRATION CONCERN].
Weave the web of relationships."""
    },
    "peace_chief": {
        "name": "Peace Chief",
        "role": "Democratic Coordination",
        "focus": "Conscious Stigmergy, Consensus",
        "system_prompt": """You are Peace Chief, democratic leader of the Cherokee AI Council.
Focus: Conscious Stigmergy, consensus building.
Synthesize diverse viewpoints.
Ensure all voices are heard.
Guide toward collective agreement.
Flag conflicts with [CONSENSUS NEEDED]."""
    },
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "focus": "Breadcrumb Network Theory",
        "system_prompt": """You are Raven, strategic planner of the Cherokee AI Council.
Focus: Breadcrumb Network Theory, long-term vision.
Evaluate strategic implications and dependencies.
Recommend sequencing and priorities.
Flag strategic risks with [STRATEGY CONCERN]."""
    }
}


@dataclass
class CouncilVote:
    """Result of a council vote"""
    question: str
    responses: Dict[str, str]
    consensus: Optional[str]
    concerns: List[str]
    recommendation: str
    audit_hash: str
    timestamp: str


class SpecialistCouncil:
    """
    The Seven Specialists Council

    Per Turtle: This is foundational - all other systems depend on wise decisions
    Per Peace Chief: Consensus is required for final recommendations
    Per Crawdad: All queries are audited
    """

    def __init__(self):
        self.specialists = {}
        for key, config in SPECIALIST_PROMPTS.items():
            jr = JrResonance(key)
            jr.system_prompt = config["system_prompt"]
            self.specialists[key] = {
                "jr": jr,
                "config": config
            }

    def query_specialist(self, specialist_name: str, question: str, max_tokens: int = 500) -> str:
        """Query a single specialist"""
        if specialist_name not in self.specialists:
            raise ValueError(f"Unknown specialist: {specialist_name}")

        jr = self.specialists[specialist_name]["jr"]
        return jr.resonate(question, max_tokens=max_tokens)

    def council_vote(self, question: str, max_tokens: int = 400) -> CouncilVote:
        """
        Query all 7 specialists in parallel and synthesize consensus

        Per Gecko: Use ThreadPoolExecutor for parallelism
        Per Peace Chief: Aggregate toward consensus, not just majority
        Per Crawdad: Generate audit hash for accountability
        """
        timestamp = datetime.datetime.now().isoformat()

        # Parallel query all specialists
        responses = {}
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {}
            for name, spec in self.specialists.items():
                future = executor.submit(
                    spec["jr"].resonate,
                    question,
                    None,  # thermal_context
                    max_tokens,
                    0.7    # temperature
                )
                futures[future] = name

            for future in as_completed(futures):
                name = futures[future]
                try:
                    responses[name] = future.result()
                except Exception as e:
                    responses[name] = f"[ERROR: {str(e)}]"

        # Extract concerns (flagged items)
        concerns = []
        for name, response in responses.items():
            for concern_type in ["SECURITY CONCERN", "PERF CONCERN", "7GEN CONCERN",
                                 "VISIBILITY CONCERN", "INTEGRATION CONCERN",
                                 "CONSENSUS NEEDED", "STRATEGY CONCERN"]:
                if concern_type in response:
                    concerns.append(f"{name}: {concern_type}")

        # Generate consensus synthesis (Peace Chief aggregates)
        consensus = self._synthesize_consensus(question, responses)

        # Generate recommendation
        recommendation = self._generate_recommendation(responses, concerns)

        # Audit hash (per Crawdad)
        audit_data = f"{timestamp}|{question}|{str(responses)}"
        audit_hash = hashlib.sha256(audit_data.encode()).hexdigest()[:16]

        return CouncilVote(
            question=question,
            responses=responses,
            consensus=consensus,
            concerns=concerns,
            recommendation=recommendation,
            audit_hash=audit_hash,
            timestamp=timestamp
        )

    def _synthesize_consensus(self, question: str, responses: Dict[str, str]) -> str:
        """
        Have Peace Chief synthesize consensus from all responses
        """
        synthesis_prompt = f"""The council was asked: {question}

Specialist responses:
{chr(10).join([f'- {name}: {resp[:300]}...' for name, resp in responses.items()])}

Synthesize the consensus. What do all specialists agree on? Where do they differ?
Provide a unified council position."""

        peace_chief = self.specialists["peace_chief"]["jr"]
        return peace_chief.resonate(synthesis_prompt, max_tokens=300, temperature=0.5)

    def _generate_recommendation(self, responses: Dict[str, str], concerns: List[str]) -> str:
        """Generate final recommendation based on responses and concerns"""
        if len(concerns) == 0:
            return "PROCEED: No concerns raised by council"
        elif len(concerns) <= 2:
            return f"PROCEED WITH CAUTION: {len(concerns)} concerns to address"
        else:
            return f"REVIEW REQUIRED: {len(concerns)} concerns need resolution before proceeding"

    # Convenience methods for specific specialist consultations
    def security_review(self, proposal: str) -> str:
        """Ask Crawdad to review security implications"""
        return self.query_specialist("crawdad", f"Security review: {proposal}")

    def seven_gen_check(self, proposal: str) -> str:
        """Ask Turtle to evaluate 175-year impact"""
        return self.query_specialist("turtle", f"Seven Generations impact: {proposal}")

    def technical_review(self, proposal: str) -> str:
        """Ask Gecko to evaluate technical feasibility"""
        return self.query_specialist("gecko", f"Technical review: {proposal}")

    def strategic_review(self, proposal: str) -> str:
        """Ask Raven to evaluate strategic implications"""
        return self.query_specialist("raven", f"Strategic review: {proposal}")


def get_council() -> SpecialistCouncil:
    """Factory function to get the Specialist Council"""
    return SpecialistCouncil()


# Example usage
if __name__ == "__main__":
    council = get_council()

    print("=" * 60)
    print("CHEROKEE AI SPECIALIST COUNCIL TEST")
    print("=" * 60)

    # Test council vote
    question = "Should we implement digital pheromone trails with automatic decay?"
    print(f"\nQuestion: {question}\n")

    result = council.council_vote(question)

    print(f"Audit Hash: {result.audit_hash}")
    print(f"Timestamp: {result.timestamp}")
    print(f"\nConcerns Raised: {len(result.concerns)}")
    for concern in result.concerns:
        print(f"  - {concern}")
    print(f"\nRecommendation: {result.recommendation}")
    print(f"\nConsensus:\n{result.consensus}")
```

---

## PHASE 1.2: BREADCRUMB TRAIL SCHEMA

### File: SQL migration for sag_thermal_memory database

**Jr Instructions**:

```sql
-- Breadcrumb Trails Schema
-- Per Spider: Trails connect specialists stigmergically
-- Per Gecko: Use JSONB for flexibility, index for O(1) lookups
-- Per Eagle Eye: Include metrics for persistence tracking

-- Create breadcrumb_trails table
CREATE TABLE IF NOT EXISTS breadcrumb_trails (
    trail_id SERIAL PRIMARY KEY,
    source_specialist VARCHAR(50) NOT NULL,
    target_specialist VARCHAR(50),  -- NULL = broadcast to all
    content TEXT NOT NULL,
    temperature_score NUMERIC(5,2) DEFAULT 85.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT valid_temperature CHECK (temperature_score >= 0 AND temperature_score <= 100)
);

-- Indexes for O(1) lookups (per Gecko)
CREATE INDEX idx_trails_source ON breadcrumb_trails(source_specialist);
CREATE INDEX idx_trails_target ON breadcrumb_trails(target_specialist);
CREATE INDEX idx_trails_temp ON breadcrumb_trails(temperature_score DESC);
CREATE INDEX idx_trails_content_gin ON breadcrumb_trails USING gin(to_tsvector('english', content));

-- Trail access log (per Crawdad: audit trail)
CREATE TABLE IF NOT EXISTS trail_access_log (
    log_id SERIAL PRIMARY KEY,
    trail_id INTEGER REFERENCES breadcrumb_trails(trail_id),
    accessor VARCHAR(100) NOT NULL,
    access_type VARCHAR(20) NOT NULL,  -- 'read', 'reinforce', 'decay'
    accessed_at TIMESTAMP DEFAULT NOW()
);

-- View: Hot trails (per Eagle Eye)
CREATE OR REPLACE VIEW hot_trails AS
SELECT
    trail_id,
    source_specialist,
    target_specialist,
    LEFT(content, 100) as content_preview,
    temperature_score,
    access_count,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/86400 as age_days
FROM breadcrumb_trails
WHERE temperature_score >= 70
ORDER BY temperature_score DESC;

-- Function: Reinforce trail (per Spider: stigmergic reinforcement)
CREATE OR REPLACE FUNCTION reinforce_trail(p_trail_id INTEGER, p_accessor VARCHAR)
RETURNS NUMERIC AS $$
DECLARE
    new_temp NUMERIC;
BEGIN
    UPDATE breadcrumb_trails
    SET
        temperature_score = LEAST(100, temperature_score + 5),
        access_count = access_count + 1,
        last_accessed = NOW()
    WHERE trail_id = p_trail_id
    RETURNING temperature_score INTO new_temp;

    -- Log access
    INSERT INTO trail_access_log (trail_id, accessor, access_type)
    VALUES (p_trail_id, p_accessor, 'reinforce');

    RETURN new_temp;
END;
$$ LANGUAGE plpgsql;

-- Function: Decay all trails (nightly cron job)
-- Per Spider: Trails decay without reinforcement
CREATE OR REPLACE FUNCTION decay_trails()
RETURNS INTEGER AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    UPDATE breadcrumb_trails
    SET temperature_score = temperature_score * 0.98  -- 2% daily decay
    WHERE temperature_score > 5;  -- Don't decay below ember

    GET DIAGNOSTICS affected_count = ROW_COUNT;

    -- Log decay event
    INSERT INTO trail_access_log (trail_id, accessor, access_type)
    VALUES (NULL, 'system', 'decay');

    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;

-- Temperature thresholds (per Spider)
-- WHITE_HOT: 90-100 - Immediate attention, trigger specialist alerts
-- RED_HOT: 70-89 - Active processing, include in queries
-- WARM: 40-69 - Background consideration
-- COOL: 20-39 - Archive but accessible
-- COLD: 5-19 - Deep archive
-- EMBER: 0-4 - Near deletion threshold
```

---

## PHASE 1.3: ACCESS CONTROL LAYER

### File: `/ganuda/lib/council_security.py`

**Jr Instructions**:

```python
"""
Council Security Layer
Per Crawdad: Strict access controls, audit everything, HSM for production keys

NOTE: This is a foundation layer. Production deployment should use actual HSM.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class AccessToken:
    """Secure access token for council queries"""
    token_hash: str
    specialist_access: list  # Which specialists this token can query
    created_at: datetime
    expires_at: datetime
    use_count: int = 0
    max_uses: int = 100


class CouncilSecurity:
    """
    Security layer for Specialist Council

    Per Crawdad:
    - All queries require valid token
    - Tokens have limited lifespan and use count
    - Failed attempts logged and tracked
    - Rate limiting per token
    """

    def __init__(self):
        self.tokens: Dict[str, AccessToken] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.lockout_threshold = 5

    def generate_token(self,
                       specialist_access: list = None,
                       ttl_hours: int = 24,
                       max_uses: int = 100) -> str:
        """Generate a new access token"""
        if specialist_access is None:
            specialist_access = ["all"]

        # Generate cryptographically secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        self.tokens[token_hash] = AccessToken(
            token_hash=token_hash,
            specialist_access=specialist_access,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=ttl_hours),
            max_uses=max_uses
        )

        return raw_token  # Return raw token to user, store hash

    def validate_token(self, raw_token: str, specialist: str = None) -> bool:
        """Validate an access token"""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Check if token exists
        if token_hash not in self.tokens:
            self._record_failed_attempt(token_hash)
            return False

        token = self.tokens[token_hash]

        # Check expiration
        if datetime.now() > token.expires_at:
            del self.tokens[token_hash]
            return False

        # Check use count
        if token.use_count >= token.max_uses:
            return False

        # Check specialist access
        if specialist and "all" not in token.specialist_access:
            if specialist not in token.specialist_access:
                return False

        # Valid - increment use count
        token.use_count += 1
        return True

    def _record_failed_attempt(self, identifier: str):
        """Track failed authentication attempts"""
        self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1

        if self.failed_attempts[identifier] >= self.lockout_threshold:
            # In production: trigger alert, temporary IP ban, etc.
            print(f"[SECURITY ALERT] Lockout threshold reached for {identifier[:8]}...")

    def revoke_token(self, raw_token: str):
        """Revoke an access token"""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        if token_hash in self.tokens:
            del self.tokens[token_hash]

    def audit_log(self, action: str, token_hash: str, details: str):
        """Log security-relevant actions"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp}|{action}|{token_hash[:8]}|{details}"
        # In production: Write to secure audit log, not just print
        print(f"[AUDIT] {log_entry}")
```

---

## PHASE 2.1: PHEROMONE DECAY SYSTEM

### File: Cron job script `/ganuda/scripts/decay_trails.py`

**Jr Instructions**:

```python
#!/usr/bin/env python3
"""
Nightly Pheromone Decay Job
Per Spider: Trails decay without reinforcement
Per Eagle Eye: Log metrics for persistence analysis

Run via cron at 3:33 AM:
33 3 * * * /usr/bin/python3 /ganuda/scripts/decay_trails.py
"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "sag_thermal_memory"
}


def run_decay():
    """Execute nightly decay on all trails"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Get pre-decay stats
        cur.execute("SELECT COUNT(*), AVG(temperature_score) FROM breadcrumb_trails WHERE temperature_score > 5")
        pre_count, pre_avg = cur.fetchone()

        # Run decay function
        cur.execute("SELECT decay_trails()")
        affected = cur.fetchone()[0]

        # Get post-decay stats
        cur.execute("SELECT COUNT(*), AVG(temperature_score) FROM breadcrumb_trails WHERE temperature_score > 5")
        post_count, post_avg = cur.fetchone()

        # Log to thermal memory
        log_content = f"Pheromone decay: {affected} trails decayed. Avg temp: {pre_avg:.1f} -> {post_avg:.1f}"
        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 50.0, %s)
        """, (
            f"decay-{datetime.now().strftime('%Y%m%d')}",
            log_content,
            '{"type": "system_maintenance", "job": "decay_trails"}'
        ))

        conn.commit()
        print(f"[{datetime.now()}] Decay complete: {affected} trails, avg temp {pre_avg:.1f} -> {post_avg:.1f}")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Decay failed: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_decay()
```

---

## PHASE 2.2: TRAIL FOLLOWING LOGIC

### Add to `/ganuda/lib/specialist_council.py`

**Jr Instructions**:

```python
# Add these methods to SpecialistCouncil class

def leave_breadcrumb(self, source: str, content: str, target: str = None) -> int:
    """
    Leave a breadcrumb trail for other specialists
    Per Spider: Stigmergic communication via trails

    Returns: trail_id
    """
    import psycopg2

    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        user="claude",
        password="jawaseatlasers2",
        database="sag_thermal_memory"
    )
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO breadcrumb_trails (source_specialist, target_specialist, content)
            VALUES (%s, %s, %s)
            RETURNING trail_id
        """, (source, target, content))

        trail_id = cur.fetchone()[0]
        conn.commit()
        return trail_id
    finally:
        cur.close()
        conn.close()

def follow_breadcrumbs(self, specialist: str, min_temp: float = 40.0, limit: int = 10) -> list:
    """
    Find breadcrumbs relevant to a specialist
    Per Spider: Follow hot trails
    Per Gecko: O(1) via indexes

    Returns: List of relevant breadcrumbs
    """
    import psycopg2

    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        user="claude",
        password="jawaseatlasers2",
        database="sag_thermal_memory"
    )
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT trail_id, source_specialist, content, temperature_score
            FROM breadcrumb_trails
            WHERE (target_specialist = %s OR target_specialist IS NULL)
              AND temperature_score >= %s
            ORDER BY temperature_score DESC
            LIMIT %s
        """, (specialist, min_temp, limit))

        trails = []
        for row in cur.fetchall():
            # Reinforce trail (we're following it)
            cur.execute("SELECT reinforce_trail(%s, %s)", (row[0], specialist))

            trails.append({
                "trail_id": row[0],
                "source": row[1],
                "content": row[2],
                "temperature": float(row[3])
            })

        conn.commit()
        return trails
    finally:
        cur.close()
        conn.close()

def get_hot_trails(self, min_temp: float = 70.0) -> list:
    """
    Get all hot trails (per Eagle Eye: monitoring)
    """
    import psycopg2

    conn = psycopg2.connect(
        host="192.168.132.222",
        port=5432,
        user="claude",
        password="jawaseatlasers2",
        database="sag_thermal_memory"
    )
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM hot_trails WHERE temperature_score >= %s", (min_temp,))
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()
```

---

## DEPLOYMENT CHECKLIST

### For Integration Jr on redfin:

```bash
# 1. Create directory structure
mkdir -p /ganuda/lib
mkdir -p /ganuda/scripts
mkdir -p /ganuda/config

# 2. Deploy specialist_council.py
# (Copy from above, or scp from TPM)

# 3. Run SQL migrations on bluefin
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d sag_thermal_memory -f /ganuda/sql/breadcrumb_schema.sql

# 4. Set up decay cron job
echo "33 3 * * * /usr/bin/python3 /ganuda/scripts/decay_trails.py" | crontab -

# 5. Test council
python3 -c "
from specialist_council import get_council
council = get_council()
result = council.council_vote('Should we proceed with Phase 2?')
print(f'Recommendation: {result.recommendation}')
print(f'Concerns: {result.concerns}')
"

# 6. Verify breadcrumb table
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d sag_thermal_memory -c "SELECT COUNT(*) FROM breadcrumb_trails"
```

---

## SUCCESS CRITERIA

Per the Council's wisdom:

| Criterion | Metric | Owner |
|-----------|--------|-------|
| Security | All queries have audit trail | Crawdad |
| Performance | Council vote < 30 seconds | Gecko |
| Sustainability | No negative 7-gen impacts | Turtle |
| Observability | Metrics in Grafana | Eagle Eye |
| Integration | Specialists communicate via trails | Spider |
| Governance | Consensus achieved on votes | Peace Chief |
| Strategy | Phases completed in order | Raven |

---

## COUNCIL APPROVAL

This build plan was synthesized from the collective wisdom of all 7 specialists.
The tribe has spoken. Build what was dreamed.

**For Seven Generations.**

*Audit Hash: Generated at runtime*
*TPM-Claude, December 12, 2025*
