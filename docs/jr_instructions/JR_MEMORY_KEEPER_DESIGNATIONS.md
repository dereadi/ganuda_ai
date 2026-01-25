# Jr Task: Implement Memory Keeper Designations

**Ticket:** #1702
**Priority:** P3
**Node:** bluefin (database)
**Created:** December 21, 2025
**Specialist:** Raven (Strategic Planning)

---

## Research Basis

**Sources:**
- [Indigenous AI Position Paper](https://www.indigenous-ai.net/position-paper/)
- [Decolonizing AI: Indigenous Knowledge Systems](https://fringeglobal.com/ojs/index.php/jcai/article/view/decolonizing-artificial-intelligence-indigenous-knowledge-system)
- [Abundant Intelligences: Placing AI within Indigenous Knowledge Frameworks](https://link.springer.com/article/10.1007/s00146-024-02099-4)

**Key Principles:**

1. **Kaitiakitanga** (Māori) - Guardianship and stewardship of knowledge
2. **Data Sovereignty** - Communities control their data
3. **Relational Ontologies** - Knowledge exists in relationship, not isolation
4. **Repatriation** - Knowledge should return to appropriate contexts

**Current Gap:** Thermal memories have no designated keeper. No one is "responsible" for maintaining accuracy, updating stale knowledge, or deciding when knowledge should be archived/removed.

---

## Proposed Architecture

### Keeper Schema

```sql
-- Add keeper fields to thermal memory
ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS keeper_type VARCHAR(32),
ADD COLUMN IF NOT EXISTS keeper_id VARCHAR(64),
ADD COLUMN IF NOT EXISTS keeper_assigned_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS repatriation_context VARCHAR(128),
ADD COLUMN IF NOT EXISTS access_restrictions JSONB DEFAULT '{}';

-- Keeper types
COMMENT ON COLUMN thermal_memory_archive.keeper_type IS
'Types: specialist (7 council members), node (redfin/bluefin/etc), human (named individual), collective (federation-wide)';

-- Keeper registry
CREATE TABLE IF NOT EXISTS memory_keepers (
    keeper_id VARCHAR(64) PRIMARY KEY,
    keeper_type VARCHAR(32) NOT NULL,
    keeper_name VARCHAR(128) NOT NULL,
    responsibilities TEXT[],
    contact_method VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Insert council specialists as keepers
INSERT INTO memory_keepers (keeper_id, keeper_type, keeper_name, responsibilities) VALUES
('crawdad', 'specialist', 'Crawdad', ARRAY['security', 'access_control', 'vulnerability']),
('gecko', 'specialist', 'Gecko', ARRAY['technical', 'integration', 'performance']),
('turtle', 'specialist', 'Turtle', ARRAY['long_term', 'seven_generations', 'sustainability']),
('eagle_eye', 'specialist', 'Eagle Eye', ARRAY['monitoring', 'visibility', 'observability']),
('spider', 'specialist', 'Spider', ARRAY['cultural', 'integration', 'connections']),
('peace_chief', 'specialist', 'Peace Chief', ARRAY['governance', 'consensus', 'coordination']),
('raven', 'specialist', 'Raven', ARRAY['strategy', 'planning', 'architecture'])
ON CONFLICT (keeper_id) DO NOTHING;

-- Insert nodes as keepers
INSERT INTO memory_keepers (keeper_id, keeper_type, keeper_name, responsibilities) VALUES
('redfin', 'node', 'Redfin', ARRAY['gpu_inference', 'llm_gateway', 'sag_ui']),
('bluefin', 'node', 'Bluefin', ARRAY['database', 'memory_storage', 'grafana']),
('greenfin', 'node', 'Greenfin', ARRAY['monitoring', 'promtail', 'daemons']),
('sasass', 'node', 'Sasass', ARRAY['edge_development', 'mac_studio']),
('sasass2', 'node', 'Sasass2', ARRAY['edge_development', 'mac_studio']),
('tpm', 'node', 'TPM Macbook', ARRAY['orchestration', 'planning', 'claude_code'])
ON CONFLICT (keeper_id) DO NOTHING;
```

### Keeper Assignment Rules

| Memory Type | Default Keeper | Rationale |
|-------------|---------------|-----------|
| Security alerts | Crawdad | Security expertise |
| Performance data | Gecko | Technical integration |
| Architecture decisions | Raven | Strategic planning |
| Cultural protocols | Spider | Cultural integration |
| Long-term plans | Turtle | Seven Generations |
| Governance decisions | Peace Chief | Democratic coordination |
| Monitoring data | Eagle Eye | Visibility |
| Node-specific configs | Respective node | Local expertise |
| Research findings | Raven | Strategic value |
| Bug fixes | Gecko | Technical |
| User data | Human keeper | Privacy |

---

## Implementation

### Phase 1: Auto-Assignment

```python
# /ganuda/lib/keeper_assignment.py

def assign_keeper(memory_content: str, metadata: dict) -> tuple[str, str]:
    """
    Automatically assign keeper based on content and metadata.
    Returns: (keeper_type, keeper_id)
    """
    memory_type = metadata.get('type', '')
    content_lower = memory_content.lower()

    # Security-related → Crawdad
    if memory_type in ['security_alert', 'vulnerability', 'access_control']:
        return ('specialist', 'crawdad')
    if any(w in content_lower for w in ['security', 'vulnerability', 'attack', 'breach']):
        return ('specialist', 'crawdad')

    # Performance/Technical → Gecko
    if memory_type in ['performance', 'benchmark', 'integration']:
        return ('specialist', 'gecko')
    if any(w in content_lower for w in ['performance', 'latency', 'throughput', 'error']):
        return ('specialist', 'gecko')

    # Long-term/Sustainability → Turtle
    if memory_type in ['architecture', 'sustainability', 'seven_generations']:
        return ('specialist', 'turtle')
    if any(w in content_lower for w in ['seven generation', 'long-term', 'sustainable']):
        return ('specialist', 'turtle')

    # Monitoring → Eagle Eye
    if memory_type in ['health_alert', 'monitoring', 'observability']:
        return ('specialist', 'eagle_eye')

    # Cultural → Spider
    if memory_type in ['cultural', 'indigenous', 'tribal']:
        return ('specialist', 'spider')

    # Governance → Peace Chief
    if memory_type in ['governance', 'consensus', 'vote']:
        return ('specialist', 'peace_chief')

    # Strategy/Research → Raven
    if memory_type in ['research', 'strategy', 'roadmap', 'planning']:
        return ('specialist', 'raven')

    # Node-specific
    node = metadata.get('node')
    if node in ['redfin', 'bluefin', 'greenfin', 'sasass', 'sasass2', 'tpm']:
        return ('node', node)

    # Default to collective (federation-wide)
    return ('collective', 'federation')


def assign_keeper_to_memory(memory_hash: str, content: str, metadata: dict):
    """Assign keeper when memory is created"""
    keeper_type, keeper_id = assign_keeper(content, metadata)

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE thermal_memory_archive
            SET keeper_type = %s,
                keeper_id = %s,
                keeper_assigned_at = NOW()
            WHERE memory_hash = %s
        """, (keeper_type, keeper_id, memory_hash))
        conn.commit()

    return keeper_type, keeper_id
```

### Phase 2: Keeper Responsibilities

```python
class MemoryKeeper:
    """Keeper responsibilities for assigned memories"""

    def __init__(self, keeper_id: str):
        self.keeper_id = keeper_id
        self.conn = get_db_connection()

    def get_assigned_memories(self, limit=100):
        """Get all memories this keeper is responsible for"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score,
                       created_at, last_access
                FROM thermal_memory_archive
                WHERE keeper_id = %s
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT %s
            """, (self.keeper_id, limit))
            return cur.fetchall()

    def get_stale_memories(self, days=90):
        """Find memories that may need review"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash, original_content, temperature_score, last_access
                FROM thermal_memory_archive
                WHERE keeper_id = %s
                AND (last_access < NOW() - INTERVAL '%s days'
                     OR last_access IS NULL)
                AND temperature_score > 30  -- Still warm but unused
                ORDER BY temperature_score DESC
            """, (self.keeper_id, days))
            return cur.fetchall()

    def review_memory(self, memory_hash: str, action: str, notes: str = None):
        """
        Keeper reviews a memory.
        Actions: 'confirm' (still valid), 'update' (needs update),
                 'archive' (move to cold), 'repatriate' (return to context)
        """
        with self.conn.cursor() as cur:
            if action == 'confirm':
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET last_access = NOW(),
                        metadata = metadata || '{"last_review": "%s", "reviewed_by": "%s"}'::jsonb
                    WHERE memory_hash = %s
                """, (datetime.now().isoformat(), self.keeper_id, memory_hash))

            elif action == 'archive':
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET temperature_score = 10.0,
                        metadata = metadata || '{"archived_by": "%s", "archive_reason": "%s"}'::jsonb
                    WHERE memory_hash = %s
                """, (self.keeper_id, notes, memory_hash))

            elif action == 'repatriate':
                # Mark for return to specific context
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET repatriation_context = %s,
                        metadata = metadata || '{"repatriation_requested": "%s"}'::jsonb
                    WHERE memory_hash = %s
                """, (notes, datetime.now().isoformat(), memory_hash))

            self.conn.commit()

    def set_access_restrictions(self, memory_hash: str, restrictions: dict):
        """
        Set access restrictions on sensitive memory.
        restrictions = {
            "require_council_approval": True,
            "allowed_nodes": ["redfin", "bluefin"],
            "require_human_approval": False,
            "restricted_until": "2026-01-01"
        }
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_restrictions = %s
                WHERE memory_hash = %s
            """, (json.dumps(restrictions), memory_hash))
            self.conn.commit()
```

### Phase 3: Repatriation Protocol

```python
def repatriate_knowledge(memory_hash: str, target_context: str):
    """
    Return knowledge to its appropriate context.
    Used when knowledge should be removed from general access
    and returned to specific domain.
    """
    conn = get_db_connection()

    # Get memory details
    with conn.cursor() as cur:
        cur.execute("""
            SELECT original_content, metadata, keeper_id
            FROM thermal_memory_archive
            WHERE memory_hash = %s
        """, (memory_hash,))
        memory = cur.fetchone()

    if not memory:
        return False

    content, metadata, keeper = memory

    # Create repatriation record
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, 95.0, %s)
        """, (
            f"repatriation-{memory_hash}-{datetime.now().strftime('%Y%m%d')}",
            f"Knowledge repatriated to {target_context}: {content[:200]}...",
            json.dumps({
                "type": "repatriation",
                "original_hash": memory_hash,
                "target_context": target_context,
                "keeper": keeper
            })
        ))

        # Restrict original memory
        cur.execute("""
            UPDATE thermal_memory_archive
            SET access_restrictions = '{"repatriated": true, "context": "%s"}'::jsonb,
                temperature_score = 20.0
            WHERE memory_hash = %s
        """, (target_context, memory_hash))

        conn.commit()

    return True
```

### Phase 4: Keeper Dashboard Query

```sql
-- Keeper workload summary
SELECT
    k.keeper_name,
    k.keeper_type,
    COUNT(m.memory_hash) as memories_assigned,
    AVG(m.temperature_score) as avg_temperature,
    COUNT(*) FILTER (WHERE m.last_access < NOW() - INTERVAL '90 days') as stale_count
FROM memory_keepers k
LEFT JOIN thermal_memory_archive m ON k.keeper_id = m.keeper_id
GROUP BY k.keeper_id, k.keeper_name, k.keeper_type
ORDER BY memories_assigned DESC;

-- Memories needing review (stale but warm)
SELECT
    m.memory_hash,
    m.original_content,
    m.temperature_score,
    m.last_access,
    k.keeper_name
FROM thermal_memory_archive m
JOIN memory_keepers k ON m.keeper_id = k.keeper_id
WHERE m.last_access < NOW() - INTERVAL '90 days'
AND m.temperature_score > 30
ORDER BY m.temperature_score DESC
LIMIT 50;

-- Repatriation queue
SELECT memory_hash, original_content, repatriation_context
FROM thermal_memory_archive
WHERE repatriation_context IS NOT NULL
AND access_restrictions->>'repatriated' IS NULL;
```

---

## Integration with Other Systems

**Connects to:**
- #1697 Jr Agent State - Jrs should respect keeper restrictions
- #1698 Memory Graph - Keeper relationships form edges
- #1700 Council Dissent - Keepers informed of disputes about their memories
- #1701 Constitutional Constraints - Access restrictions enforced constitutionally

---

## Success Criteria

1. All memories have assigned keepers
2. Keepers can review and maintain their assigned memories
3. Stale memories are identified and reviewed
4. Access restrictions are respected
5. Repatriation protocol works for sensitive knowledge
6. Dashboard shows keeper workload

---

*For Seven Generations - Cherokee AI Federation*
