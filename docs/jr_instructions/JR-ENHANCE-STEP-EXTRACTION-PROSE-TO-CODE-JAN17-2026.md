# Jr Instruction: Enhance Step Extraction for Prose-to-Code

**Priority**: P0 - CRITICAL (blocks VetAssist)
**Assigned**: it_triad_jr
**Sacred Fire**: YES
**Created**: January 17, 2026
**Research Sources**: Devika AI, GPT-Engineer

---

## Problem Statement

The Jr executor's `_extract_steps_via_llm()` method doesn't reliably extract actionable steps from prose instructions. Tasks are marked "completed" but no files are created because:
1. LLM understanding doesn't return `files_to_create` or `files_to_modify`
2. No fallback parsing for prose descriptions
3. Missing structured output format enforcement

## Research Findings

### Devika AI Approach (github.com/stitionai/devika)
- Uses Jinja2 prompt templates with **strict output format**
- Planner agent outputs numbered checkbox items: `- [ ] Step X: description`
- Parses response line-by-line looking for step patterns
- Separates planning from code generation phases

### GPT-Engineer Approach (github.com/AntonOsika/gpt-engineer)
- Uses customizable pre-prompts to shape agent behavior
- Separates specification understanding from code generation
- Supports iterative improvement via follow-up prompts

---

## Solution Design

### Phase 1: Add Structured Planning Prompt

Create a planning prompt that forces structured output:

**File to Create**: `/ganuda/lib/jr_planning_prompt.py`

```python
"""
Jr Planning Prompt Template
Based on Devika AI architecture patterns
Cherokee AI Federation - For Seven Generations
"""

PLANNING_PROMPT = '''
You are a Cherokee AI Jr engineer. Analyze the following task instructions and create a structured execution plan.

## TASK INSTRUCTIONS:
{instructions}

## REQUIRED OUTPUT FORMAT (follow exactly):

```plan
PROJECT_NAME: [concise name, max 5 words]

FOCUS: [main objective in one sentence]

FILES_TO_CREATE:
- /path/to/file1.py: [brief description]
- /path/to/file2.tsx: [brief description]

FILES_TO_MODIFY:
- /path/to/existing.py: [what changes needed]

STEPS:
- [ ] Step 1: [specific action]
- [ ] Step 2: [specific action]
- [ ] Step 3: [specific action]

SUMMARY: [key considerations and dependencies]
```

## RULES:
1. Always extract file paths from the instructions
2. If CREATE FILE: or Path: is mentioned, add to FILES_TO_CREATE
3. If UPDATE or MODIFY is mentioned, add to FILES_TO_MODIFY
4. Each step should be a clear, specific action
5. Keep steps simple - don't overcomplicate
6. Output MUST be inside the ```plan code block
'''

CODE_GENERATION_PROMPT = '''
You are a Cherokee AI Jr engineer. Generate the complete code for the following file.

## FILE TO CREATE: {file_path}
## PURPOSE: {description}
## CONTEXT FROM INSTRUCTIONS:
{relevant_context}

## RULES:
1. Output ONLY the code, no explanations
2. Include all necessary imports
3. Follow existing project patterns
4. Add minimal comments only where logic is complex
5. The code must be complete and runnable

```{language}
'''


def get_planning_prompt(instructions: str) -> str:
    """Return the planning prompt with instructions filled in."""
    return PLANNING_PROMPT.format(instructions=instructions)


def get_code_generation_prompt(file_path: str, description: str, context: str) -> str:
    """Return the code generation prompt for a specific file."""
    # Detect language from file extension
    ext = file_path.split('.')[-1] if '.' in file_path else 'python'
    lang_map = {
        'py': 'python',
        'ts': 'typescript',
        'tsx': 'typescript',
        'js': 'javascript',
        'jsx': 'javascript',
        'sql': 'sql',
        'sh': 'bash',
        'yaml': 'yaml',
        'json': 'json'
    }
    language = lang_map.get(ext, 'python')

    return CODE_GENERATION_PROMPT.format(
        file_path=file_path,
        description=description,
        relevant_context=context,
        language=language
    )
```

### Phase 2: Add Plan Parser

**File to Create**: `/ganuda/lib/jr_plan_parser.py`

```python
"""
Jr Plan Parser
Extracts structured data from LLM planning responses
Cherokee AI Federation - For Seven Generations
"""

import re
from typing import Dict, List, Optional


def parse_planning_response(response: str) -> Dict:
    """
    Parse LLM response in structured plan format.

    Returns:
        {
            'project_name': str,
            'focus': str,
            'files_to_create': [(path, description), ...],
            'files_to_modify': [(path, description), ...],
            'steps': [(step_num, description), ...],
            'summary': str
        }
    """
    result = {
        'project_name': '',
        'focus': '',
        'files_to_create': [],
        'files_to_modify': [],
        'steps': [],
        'summary': ''
    }

    # Extract content from ```plan block if present
    plan_match = re.search(r'```plan\s*(.*?)\s*```', response, re.DOTALL)
    if plan_match:
        response = plan_match.group(1)

    lines = response.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        # Project name
        if line.startswith('PROJECT_NAME:'):
            result['project_name'] = line.split(':', 1)[1].strip()
            continue

        # Focus
        if line.startswith('FOCUS:'):
            result['focus'] = line.split(':', 1)[1].strip()
            continue

        # Section headers
        if line == 'FILES_TO_CREATE:':
            current_section = 'create'
            continue
        elif line == 'FILES_TO_MODIFY:':
            current_section = 'modify'
            continue
        elif line == 'STEPS:':
            current_section = 'steps'
            continue
        elif line.startswith('SUMMARY:'):
            result['summary'] = line.split(':', 1)[1].strip()
            current_section = 'summary'
            continue

        # Parse file entries: - /path/to/file.py: description
        if current_section in ('create', 'modify') and line.startswith('- '):
            file_match = re.match(r'-\s*([/\w\.\-_]+):\s*(.+)', line)
            if file_match:
                path = file_match.group(1)
                desc = file_match.group(2)
                if current_section == 'create':
                    result['files_to_create'].append((path, desc))
                else:
                    result['files_to_modify'].append((path, desc))

        # Parse step entries: - [ ] Step N: description
        if current_section == 'steps' and line.startswith('- '):
            step_match = re.match(r'-\s*\[[ x]\]\s*Step\s*(\d+):\s*(.+)', line, re.IGNORECASE)
            if step_match:
                step_num = int(step_match.group(1))
                desc = step_match.group(2)
                result['steps'].append((step_num, desc))
            else:
                # Also handle simpler format: - Step N: description
                simple_match = re.match(r'-\s*Step\s*(\d+):\s*(.+)', line, re.IGNORECASE)
                if simple_match:
                    step_num = int(simple_match.group(1))
                    desc = simple_match.group(2)
                    result['steps'].append((step_num, desc))

        # Summary continuation
        if current_section == 'summary' and line and not line.startswith(('PROJECT', 'FOCUS', 'FILES', 'STEPS', 'SUMMARY')):
            result['summary'] += ' ' + line

    return result


def extract_files_from_prose(instructions: str) -> Dict[str, List[str]]:
    """
    Fallback extraction of file paths from prose instructions.
    Looks for common patterns like:
    - CREATE FILE: /path/to/file.py
    - Path: /path/to/file.py
    - Modify `/path/to/file.py`
    """
    result = {
        'files_to_create': [],
        'files_to_modify': []
    }

    # Pattern: CREATE FILE: or CREATE FILES: followed by path
    create_patterns = [
        r'CREATE\s+FILE[S]?:\s*([/\w\.\-_]+)',
        r'CREATE\s+FILE[S]?:\s*`([^`]+)`',
        r'File\s+to\s+Create:\s*([/\w\.\-_]+)',
        r'New\s+file:\s*([/\w\.\-_]+)',
    ]

    for pattern in create_patterns:
        matches = re.findall(pattern, instructions, re.IGNORECASE)
        result['files_to_create'].extend(matches)

    # Pattern: MODIFY or UPDATE followed by path
    modify_patterns = [
        r'MODIFY:\s*([/\w\.\-_]+)',
        r'UPDATE:\s*([/\w\.\-_]+)',
        r'File\s+to\s+Modify:\s*([/\w\.\-_]+)',
        r'Modify\s+`([^`]+)`',
        r'Update\s+`([^`]+)`',
    ]

    for pattern in modify_patterns:
        matches = re.findall(pattern, instructions, re.IGNORECASE)
        result['files_to_modify'].extend(matches)

    # Deduplicate
    result['files_to_create'] = list(set(result['files_to_create']))
    result['files_to_modify'] = list(set(result['files_to_modify']))

    return result
```

### Phase 3: Update Task Executor

**File to Modify**: `/ganuda/jr_executor/task_executor.py`

Update `_extract_steps_via_llm()` to use the new planning approach:

```python
def _extract_steps_via_llm(self, instructions: str) -> List[Dict]:
    """
    Use JrLLMReasoner with structured planning prompt to extract steps.

    Two-phase approach based on Devika AI architecture:
    1. Planning phase: Extract structure (files, steps)
    2. Code generation phase: Generate code for each file
    """
    from jr_planning_prompt import get_planning_prompt, get_code_generation_prompt
    from jr_plan_parser import parse_planning_response, extract_files_from_prose

    reasoner = get_reasoner_sync()
    steps = []

    # Phase 1: Planning - get structured breakdown
    planning_prompt = get_planning_prompt(instructions)
    plan_response = reasoner.simple_completion(planning_prompt)

    print(f"[LLM] Planning response received ({len(plan_response)} chars)")

    # Parse the structured response
    plan = parse_planning_response(plan_response)

    print(f"[LLM] Parsed plan: {plan['project_name']}")
    print(f"[LLM] Files to create: {len(plan['files_to_create'])}")
    print(f"[LLM] Files to modify: {len(plan['files_to_modify'])}")
    print(f"[LLM] Steps: {len(plan['steps'])}")

    # Fallback: if no files found, try prose extraction
    if not plan['files_to_create'] and not plan['files_to_modify']:
        print("[LLM] No files in plan, trying prose extraction fallback")
        prose_files = extract_files_from_prose(instructions)
        plan['files_to_create'] = [(f, 'Extracted from prose') for f in prose_files['files_to_create']]
        plan['files_to_modify'] = [(f, 'Extracted from prose') for f in prose_files['files_to_modify']]

    # Phase 2: Code generation for each file
    for file_path, description in plan['files_to_create']:
        code_prompt = get_code_generation_prompt(file_path, description, instructions)
        code = reasoner.simple_completion(code_prompt)

        # Extract code from markdown block if present
        code_match = re.search(r'```\w*\n(.*?)```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1)

        if code and len(code.strip()) > 10:
            steps.append({
                'type': 'file',
                'args': {
                    'operation': 'write',
                    'path': file_path,
                    'content': code.strip()
                },
                'description': f"Create {file_path}: {description}"
            })

    for file_path, description in plan['files_to_modify']:
        # Read existing file
        existing_code = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    existing_code = f.read()
            except:
                pass

        code_prompt = get_code_generation_prompt(
            file_path,
            description,
            instructions + f"\n\nEXISTING CODE:\n{existing_code}" if existing_code else instructions
        )
        code = reasoner.simple_completion(code_prompt)

        # Extract code from markdown block
        code_match = re.search(r'```\w*\n(.*?)```', code, re.DOTALL)
        if code_match:
            code = code_match.group(1)

        if code and len(code.strip()) > 10:
            steps.append({
                'type': 'file',
                'args': {
                    'operation': 'write',
                    'path': file_path,
                    'content': code.strip()
                },
                'description': f"Modify {file_path}: {description}"
            })

    return steps
```

---

## Testing

After implementing, test with:

```bash
# Reset a VetAssist task
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
UPDATE jr_work_queue SET status='pending', result=NULL, completed_at=NULL
WHERE id = 108;
"

# Monitor logs during execution
tail -f /var/log/ganuda/jr_queue_worker.log

# Verify file was created
ls -la /ganuda/vetassist/backend/app/api/v1/endpoints/workbench*.py
```

---

## Success Criteria

1. Tasks with prose instructions produce actual files
2. Planning phase extracts files_to_create and files_to_modify
3. Code generation phase produces valid code
4. VetAssist Workbench files get created

---

## References

- [Devika Architecture](https://github.com/stitionai/devika/blob/main/ARCHITECTURE.md)
- [Devika Planner](https://github.com/stitionai/devika/blob/main/src/agents/planner/)
- [GPT-Engineer](https://github.com/AntonOsika/gpt-engineer)
- [SourceForge AI Coding Agents](https://sourceforge.net/software/ai-coding-agents/free-version/)

---

*Cherokee AI Federation - For Seven Generations*
