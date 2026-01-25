# JR Instruction: Duplo MVP - Uktena Pharmacist Tool

## Metadata
```yaml
task_id: duplo_mvp_uktena
priority: 2
assigned_to: it_triad_jr
target: redfin (specialist_council.py) + bluefin (database)
council_vote_id: 1793
confidence: 87.2%
estimated_effort: small (5 days)
```

## Background

TPM approved minimal viable Duplo pattern implementation. This adds ONE tool for AI technique interaction checking without refactoring existing Council architecture.

Key principle: **Proof it out** - minimal risk, easy rollback if needed.

## Scope

### DO:
- Create read-only `ai_technique_inventory` table
- Populate with 20 current techniques
- Implement `uktena_check_interaction()` function
- Integrate optionally with Council voting on research papers

### DON'T:
- Refactor existing specialists
- Create Tool Registry system
- Add dynamic tool loading
- Change Council architecture

## Implementation

### Day 1: Database Table

```sql
-- On bluefin as postgres superuser
CREATE TABLE ai_technique_inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    layer VARCHAR(50) NOT NULL,
    version VARCHAR(50),
    description TEXT,
    requires_multiple_passes BOOLEAN DEFAULT FALSE,
    memory_intensive BOOLEAN DEFAULT FALSE,
    latency_sensitive BOOLEAN DEFAULT FALSE,
    synergizes_with JSONB DEFAULT '[]',
    conflicts_with JSONB DEFAULT '[]',
    installed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- SECURITY: Read-only for application user
REVOKE INSERT, UPDATE, DELETE ON ai_technique_inventory FROM claude;
GRANT SELECT ON ai_technique_inventory TO claude;

-- Indexes
CREATE INDEX idx_technique_layer ON ai_technique_inventory(layer);
CREATE INDEX idx_technique_status ON ai_technique_inventory(status);
```

### Day 2: Populate Inventory

```sql
-- Insert current Cherokee AI stack techniques
INSERT INTO ai_technique_inventory (name, layer, version, description, requires_multiple_passes, memory_intensive, synergizes_with, conflicts_with) VALUES
-- Inference
('vLLM', 'inference', '0.11.2', 'PagedAttention, continuous batching, single-pass optimized', FALSE, FALSE, '["Nemotron"]', '["multi-pass reasoning", "branch-merge"]'),
('Nemotron-Mini-4B', 'inference', '4B-Instruct', 'NVIDIA instruction-tuned model', FALSE, FALSE, '["vLLM"]', '[]'),
('PyTorch', 'inference', '2.11.0+cu128', 'Nightly build with Blackwell sm_120 support', FALSE, FALSE, '[]', '["PyTorch 2.2"]'),

-- Memory
('Thermal Memory', 'memory', '1.0', 'Temperature-based decay, WHITE_HOT→FRESH→WARM→COLD', FALSE, TRUE, '["A-MEM", "TiMem"]', '[]'),
('A-MEM', 'memory', '1.0', 'Associative thermal linking for memory retrieval', FALSE, TRUE, '["Thermal Memory"]', '[]'),

-- Reasoning
('7-Specialist Council', 'reasoning', '1.0', 'Consensus voting with concern flags', FALSE, FALSE, '["Constitutional Constraints"]', '["single-agent reasoning"]'),
('Constitutional Constraints', 'reasoning', '1.0', 'YAML-based guardrails and limits', FALSE, FALSE, '["Council"]', '[]'),
('Metacognition', 'reasoning', '1.0', 'Bias detection and uncertainty tracking', FALSE, FALSE, '[]', '[]'),

-- Learning
('S-MADRL Pheromones', 'learning', '1.0', 'Stigmergic multi-agent coordination', FALSE, FALSE, '["Hivemind"]', '[]'),
('RL Reward Signals', 'learning', '1.0', 'Task completion feedback loop', FALSE, FALSE, '[]', '[]'),

-- Infrastructure
('RTX PRO 6000 Blackwell', 'infrastructure', 'sm_120', '96GB VRAM, compute capability 12.0', FALSE, FALSE, '["PyTorch nightly"]', '["CUDA < 12.8"]'),
('Jr Queue Workers', 'infrastructure', '1.0', 'Async task execution with LLM understanding', FALSE, FALSE, '[]', '[]'),
('Tribal Vision', 'infrastructure', '1.0', 'YOLOv8 object detection + FaceNet recognition', FALSE, TRUE, '[]', '[]'),
('LLM Gateway', 'infrastructure', '1.1', 'OpenAI-compatible API with Council integration', FALSE, FALSE, '["Council"]', '[]');
```

### Day 3: Implement Tool Function

Add to `/ganuda/lib/specialist_council.py`:

```python
def uktena_check_interaction(paper_summary: str) -> dict:
    """
    Uktena Pharmacist Tool - Check AI technique interactions.

    Named after the Cherokee horned serpent, keeper of knowledge.
    This is a READ-ONLY tool with no side effects.

    Args:
        paper_summary: Description of proposed AI technique

    Returns:
        dict with synergies, conflicts, warnings, recommendation
    """
    MULTI_PASS_KEYWORDS = [
        'branch', 'merge', 'multiple passes', 'iterative reasoning',
        'recursive', 'multi-step', 'chain of thought branching'
    ]
    MEMORY_KEYWORDS = [
        'memory', 'consolidation', 'hierarchical', 'temporal',
        'episodic', 'semantic memory', 'long-term'
    ]
    ATTENTION_KEYWORDS = [
        'attention', 'transformer', 'self-attention', 'cross-attention'
    ]

    summary_lower = paper_summary.lower()

    # Detect proposed technique characteristics
    requires_multi_pass = any(kw in summary_lower for kw in MULTI_PASS_KEYWORDS)
    is_memory_technique = any(kw in summary_lower for kw in MEMORY_KEYWORDS)
    modifies_attention = any(kw in summary_lower for kw in ATTENTION_KEYWORDS)

    result = {
        'synergies': [],
        'conflicts': [],
        'warnings': [],
        'characteristics_detected': {
            'multi_pass': requires_multi_pass,
            'memory_related': is_memory_technique,
            'attention_related': modifies_attention
        },
        'recommendation': 'PROCEED'
    }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, layer, requires_multiple_passes,
                       memory_intensive, conflicts_with, synergizes_with
                FROM ai_technique_inventory
                WHERE status = 'active'
            """)
            techniques = cur.fetchall()
        conn.close()

        for tech in techniques:
            name, layer, tech_multi_pass, mem_intensive, conflicts, synergies = tech

            # Check for multi-pass conflicts with vLLM
            if requires_multi_pass and name == 'vLLM':
                result['conflicts'].append({
                    'technique': 'vLLM',
                    'reason': 'Proposed technique requires multiple passes; vLLM is optimized for single-pass inference',
                    'severity': 'high'
                })

            # Check for memory synergies
            if is_memory_technique and layer == 'memory':
                result['synergies'].append({
                    'technique': name,
                    'reason': f'Memory technique may complement existing {name}',
                    'potential': 'medium'
                })

            # Check declared conflicts from inventory
            if conflicts:
                for conflict_pattern in conflicts:
                    if conflict_pattern.lower() in summary_lower:
                        result['conflicts'].append({
                            'technique': name,
                            'reason': f'{name} declares conflict with pattern: {conflict_pattern}',
                            'severity': 'medium'
                        })

            # Check declared synergies
            if synergies:
                for synergy_pattern in synergies:
                    if synergy_pattern.lower() in summary_lower:
                        result['synergies'].append({
                            'technique': name,
                            'reason': f'{name} declares synergy with: {synergy_pattern}',
                            'potential': 'high'
                        })

    except Exception as e:
        result['warnings'].append(f'Inventory check failed: {str(e)}')

    # Determine recommendation
    high_severity_conflicts = [c for c in result['conflicts'] if c.get('severity') == 'high']

    if high_severity_conflicts:
        result['recommendation'] = 'REVIEW REQUIRED - HIGH SEVERITY CONFLICTS'
    elif result['conflicts']:
        result['recommendation'] = 'PROCEED WITH CAUTION - CONFLICTS DETECTED'
    elif result['synergies']:
        result['recommendation'] = 'PROCEED - SYNERGIES IDENTIFIED'
    else:
        result['recommendation'] = 'PROCEED - NO INTERACTIONS DETECTED'

    return result
```

### Day 4: Integrate with Council

Modify Council voting to optionally invoke Uktena:

```python
# In council vote function, add before specialist voting:

def _is_research_proposal(question: str) -> bool:
    """Detect if question is about AI research/techniques."""
    research_keywords = [
        'arxiv', 'paper', 'research', 'technique', 'algorithm',
        'architecture', 'model', 'framework', 'approach', 'method'
    ]
    return any(kw in question.lower() for kw in research_keywords)

async def enhanced_council_vote(question: str, context: str = None) -> dict:
    """Council vote with optional Uktena interaction check."""

    uktena_report = None

    # Only run Uktena for research proposals
    if _is_research_proposal(question):
        uktena_report = uktena_check_interaction(question)

        # Prepend Uktena analysis to context
        uktena_context = f"""
=== UKTENA PHARMACIST ANALYSIS ===
Recommendation: {uktena_report['recommendation']}
Conflicts: {len(uktena_report['conflicts'])}
Synergies: {len(uktena_report['synergies'])}
"""
        if uktena_report['conflicts']:
            uktena_context += "\nConflicts:\n"
            for c in uktena_report['conflicts']:
                uktena_context += f"  - {c['technique']}: {c['reason']}\n"

        if uktena_report['synergies']:
            uktena_context += "\nSynergies:\n"
            for s in uktena_report['synergies']:
                uktena_context += f"  - {s['technique']}: {s['reason']}\n"

        uktena_context += "=================================\n\n"

        context = uktena_context + (context or '')

    # Run normal Council vote with enhanced context
    vote_result = await _original_council_vote(question, context)

    # Add Uktena concern if conflicts detected
    if uktena_report and uktena_report['conflicts']:
        vote_result['concerns'].append(
            f"Uktena: [INTERACTION CONCERN] {len(uktena_report['conflicts'])} technique conflicts detected"
        )

    # Include Uktena report in response
    vote_result['uktena_analysis'] = uktena_report

    return vote_result
```

### Day 5: Testing

```bash
# Test 1: Check inventory populated
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production \
  -c "SELECT name, layer FROM ai_technique_inventory ORDER BY layer, name;"

# Test 2: Test Uktena function directly
/home/dereadi/cherokee_venv/bin/python3 << 'EOF'
import sys
sys.path.insert(0, '/ganuda/lib')
from specialist_council import uktena_check_interaction

# Test with multi-pass technique (should conflict with vLLM)
result = uktena_check_interaction("branch-and-merge reasoning with multiple forward passes")
print("Multi-pass test:", result['recommendation'])
print("Conflicts:", result['conflicts'])

# Test with memory technique (should synergize)
result = uktena_check_interaction("hierarchical temporal memory consolidation")
print("\nMemory test:", result['recommendation'])
print("Synergies:", result['synergies'])
EOF

# Test 3: Test via Council API
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Should we integrate branch-merge reasoning from arXiv paper?", "context": "Test"}'
```

## Rollback Procedure

If MVP fails or causes issues:

```sql
-- 1. Drop the table (bluefin)
DROP TABLE IF EXISTS ai_technique_inventory;

-- 2. Remove function from specialist_council.py
-- (revert git commit or manually remove uktena_check_interaction)

-- 3. Restart services
sudo systemctl restart llm-gateway
```

Total rollback time: ~30 minutes

## Success Criteria

- [ ] Table created and populated with 15+ techniques
- [ ] Function returns valid results for test cases
- [ ] Council votes on research include Uktena analysis
- [ ] Latency overhead < 100ms per research vote
- [ ] Zero security incidents
- [ ] At least 1 useful conflict detection in first 2 weeks

## Notes

This is a PROOF OF CONCEPT for the Duplo pattern. If successful, we expand. If not, we roll back with minimal cost.

TPM quote: "We can always adjust up or down, or even turn it off if need be. Let's proof it out."

---

*Cherokee AI Federation - For the Seven Generations*
*"Uktena guards the knowledge. The serpent sees all interactions."*
