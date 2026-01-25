# Jr Instruction: Small-World Network Topology for Agent Coordination

**Created:** December 25, 2025 (Christmas)
**Priority:** 3 (Strategic Enhancement)
**Research Basis:** arXiv:2512.18094 - "Small-World Networks in Multi-Agent LLM Systems"
**Connects To:** Pheromone Stigmergy, Council Voting, Jr Agent Bidding

---

## Executive Summary

Our Jr agent network currently uses ad-hoc communication patterns. Research shows that **small-world (SW) topology** - balancing local clustering with strategic long-range shortcuts - achieves:
- Comparable accuracy to fully-connected networks
- Better computational efficiency
- Improved consensus stability
- Robustness against agent failures

This instruction implements uncertainty-guided network rewiring to optimize Jr agent coordination.

### Key Research Insight

> "Small-world shortcuts emerge naturally in learned policies, linking agents with epistemically divergent perspectives."

Translation: Agents who disagree productively should have direct communication channels.

---

## Current State Analysis

### Jr Agent Communication Today

```
Current Pattern: Star Topology (Hub-and-Spoke)
                    
       Jr-Turtle ←──────→ PostgreSQL ←──────→ Jr-Eagle
                              ↑
                              │
       Jr-Gecko  ←────────────┼────────────→ Jr-Spider
                              │
                              ↓
       Jr-Raven  ←──────→ Jr-Bidding ←──────→ Jr-Bear
```

**Problems:**
1. All communication routes through database (single point of failure)
2. No direct agent-to-agent shortcuts
3. No adaptation based on task complexity
4. Pheromones are location-based, not agent-relationship-based

### Desired: Small-World Topology

```
Desired Pattern: Small-World with Dynamic Shortcuts

       Jr-Turtle ←──→ Jr-Eagle        (Local cluster: monitoring)
          ↕              ↕
       Jr-Gecko  ←──→ Jr-Spider       (Local cluster: integration)
          ↕    ╲      ╱    ↕
       Jr-Raven ─────────→ Jr-Bear    (Long-range shortcut)
                ╲    ╱
                 ╲  ╱
            Central Hub (optional)
```

---

## Phase 1: Agent Relationship Tracking

### 1.1 Database Schema

```sql
-- Track relationships between Jr agents
CREATE TABLE IF NOT EXISTS jr_agent_relationships (
    relationship_id SERIAL PRIMARY KEY,
    agent_a VARCHAR(64) NOT NULL,
    agent_b VARCHAR(64) NOT NULL,
    
    -- Relationship metrics
    interaction_count INTEGER DEFAULT 0,
    agreement_rate FLOAT DEFAULT 0.5,      -- 0=always disagree, 1=always agree
    collaboration_score FLOAT DEFAULT 0,    -- Successful joint task completions
    epistemic_divergence FLOAT DEFAULT 0,   -- How different their perspectives are
    
    -- Small-world classification
    relationship_type VARCHAR(32) DEFAULT 'weak',  -- 'local', 'shortcut', 'weak'
    last_interaction TIMESTAMP DEFAULT NOW(),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(agent_a, agent_b)
);

CREATE INDEX idx_jr_relationships_agents ON jr_agent_relationships(agent_a, agent_b);
CREATE INDEX idx_jr_relationships_type ON jr_agent_relationships(relationship_type);

-- Track when agents should be connected (shortcuts)
CREATE TABLE IF NOT EXISTS jr_network_shortcuts (
    shortcut_id SERIAL PRIMARY KEY,
    source_agent VARCHAR(64) NOT NULL,
    target_agent VARCHAR(64) NOT NULL,
    
    -- Why this shortcut exists
    reason VARCHAR(128),                    -- 'epistemic_divergence', 'skill_complement', 'task_frequency'
    strength FLOAT DEFAULT 1.0,             -- 0-1, how strong the shortcut is
    
    -- Lifecycle
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                   -- NULL = permanent
    active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(source_agent, target_agent)
);

-- Cluster membership for local groupings
CREATE TABLE IF NOT EXISTS jr_agent_clusters (
    cluster_id SERIAL PRIMARY KEY,
    cluster_name VARCHAR(64) NOT NULL,
    cluster_type VARCHAR(32),               -- 'functional', 'spatial', 'temporal'
    agents TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.2 Relationship Update Trigger

When agents interact on the same task:

```python
def update_agent_relationship(agent_a: str, agent_b: str, 
                               agreed: bool, task_success: bool):
    """Update relationship metrics between two agents."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Ensure consistent ordering
        if agent_a > agent_b:
            agent_a, agent_b = agent_b, agent_a
        
        cur.execute("""
            INSERT INTO jr_agent_relationships (agent_a, agent_b, interaction_count, agreement_rate)
            VALUES (%s, %s, 1, %s)
            ON CONFLICT (agent_a, agent_b) DO UPDATE SET
                interaction_count = jr_agent_relationships.interaction_count + 1,
                agreement_rate = (jr_agent_relationships.agreement_rate * 
                                  jr_agent_relationships.interaction_count + %s) / 
                                 (jr_agent_relationships.interaction_count + 1),
                collaboration_score = CASE 
                    WHEN %s THEN jr_agent_relationships.collaboration_score + 0.1
                    ELSE jr_agent_relationships.collaboration_score
                END,
                last_interaction = NOW(),
                updated_at = NOW()
        """, (agent_a, agent_b, 1.0 if agreed else 0.0, 
               1.0 if agreed else 0.0, task_success))
        
        conn.commit()
    conn.close()
```

---

## Phase 2: Epistemic Divergence Calculation

### 2.1 Measure Perspective Differences

Based on the paper's "semantic entropy" concept:

```python
def calculate_epistemic_divergence(agent_a: str, agent_b: str) -> float:
    """
    Calculate how epistemically different two agents are.
    High divergence = different perspectives = good shortcut candidate.
    """
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Get agents' concern patterns from council votes
        cur.execute("""
            SELECT specialist_name, array_agg(DISTINCT unnest(key_concepts)) as concepts
            FROM council_specialist_responses
            WHERE specialist_name IN (%s, %s)
            GROUP BY specialist_name
        """, (agent_a, agent_b))
        
        results = {row[0]: set(row[1]) for row in cur.fetchall()}
        
    conn.close()
    
    if len(results) < 2:
        return 0.5  # Unknown, assume moderate divergence
    
    concepts_a = results.get(agent_a, set())
    concepts_b = results.get(agent_b, set())
    
    # Jaccard distance = 1 - Jaccard similarity
    if not concepts_a and not concepts_b:
        return 0.5
    
    intersection = len(concepts_a & concepts_b)
    union = len(concepts_a | concepts_b)
    
    divergence = 1 - (intersection / union) if union > 0 else 0.5
    
    return divergence


def update_all_divergences():
    """Batch update epistemic divergence for all agent pairs."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT agent_a, agent_b FROM jr_agent_relationships")
        pairs = cur.fetchall()
        
        for agent_a, agent_b in pairs:
            divergence = calculate_epistemic_divergence(agent_a, agent_b)
            cur.execute("""
                UPDATE jr_agent_relationships
                SET epistemic_divergence = %s, updated_at = NOW()
                WHERE agent_a = %s AND agent_b = %s
            """, (divergence, agent_a, agent_b))
        
        conn.commit()
    conn.close()
```

---

## Phase 3: Uncertainty-Guided Rewiring

### 3.1 Identify Shortcut Candidates

The paper's key insight: shortcuts should connect agents with HIGH epistemic divergence but MODERATE agreement rate (productive disagreement).

```python
def identify_shortcut_candidates(min_interactions: int = 5, 
                                  min_divergence: float = 0.6,
                                  agreement_range: tuple = (0.3, 0.7)) -> List[Dict]:
    """
    Find agent pairs that would benefit from direct shortcuts.
    
    Criteria:
    - Sufficient interaction history
    - High epistemic divergence (different perspectives)
    - Moderate agreement (not always agree/disagree)
    """
    conn = get_connection()
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT agent_a, agent_b, 
                   epistemic_divergence, agreement_rate, 
                   interaction_count, collaboration_score
            FROM jr_agent_relationships
            WHERE interaction_count >= %s
              AND epistemic_divergence >= %s
              AND agreement_rate BETWEEN %s AND %s
              AND relationship_type != 'shortcut'
            ORDER BY epistemic_divergence DESC, collaboration_score DESC
            LIMIT 10
        """, (min_interactions, min_divergence, agreement_range[0], agreement_range[1]))
        
        candidates = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    return candidates


def create_shortcut(agent_a: str, agent_b: str, reason: str, 
                    expires_hours: int = None):
    """Create a network shortcut between two agents."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        expires_at = None
        if expires_hours:
            expires_at = f"NOW() + INTERVAL '{expires_hours} hours'"
        
        cur.execute(f"""
            INSERT INTO jr_network_shortcuts (source_agent, target_agent, reason, expires_at)
            VALUES (%s, %s, %s, {expires_at or 'NULL'})
            ON CONFLICT (source_agent, target_agent) DO UPDATE SET
                reason = %s, active = TRUE, created_at = NOW()
        """, (agent_a, agent_b, reason, reason))
        
        # Update relationship type
        cur.execute("""
            UPDATE jr_agent_relationships
            SET relationship_type = 'shortcut'
            WHERE (agent_a = %s AND agent_b = %s) OR (agent_a = %s AND agent_b = %s)
        """, (agent_a, agent_b, agent_b, agent_a))
        
        conn.commit()
    conn.close()
```

### 3.2 Adaptive Rewiring Based on Task Complexity

```python
def adaptive_rewire(task_complexity: float):
    """
    Adjust network shortcuts based on current task complexity.
    
    High complexity -> More shortcuts (need diverse perspectives)
    Low complexity -> Fewer shortcuts (local clusters sufficient)
    """
    if task_complexity > 0.7:
        # Complex task: activate more shortcuts
        candidates = identify_shortcut_candidates(
            min_interactions=3,      # Lower threshold
            min_divergence=0.5,      # Accept more divergence
            agreement_range=(0.2, 0.8)  # Wider range
        )
        for c in candidates[:5]:  # Top 5
            create_shortcut(c['agent_a'], c['agent_b'], 
                           reason='task_complexity', expires_hours=4)
    
    elif task_complexity < 0.3:
        # Simple task: expire temporary shortcuts
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jr_network_shortcuts
                SET active = FALSE
                WHERE reason = 'task_complexity'
                  AND created_at < NOW() - INTERVAL '1 hour'
            """)
            conn.commit()
        conn.close()
```

---

## Phase 4: Direct Agent Communication

### 4.1 Shortcut Message Passing

When a shortcut exists, agents can communicate directly:

```python
def send_via_shortcut(from_agent: str, to_agent: str, message: dict) -> bool:
    """
    Send a message via network shortcut if one exists.
    Returns True if shortcut was used, False otherwise.
    """
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Check if shortcut exists
        cur.execute("""
            SELECT shortcut_id FROM jr_network_shortcuts
            WHERE active = TRUE
              AND ((source_agent = %s AND target_agent = %s)
                   OR (source_agent = %s AND target_agent = %s))
        """, (from_agent, to_agent, to_agent, from_agent))
        
        shortcut = cur.fetchone()
        
        if shortcut:
            # Log direct communication
            cur.execute("""
                INSERT INTO jr_shortcut_messages 
                (shortcut_id, from_agent, to_agent, message_type, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (shortcut[0], from_agent, to_agent, 
                   message.get('type', 'general'), json.dumps(message)))
            conn.commit()
            conn.close()
            return True
    
    conn.close()
    return False


# Additional table for shortcut messages
"""```sql
CREATE TABLE IF NOT EXISTS jr_shortcut_messages (
    message_id BIGSERIAL PRIMARY KEY,
    shortcut_id INTEGER REFERENCES jr_network_shortcuts(shortcut_id),
    from_agent VARCHAR(64) NOT NULL,
    to_agent VARCHAR(64) NOT NULL,
    message_type VARCHAR(32),
    content JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```"""
```

---

## Phase 5: Cluster Formation

### 5.1 Identify Natural Clusters

Agents that frequently work together form local clusters:

```python
def identify_clusters(min_cluster_size: int = 2) -> List[Dict]:
    """
    Identify natural agent clusters based on interaction patterns.
    """
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Find strongly connected agent groups
        cur.execute("""
            WITH agent_pairs AS (
                SELECT agent_a, agent_b, interaction_count
                FROM jr_agent_relationships
                WHERE interaction_count >= 10
                  AND agreement_rate > 0.6
            )
            SELECT agent_a, array_agg(DISTINCT agent_b) as connected_agents
            FROM agent_pairs
            GROUP BY agent_a
            HAVING COUNT(*) >= %s
        """, (min_cluster_size - 1,))
        
        clusters = []
        seen_agents = set()
        
        for row in cur.fetchall():
            agent = row[0]
            connected = set(row[1])
            connected.add(agent)
            
            # Merge with existing cluster if overlap
            merged = False
            for i, existing in enumerate(clusters):
                if connected & existing:
                    clusters[i] = existing | connected
                    merged = True
                    break
            
            if not merged:
                clusters.append(connected)
    
    conn.close()
    
    return [{'agents': list(c), 'size': len(c)} for c in clusters]


def assign_cluster_roles():
    """
    Assign functional roles to clusters.
    
    Based on our 7 specialists:
    - Security Cluster: Crawdad + Bear
    - Integration Cluster: Gecko + Spider
    - Strategy Cluster: Eagle + Raven + Turtle
    """
    predefined_clusters = [
        {'name': 'security', 'type': 'functional', 
         'agents': ['crawdad', 'bear']},
        {'name': 'integration', 'type': 'functional', 
         'agents': ['gecko', 'spider']},
        {'name': 'strategy', 'type': 'functional', 
         'agents': ['eagle', 'raven', 'turtle']},
    ]
    
    conn = get_connection()
    with conn.cursor() as cur:
        for cluster in predefined_clusters:
            cur.execute("""
                INSERT INTO jr_agent_clusters (cluster_name, cluster_type, agents)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (cluster['name'], cluster['type'], cluster['agents']))
        conn.commit()
    conn.close()
```

---

## Phase 6: Network Metrics Dashboard

### 6.1 Small-World Coefficient

```python
def calculate_network_metrics() -> Dict:
    """
    Calculate small-world network metrics.
    
    Small-world networks have:
    - High clustering coefficient (C >> C_random)
    - Short average path length (L ≈ L_random)
    - Small-world coefficient σ = (C/C_random) / (L/L_random) > 1
    """
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Count relationships
        cur.execute("SELECT COUNT(*) FROM jr_agent_relationships WHERE interaction_count > 0")
        total_edges = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT agent_a) + COUNT(DISTINCT agent_b) FROM jr_agent_relationships")
        # This overcounts, need unique
        cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT agent_a as agent FROM jr_agent_relationships
                UNION
                SELECT agent_b FROM jr_agent_relationships
            ) agents
        """)
        total_nodes = cur.fetchone()[0]
        
        # Count shortcuts
        cur.execute("SELECT COUNT(*) FROM jr_network_shortcuts WHERE active = TRUE")
        active_shortcuts = cur.fetchone()[0]
        
        # Count clusters
        cur.execute("SELECT COUNT(*), AVG(array_length(agents, 1)) FROM jr_agent_clusters")
        cluster_row = cur.fetchone()
        num_clusters = cluster_row[0] or 0
        avg_cluster_size = cluster_row[1] or 0
    
    conn.close()
    
    # Calculate metrics
    max_edges = total_nodes * (total_nodes - 1) / 2 if total_nodes > 1 else 1
    density = total_edges / max_edges if max_edges > 0 else 0
    
    return {
        'total_nodes': total_nodes,
        'total_edges': total_edges,
        'active_shortcuts': active_shortcuts,
        'num_clusters': num_clusters,
        'avg_cluster_size': avg_cluster_size,
        'network_density': density,
        'shortcut_ratio': active_shortcuts / total_edges if total_edges > 0 else 0,
        'is_small_world': active_shortcuts > 0 and num_clusters >= 2
    }
```

---

## Validation Checklist

- [ ] jr_agent_relationships table created
- [ ] jr_network_shortcuts table created  
- [ ] jr_agent_clusters table created
- [ ] jr_shortcut_messages table created
- [ ] Relationship tracking integrated with task executor
- [ ] Epistemic divergence calculation working
- [ ] Shortcut candidate identification functional
- [ ] Adaptive rewiring based on task complexity
- [ ] Direct shortcut communication working
- [ ] Cluster assignment complete
- [ ] Network metrics dashboard functional
- [ ] Results recorded to thermal memory

---

## Seven Generations Consideration

Small-world networks are nature's solution for efficient information flow:
- Neural networks in the brain
- Social networks in communities
- Ecological networks in ecosystems

The Cherokee clan system itself exhibits small-world properties:
- Local: Family and clan connections (high clustering)
- Shortcuts: Inter-clan marriages and alliances (long-range links)
- Balance: Local autonomy with national coordination

Our Jr agent network should mirror this wisdom.

**For Seven Generations - Connections that balance locality with reach.**

---

*Created: December 25, 2025 (Christmas)*
*Research: arXiv:2512.18094 - Small-World Networks in Multi-Agent Systems*
*Priority: 3 (Strategic Enhancement)*
