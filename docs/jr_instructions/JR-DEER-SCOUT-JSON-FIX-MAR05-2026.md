# JR Instruction: Fix Fragile JSON Parsing in deer_scout.py

**Task**: Replace fragile regex JSON extraction with robust parsing
**Priority**: 6 (MEDIUM — silent failure risk)
**Sacred Fire**: No
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**TEG Plan**: false

## Context

deer_scout.py line 107 uses `re.search(r'\{[^}]+\}', content)` to extract JSON from LLM responses. This regex breaks on nested objects (e.g. `{"key": {"nested": "value"}}`) because `[^}]+` stops at the first `}`. Currently works because the expected output format has no nested braces, but any LLM variation with nested JSON will silently fail and return default classification.

## Changes

File: `email_daemon/deer_scout.py`

<<<<<<< SEARCH
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
=======
            # Try direct JSON parse first, then regex fallback
            result = None
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Extract JSON from mixed text — find outermost braces
                brace_start = content.find('{')
                if brace_start >= 0:
                    depth = 0
                    for i, ch in enumerate(content[brace_start:], brace_start):
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    result = json.loads(content[brace_start:i+1])
                                except json.JSONDecodeError:
                                    pass
                                break
            if result is not None:
>>>>>>> REPLACE

## Verification

The fix should handle:
1. Clean JSON response: `{"jewel_type": 1, "summary": "test", "tags": ["ai"]}` — direct parse
2. JSON embedded in text: `Here is the classification: {"jewel_type": 2, ...}` — brace matching
3. Nested JSON: `{"jewel_type": 1, "meta": {"source": "nate"}}` — depth tracking
4. No JSON at all: falls through to default classification (existing behavior)
