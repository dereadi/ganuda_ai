# ULTRATHINK: Duplo MVP - Minimum Viable Pharmacist

## Executive Summary

Instead of refactoring the entire Council architecture, we implement **one tool** that proves the Duplo pattern with minimal risk. The 7 specialists remain unchanged - they simply gain access to a new tool they can call when evaluating AI research.

> "Prove the pattern before betting the farm."

## Risk Mitigation

### Gecko's Performance Concerns

| Concern | Full Duplo Risk | MVP Mitigation |
|---------|-----------------|----------------|
| Tool loading overhead | Every vote loads tools | Tool called only for research votes |
| Composition latency | Dynamic assembly | No composition - direct function call |
| Memory pressure | Tool registry in RAM | Single function, lazy-loaded |
| Inference slowdown | Multiple tool invocations | One optional call per vote |

**MVP Performance Impact**: ~50ms per research paper vote (single DB query + comparison)

### Crawdad's Security Concerns

| Concern | Full Duplo Risk | MVP Mitigation |
|---------|-----------------|----------------|
| Tool injection | Dynamic tool loading | Hardcoded single function |
| Registry tampering | Mutable tool registry | READ-ONLY inventory table |
| Privilege escalation | Tools with write access | Tool only READS technique data |
| Attack surface | Multiple new systems | One table, one function |

**MVP Attack Surface**:
- One new table (read-only by application)
- One new function (no external calls, no writes)
- No new network endpoints
- No dynamic code execution

## Architecture: Duplo MVP

```
CURRENT COUNCIL (Unchanged)
┌─────────────────────────────────────────────────────────┐
│  Crawdad → Gecko → Turtle → Eagle Eye → Spider → ...   │
│                        │                                │
│                        ▼                                │
│            ┌───────────────────────┐                   │
│            │  NEW: uktena_check()  │ ◄── Single tool   │
│            │  (read-only helper)   │                   │
│            └───────────────────────┘                   │
│                        │                                │
│                        ▼                                │
│            ┌───────────────────────┐                   │
│            │ ai_technique_inventory│ ◄── Read-only DB │
│            │ (populated manually)  │                   │
│            └───────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### 1. Database Table (Read-Only)

```sql
-- Technique inventory - populated by TPM, read by specialists
CREATE TABLE ai_technique_inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    layer VARCHAR(50) NOT NULL,  -- inference, memory, reasoning, learning
    version VARCHAR(50),
    description TEXT,

    -- Interaction characteristics (simple flags)
    requires_multiple_passes BOOLEAN DEFAULT FALSE,
    memory_intensive BOOLEAN DEFAULT FALSE,
    latency_sensitive BOOLEAN DEFAULT FALSE,

    -- Known interactions (JSON for flexibility)
    synergizes_with JSONB DEFAULT '[]',
    conflicts_with JSONB DEFAULT '[]',

    installed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- Read-only access for application
REVOKE INSERT, UPDATE, DELETE ON ai_technique_inventory FROM claude;
GRANT SELECT ON ai_technique_inventory TO claude;

-- Index for fast lookups
CREATE INDEX idx_technique_layer ON ai_technique_inventory(layer);
CREATE INDEX idx_technique_status ON ai_technique_inventory(status);
```

### 2. Initial Inventory (20 Techniques)

```sql
INSERT INTO ai_technique_inventory (name, layer, description, requires_multiple_passes, memory_intensive, synergizes_with, conflicts_with) VALUES
-- Inference Layer
('vLLM', 'inference', 'PagedAttention, continuous batching', FALSE, FALSE, '["Nemotron"]', '["multi-pass reasoning"]'),
('Nemotron-Mini-4B', 'inference', 'NVIDIA instruct model', FALSE, FALSE, '["vLLM"]', '[]'),
('PyTorch 2.11 nightly', 'inference', 'Blackwell sm_120 support', FALSE, FALSE, '[]', '["PyTorch stable"]'),

-- Memory Layer
('Thermal Memory', 'memory', 'Temperature-based decay, 4 stages', FALSE, TRUE, '["A-MEM", "TiMem"]', '[]'),
('A-MEM', 'memory', 'Associative thermal linking', FALSE, TRUE, '["Thermal Memory"]', '[]'),
('PostgreSQL', 'memory', 'Relational storage for memories', FALSE, FALSE, '[]', '[]'),

-- Reasoning Layer
('7-Specialist Council', 'reasoning', 'Consensus voting with concerns', FALSE, FALSE, '["Constitutional Constraints"]', '["single-agent"]'),
('Constitutional Constraints', 'reasoning', 'YAML guardrails', FALSE, FALSE, '["Council"]', '[]'),
('Metacognition', 'reasoning', 'Bias detection, uncertainty', FALSE, FALSE, '[]', '[]'),

-- Learning Layer
('S-MADRL Pheromones', 'learning', 'Stigmergic coordination', FALSE, FALSE, '["Hivemind"]', '[]'),
('RL Reward Signals', 'learning', 'Task completion feedback', FALSE, FALSE, '[]', '[]'),
('Hivemind Tracking', 'learning', 'Contribution tracking', FALSE, FALSE, '["S-MADRL"]', '[]'),

-- Infrastructure
('RTX PRO 6000 Blackwell', 'infrastructure', '96GB VRAM, compute 12.0', FALSE, FALSE, '["PyTorch nightly"]', '["older CUDA"]'),
('Jr Queue Workers', 'infrastructure', 'Async task execution', FALSE, FALSE, '[]', '[]'),
('Tribal Vision', 'infrastructure', 'YOLOv8 + FaceNet', FALSE, TRUE, '[]', '[]');
```

### 3. Single Tool Function

```python
# Add to specialist_council.py - ONE new function

def uktena_check_interaction(paper_summary: str) -> dict:
    """
    Check if a proposed AI technique conflicts with installed stack.

    This is the ONLY new code. Read-only, no side effects.

    Args:
        paper_summary: Brief description of the proposed technique

    Returns:
        dict with synergies, conflicts, warnings, recommendation
    """
    # Keywords that suggest technique characteristics
    MULTI_PASS_KEYWORDS = ['branch', 'merge', 'multiple passes', 'iterative', 'recursive reasoning']
    MEMORY_KEYWORDS = ['memory', 'consolidation', 'hierarchical', 'temporal']
    LATENCY_KEYWORDS = ['real-time', 'streaming', 'low-latency']

    summary_lower = paper_summary.lower()

    # Detect characteristics
    requires_multi_pass = any(kw in summary_lower for kw in MULTI_PASS_KEYWORDS)
    is_memory_technique = any(kw in summary_lower for kw in MEMORY_KEYWORDS)
    is_latency_sensitive = any(kw in summary_lower for kw in LATENCY_KEYWORDS)

    result = {
        'synergies': [],
        'conflicts': [],
        'warnings': [],
        'recommendation': 'PROCEED'
    }

    # Check against installed techniques
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, layer, requires_multiple_passes,
                           memory_intensive, conflicts_with, synergizes_with
                    FROM ai_technique_inventory
                    WHERE status = 'active'
                """)
                techniques = cur.fetchall()

        for tech in techniques:
            name, layer, multi_pass, mem_intensive, conflicts, synergies = tech

            # Check for conflicts
            if requires_multi_pass and name == 'vLLM':
                result['conflicts'].append(
                    f"Multi-pass reasoning conflicts with vLLM single-pass optimization"
                )

            if is_memory_technique and mem_intensive:
                result['synergies'].append(
                    f"Memory technique may synergize with {name}"
                )

            # Check declared conflicts
            if conflicts:
                for conflict_pattern in conflicts:
                    if conflict_pattern.lower() in summary_lower:
                        result['conflicts'].append(
                            f"{name} declares conflict with '{conflict_pattern}'"
                        )

    except Exception as e:
        result['warnings'].append(f"Could not check inventory: {e}")

    # Set recommendation
    if result['conflicts']:
        result['recommendation'] = 'REVIEW - CONFLICTS DETECTED'
    elif result['warnings']:
        result['recommendation'] = 'PROCEED WITH CAUTION'

    return result
```

### 4. Integration with Council Voting

```python
# Modify council vote to optionally call uktena

async def council_vote(question: str, context: str = None) -> CouncilVote:
    """Enhanced council vote with optional Uktena check."""

    # Detect if this is an AI research proposal
    is_research = any(kw in question.lower() for kw in [
        'arxiv', 'paper', 'research', 'technique', 'algorithm', 'architecture'
    ])

    uktena_report = None
    if is_research:
        # Call Uktena tool - single function, ~50ms
        uktena_report = uktena_check_interaction(question)

        # Add to context for specialists
        if uktena_report['conflicts']:
            context = f"""
UKTENA INTERACTION CHECK:
- Conflicts: {uktena_report['conflicts']}
- Synergies: {uktena_report['synergies']}
- Recommendation: {uktena_report['recommendation']}

{context or ''}
"""

    # Proceed with normal Council vote
    vote = await _run_specialist_votes(question, context)

    # Add Uktena concern if conflicts found
    if uktena_report and uktena_report['conflicts']:
        vote.concerns.append(f"Uktena: [INTERACTION CONCERN] {len(uktena_report['conflicts'])} conflicts")

    return vote
```

## What We DON'T Do (Risk Avoidance)

| Full Duplo Feature | MVP Decision | Reason |
|--------------------|--------------|--------|
| Tool Registry system | Skip | Adds complexity, attack surface |
| Context Profiles YAML | Skip | Specialists work fine as-is |
| Duplo Composer | Skip | No composition needed yet |
| Dynamic tool loading | Skip | Hardcode single function |
| Tool marketplace | Skip | Future phase if MVP succeeds |

## Success Metrics

After 2 weeks of MVP:

1. **Performance**: Measure Council vote latency with/without Uktena
   - Target: <100ms overhead per research vote

2. **Accuracy**: Track Uktena predictions vs actual integration outcomes
   - Target: 70%+ correct conflict/synergy predictions

3. **Usage**: How often does Uktena flag real concerns?
   - Target: At least 1 useful catch per week

4. **Security**: Any attempted exploits or unexpected behavior?
   - Target: Zero incidents

## Graduation Criteria

If MVP succeeds after 30 days, consider Phase 2:

- Add 2-3 more tools (performance profiler, dependency checker)
- Implement lightweight Tool Registry
- Begin Context Profile extraction

If MVP fails or underperforms:

- Remove the single function
- Delete the table
- Total rollback: 30 minutes

## Timeline

| Day | Task |
|-----|------|
| 1 | Create ai_technique_inventory table |
| 2 | Populate with 20 current techniques |
| 3 | Implement uktena_check_interaction() |
| 4 | Integrate with Council voting |
| 5 | Test with recent research papers |

## Cost/Benefit Summary

```
COST:
- 5 days Jr time
- 1 new table (read-only)
- 1 new function (~100 lines)
- ~50ms latency on research votes

BENEFIT:
- Technique interaction checking
- Proves Duplo pattern works
- Foundation for future tools
- Addresses TPM's drug interaction concern
- Minimal risk to existing system
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Small steps on solid ground. The Duplo way."*
