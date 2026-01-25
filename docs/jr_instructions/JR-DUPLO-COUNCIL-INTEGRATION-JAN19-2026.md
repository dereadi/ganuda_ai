# JR Instruction: Duplo MVP - Council Integration

## Metadata
```yaml
task_id: duplo_council_integration
priority: 2
assigned_to: it_triad_jr
target: redfin (specialist_council.py)
depends_on: uktena_check_interaction() function (DONE - tested)
estimated_effort: small (1 day)
```

## Context

Uktena Pharmacist Tool is now operational:
- `ai_technique_inventory` table: 18 techniques
- `uktena_check_interaction()` function: All 3 tests pass

This task integrates Uktena with Council voting so that research paper proposals automatically get technique interaction analysis.

## Implementation

### File to Edit: `/ganuda/lib/specialist_council.py`

#### Step 1: Add Research Detection Helper

Find the existing imports section and add this helper function NEAR the `uktena_check_interaction()` function:

```python
def _is_research_proposal(question: str) -> bool:
    """Detect if question is about AI research/techniques."""
    research_keywords = [
        'arxiv', 'paper', 'research', 'technique', 'algorithm',
        'architecture', 'model', 'framework', 'approach', 'method',
        'integrate', 'implement', 'adopt', 'add'
    ]
    return any(kw in question.lower() for kw in research_keywords)
```

#### Step 2: Modify Council Vote Function

Find the main council vote function (likely `council_vote` or `run_council_vote` or similar).

Add Uktena check BEFORE the specialist voting loop:

```python
# Add near the beginning of the vote function, after initial setup:

uktena_report = None

# Run Uktena check for research proposals
if _is_research_proposal(question):
    try:
        uktena_report = uktena_check_interaction(question)

        # Prepend Uktena analysis to context for specialists
        uktena_context = f"""
=== UKTENA PHARMACIST ANALYSIS ===
Recommendation: {uktena_report['recommendation']}
Conflicts: {len(uktena_report['conflicts'])}
Synergies: {len(uktena_report['synergies'])}
"""
        if uktena_report['conflicts']:
            uktena_context += "\nConflicts:\n"
            for c in uktena_report['conflicts']:
                uktena_context += f"  - {c.get('technique', 'unknown')}: {c.get('reason', str(c))[:100]}\n"

        if uktena_report['synergies']:
            uktena_context += "\nSynergies:\n"
            for s in uktena_report['synergies']:
                uktena_context += f"  - {s.get('technique', 'unknown')}: {s.get('reason', str(s))[:100]}\n"

        uktena_context += "=================================\n\n"

        # Prepend to existing context
        context = uktena_context + (context or '')
    except Exception as e:
        # Don't fail vote if Uktena fails - just log warning
        print(f"[WARN] Uktena check failed: {e}")
```

#### Step 3: Add Uktena Concern to Vote Result

Find where concerns are collected and the vote result is assembled. Add:

```python
# After specialist voting is complete, before returning result:

if uktena_report and uktena_report['conflicts']:
    # Add Uktena concern to the vote
    concerns.append(
        f"Uktena: [INTERACTION CONCERN] {len(uktena_report['conflicts'])} technique conflicts detected"
    )

# Include Uktena report in response metadata
result['uktena_analysis'] = uktena_report
```

## Testing

After modifying the function, test via LLM Gateway:

```bash
# Test 1: Research proposal with known conflicts
curl -s -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Should we integrate branch-merge reasoning from this arXiv paper?", "context": "Test paper proposes multiple forward passes"}' \
  | python3 -m json.tool | grep -A5 "uktena"

# Expected: uktena_analysis with conflicts about vLLM

# Test 2: Non-research question (should NOT trigger Uktena)
curl -s -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "What is the best color for our logo?", "context": "Marketing question"}' \
  | python3 -m json.tool | grep "uktena"

# Expected: No uktena_analysis or uktena_analysis: null
```

## Acceptance Criteria

- [ ] `_is_research_proposal()` helper function exists
- [ ] Council votes on research include Uktena context
- [ ] Uktena conflicts appear in vote concerns
- [ ] `uktena_analysis` field appears in vote response
- [ ] Non-research questions do NOT trigger Uktena
- [ ] Vote latency overhead < 100ms for research questions

## Rollback

If integration causes issues:
1. Remove the `if _is_research_proposal` block
2. Remove `_is_research_proposal` helper
3. Restart llm-gateway: `sudo systemctl restart llm-gateway`

Uktena function remains available for manual use.

---

*Cherokee AI Federation - For the Seven Generations*
*"The Council now sees what Uktena sees."*
