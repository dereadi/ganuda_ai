#!/usr/bin/env python3
"""Debug HALO JSON extraction with live LLM."""

import sys
sys.path.insert(0, '/ganuda')

from lib.halo_council import query_llm, query_llm_json, PlanningAgent
import json

planner = PlanningAgent()

test_prompt = """Break this task into 4 subtasks.
Task: How should we optimize our thermal memory system?

Available specialists: crawdad, turtle, bear, eagle, spider, owl, wolf, raven

Respond with ONLY a JSON array:
[{"subtask": "...", "type": "...", "specialist": "..."}]"""

print("=== RAW RESPONSE ===")
raw = query_llm(planner.SYSTEM_PROMPT, test_prompt, max_tokens=1500)
print(raw[:500])
print("...")
print(raw[-500:])
print()
print(f"Total length: {len(raw)}")
bracket_pos = raw.find('[')
print(f"First [ at: {bracket_pos}")
print(f"Last ] at: {raw.rfind(']')}")
print()

print("=== MANUAL EXTRACTION ===")
best = None
i = 0
while i < len(raw):
    if raw[i] == '[':
        depth = 1
        j = i + 1
        while j < len(raw) and depth > 0:
            if raw[j] == '[':
                depth += 1
            elif raw[j] == ']':
                depth -= 1
            j += 1
        if depth == 0:
            candidate = raw[i:j]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    print(f"Found {len(parsed)} items from {i} to {j}")
                    best = parsed
            except Exception as e:
                print(f"Parse error at {i}: {e}")
                print(f"Candidate start: {candidate[:100]}...")
        i = j
    else:
        i += 1

print()
print("=== RESULT ===")
if best:
    print(f"Extracted {len(best)} subtasks:")
    for i, st in enumerate(best, 1):
        print(f"  {i}. [{st.get('specialist', 'N/A')}] {st.get('subtask', str(st))[:60]}...")
else:
    print("No array found!")

print()
print("=== COMPARING TO query_llm_json ===")
result2 = query_llm_json(planner.SYSTEM_PROMPT, test_prompt)
print(f"query_llm_json returned: {type(result2)}")
if isinstance(result2, list):
    print(f"  {len(result2)} items")
elif isinstance(result2, dict) and 'error' in result2:
    print(f"  Error: {result2.get('error')}")
    print(f"  Raw: {result2.get('raw', '')[:200]}...")
