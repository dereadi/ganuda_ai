# JR Instruction: Fix CREATE FILES Plural Pattern Parser

## Metadata
```yaml
task_id: fix_create_files_plural
priority: 1
assigned_to: it_triad_jr
estimated_effort: low
category: bug_fix
```

## Overview

The Jr plan parser (`/ganuda/lib/jr_plan_parser.py`) cannot parse the "CREATE FILES:" (plural) instruction format with numbered lists. This causes frontend tasks to complete without creating any files.

## Problem

Current instruction format that fails:
```
FRONTEND LOCATION: /ganuda/vetassist/frontend/src/app/workbench/

CREATE FILES:
1. page.tsx - Main workbench dashboard
2. layout.tsx - Workbench layout wrapper
3. components/ClaimCard.tsx - Individual claim display
```

The parser only handles singular "CREATE FILE:" pattern.

## BACKEND LOCATION: /ganuda/lib

## MODIFY FILE: jr_plan_parser.py

## Required Changes

### 1. Update `extract_files_from_prose()` function

Add pattern to handle numbered list after "CREATE FILES:" (plural):

```python
# In extract_files_from_prose() function, after the existing single_file_match block:

# Pattern 2: CREATE FILES: followed by numbered list
create_section = re.search(r'CREATE\s+FILES:\s*(.*?)(?:FEATURES|API|DATABASE|SECURITY|MODIFY|UPDATE|$)', instructions, re.DOTALL | re.IGNORECASE)
if create_section:
    section_text = create_section.group(1)

    # Look for numbered list: 1. filename.tsx - description
    file_matches = re.findall(r'^\s*\d+\.\s+(\S+\.(?:py|tsx?|jsx?|sql|md|json|yaml|sh))', section_text, re.MULTILINE)
    for fname in file_matches:
        # Handle nested paths like components/ClaimCard.tsx
        if base_path:
            full_path = f"{base_path}/{fname}"
        else:
            full_path = fname
        if full_path not in result['files_to_create']:
            result['files_to_create'].append(full_path)

    # Also handle bullet points: - filename.tsx
    bullet_matches = re.findall(r'^\s*[-*]\s+(\S+\.(?:py|tsx?|jsx?|sql|md|json|yaml|sh))', section_text, re.MULTILINE)
    for fname in bullet_matches:
        if base_path:
            full_path = f"{base_path}/{fname}"
        else:
            full_path = fname
        if full_path not in result['files_to_create']:
            result['files_to_create'].append(full_path)
```

### 2. Handle nested component paths

The regex should capture paths like `components/ClaimCard.tsx`:
- Change `\w+\.` to `\S+\.` to allow slashes in filename

### 3. Add unit test

Create test case in the `if __name__ == '__main__':` block:

```python
# Test plural pattern
test_plural = '''
FRONTEND LOCATION: /ganuda/vetassist/frontend/src/app/workbench/

CREATE FILES:
1. page.tsx - Main dashboard
2. layout.tsx - Layout wrapper
3. components/ClaimCard.tsx - Claim card component

FEATURES:
- Dashboard view
'''
result = extract_files_from_prose(test_plural)
print(f"Plural pattern test: {result['files_to_create']}")
assert '/ganuda/vetassist/frontend/src/app/workbench/page.tsx' in result['files_to_create']
assert '/ganuda/vetassist/frontend/src/app/workbench/components/ClaimCard.tsx' in result['files_to_create']
print("  PASS")
```

## Success Criteria

1. `extract_files_from_prose()` returns correct paths for:
   - `CREATE FILE:` (singular)
   - `CREATE FILES:` (plural with numbered list)
   - `CREATE FILES:` (plural with bullet points)
   - Nested paths like `components/Foo.tsx`

2. Re-running VetAssist task 109 creates frontend files

## Testing

```bash
cd /ganuda/lib
python jr_plan_parser.py
```

## Reference

See KB article: KB-JR-PLAN-PARSER-PROSE-EXTRACTION-JAN18-2026.md

---
Cherokee AI Federation - For Seven Generations
