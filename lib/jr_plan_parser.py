"""
Jr Plan Parser
Extracts structured data from LLM planning responses
Based on Devika AI parsing patterns
Cherokee AI Federation - For Seven Generations

Created: January 17, 2026
Updated: 2026-05-12 (Partner) — Strategy 3 widened to extract_any_absolute_paths
Updated: 2026-05-16 (TPM-Stoneclad inline) — Strategies 2 (markdown headers),
         4 (JSON), 5 (instruction-text override) per KB-JR-EXECUTOR-QWEN36
         Fix 2. Council fix plan 2026-05-15. Tests at
         /ganuda/tests/test_jr_plan_parser_strategies.py.
         Recursive-trap context: Jr's own broken parser could not produce the
         fix; TPM-inline takeover per Crawdad's "Jr has the bug we're fixing."
"""

import json
import re
from typing import Dict, List, Tuple


def parse_planning_response(response: str) -> Dict:
    """
    Parse LLM response in structured plan format.
    Multi-strategy: tries structured format first, falls back to path extraction.

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

    # Strip think tags before parsing
    from lib.llm_config import strip_think_tags
    response = strip_think_tags(response)

    # Strategy 1: Extract content from ```plan block if present
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

    # Strategy 2 (May 16 2026): markdown header sections.
    # Catches LLM responses formatted with `## FILES TO CREATE` / `## MODIFY`
    # style headers when the structured PROJECT_NAME/FILES_TO_CREATE: block
    # is absent. Cascades only if Strategy 1 found nothing.
    if not result['files_to_create'] and not result['files_to_modify']:
        md_sections = _extract_markdown_header_sections(response)
        result['files_to_create'].extend(md_sections['files_to_create'])
        result['files_to_modify'].extend(md_sections['files_to_modify'])
        if (result['files_to_create'] or result['files_to_modify']) and not result['steps']:
            n = len(result['files_to_create']) + len(result['files_to_modify'])
            result['steps'] = [(1, f'Process {n} file(s) from markdown sections')]

    # Strategy 3 (May 16 2026): JSON extraction.
    # Promoted ahead of path-scan because when ```json or raw {...} is present
    # it's authoritative for create-vs-modify classification, whereas path-scan
    # has to guess from English keywords and gets confused by JSON syntax in
    # the surrounding context. Cascades only if Strategies 1+2 found nothing.
    # (KB-JR-EXECUTOR-QWEN36 Fix 2 called this Strategy 4; reordered for
    # correctness — JSON beats heuristic.)
    if not result['files_to_create'] and not result['files_to_modify']:
        json_data = _extract_json_files(response)
        result['files_to_create'].extend(json_data['files_to_create'])
        result['files_to_modify'].extend(json_data['files_to_modify'])
        if (result['files_to_create'] or result['files_to_modify']) and not result['steps']:
            n = len(result['files_to_create']) + len(result['files_to_modify'])
            result['steps'] = [(1, f'Process {n} file(s) from JSON response')]

    # Strategy 4 (May 12 2026): absolute-path scan across response.
    # Widened from /ganuda/-only to all known prefixes via extract_any_absolute_paths.
    # Last-resort heuristic — runs only if 1+2+3 (JSON) found nothing.
    if not result['files_to_create'] and not result['files_to_modify']:
        for path in extract_any_absolute_paths(response):
            # Guess create vs modify based on context words near each path
            idx = response.find(path)
            context = response[max(0, idx-100):idx].lower() if idx >= 0 else ''
            if any(w in context for w in ['create', 'new file', 'generate', 'write', 'produce', 'output']):
                result['files_to_create'].append((path, 'Extracted from path scan'))
            else:
                result['files_to_modify'].append((path, 'Extracted from path scan'))

        if (result['files_to_create'] or result['files_to_modify']) and not result['steps']:
            n = len(result['files_to_create']) + len(result['files_to_modify'])
            result['steps'] = [(1, f'Process {n} file(s)')]

    return result


# Path-scanning helper used by both parse_planning_response (Strategy 2)
# and extract_files_from_prose (final fallback). Accepts any plausible
# Unix absolute path under a known prefix, with or without an extension,
# excluding obvious placeholders.
_PATH_PREFIXES = ('/ganuda/', '/tmp/', '/home/', '/var/', '/etc/', '/opt/',
                  '/usr/', '/root/', '/srv/', '/Users/')
_PLACEHOLDER_FRAGMENTS = ('/path/to/', '/your/path/', '[name]', '[path]',
                          '<path>', '<file>', 'example.com', '/dev/null')


def extract_any_absolute_paths(text: str) -> List[str]:
    """Scan text for any plausible Unix absolute path under a known prefix.

    Returns deduplicated list, original order preserved. Excludes
    placeholder fragments like /path/to/, [name], etc. Path may end in
    a file extension or be a directory-leaf-with-no-extension.
    """
    if not text:
        return []
    # Match absolute paths with optional extension; trailing punctuation stripped.
    pattern = re.compile(r'(/[A-Za-z][\w\-./]+?)(?=[\s\),:;\'"]|$)', re.MULTILINE)
    candidates = pattern.findall(text)
    seen = set()
    out = []
    for raw in candidates:
        p = raw.rstrip('.,;:)\'"')
        if not any(p.startswith(prefix) for prefix in _PATH_PREFIXES):
            continue
        if any(frag in p for frag in _PLACEHOLDER_FRAGMENTS):
            continue
        # Require either an extension OR depth >= 3 (e.g. /tmp/foo would
        # NOT match by depth alone; /tmp/foo/bar would). This filters out
        # bare directory names that aren't real targets.
        if '.' not in p.rsplit('/', 1)[-1] and p.count('/') < 3:
            continue
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _extract_markdown_header_sections(response: str) -> Dict[str, List[Tuple[str, str]]]:
    """Strategy 2 (KB-JR-EXECUTOR-QWEN36 Fix 2): extract from markdown header sections.

    Catches LLM responses formatted as::

        ## FILES TO CREATE
        - /path/to/file.py
        - `/path/to/other.py`: some description

        ### MODIFY
        /path/to/edit.py
        - /another/path.sql

    Recognises a small allowlist of section names (case-insensitive). Within
    each section, accepts bulleted, backticked, or bare path lines. Stops
    accumulating when the next markdown header begins. Path validation
    delegates to extract_any_absolute_paths semantics (must start with a
    known prefix; placeholders excluded).
    """
    create: List[Tuple[str, str]] = []
    modify: List[Tuple[str, str]] = []

    header_re = re.compile(
        r'^#{1,6}\s+'
        r'(?P<header>'
        r'(?:NEW\s+)?FILES?\s+TO\s+(?:CREATE|MODIFY|UPDATE|EDIT)'
        r'|CREATE\s+FILES?|MODIFY\s+FILES?|UPDATE\s+FILES?'
        r'|NEW\s+FILES?|EDIT|FILES?'
        r')'
        r'\s*:?\s*$',
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(header_re.finditer(response))
    for i, m in enumerate(matches):
        header = m.group('header').upper().strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(response)
        body = response[body_start:body_end]

        # Classify section as create vs modify (default modify when ambiguous —
        # safer because edits to existing files are reversible via git).
        if 'CREATE' in header or 'NEW' in header:
            target = create
        elif any(w in header for w in ('MODIFY', 'UPDATE', 'EDIT')):
            target = modify
        else:
            target = modify

        for raw_line in body.split('\n'):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#'):
                # Defensive: a nested header inside the body means our regex
                # missed it — stop processing this section to avoid bleed-over.
                break
            # Try: - `/path`: desc / - /path: desc / `/path` / /path
            m2 = re.match(
                r'-?\s*`?(?P<path>/[\w/.\-_]+(?:\.[\w]+)?)`?'
                r'(?:\s*[:\-—]\s*(?P<desc>.+))?$',
                line,
            )
            if not m2:
                continue
            path = m2.group('path').rstrip('.,;:)\'"')
            if not any(path.startswith(prefix) for prefix in _PATH_PREFIXES):
                continue
            if any(frag in path for frag in _PLACEHOLDER_FRAGMENTS):
                continue
            desc = (m2.group('desc') or 'From markdown section').strip().rstrip('.')
            entry = (path, desc)
            if entry not in target:
                target.append(entry)

    return {'files_to_create': create, 'files_to_modify': modify}


def _extract_json_files(response: str) -> Dict[str, List[Tuple[str, str]]]:
    """Strategy 4 (KB-JR-EXECUTOR-QWEN36 Fix 2): try json.loads on the response.

    Matches LLM responses that return plans as JSON. Looks for the keys
    ``files_to_create`` and ``files_to_modify`` (each a list of either
    strings or dicts with ``path`` + optional ``description``/``desc``).

    Tries (in order): explicit ```json fenced blocks, the response if it
    looks like a bare JSON object, and any { ... } region that mentions
    one of the target keys. Returns the first candidate that parses AND
    yields at least one file entry.
    """
    create: List[Tuple[str, str]] = []
    modify: List[Tuple[str, str]] = []

    def _collect(items, target):
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, str):
                path = item.strip().strip('`').rstrip('.,;:)\'"')
                if path:
                    target.append((path, 'From JSON response'))
            elif isinstance(item, dict):
                raw_path = item.get('path') or item.get('file') or item.get('filename')
                if not raw_path:
                    continue
                path = str(raw_path).strip().strip('`').rstrip('.,;:)\'"')
                desc = (
                    item.get('description')
                    or item.get('desc')
                    or item.get('purpose')
                    or 'From JSON response'
                )
                target.append((path, str(desc)))

    candidates: List[str] = []
    for m in re.finditer(r'```json\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE):
        candidates.append(m.group(1))
    stripped = response.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        candidates.append(stripped)
    # Also pick out any { ... } block that mentions one of the target keys.
    # Non-greedy with no nested-brace handling — sufficient for typical
    # flat plan payloads.
    for m in re.finditer(
        r'\{[^{}]*"files_to_(?:create|modify)"[^{}]*\}',
        response,
        re.DOTALL,
    ):
        candidates.append(m.group(0))

    seen = set()
    for raw in candidates:
        if raw in seen:
            continue
        seen.add(raw)
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        c_local: List[Tuple[str, str]] = []
        m_local: List[Tuple[str, str]] = []
        _collect(data.get('files_to_create'), c_local)
        _collect(data.get('files_to_modify'), m_local)
        if c_local or m_local:
            create.extend(c_local)
            modify.extend(m_local)
            break  # First successful candidate wins.

    return {'files_to_create': create, 'files_to_modify': modify}


def _extract_instruction_overrides(instructions: str) -> Dict[str, List[str]]:
    """Strategy 5 (KB-JR-EXECUTOR-QWEN36 Fix 2): operator-direct overrides.

    Scans the ORIGINAL instruction text for explicit ``CREATE FILE: /abs/path``
    or ``MODIFY FILE: /abs/path`` lines. These represent operator intent
    expressed directly, bypassing any LLM-mediated interpretation — when
    present, they should win over LLM-derived choices.

    Caller integration: ``extract_files_from_prose`` calls this first; if it
    returns any paths, those become the authoritative answer. Executors
    that want to skip the LLM call entirely should invoke this helper
    directly before sending the planning prompt.
    """
    create: List[str] = []
    modify: List[str] = []

    # CREATE FILE: /abs/path | CREATE FILES: /abs/path | CREATE: /abs/path
    create_re = re.compile(
        r'(?:^|\n)\s*CREATE(?:\s+FILES?)?\s*[:=]\s*`?(?P<path>/[/\w.\-_]+)`?',
        re.IGNORECASE,
    )
    modify_re = re.compile(
        r'(?:^|\n)\s*(?:MODIFY|UPDATE|EDIT)(?:\s+FILES?)?\s*[:=]\s*`?(?P<path>/[/\w.\-_]+)`?',
        re.IGNORECASE,
    )
    for m in create_re.finditer(instructions):
        path = m.group('path').rstrip('.,;:)\'"')
        if any(path.startswith(prefix) for prefix in _PATH_PREFIXES) and \
           not any(frag in path for frag in _PLACEHOLDER_FRAGMENTS):
            if path not in create:
                create.append(path)
    for m in modify_re.finditer(instructions):
        path = m.group('path').rstrip('.,;:)\'"')
        if any(path.startswith(prefix) for prefix in _PATH_PREFIXES) and \
           not any(frag in path for frag in _PLACEHOLDER_FRAGMENTS):
            if path not in modify:
                modify.append(path)
    return {'files_to_create': create, 'files_to_modify': modify}


def extract_files_from_prose(instructions: str) -> Dict[str, List[str]]:
    """
    Fallback extraction of file paths from prose instructions.
    Looks for common patterns in JR instruction files.
    """
    result = {
        'files_to_create': [],
        'files_to_modify': []
    }

    # Strategy 5 (May 16 2026): instruction-text overrides win.
    # When the operator writes ``CREATE FILE: /abs/path`` or ``MODIFY FILE:
    # /abs/path`` directly in the instructions, that's authoritative — no
    # need to fall through the LLM-derived heuristics. Return immediately.
    overrides = _extract_instruction_overrides(instructions)
    if overrides['files_to_create'] or overrides['files_to_modify']:
        result['files_to_create'].extend(overrides['files_to_create'])
        result['files_to_modify'].extend(overrides['files_to_modify'])
        return result

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

    # Final fallback (May 12 2026): generic absolute-path scan against
    # the original instructions. Catches /tmp/, /home/, /etc/, .txt, .conf
    # — anything the rigid pattern set missed. Same intent-guessing logic
    # as parse_planning_response Strategy 2.
    if not result['files_to_create'] and not result['files_to_modify']:
        for path in extract_any_absolute_paths(instructions):
            idx = instructions.find(path)
            context = instructions[max(0, idx-150):idx].lower() if idx >= 0 else ''
            if any(w in context for w in ['create', 'new file', 'generate', 'write', 'produce', 'output']):
                result['files_to_create'].append(path)
            else:
                result['files_to_modify'].append(path)

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
