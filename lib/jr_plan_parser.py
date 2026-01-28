"""
Jr Plan Parser
Extracts structured data from LLM planning responses
Based on Devika AI parsing patterns
Cherokee AI Federation - For Seven Generations

Created: January 17, 2026
"""

import re
from typing import Dict, List, Tuple


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
            # Try multiple patterns
            file_match = re.match(r'-\s*(/[/\w\.\-_]+):\s*(.+)', line)
            if not file_match:
                # Try with backticks
                file_match = re.match(r'-\s*`(/[^`]+)`:\s*(.+)', line)
            if not file_match:
                # Try simpler pattern
                file_match = re.match(r'-\s*([/\w\.\-_]+\.(?:py|tsx?|jsx?|sql|sh|yaml|json|md))(?::\s*(.*))?', line)

            if file_match:
                path = file_match.group(1)
                desc = file_match.group(2) if file_match.lastindex >= 2 and file_match.group(2) else 'Generated file'
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
                else:
                    # Handle numbered list: 1. description
                    numbered_match = re.match(r'-?\s*(\d+)\.\s*(.+)', line)
                    if numbered_match:
                        step_num = int(numbered_match.group(1))
                        desc = numbered_match.group(2)
                        result['steps'].append((step_num, desc))

        # Summary continuation
        if current_section == 'summary' and line and not line.startswith(('PROJECT', 'FOCUS', 'FILES', 'STEPS', 'SUMMARY', '-')):
            result['summary'] += ' ' + line

    return result


def extract_files_from_prose(instructions: str) -> Dict[str, List[str]]:
    """
    Fallback extraction of file paths from prose instructions.
    Looks for common patterns in JR instruction files.
    """
    result = {
        'files_to_create': [],
        'files_to_modify': []
    }

    # Patterns for files to create
    create_patterns = [
        r'CREATE\s+FILE[S]?:\s*([/\w\.\-_]+)',
        r'CREATE\s+FILE[S]?:\s*`([^`]+)`',
        r'File\s+to\s+Create:\s*`?([/\w\.\-_]+)`?',
        r'New\s+file:\s*`?([/\w\.\-_]+)`?',
        r'CREATE:\s*`?([/\w\.\-_]+\.(?:py|tsx?|jsx?|sql))`?',
        # Pattern for numbered file lists
        r'^\d+\.\s+([/\w\.\-_]+\.(?:py|tsx?|jsx?|sql))\s*[-–]',
        # Pattern for paths after "Path:"
        r'Path:\s*`?([/\w\.\-_]+)`?',
    ]

    for pattern in create_patterns:
        matches = re.findall(pattern, instructions, re.IGNORECASE | re.MULTILINE)
        result['files_to_create'].extend(matches)

    # Patterns for files to modify
    # Updated Jan 26, 2026: Added bracket support for Next.js dynamic routes like [sessionId]
    modify_patterns = [
        r'MODIFY:\s*`([^`]+)`',  # MODIFY: `/path/with/[brackets]/file.tsx`
        r'MODIFY:\s*([/\w\.\-_\[\]]+)',  # MODIFY: /path/with/[brackets]/file.tsx
        r'UPDATE:\s*`([^`]+)`',
        r'UPDATE:\s*([/\w\.\-_\[\]]+)',
        r'File\s+to\s+Modify:\s*`([^`]+)`',
        r'UPDATE\s+FILE[S]?:\s*`([^`]+)`',
        r'Modify\s+`([^`]+)`',
        r'Update\s+`([^`]+)`',
        r'Edit\s+`([^`]+)`',
    ]

    for pattern in modify_patterns:
        matches = re.findall(pattern, instructions, re.IGNORECASE | re.MULTILINE)
        result['files_to_modify'].extend(matches)

    # Look for BACKEND LOCATION or FRONTEND LOCATION patterns
    location_match = re.search(r'(?:BACKEND|FRONTEND)\s+LOCATION:\s*([/\w\.\-_/]+)', instructions, re.IGNORECASE)
    base_path = location_match.group(1).rstrip('/') if location_match else None

    if base_path:
        # Find file names mentioned after CREATE FILE(S):
        # Pattern 1: CREATE FILE: filename.py on same line
        single_file_match = re.search(r'CREATE\s+FILE:\s*(\w+\.(?:py|tsx?|jsx?|sql|md))', instructions, re.IGNORECASE)
        if single_file_match:
            fname = single_file_match.group(1)
            full_path = f"{base_path}/{fname}"
            if full_path not in result['files_to_create']:
                result['files_to_create'].append(full_path)

        # Pattern 2: CREATE FILES: followed by numbered list
        create_section = re.search(r'CREATE\s+FILES:\s*(.*?)(?:FEATURES|API|DATABASE|SECURITY|$)', instructions, re.DOTALL | re.IGNORECASE)
        if create_section:
            # Look for numbered list: 1. filename.py
            file_names = re.findall(r'^\s*\d+\.\s+(\w+\.(?:py|tsx?|jsx?|sql|md))', create_section.group(1), re.MULTILINE)
            for fname in file_names:
                full_path = f"{base_path}/{fname}"
                if full_path not in result['files_to_create']:
                    result['files_to_create'].append(full_path)
            # Also look for: - filename.py
            file_names = re.findall(r'^\s*-\s*(\w+\.(?:py|tsx?|jsx?|sql|md))', create_section.group(1), re.MULTILINE)
            for fname in file_names:
                full_path = f"{base_path}/{fname}"
                if full_path not in result['files_to_create']:
                    result['files_to_create'].append(full_path)

    # For any files without full paths, try to prepend base_path
    if base_path:
        updated_creates = []
        for f in result['files_to_create']:
            if not f.startswith('/'):
                updated_creates.append(f"{base_path}/{f}")
            else:
                updated_creates.append(f)
        result['files_to_create'] = updated_creates

    # Deduplicate while preserving order
    seen_create = set()
    result['files_to_create'] = [f for f in result['files_to_create']
                                  if not (f in seen_create or seen_create.add(f))]

    seen_modify = set()
    result['files_to_modify'] = [f for f in result['files_to_modify']
                                  if not (f in seen_modify or seen_modify.add(f))]

    return result


def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Extract code blocks from markdown text.

    Returns:
        [(language, code), ...]
    """
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang or 'text', code.strip()) for lang, code in matches]


if __name__ == '__main__':
    # Test the parser
    test_response = '''
```plan
PROJECT_NAME: VetAssist Document API

FOCUS: Build secure document upload API for veteran claim workbench

FILES_TO_CREATE:
- /ganuda/vetassist/backend/app/api/v1/endpoints/workbench_documents.py: Document upload/download endpoints
- /ganuda/vetassist/backend/app/models/document.py: Document database model

FILES_TO_MODIFY:
- /ganuda/vetassist/backend/app/api/v1/__init__.py: Register new router

STEPS:
- [ ] Step 1: Create Document model with SQLAlchemy
- [ ] Step 2: Implement upload endpoint with file validation
- [ ] Step 3: Add download and delete endpoints
- [ ] Step 4: Register router in API init

SUMMARY: Secure document handling with Presidio PII detection, goldfin storage
```
'''
    result = parse_planning_response(test_response)
    print("Parsed result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
