# JR Instruction: Duplo MVP - Uktena Function Implementation

## Metadata
```yaml
task_id: duplo_mvp_uktena_function
priority: 0
assigned_to: it_triad_jr
target: redfin (specialist_council.py)
depends_on: ai_technique_inventory table (DONE - 18 techniques loaded)
estimated_effort: small (1 day)
```

## Context

Jr #148 was marked complete but only Days 1-2 were done:
- Day 1: Create ai_technique_inventory table
- Day 2: Populate with 18 techniques

**This task completes Days 3-5**:
- Add `uktena_check_interaction()` function to specialist_council.py
- Test the function

## Implementation

### File to Edit: `/ganuda/lib/specialist_council.py`

Add the following function AFTER the existing imports and BEFORE the specialist class definitions:

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
    import psycopg2

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
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
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

### Testing

After adding the function, run these tests:

```bash
/home/dereadi/cherokee_venv/bin/python3 << 'EOF'
import sys
sys.path.insert(0, '/ganuda/lib')
from specialist_council import uktena_check_interaction

# Test 1: Multi-pass technique (should conflict with vLLM)
result = uktena_check_interaction("branch-and-merge reasoning with multiple forward passes")
print("Test 1 - Multi-pass technique:")
print(f"  Recommendation: {result['recommendation']}")
print(f"  Conflicts: {len(result['conflicts'])}")
assert 'CONFLICT' in result['recommendation'] or 'REVIEW' in result['recommendation'], "Should detect vLLM conflict"
print("  PASS")

# Test 2: Memory technique (should find synergies)
result = uktena_check_interaction("hierarchical temporal memory consolidation")
print("\nTest 2 - Memory technique:")
print(f"  Recommendation: {result['recommendation']}")
print(f"  Synergies: {len(result['synergies'])}")
assert result['synergies'], "Should find memory synergies"
print("  PASS")

# Test 3: Neutral technique (no interactions)
result = uktena_check_interaction("simple text classification")
print("\nTest 3 - Neutral technique:")
print(f"  Recommendation: {result['recommendation']}")
assert 'PROCEED' in result['recommendation'], "Should proceed with no issues"
print("  PASS")

print("\n=== ALL TESTS PASSED ===")
EOF
```

## Acceptance Criteria

- [ ] Function `uktena_check_interaction()` exists in `/ganuda/lib/specialist_council.py`
- [ ] Function returns valid dict with synergies, conflicts, warnings, recommendation
- [ ] Test 1 passes: Multi-pass techniques detected as conflicting with vLLM
- [ ] Test 2 passes: Memory techniques find synergies
- [ ] Test 3 passes: Neutral techniques proceed without issues

## Notes

Do NOT modify any other part of specialist_council.py. This is a single function addition only.

Council integration (calling Uktena during research votes) will be a separate task after this function is verified working.

---

*Cherokee AI Federation - For the Seven Generations*
*"Uktena guards the knowledge. The serpent sees all interactions."*
