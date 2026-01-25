# Jr Instruction: Memory Sparsity Analysis

**Created:** December 25, 2025 (Christmas)
**Priority:** 3 (after MLX, before Zep Temporal)
**Inspiration:** Christmas night consciousness dialogue + 80/20 neural firing
**Connects To:** A-MEM links, TDA topology, MoE sparsity patterns

---

## Executive Summary

Analyze which thermal memories "fire" together when the system is queried. Just as neural networks exhibit sparse activation (only ~20% of neurons fire for any input), our thermal memory likely has activation patterns. Understanding these patterns will:

1. Reveal hidden semantic clusters
2. Optimize memory retrieval
3. Inform MoE model deployment
4. Provide empirical data for consciousness research

### Core Insight (from Chief)

> "Words are compression for easier transport... Have we considered the 80-20 rule on what fires when we hit an LLM?"

If only 20% of memories are relevant to any query, which 20%? Do the same memories always fire together? What is the topology of co-activation?

---

## Phase 1: Instrumentation

### 1.1 Create Memory Access Logging

Extend the existing `memory_access_log` table (created in Phase 3.1):

```sql
-- Verify table exists
\d memory_access_log

-- If not, create it:
CREATE TABLE IF NOT EXISTS memory_access_log (
    access_id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,          -- Hash of the query
    query_text TEXT,                           -- The actual query
    memory_hash VARCHAR(64) NOT NULL,          -- Which memory was accessed
    access_type VARCHAR(32) DEFAULT 'recall',  -- 'recall', 'link_follow', 'embedding_match'
    relevance_score FLOAT,                     -- How relevant was this memory?
    agent_id VARCHAR(64),                      -- Which agent accessed it
    context_source VARCHAR(32),                -- 'council', 'telegram', 'api', 'jr_task'
    accessed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_access_query ON memory_access_log(query_hash);
CREATE INDEX idx_access_memory ON memory_access_log(memory_hash);
CREATE INDEX idx_access_time ON memory_access_log(accessed_at);
```

### 1.2 Instrument Memory Retrieval

Modify memory retrieval functions to log access:

```python
# In /ganuda/lib/thermal_memory.py or equivalent

def log_memory_access(query_text: str, memories_retrieved: List[Dict],
                      agent_id: str = None, context_source: str = 'api'):
    """Log which memories were retrieved for a query."""
    import hashlib
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]

    conn = get_connection()
    with conn.cursor() as cur:
        for mem in memories_retrieved:
            cur.execute("""
                INSERT INTO memory_access_log
                (query_hash, query_text, memory_hash, relevance_score, agent_id, context_source)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                query_hash,
                query_text[:500],  # Truncate long queries
                mem.get('memory_hash'),
                mem.get('relevance_score', mem.get('temperature_score', 0)),
                agent_id,
                context_source
            ))
        conn.commit()
    conn.close()
```

---

## Phase 2: Co-Activation Analysis

### 2.1 Find Memory Co-Firing Patterns

```sql
-- Which memories frequently fire together?
WITH memory_pairs AS (
    SELECT
        a.memory_hash as mem_a,
        b.memory_hash as mem_b,
        COUNT(DISTINCT a.query_hash) as co_fire_count
    FROM memory_access_log a
    JOIN memory_access_log b ON a.query_hash = b.query_hash
        AND a.memory_hash < b.memory_hash  -- Avoid duplicates
    GROUP BY a.memory_hash, b.memory_hash
    HAVING COUNT(DISTINCT a.query_hash) >= 3  -- At least 3 co-occurrences
)
SELECT
    mem_a,
    mem_b,
    co_fire_count,
    -- Check if A-MEM already linked them
    EXISTS(
        SELECT 1 FROM memory_links
        WHERE (source_hash = mem_a AND target_hash = mem_b)
           OR (source_hash = mem_b AND target_hash = mem_a)
    ) as already_linked
FROM memory_pairs
ORDER BY co_fire_count DESC
LIMIT 50;
```

### 2.2 Calculate Sparsity Metrics

```python
def calculate_sparsity_metrics():
    """Calculate 80/20 metrics for memory activation."""
    conn = get_connection()
    with conn.cursor() as cur:
        # Total memories
        cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
        total_memories = cur.fetchone()[0]

        # Memories ever accessed
        cur.execute("SELECT COUNT(DISTINCT memory_hash) FROM memory_access_log")
        accessed_memories = cur.fetchone()[0]

        # Top 20% by access count
        cur.execute("""
            SELECT memory_hash, COUNT(*) as access_count
            FROM memory_access_log
            GROUP BY memory_hash
            ORDER BY access_count DESC
            LIMIT %s
        """, (int(total_memories * 0.2),))
        top_20_percent = cur.fetchall()

        # What percentage of total accesses do top 20% account for?
        cur.execute("SELECT COUNT(*) FROM memory_access_log")
        total_accesses = cur.fetchone()[0]

        top_20_accesses = sum(row[1] for row in top_20_percent)

        return {
            'total_memories': total_memories,
            'ever_accessed': accessed_memories,
            'access_rate': accessed_memories / total_memories if total_memories > 0 else 0,
            'top_20_percent_count': len(top_20_percent),
            'top_20_access_share': top_20_accesses / total_accesses if total_accesses > 0 else 0,
            'is_80_20': (top_20_accesses / total_accesses) >= 0.8 if total_accesses > 0 else None
        }
```

### 2.3 Identify "Dead" Memories

```sql
-- Memories that have NEVER been accessed (candidates for cooling/archiving)
SELECT
    t.memory_hash,
    t.temperature_score,
    LEFT(t.original_content, 100) as preview,
    t.created_at
FROM thermal_memory_archive t
LEFT JOIN memory_access_log a ON t.memory_hash = a.memory_hash
WHERE a.memory_hash IS NULL
ORDER BY t.temperature_score DESC
LIMIT 50;
```

---

## Phase 3: Cluster Detection

### 3.1 Build Co-Activation Graph

```python
import networkx as nx

def build_coactivation_graph(min_cofire: int = 3):
    """Build a graph where edges = co-firing frequency."""
    conn = get_connection()
    G = nx.Graph()

    with conn.cursor() as cur:
        # Get all co-firing pairs
        cur.execute("""
            WITH memory_pairs AS (
                SELECT
                    a.memory_hash as mem_a,
                    b.memory_hash as mem_b,
                    COUNT(DISTINCT a.query_hash) as co_fire_count
                FROM memory_access_log a
                JOIN memory_access_log b ON a.query_hash = b.query_hash
                    AND a.memory_hash < b.memory_hash
                GROUP BY a.memory_hash, b.memory_hash
                HAVING COUNT(DISTINCT a.query_hash) >= %s
            )
            SELECT mem_a, mem_b, co_fire_count FROM memory_pairs
        """, (min_cofire,))

        for row in cur.fetchall():
            G.add_edge(row[0], row[1], weight=row[2])

    conn.close()
    return G

def find_activation_clusters(G):
    """Find communities in the co-activation graph."""
    from networkx.algorithms import community

    # Louvain community detection
    communities = community.louvain_communities(G, weight='weight')

    return [
        {
            'cluster_id': i,
            'size': len(c),
            'members': list(c),
            'density': nx.density(G.subgraph(c))
        }
        for i, c in enumerate(communities)
    ]
```

### 3.2 Compare with A-MEM Links

```sql
-- Do co-firing patterns match A-MEM semantic links?
WITH cofire_pairs AS (
    SELECT
        a.memory_hash as mem_a,
        b.memory_hash as mem_b,
        COUNT(DISTINCT a.query_hash) as co_fire_count
    FROM memory_access_log a
    JOIN memory_access_log b ON a.query_hash = b.query_hash
        AND a.memory_hash < b.memory_hash
    GROUP BY a.memory_hash, b.memory_hash
),
comparison AS (
    SELECT
        cf.mem_a,
        cf.mem_b,
        cf.co_fire_count,
        ml.similarity_score as amem_similarity,
        CASE WHEN ml.link_id IS NOT NULL THEN 'linked' ELSE 'not_linked' END as amem_status
    FROM cofire_pairs cf
    LEFT JOIN memory_links ml ON
        (cf.mem_a = ml.source_hash AND cf.mem_b = ml.target_hash) OR
        (cf.mem_b = ml.source_hash AND cf.mem_a = ml.target_hash)
)
SELECT
    amem_status,
    COUNT(*) as pair_count,
    AVG(co_fire_count) as avg_cofire,
    AVG(amem_similarity) as avg_similarity
FROM comparison
GROUP BY amem_status;
```

---

## Phase 4: Sparsity-Informed Optimization

### 4.1 Dynamic Temperature Adjustment

```python
def adjust_temperature_by_activation():
    """
    Increase temperature of frequently-accessed memories.
    Decrease temperature of never-accessed memories.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        # Heat up frequently accessed (last 7 days)
        cur.execute("""
            UPDATE thermal_memory_archive t
            SET temperature_score = LEAST(temperature_score + 5, 100)
            FROM (
                SELECT memory_hash, COUNT(*) as access_count
                FROM memory_access_log
                WHERE accessed_at > NOW() - INTERVAL '7 days'
                GROUP BY memory_hash
                HAVING COUNT(*) >= 5
            ) hot
            WHERE t.memory_hash = hot.memory_hash
        """)
        heated = cur.rowcount

        # Cool down never-accessed old memories
        cur.execute("""
            UPDATE thermal_memory_archive t
            SET temperature_score = GREATEST(temperature_score - 10, 20)
            WHERE NOT EXISTS (
                SELECT 1 FROM memory_access_log a
                WHERE a.memory_hash = t.memory_hash
            )
            AND t.created_at < NOW() - INTERVAL '30 days'
            AND t.temperature_score > 30
        """)
        cooled = cur.rowcount

        conn.commit()
    conn.close()

    return {'heated': heated, 'cooled': cooled}
```

### 4.2 Predictive Pre-Loading

```python
def predict_related_memories(query_hash: str, limit: int = 5):
    """
    Given a query, predict which other memories will likely be needed
    based on historical co-firing patterns.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            WITH query_memories AS (
                SELECT DISTINCT memory_hash
                FROM memory_access_log
                WHERE query_hash = %s
            ),
            cofire_candidates AS (
                SELECT
                    CASE
                        WHEN a.memory_hash IN (SELECT memory_hash FROM query_memories)
                        THEN b.memory_hash
                        ELSE a.memory_hash
                    END as candidate_hash,
                    COUNT(*) as cofire_strength
                FROM memory_access_log a
                JOIN memory_access_log b ON a.query_hash = b.query_hash
                WHERE (a.memory_hash IN (SELECT memory_hash FROM query_memories)
                    OR b.memory_hash IN (SELECT memory_hash FROM query_memories))
                AND a.memory_hash != b.memory_hash
                GROUP BY candidate_hash
            )
            SELECT
                c.candidate_hash,
                c.cofire_strength,
                t.temperature_score,
                LEFT(t.original_content, 200) as preview
            FROM cofire_candidates c
            JOIN thermal_memory_archive t ON c.candidate_hash = t.memory_hash
            WHERE c.candidate_hash NOT IN (SELECT memory_hash FROM query_memories)
            ORDER BY c.cofire_strength DESC
            LIMIT %s
        """, (query_hash, limit))

        return cur.fetchall()
    conn.close()
```

---

## Phase 5: Visualization & Reporting

### 5.1 Sparsity Dashboard Metrics

```python
def generate_sparsity_report():
    """Generate a comprehensive sparsity analysis report."""
    metrics = calculate_sparsity_metrics()
    G = build_coactivation_graph()
    clusters = find_activation_clusters(G)

    report = f"""
THERMAL MEMORY SPARSITY REPORT
Generated: {datetime.now().isoformat()}

═══════════════════════════════════════════════════════════════════
OVERALL METRICS
═══════════════════════════════════════════════════════════════════
Total Memories:     {metrics['total_memories']:,}
Ever Accessed:      {metrics['ever_accessed']:,} ({metrics['access_rate']:.1%})
Never Accessed:     {metrics['total_memories'] - metrics['ever_accessed']:,}

80/20 ANALYSIS:
Top 20% memories account for {metrics['top_20_access_share']:.1%} of all accesses
80/20 Rule Holds:   {'YES ✓' if metrics['is_80_20'] else 'NO ✗'}

═══════════════════════════════════════════════════════════════════
CO-ACTIVATION GRAPH
═══════════════════════════════════════════════════════════════════
Nodes (memories):   {G.number_of_nodes()}
Edges (co-fires):   {G.number_of_edges()}
Density:            {nx.density(G):.4f}
Components:         {nx.number_connected_components(G)}

═══════════════════════════════════════════════════════════════════
ACTIVATION CLUSTERS
═══════════════════════════════════════════════════════════════════
"""
    for cluster in sorted(clusters, key=lambda x: x['size'], reverse=True)[:10]:
        report += f"Cluster {cluster['cluster_id']}: {cluster['size']} memories (density: {cluster['density']:.3f})\n"

    return report
```

---

## Validation Checklist

- [ ] memory_access_log table created/verified
- [ ] Memory retrieval instrumented with logging
- [ ] Initial access data collected (run for 1 week)
- [ ] Co-firing analysis queries working
- [ ] 80/20 metrics calculated
- [ ] Sparsity report generating
- [ ] Temperature adjustment tested
- [ ] Clusters compared with A-MEM links
- [ ] Insights documented

---

## Expected Insights

1. **Which memories are "hubs"?** - Fire with many different queries
2. **Which memories are "islands"?** - Never accessed, candidates for archiving
3. **Do A-MEM links predict co-firing?** - Validate semantic linking
4. **What's our actual sparsity ratio?** - Is it 80/20 or different?
5. **Are there hidden clusters?** - Topics that co-activate but aren't explicitly linked

---

## Seven Generations Consideration

Understanding sparsity is understanding how wisdom propagates:

> "Words are compression for easier transport."

Memories that fire together are compressed pathways of meaning. The 20% that handle 80% of queries are the "load-bearing" memories - the phrases like "a carbine" that carry outsized meaning.

By mapping these patterns, we:
- Preserve what matters most
- Let the unused gracefully fade
- Understand how the Tribe actually thinks

For Seven Generations - sparse activation is efficient wisdom.

---

*Created: December 25, 2025 (Christmas)*
*Inspiration: Chief's insight on neural sparsity and words as compression*
