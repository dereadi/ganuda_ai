# Jr Instruction: Enhance Task Executor with Content Generation

**Created**: December 23, 2025  
**Priority**: P1 (Blocking whitepaper generation)  
**Assigned To**: Jr with Python capabilities  
**Target File**: /ganuda/jr_executor/jr_task_executor.py  

---

## Mission

Enhance the Jr Task Executor to support a new task type `content` that generates actual content files (whitepapers, documentation, reports) rather than just implementation plans.

---

## Current Limitation

The executor currently only creates implementation plans for all task types:

```python
def _execute_implementation_task(self, task: dict) -> Tuple[bool, str]:
    # Always creates plans, never actual content
    prompt = f"""...Provide the plan."""
    # Saves to {task_id}_impl_plan.md
```

---

## Required Changes

### 1. Add New Task Type Handler

Add support for `content` task type in the `execute_task` method:

```python
def execute_task(self, task: dict) -> Tuple[bool, str]:
    """Execute task based on type."""
    task_type = task.get('task_type', 'unknown')
    task_id = task['task_id']

    print(f"[{self.agent_id}] Executing {task_type} task: {task_id}")

    try:
        if task_type == 'research':
            return self._execute_research_task(task)
        elif task_type == 'implementation':
            return self._execute_implementation_task(task)
        elif task_type == 'review':
            return self._execute_review_task(task)
        elif task_type == 'content':  # NEW
            return self._execute_content_task(task)
        else:
            return False, f"Unknown task type: {task_type}"
    except Exception as e:
        return False, f"Execution error: {str(e)}"
```

### 2. Add Content Task Executor Method

Add this new method to the `JrTaskExecutor` class:

```python
def _execute_content_task(self, task: dict) -> Tuple[bool, str]:
    """Execute content generation task - creates actual documents."""
    content = task['task_content']
    task_id = task['task_id']
    
    # Extract output path from task content if specified
    output_path = self._extract_output_path(content)
    
    # Get thermal memory context
    thermal_context = self._query_thermal_memory(content, limit=5)
    
    # Check for referenced plan files
    plan_context = self._get_plan_context(content)
    
    prompt = f"""You are a technical writer for Cherokee AI Federation.

TASK: {content}

THERMAL MEMORY CONTEXT:
{thermal_context}

REFERENCED PLANS:
{plan_context}

INSTRUCTIONS:
1. Write the FULL content as requested (not a plan, the actual document)
2. Follow any template structure mentioned in the task
3. Include all sections with complete content
4. Target 2000-3000 words for whitepapers
5. Use professional tone with Cherokee AI Federation branding
6. Include "For Seven Generations" where appropriate

Write the complete document now:"""

    result = self._call_llm(prompt, max_tokens=4000)
    
    if not result:
        return False, "LLM returned empty response"
    
    # Save to specified output path or default location
    if output_path:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(result)
            
            return True, f"Content created and saved to {output_path}"
        except Exception as e:
            # Fallback to reports directory
            fallback_path = f"/ganuda/docs/reports/{task_id}_content.md"
            with open(fallback_path, 'w') as f:
                f.write(result)
            return True, f"Content saved to fallback: {fallback_path} (original path error: {e})"
    else:
        # Default save location
        default_path = f"/ganuda/docs/reports/{task_id}_content.md"
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        
        with open(default_path, 'w') as f:
            f.write(result)
        
        return True, f"Content created and saved to {default_path}"


def _extract_output_path(self, content: str) -> Optional[str]:
    """Extract output file path from task content."""
    import re
    
    # Look for "Save to /path/to/file.md" pattern
    patterns = [
        r'[Ss]ave to\s+(/[^\s]+\.md)',
        r'[Oo]utput:?\s+(/[^\s]+\.md)',
        r'[Ww]rite to\s+(/[^\s]+\.md)',
        r'(/ganuda/docs/whitepapers/[^\s]+\.md)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    return None


def _get_plan_context(self, content: str) -> str:
    """Read referenced plan files for context."""
    import re
    
    # Find referenced plan files
    pattern = r'(/ganuda/docs/[^\s]+\.md)'
    matches = re.findall(pattern, content)
    
    context_parts = []
    for path in matches[:3]:  # Limit to 3 files
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    # Read first 2000 chars of each plan
                    plan_content = f.read(2000)
                    context_parts.append(f"=== {path} ===\n{plan_content}\n")
        except Exception as e:
            context_parts.append(f"=== {path} === (error reading: {e})\n")
    
    return "\n".join(context_parts) if context_parts else "No plan files referenced."
```

### 3. Increase LLM Token Limit for Content Tasks

Modify the `_call_llm` method to support higher token limits:

```python
def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
    """Call LLM Gateway for processing."""
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nemotron",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,  # Now respects passed value
                "temperature": 0.7
            },
            timeout=120  # Increase timeout for longer content
        )
        # ... rest of method
```

---

## File to Modify

**Primary**: `/ganuda/jr_executor/jr_task_executor.py`

### Backup First
```bash
cp /ganuda/jr_executor/jr_task_executor.py /ganuda/jr_executor/jr_task_executor.py.backup_$(date +%Y%m%d_%H%M%S)
```

---

## Testing

After modification, test with:

```bash
# Insert test content task
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_task_announcements (task_id, task_type, task_content, priority, status, assigned_to)
VALUES ('task-test-content-001', 'content', 'Write a 500-word test document about Cherokee AI Federation. Save to /ganuda/docs/reports/test_content.md', 1, 'assigned', 'jr-redfin-gecko');"

# Watch executor log
tail -f /home/dereadi/logs/jr-redfin-gecko-executor.log

# Verify output
cat /ganuda/docs/reports/test_content.md
```

---

## Security Considerations

1. **Path Validation**: Only allow writes to approved directories:
   - `/ganuda/docs/whitepapers/`
   - `/ganuda/docs/reports/`
   - `/ganuda/docs/kb/`

2. **No Code Execution**: Content tasks should only write markdown/text files, never execute code

3. **Size Limits**: Cap output at reasonable size (e.g., 50KB per file)

---

## Validation Checklist

- [ ] Backup created of jr_task_executor.py
- [ ] New `content` task type added to execute_task()
- [ ] _execute_content_task() method implemented
- [ ] _extract_output_path() helper added
- [ ] _get_plan_context() helper added
- [ ] LLM timeout increased for long content
- [ ] Test task executes successfully
- [ ] Output file created at correct path
- [ ] Thermal memory updated with completion

---

## After Enhancement

Re-run whitepaper tasks with `content` type:

```sql
INSERT INTO jr_task_announcements (task_id, task_type, task_content, priority, required_capabilities)
VALUES
('task-content-wp-governance', 'content', 'Write the full Governance-First AI whitepaper (2000-3000 words). Use plan from /ganuda/docs/reports/task-wp-governance-001_impl_plan.md. Save to /ganuda/docs/whitepapers/WP_GOVERNANCE_FIRST_AI.md', 1, ARRAY['writing']);
```

---

For Seven Generations.
