# JR Instruction: Context Enforcement Layer

**JR ID:** JR-CONTEXT-ENFORCEMENT-LAYER-JAN28-2026
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Council Vote:** 3f55bdf2de9bd97a (79.2% confidence)
**Depends On:** Research Task #404 findings

---

## Background

Based on the AI Architecture Entropy thesis and Council consensus:
- Architectural failures are CONTEXT failures, not judgment failures
- AI excels at pattern matching at scale
- Humans excel at judgment under uncertainty
- We have built context tools but need to USE them consistently

---

## Objective

Implement a Context Enforcement Layer that ensures Jr workers automatically query relevant context before executing tasks.

---

## Design

### 1. Pre-Execution Context Query

Before executing any task, Jr workers should:
1. Query thermal memory for related patterns/memories
2. Check KB articles for relevant learnings
3. Search CMDB for infrastructure context
4. Look for pheromone trails from similar tasks

### 2. Context Prompt Injection

Add relevant context to the task prompt automatically:
```python
def enrich_task_with_context(task: Dict) -> Dict:
    """
    Automatically enrich task with relevant context from:
    - Thermal memory (related patterns)
    - KB articles (documented learnings)
    - CMDB (infrastructure context)
    - Pheromone trails (breadcrumbs)
    """
    context_additions = []

    # Query thermal memory
    related_memories = query_thermal_memory(
        keywords=extract_keywords(task['title']),
        limit=3,
        min_temperature=0.5
    )
    if related_memories:
        context_additions.append({
            'source': 'thermal_memory',
            'content': summarize_memories(related_memories)
        })

    # Query KB articles
    kb_articles = search_kb_articles(
        query=task['title'],
        limit=2
    )
    if kb_articles:
        context_additions.append({
            'source': 'kb_articles',
            'content': summarize_kb(kb_articles)
        })

    # Check for related pheromone trails
    trails = find_related_trails(
        task_type=task.get('type'),
        keywords=extract_keywords(task['description'])
    )
    if trails:
        context_additions.append({
            'source': 'pheromone_trails',
            'content': summarize_trails(trails)
        })

    task['enriched_context'] = context_additions
    return task
```

### 3. Entropy Detection Hook

Add a post-execution hook that detects potential entropy:
```python
def detect_entropy_patterns(task_result: Dict) -> List[str]:
    """
    Analyze task output for patterns that indicate entropy:
    - Duplicate code added
    - Missing error handling patterns
    - Inconsistent naming conventions
    - Unused imports added
    - Cache patterns that may break
    """
    warnings = []

    if task_result.get('files_modified'):
        for file_path in task_result['files_modified']:
            # Check for duplicate patterns
            duplicates = find_duplicate_patterns(file_path)
            if duplicates:
                warnings.append(f"ENTROPY: Duplicate pattern in {file_path}")

            # Check for missing KB-documented patterns
            missing = check_kb_patterns(file_path)
            if missing:
                warnings.append(f"ENTROPY: Missing pattern from KB: {missing}")

    return warnings
```

---

## Files to Create/Modify

| File | Description |
|------|-------------|
| `/ganuda/lib/context_enforcer.py` | Context enforcement layer |
| `/ganuda/jr_executor/task_executor.py` | Add pre-execution context query |
| `/ganuda/lib/entropy_detector.py` | Post-execution entropy detection |

---

## Integration Points

1. **jr_queue_worker.py** - Call `enrich_task_with_context()` before execution
2. **task_executor.py** - Include enriched context in LLM prompts
3. **Post-execution** - Run entropy detection and log warnings

---

## Verification

```bash
# Test context enrichment
python3 -c "
from lib.context_enforcer import enrich_task_with_context
task = {'title': 'Add caching to API endpoint', 'description': 'Implement Redis cache'}
enriched = enrich_task_with_context(task)
print(f'Context sources: {len(enriched.get(\"enriched_context\", []))}')
"

# Test entropy detection
python3 -c "
from lib.entropy_detector import detect_entropy_patterns
result = {'files_modified': ['/ganuda/lib/test.py']}
warnings = detect_entropy_patterns(result)
print(f'Entropy warnings: {len(warnings)}')
"
```

---

## Success Criteria

1. Jr workers automatically query context before execution
2. Related thermal memories surface in task prompts
3. KB articles are referenced when relevant
4. Entropy patterns are detected and logged
5. Context usage is tracked in MAGRPO for learning

---

FOR SEVEN GENERATIONS
