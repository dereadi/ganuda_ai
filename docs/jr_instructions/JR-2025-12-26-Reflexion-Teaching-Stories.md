# Jr Instructions: Implement Reflexion (Teaching Stories) Pattern

**Date**: 2025-12-26
**Priority**: #1 - Council Unanimous Vote
**Assigned To**: Jr on any node
**Timeline**: 1 week

---

## Objective

Implement the Reflexion pattern for Jr agents, using the Cherokee-inspired "Teaching Stories" format. When Jr agents fail at tasks, they generate structured reflections that are stored in Thermal Memory and retrieved before similar future tasks.

## Background

**Research Paper**: Reflexion: Language Agents with Verbal Reinforcement Learning (NeurIPS 2023)
- Achieves 91% pass@1 on HumanEval through verbal reinforcement
- Agents store failure reflections in episodic memory
- Retrieved reflections prevent repeating mistakes

**Council Adaptation**: Spider reframed reflections as "Teaching Stories" - narrative structures that align with Cherokee oral tradition.

---

## Teaching Story Format

Each Teaching Story has 5 required fields:

```json
{
  "story_id": "ts_20251226_001",
  "timestamp": "2025-12-26T22:45:00Z",
  "story_type": "teaching_story",

  "who": {
    "agents": ["Jr-redfin-001"],
    "nodes": ["redfin", "bluefin"],
    "human_involved": false
  },

  "context": {
    "task_type": "database_migration",
    "task_description": "Migrate user table from old schema to new schema",
    "initial_approach": "Direct ALTER TABLE on production",
    "why_attempted": "Seemed like the fastest approach"
  },

  "outcome": {
    "success": false,
    "what_happened": "Table lock caused 30-second service interruption",
    "error_messages": ["Lock wait timeout exceeded"],
    "impact": "API returned 503 for 30 seconds"
  },

  "lesson": {
    "what_went_wrong": "Did not consider table lock implications on production",
    "better_approach": "Use pt-online-schema-change or create new table and swap",
    "responsibility": "Always test schema changes on staging first",
    "applies_to": ["database_migration", "schema_changes", "production_operations"]
  },

  "metadata": {
    "reviewed": false,
    "review_date": null,
    "deprecated": false,
    "retrieval_count": 0,
    "success_after_retrieval": 0
  }
}
```

---

## Implementation Steps

### Step 1: Create Database Schema

On **bluefin** (PostgreSQL), add the teaching_stories table:

```sql
-- Connect to triad_federation database
-- File: /ganuda/sql/teaching_stories_schema.sql

CREATE TABLE IF NOT EXISTS teaching_stories (
    id SERIAL PRIMARY KEY,
    story_id VARCHAR(50) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    story_type VARCHAR(50) DEFAULT 'teaching_story',

    -- Who was involved
    agents JSONB NOT NULL,
    nodes TEXT[] NOT NULL,
    human_involved BOOLEAN DEFAULT FALSE,

    -- Context of what was attempted
    task_type VARCHAR(100) NOT NULL,
    task_description TEXT NOT NULL,
    initial_approach TEXT NOT NULL,
    why_attempted TEXT,

    -- What happened
    success BOOLEAN NOT NULL,
    what_happened TEXT NOT NULL,
    error_messages TEXT[],
    impact TEXT,

    -- The lesson learned
    what_went_wrong TEXT,
    better_approach TEXT,
    responsibility TEXT NOT NULL,
    applies_to TEXT[] NOT NULL,

    -- Metadata for tracking effectiveness
    reviewed BOOLEAN DEFAULT FALSE,
    review_date TIMESTAMPTZ,
    deprecated BOOLEAN DEFAULT FALSE,
    retrieval_count INTEGER DEFAULT 0,
    success_after_retrieval INTEGER DEFAULT 0,

    -- Full-text search
    search_vector TSVECTOR,

    -- Encryption flag (for Crawdad's security requirement)
    encrypted BOOLEAN DEFAULT FALSE
);

-- Index for fast retrieval by task type
CREATE INDEX idx_teaching_stories_task_type ON teaching_stories(task_type);
CREATE INDEX idx_teaching_stories_applies_to ON teaching_stories USING GIN(applies_to);
CREATE INDEX idx_teaching_stories_search ON teaching_stories USING GIN(search_vector);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION update_teaching_story_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.task_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.task_description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.what_went_wrong, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.better_approach, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.responsibility, '')), 'A');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER teaching_story_search_update
    BEFORE INSERT OR UPDATE ON teaching_stories
    FOR EACH ROW EXECUTE FUNCTION update_teaching_story_search();
```

### Step 2: Create Python Library

File: `/Users/Shared/ganuda/lib/teaching_stories.py`

```python
#!/usr/bin/env python3
"""
Teaching Stories - Reflexion Pattern Implementation
Cherokee AI Federation

Implements verbal reinforcement learning through structured
narrative reflections stored in Thermal Memory.
"""

import json
import psycopg2
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib


# Database configuration
DB_CONFIG = {
    "host": "192.168.132.222",  # bluefin
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2",
}


def generate_story_id() -> str:
    """Generate unique story ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"ts_{timestamp}_{hash_suffix}"


def create_teaching_story(
    agents: List[str],
    nodes: List[str],
    task_type: str,
    task_description: str,
    initial_approach: str,
    success: bool,
    what_happened: str,
    responsibility: str,
    applies_to: List[str],
    why_attempted: Optional[str] = None,
    error_messages: Optional[List[str]] = None,
    impact: Optional[str] = None,
    what_went_wrong: Optional[str] = None,
    better_approach: Optional[str] = None,
    human_involved: bool = False,
) -> str:
    """
    Create and store a new Teaching Story.

    Returns the story_id of the created story.
    """
    story_id = generate_story_id()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO teaching_stories (
                story_id, agents, nodes, human_involved,
                task_type, task_description, initial_approach, why_attempted,
                success, what_happened, error_messages, impact,
                what_went_wrong, better_approach, responsibility, applies_to
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            story_id,
            json.dumps(agents),
            nodes,
            human_involved,
            task_type,
            task_description,
            initial_approach,
            why_attempted,
            success,
            what_happened,
            error_messages,
            impact,
            what_went_wrong,
            better_approach,
            responsibility,
            applies_to,
        ))

        conn.commit()
        return story_id

    finally:
        cur.close()
        conn.close()


def retrieve_relevant_stories(
    task_type: str,
    task_description: str,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant Teaching Stories before attempting a task.

    Uses full-text search and task_type matching.
    Increments retrieval_count for tracking effectiveness.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Search by task_type and full-text
        cur.execute("""
            SELECT
                story_id,
                task_type,
                task_description,
                initial_approach,
                success,
                what_happened,
                what_went_wrong,
                better_approach,
                responsibility,
                applies_to
            FROM teaching_stories
            WHERE
                deprecated = FALSE
                AND (
                    task_type = %s
                    OR %s = ANY(applies_to)
                    OR search_vector @@ plainto_tsquery('english', %s)
                )
            ORDER BY
                CASE WHEN task_type = %s THEN 0 ELSE 1 END,
                ts_rank(search_vector, plainto_tsquery('english', %s)) DESC,
                timestamp DESC
            LIMIT %s
        """, (task_type, task_type, task_description, task_type, task_description, limit))

        rows = cur.fetchall()
        stories = []

        for row in rows:
            story = {
                "story_id": row[0],
                "task_type": row[1],
                "task_description": row[2],
                "initial_approach": row[3],
                "success": row[4],
                "what_happened": row[5],
                "what_went_wrong": row[6],
                "better_approach": row[7],
                "responsibility": row[8],
                "applies_to": row[9],
            }
            stories.append(story)

            # Increment retrieval count
            cur.execute("""
                UPDATE teaching_stories
                SET retrieval_count = retrieval_count + 1
                WHERE story_id = %s
            """, (row[0],))

        conn.commit()
        return stories

    finally:
        cur.close()
        conn.close()


def mark_retrieval_success(story_ids: List[str]) -> None:
    """
    Mark that retrieved stories led to successful task completion.
    Called after a task succeeds when stories were retrieved.
    """
    if not story_ids:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        for story_id in story_ids:
            cur.execute("""
                UPDATE teaching_stories
                SET success_after_retrieval = success_after_retrieval + 1
                WHERE story_id = %s
            """, (story_id,))

        conn.commit()

    finally:
        cur.close()
        conn.close()


def format_stories_for_prompt(stories: List[Dict[str, Any]]) -> str:
    """
    Format retrieved stories into a prompt-friendly string.
    """
    if not stories:
        return "No relevant Teaching Stories found."

    output = "## Relevant Teaching Stories from Federation Memory\n\n"

    for i, story in enumerate(stories, 1):
        output += f"### Story {i}: {story['task_type']}\n"
        output += f"**What was attempted**: {story['initial_approach']}\n"

        if story['success']:
            output += f"**Outcome**: SUCCESS - {story['what_happened']}\n"
        else:
            output += f"**Outcome**: FAILURE - {story['what_happened']}\n"
            if story['what_went_wrong']:
                output += f"**What went wrong**: {story['what_went_wrong']}\n"
            if story['better_approach']:
                output += f"**Better approach**: {story['better_approach']}\n"

        output += f"**Responsibility**: {story['responsibility']}\n\n"

    return output


def generate_reflection_prompt(
    task_type: str,
    task_description: str,
    approach_taken: str,
    outcome: str,
    error_messages: Optional[List[str]] = None,
) -> str:
    """
    Generate a prompt for the LLM to create a Teaching Story reflection.
    """
    prompt = f"""You are helping create a Teaching Story for the Cherokee AI Federation's institutional memory.

A task was just attempted. Please generate a structured reflection.

## Task Information
- **Task Type**: {task_type}
- **Description**: {task_description}
- **Approach Taken**: {approach_taken}
- **Outcome**: {outcome}
"""

    if error_messages:
        prompt += f"- **Error Messages**: {', '.join(error_messages)}\n"

    prompt += """
## Generate a Teaching Story

Please provide:

1. **What went wrong** (or what went right if successful):
   - Be specific about the root cause
   - Don't just restate the error

2. **Better approach** (for failures) or **Key success factors** (for successes):
   - Actionable guidance for future attempts
   - Specific steps or checks to follow

3. **Responsibility** (what the agent/Federation should always do):
   - Frame as a positive commitment
   - Example: "Always test schema changes on staging first"

4. **Applies to** (list of task types this lesson applies to):
   - Include the current task type
   - Add related task types where this lesson is relevant

Format your response as JSON:
```json
{
  "what_went_wrong": "...",
  "better_approach": "...",
  "responsibility": "...",
  "applies_to": ["task_type_1", "task_type_2"]
}
```
"""
    return prompt
```

### Step 3: Integration with Jr Agent Loop

Modify Jr agent execution to include Reflexion:

```python
# Add to Jr agent task execution flow

from teaching_stories import (
    retrieve_relevant_stories,
    format_stories_for_prompt,
    create_teaching_story,
    mark_retrieval_success,
)

async def execute_task_with_reflexion(task_type: str, task_description: str):
    """
    Execute a task with Reflexion pattern.

    1. Retrieve relevant Teaching Stories before starting
    2. Include stories in the task prompt
    3. Execute the task
    4. If failure: generate and store new Teaching Story
    5. If success after retrieval: mark stories as helpful
    """

    # Step 1: Retrieve relevant stories
    stories = retrieve_relevant_stories(task_type, task_description)
    story_ids = [s['story_id'] for s in stories]

    # Step 2: Format for prompt
    stories_context = format_stories_for_prompt(stories)

    # Step 3: Build enhanced prompt
    enhanced_prompt = f"""
{stories_context}

---

## Current Task
**Type**: {task_type}
**Description**: {task_description}

Please complete this task, keeping the Teaching Stories above in mind.
If any story warns against a particular approach, avoid that approach.
"""

    # Step 4: Execute task (your existing execution logic)
    try:
        result = await execute_task(enhanced_prompt)
        success = True
        outcome = "Task completed successfully"

        # Mark retrieved stories as helpful
        if story_ids:
            mark_retrieval_success(story_ids)

    except Exception as e:
        success = False
        outcome = str(e)
        result = None

    # Step 5: Generate reflection for failures (or notable successes)
    if not success:
        # Generate Teaching Story
        reflection = await generate_reflection(
            task_type=task_type,
            task_description=task_description,
            approach_taken="[extracted from execution log]",
            outcome=outcome,
        )

        create_teaching_story(
            agents=["current_jr_agent"],
            nodes=["current_node"],
            task_type=task_type,
            task_description=task_description,
            initial_approach=reflection.get("approach", "Unknown"),
            success=False,
            what_happened=outcome,
            what_went_wrong=reflection.get("what_went_wrong"),
            better_approach=reflection.get("better_approach"),
            responsibility=reflection.get("responsibility", "Review approach before retrying"),
            applies_to=reflection.get("applies_to", [task_type]),
        )

    return result
```

---

## Testing

### Test 1: Schema Creation
```bash
# On bluefin (ALREADY DEPLOYED 2025-12-27)
PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production -f /ganuda/sql/teaching_stories_schema.sql
# Schema created with all indexes and triggers
```

### Test 2: Create Sample Story
```python
from teaching_stories import create_teaching_story

story_id = create_teaching_story(
    agents=["test-jr"],
    nodes=["tpm-macbook"],
    task_type="file_operation",
    task_description="Delete temporary files from /tmp",
    initial_approach="Used rm -rf /tmp/*",
    success=False,
    what_happened="Accidentally deleted socket files needed by running processes",
    what_went_wrong="Glob pattern too broad, didn't exclude active sockets",
    better_approach="Use find with -mtime to only delete old files, exclude .sock files",
    responsibility="Always use targeted deletion patterns, never rm -rf on system directories",
    applies_to=["file_operation", "cleanup", "system_maintenance"],
)
print(f"Created story: {story_id}")
```

### Test 3: Retrieve Stories
```python
from teaching_stories import retrieve_relevant_stories, format_stories_for_prompt

stories = retrieve_relevant_stories(
    task_type="file_operation",
    task_description="Clean up old log files",
)
print(format_stories_for_prompt(stories))
```

---

## Monitoring (Eagle Eye Requirements)

Add to Grafana dashboard:

```sql
-- Teaching Stories effectiveness metrics
SELECT
    COUNT(*) as total_stories,
    SUM(retrieval_count) as total_retrievals,
    SUM(success_after_retrieval) as successes_after_retrieval,
    ROUND(
        SUM(success_after_retrieval)::numeric /
        NULLIF(SUM(retrieval_count), 0) * 100,
        2
    ) as effectiveness_percentage
FROM teaching_stories
WHERE deprecated = FALSE;

-- Stories needing review (high retrieval, low success)
SELECT story_id, task_type, retrieval_count, success_after_retrieval
FROM teaching_stories
WHERE retrieval_count > 5
  AND success_after_retrieval < retrieval_count * 0.5
  AND reviewed = FALSE
ORDER BY retrieval_count DESC;
```

---

## Success Criteria

- [ ] Schema created on bluefin
- [ ] Python library working from any node
- [ ] Sample Teaching Stories created and retrievable
- [ ] Jr agent integration tested with deliberate failure
- [ ] Monitoring queries returning data
- [ ] At least 5 Teaching Stories generated from real Jr failures

---

*For Seven Generations*
