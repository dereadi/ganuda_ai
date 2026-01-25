# Jr Instructions: Implement teaching_stories.py Library

**Date**: 2025-12-27
**Priority**: High - Follows Council Priority #1 (Schema Complete)
**Assigned To**: Jr on redfin or any node with Python
**Depends On**: Schema deployed (DONE - see KB-0014)

---

## Objective

Create the Python library for Teaching Stories CRUD operations. The schema is already deployed on bluefin. This library enables Jr agents to store and retrieve failure reflections.

## Output File

`/ganuda/lib/teaching_stories.py` (Linux nodes)
or `/Users/Shared/ganuda/lib/teaching_stories.py` (macOS)

---

## Database Configuration

```python
DB_CONFIG = {
    "host": "192.168.132.222",  # bluefin
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2",
}
```

---

## Required Functions

### 1. generate_story_id()
```python
def generate_story_id() -> str:
    """Generate unique story ID: ts_YYYYMMDD_HHMMSS_hash6"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"ts_{timestamp}_{hash_suffix}"
```

### 2. create_teaching_story()
Store a new Teaching Story after task failure (or notable success).

**Parameters**:
- agents: List[str] - Which Jr agents were involved
- nodes: List[str] - Which cluster nodes
- task_type: str - Category (e.g., "browser_automation", "database_migration")
- task_description: str - What was being attempted
- initial_approach: str - How it was approached
- success: bool - Did it work
- what_happened: str - Outcome description
- responsibility: str - Commitment statement ("Always...")
- applies_to: List[str] - Related task types for cross-retrieval
- Optional: why_attempted, error_messages, impact, what_went_wrong, better_approach, human_involved

**Returns**: story_id of created story

### 3. retrieve_relevant_stories() - PERFORMANCE CRITICAL

Retrieve Teaching Stories before attempting a task.

**Query Strategy** (in order of preference):
1. FIRST: Exact match on task_type (btree index - fast)
2. SECOND: Array contains on applies_to (GIN index - fast)
3. LAST RESORT: Full-text search on search_vector (expensive - use sparingly)

```python
def retrieve_relevant_stories(
    task_type: str,
    task_description: str,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant Teaching Stories.

    IMPORTANT: Use indexed lookups first, full-text only as fallback.
    Increment retrieval_count for effectiveness tracking.
    """
    # Query 1: Exact task_type match (FAST)
    # Query 2: applies_to array contains (FAST)
    # Query 3: Full-text only if above return < limit (SLOW)
```

### 4. mark_retrieval_success()
Called after a task succeeds when stories were retrieved.

```python
def mark_retrieval_success(story_ids: List[str]) -> None:
    """Increment success_after_retrieval for effectiveness tracking."""
```

### 5. format_stories_for_prompt()
Format retrieved stories into prompt-friendly markdown.

```python
def format_stories_for_prompt(stories: List[Dict[str, Any]]) -> str:
    """
    Format stories for LLM prompt injection.

    Output format:
    ## Relevant Teaching Stories

    ### Story 1: {task_type}
    **What was attempted**: {initial_approach}
    **Outcome**: SUCCESS/FAILURE - {what_happened}
    **What went wrong**: {what_went_wrong}
    **Better approach**: {better_approach}
    **Responsibility**: {responsibility}
    """
```

---

## Testing

### Test 1: Retrieve existing stories
```python
from teaching_stories import retrieve_relevant_stories, format_stories_for_prompt

stories = retrieve_relevant_stories(
    task_type="browser_automation",
    task_description="Automate job applications",
)
print(format_stories_for_prompt(stories))
# Should return 2 seed stories about Indeed/ZipRecruiter
```

### Test 2: Create new story
```python
from teaching_stories import create_teaching_story

story_id = create_teaching_story(
    agents=["test-jr"],
    nodes=["redfin"],
    task_type="api_integration",
    task_description="Connect to external API",
    initial_approach="Used requests without timeout",
    success=False,
    what_happened="Request hung indefinitely",
    what_went_wrong="No timeout specified, remote server unresponsive",
    better_approach="Always set timeout parameter: requests.get(url, timeout=30)",
    responsibility="Always specify timeouts on external API calls",
    applies_to=["api_integration", "http_requests", "external_services"],
)
print(f"Created: {story_id}")
```

### Test 3: Mark success
```python
from teaching_stories import mark_retrieval_success

# After a task succeeds that used retrieved stories
mark_retrieval_success(["ts_20251227_seed_001", "ts_20251227_seed_002"])
```

---

## Success Criteria

- [ ] Library imports without errors
- [ ] retrieve_relevant_stories finds the 2 seed stories
- [ ] create_teaching_story inserts and returns valid story_id
- [ ] mark_retrieval_success increments counters
- [ ] format_stories_for_prompt produces readable markdown
- [ ] No full-text search when indexed lookup returns results

---

## Dependencies

```bash
pip install psycopg2-binary
```

---

*For Seven Generations*
