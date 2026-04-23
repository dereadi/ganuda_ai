"""
Jr Planning Prompt Template
Based on Devika AI architecture patterns
Cherokee AI Federation - For Seven Generations

Created: January 17, 2026
"""

PLANNING_PROMPT = '''You are a task executor. Read the instructions and output ONLY a structured plan. No reasoning, no explanation, no thinking — just the plan in the exact format below.

TASK INSTRUCTIONS:
{instructions}

OUTPUT THIS EXACT FORMAT AND NOTHING ELSE:

```plan
PROJECT_NAME: <fill in>

FOCUS: <fill in>

FILES_TO_CREATE:
- <extract actual file paths from the instructions above>

FILES_TO_MODIFY:
- <extract actual file paths from the instructions above>

STEPS:
- [ ] Step 1: <fill in>
- [ ] Step 2: <fill in>

SUMMARY: <fill in>
```

RULES:
- Extract REAL file paths mentioned in the task instructions. Do NOT invent paths.
- Paths like /ganuda/lib/specialist_council.py or /ganuda/jr_executor/task_executor.py are real paths. Use them.
- Do NOT use placeholder paths like /path/to/file.py — those will be rejected.
- If instructions say CREATE, put in FILES_TO_CREATE
- If instructions say MODIFY/UPDATE/FIX, put in FILES_TO_MODIFY
- Output ONLY the ```plan block. Nothing before it. Nothing after it.
'''

CODE_GENERATION_PROMPT = '''Generate code for this file.

FILE: {file_path}
PURPOSE: {description}
CONTEXT:
{relevant_context}

INSTRUCTIONS:
- For NEW files: write the complete file inside a ```{language} code block.
- For MODIFYING existing files: write one or more SEARCH/REPLACE blocks.
  Each block must contain the EXACT old code to find and the new code to replace it with.
  Format:

<<<<<<< SEARCH
exact old code copied from the file above
=======
new replacement code
>>>>>>> REPLACE

- Include enough surrounding lines in SEARCH to make the match unique (at least 3-5 lines).
- You may include multiple SEARCH/REPLACE blocks if multiple changes are needed.
- Make sure each SEARCH block contains code that ACTUALLY EXISTS in the file shown above.

Write your code now:

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
        'json': 'json',
        'md': 'markdown'
    }
    language = lang_map.get(ext, 'python')

    return CODE_GENERATION_PROMPT.format(
        file_path=file_path,
        description=description,
        relevant_context=context,
        language=language
    )
