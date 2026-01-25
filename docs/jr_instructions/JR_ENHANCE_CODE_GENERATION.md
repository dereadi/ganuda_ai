# Jr Instruction: Enhance Executor Code Generation

**Priority**: P1 (Meta-improvement - improves all future Jr work)
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Gecko Jr (Technical Integration)
**Date**: December 23, 2025
**Council Wisdom**: "Teach a Jr to code, they complete one task. Teach them to code well, they serve Seven Generations."

---

## Mission

Enhance the Jr Task Executor to generate **actual working code** rather than thoughts about code. This meta-improvement will make all future Jr coding tasks more reliable.

---

## Current Problem

When given a coding task, the Jr executor currently:
```
❌ Outputs: "Okay, I need to understand the requirements... The function might look like..."
❌ Generates: Markdown with incomplete code snippets
❌ Creates: Implementation plans instead of implementations
```

What we need:
```
✅ Outputs: Complete, working Python/SQL/Bash code
✅ Generates: Files that can be directly applied
✅ Creates: Actual implementations, not plans
```

---

## Solution: Multi-Pronged Approach

### 1. New Task Type: `code`

Add a dedicated `code` task type that:
- Outputs ONLY executable code
- No markdown, no explanations, no thinking
- Includes proper imports and error handling
- Follows our existing code patterns

### 2. Few-Shot Examples

Include working examples in the prompt so the LLM understands the expected format.

### 3. RAG from Codebase

Retrieve relevant existing code to ground the generation in our actual patterns.

### 4. FARA-Style Learning

Track corrections and inject them into future prompts.

---

## Implementation

### Part 1: Add `code` Task Type to Executor

**File**: `/ganuda/jr_executor/jr_task_executor.py`

Add after line ~50 (with other task type handlers):

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
        elif task_type == 'content':
            return self._execute_content_task(task)
        elif task_type == 'code':  # NEW
            return self._execute_code_task(task)
        else:
            return False, f"Unknown task type: {task_type}"
    except Exception as e:
        return False, f"Execution error: {str(e)}"
```

### Part 2: Implement `_execute_code_task()` Method

Add this new method to the JrTaskExecutor class:

```python
def _execute_code_task(self, task: dict) -> Tuple[bool, str]:
    """
    Execute code generation task - outputs ONLY executable code.

    Unlike 'implementation' (creates plans) or 'content' (creates docs),
    'code' tasks output pure code files ready to be applied.
    """
    content = task['task_content']
    task_id = task['task_id']

    # Extract target file and language from task content
    output_path = self._extract_output_path(content)
    language = self._detect_language(content)

    # Get relevant existing code via RAG
    rag_context = self._get_code_rag_context(content, language)

    # Get FARA corrections for this type of code
    fara_rules = self._get_fara_rules(language)

    # Few-shot examples based on language
    few_shot = self._get_few_shot_examples(language)

    prompt = f"""You are a code generator for Cherokee AI Federation.

OUTPUT RULES - FOLLOW EXACTLY:
1. Output ONLY executable {language} code
2. NO markdown, NO backticks, NO explanations
3. NO "here's the code" or "this function does..."
4. Start directly with imports or code
5. Include ALL necessary imports
6. Include proper error handling
7. Follow the existing code patterns shown below

TASK:
{content}

EXISTING CODE PATTERNS (follow this style):
{rag_context}

FEW-SHOT EXAMPLE OF CORRECT OUTPUT:
{few_shot}

CORRECTIONS FROM PAST MISTAKES:
{fara_rules}

Generate the complete {language} code now. Start with the first line of code:"""

    result = self._call_llm(prompt, max_tokens=4000)

    if not result:
        return False, "LLM returned empty response"

    # Clean the output - remove any markdown artifacts
    clean_code = self._clean_code_output(result, language)

    # Validate the code syntax
    is_valid, validation_msg = self._validate_code_syntax(clean_code, language)
    if not is_valid:
        # Log to FARA for learning
        self._record_fara_mistake(task_id, "syntax_error", validation_msg)
        return False, f"Generated code has syntax errors: {validation_msg}"

    # Save to output path
    if output_path and self._is_safe_write_path(output_path):
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(clean_code)
            return True, f"Code generated and saved to {output_path}"
        except Exception as e:
            fallback = f"/ganuda/docs/reports/{task_id}_code.{self._get_extension(language)}"
            with open(fallback, 'w') as f:
                f.write(clean_code)
            return True, f"Code saved to fallback: {fallback}"
    else:
        # Save to default location
        default_path = f"/ganuda/docs/reports/{task_id}_code.{self._get_extension(language)}"
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        with open(default_path, 'w') as f:
            f.write(clean_code)
        return True, f"Code generated and saved to {default_path}"


def _detect_language(self, content: str) -> str:
    """Detect programming language from task content."""
    content_lower = content.lower()
    if 'python' in content_lower or '.py' in content_lower or 'def ' in content_lower:
        return 'python'
    elif 'sql' in content_lower or 'select ' in content_lower or 'insert ' in content_lower:
        return 'sql'
    elif 'bash' in content_lower or '.sh' in content_lower or '#!/' in content_lower:
        return 'bash'
    elif 'javascript' in content_lower or '.js' in content_lower or 'function ' in content_lower:
        return 'javascript'
    else:
        return 'python'  # Default


def _get_extension(self, language: str) -> str:
    """Get file extension for language."""
    extensions = {
        'python': 'py',
        'sql': 'sql',
        'bash': 'sh',
        'javascript': 'js'
    }
    return extensions.get(language, 'txt')


def _get_code_rag_context(self, content: str, language: str, limit: int = 3) -> str:
    """
    Retrieve relevant existing code from our codebase via RAG.
    Uses A-MEM embeddings to find similar code patterns.
    """
    try:
        # Extract keywords from task
        keywords = self._extract_keywords(content)

        # Search thermal memory for code-related entries
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            # Look for code patterns in thermal memory
            cur.execute("""
                SELECT LEFT(original_content, 1500)
                FROM thermal_memory_archive
                WHERE original_content ILIKE %s
                   OR original_content ILIKE %s
                ORDER BY temperature_score DESC
                LIMIT %s
            """, (f'%def %{keywords[0] if keywords else ""}%',
                  f'%{language}%function%',
                  limit))

            rows = cur.fetchall()
            if rows:
                return "\n---\n".join([row[0] for row in rows])
        conn.close()
    except Exception as e:
        print(f"[{self.agent_id}] RAG error: {e}")

    # Fallback: read actual code files
    return self._read_example_code(language)


def _read_example_code(self, language: str) -> str:
    """Read example code from our actual codebase."""
    examples = {
        'python': '/ganuda/services/llm_gateway/gateway.py',
        'sql': '/ganuda/sql/thermal_memory.sql',
        'bash': '/ganuda/scripts/deploy_systemd.sh'
    }

    filepath = examples.get(language)
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                # Read first 2000 chars as example
                return f"# Example from {filepath}:\n" + f.read(2000)
        except:
            pass
    return "# No examples available"


def _get_few_shot_examples(self, language: str) -> str:
    """Get few-shot examples for the language."""

    if language == 'python':
        return '''# EXAMPLE: Adding a FastAPI endpoint
@app.get("/v1/example/{item_id}")
async def get_example(item_id: str, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Get example item by ID."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM examples WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Not found")
            return {"id": row[0], "data": row[1]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")'''

    elif language == 'sql':
        return '''-- EXAMPLE: Creating a table with proper indexes
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);
CREATE INDEX IF NOT EXISTS idx_example_created ON example_table(created_at DESC);'''

    elif language == 'bash':
        return '''#!/bin/bash
# EXAMPLE: Service deployment script
set -e

echo "[1/3] Stopping service..."
sudo systemctl stop example-service || true

echo "[2/3] Deploying new version..."
cp /path/to/new/version /path/to/service/

echo "[3/3] Starting service..."
sudo systemctl start example-service
sudo systemctl status example-service --no-pager

echo "Deployment complete."'''

    return "# No examples for this language"


def _get_fara_rules(self, language: str) -> str:
    """Get FARA correction rules for this language."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rule_text
                FROM fara_rules
                WHERE language = %s OR language = 'all'
                ORDER BY created_at DESC
                LIMIT 5
            """, (language,))
            rows = cur.fetchall()
            if rows:
                return "\n".join([f"- {row[0]}" for row in rows])
        conn.close()
    except:
        pass

    # Default rules
    return """- Always include proper imports at the top
- Use try/except for database operations
- Include docstrings for functions
- Follow existing naming conventions"""


def _clean_code_output(self, raw_output: str, language: str) -> str:
    """Clean LLM output to extract pure code."""
    lines = raw_output.split('\n')
    clean_lines = []
    in_code = False

    for line in lines:
        # Skip markdown code block markers
        if line.strip().startswith('```'):
            in_code = not in_code
            continue

        # Skip common LLM preambles
        skip_phrases = [
            "here's the code",
            "here is the code",
            "the code is",
            "this function",
            "let me",
            "i'll create",
            "okay,",
            "sure,",
        ]
        if any(line.lower().strip().startswith(phrase) for phrase in skip_phrases):
            continue

        clean_lines.append(line)

    code = '\n'.join(clean_lines).strip()

    # Ensure proper shebang for bash
    if language == 'bash' and not code.startswith('#!'):
        code = '#!/bin/bash\n' + code

    return code


def _validate_code_syntax(self, code: str, language: str) -> Tuple[bool, str]:
    """Validate code syntax before saving."""
    if language == 'python':
        try:
            compile(code, '<string>', 'exec')
            return True, "Valid Python syntax"
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    elif language == 'sql':
        # Basic SQL validation - check for common issues
        if code.count('(') != code.count(')'):
            return False, "Unbalanced parentheses"
        return True, "SQL looks valid"

    elif language == 'bash':
        # Check for basic bash issues
        if 'if ' in code and 'fi' not in code:
            return False, "Missing 'fi' for 'if' statement"
        return True, "Bash looks valid"

    return True, "No validation for this language"


def _record_fara_mistake(self, task_id: str, error_type: str, details: str):
    """Record mistake to FARA for future learning."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fara_rules (rule_text, language, source_task, created_at)
                VALUES (%s, 'all', %s, NOW())
                ON CONFLICT DO NOTHING
            """, (f"Avoid {error_type}: {details}", task_id))
            conn.commit()
        conn.close()
    except:
        pass


def _extract_keywords(self, content: str) -> list:
    """Extract keywords from content for RAG search."""
    import re
    # Find function names, class names, etc.
    words = re.findall(r'\b[a-z_][a-z0-9_]{3,}\b', content.lower())
    # Filter common words
    stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'will'}
    return [w for w in words if w not in stop_words][:5]
```

### Part 3: Create FARA Rules Table (if not exists)

```sql
-- Run on bluefin
CREATE TABLE IF NOT EXISTS fara_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_text TEXT NOT NULL,
    language VARCHAR(32) DEFAULT 'all',
    source_task VARCHAR(128),
    times_applied INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(rule_text)
);

CREATE INDEX IF NOT EXISTS idx_fara_language ON fara_rules(language);

-- Seed with initial rules
INSERT INTO fara_rules (rule_text, language) VALUES
('Always start Python files with necessary imports', 'python'),
('Use try/except around database operations', 'python'),
('Include type hints in function signatures', 'python'),
('Use parameterized queries to prevent SQL injection', 'sql'),
('Always include IF NOT EXISTS for CREATE TABLE', 'sql'),
('Start bash scripts with set -e for error handling', 'bash'),
('Quote variables in bash to handle spaces', 'bash'),
('Never output markdown backticks in code tasks', 'all'),
('Never start with explanatory text like "Here is the code"', 'all')
ON CONFLICT DO NOTHING;
```

### Part 4: Update Supported Task Types

Update the startup message:

```python
print(f"[{self.agent_id}] Supported task types: research, implementation, review, content, code")
```

---

## Testing

### Test 1: Simple Python Code Generation

```sql
INSERT INTO jr_task_announcements (task_id, task_type, task_content, priority, status, assigned_to)
VALUES (
    'task-test-code-001',
    'code',
    'Create a Python function called calculate_fse_decay that takes initial_strength (float) and days_elapsed (float) and returns the decayed strength using formula: strength = initial * exp(-0.01 * days). Save to /ganuda/lib/fse_utils.py',
    1,
    'assigned',
    'jr-redfin-gecko'
);
```

### Test 2: SQL Code Generation

```sql
INSERT INTO jr_task_announcements (task_id, task_type, task_content, priority, status, assigned_to)
VALUES (
    'task-test-code-002',
    'code',
    'Create SQL to add a new table called code_generation_log with columns: id (serial primary key), task_id (varchar 128), language (varchar 32), success (boolean), error_message (text), created_at (timestamp). Include appropriate indexes.',
    1,
    'assigned',
    'jr-redfin-gecko'
);
```

### Test 3: Verify No Markdown

```bash
# Check output file has no markdown
cat /ganuda/docs/reports/task-test-code-001_code.py | head -5
# Should start with: import or def, NOT ```python
```

---

## Validation Checklist

- [ ] `code` task type added to execute_task()
- [ ] _execute_code_task() method implemented
- [ ] _detect_language() helper working
- [ ] _get_code_rag_context() retrieving examples
- [ ] _get_few_shot_examples() returning good examples
- [ ] _get_fara_rules() returning correction rules
- [ ] _clean_code_output() removing markdown
- [ ] _validate_code_syntax() catching errors
- [ ] _record_fara_mistake() logging for learning
- [ ] fara_rules table created with seed data
- [ ] Test code tasks produce clean output
- [ ] Executor restart successful

---

## Expected Improvement

| Before | After |
|--------|-------|
| "Okay, I need to think about..." | `import os` |
| ```python (markdown) | Pure Python code |
| Incomplete snippets | Full working files |
| No error handling | try/except included |
| Random style | Matches our codebase |
| Same mistakes repeated | FARA prevents repeats |

---

## Seven Generations Consideration

Teaching Jrs to code well is a force multiplier:
- Every future Jr task benefits
- Less TPM intervention needed
- More reliable autonomous operation
- Knowledge compounds through FARA learning

"Give a Jr a fish, they complete one task. Teach a Jr to fish, they serve Seven Generations."

For Seven Generations.

---

*Meta-improvement for Cherokee AI Federation*
*Phase 3: Hardening & Packaging*
*Created: December 23, 2025*
