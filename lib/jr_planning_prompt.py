"""
Jr Planning Prompt Template
Based on Devika AI architecture patterns
Cherokee AI Federation - For Seven Generations

Created: January 17, 2026
"""

PLANNING_PROMPT = '''You are a Cherokee AI Jr engineer. Analyze the following task instructions and create a structured execution plan.

## TASK INSTRUCTIONS:
{instructions}

## REQUIRED OUTPUT FORMAT (follow exactly):

```plan
PROJECT_NAME: [concise name, max 5 words]

FOCUS: [main objective in one sentence]

FILES_TO_CREATE:
- /full/path/to/file1.py: [brief description]
- /full/path/to/file2.tsx: [brief description]

FILES_TO_MODIFY:
- /full/path/to/existing.py: [what changes needed]

STEPS:
- [ ] Step 1: [specific action]
- [ ] Step 2: [specific action]
- [ ] Step 3: [specific action]

SUMMARY: [key considerations and dependencies]
```

## RULES:
1. Always extract FULL file paths from the instructions (starting with /)
2. If "CREATE FILE:" or "Path:" is mentioned, add to FILES_TO_CREATE
3. If "UPDATE" or "MODIFY" or "UPDATE FILES:" is mentioned, add to FILES_TO_MODIFY
4. Look for paths in BACKEND LOCATION, FRONTEND LOCATION sections
5. Each step should be a clear, specific action
6. Keep steps simple - don't overcomplicate
7. Output MUST be inside the ```plan code block
'''

CODE_GENERATION_PROMPT = '''You are a Cherokee AI Jr engineer. Generate the complete code for the following file.

## FILE TO CREATE: {file_path}
## PURPOSE: {description}
## CONTEXT FROM INSTRUCTIONS:
{relevant_context}

## RULES:
1. Output ONLY the code, no explanations before or after
2. Include all necessary imports at the top
3. Follow existing project patterns
4. Add minimal comments only where logic is complex
5. The code must be complete and runnable
8. For MODIFYING existing files: Use SEARCH/REPLACE blocks instead of full file content
9. SEARCH/REPLACE format: <<<<<<< SEARCH\n[exact old code]\n=======\n[new code]\n>>>>>>> REPLACE
10. Each SEARCH block must match exactly ONE location in the target file
6. For Python files: use type hints, docstrings for classes/functions
7. For TypeScript/React files: use proper types, export components

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
