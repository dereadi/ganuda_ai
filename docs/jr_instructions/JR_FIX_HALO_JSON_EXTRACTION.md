# JR INSTRUCTION: Fix HALO Council JSON Extraction

**Created**: December 24, 2025
**Priority**: HIGH
**Effort**: LOW
**Target File**: `/ganuda/lib/halo_council.py`

---

## PROBLEM

The `PlanningAgent.decompose()` method calls `query_llm_json()` expecting a clean JSON array, but the Nemotron-9B model outputs verbose "thinking" text before the JSON:

```
Okay, let's tackle this task. The user wants to break down...
[{"subtask": "Analyze security...", ...}]
```

This causes the JSON parser to fail or return only 1 subtask instead of 3-5.

---

## ROOT CAUSE

The `query_llm_json()` function in `halo_council.py` uses basic regex to find JSON:

```python
json_match = re.search(r'\[[\s\S]*\]', text)
```

This works but if the model outputs multiple JSON fragments or wraps them in markdown code blocks, it may not capture correctly.

---

## SOLUTION

Update the `query_llm_json()` function (around line 70-100 in halo_council.py) with more robust JSON extraction:

### Current Code (approximate):
```python
def query_llm_json(system_prompt: str, user_prompt: str) -> Any:
    """Query LLM and parse JSON response."""
    response = query_llm(system_prompt, user_prompt)

    # Try direct parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array
    json_match = re.search(r'\[[\s\S]*\]', response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback
    return {"error": "Could not parse JSON", "raw": response[:500]}
```

### Updated Code:
```python
def query_llm_json(system_prompt: str, user_prompt: str) -> Any:
    """Query LLM and parse JSON response with robust extraction."""
    response = query_llm(system_prompt, user_prompt)

    # Clean markdown code blocks
    clean = response
    if '```json' in clean:
        clean = re.sub(r'```json\s*', '', clean)
        clean = re.sub(r'```\s*', '', clean)
    elif '```' in clean:
        clean = re.sub(r'```\s*', '', clean)

    # Try direct parse first
    try:
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        pass

    # Find the LARGEST JSON array in the response
    # This handles cases where model outputs multiple fragments
    json_arrays = re.findall(r'\[[\s\S]*?\](?=\s*(?:\n|$|[^,\[\]]))', response)

    best_result = None
    best_length = 0

    for potential in json_arrays:
        try:
            parsed = json.loads(potential)
            if isinstance(parsed, list) and len(parsed) > best_length:
                best_result = parsed
                best_length = len(parsed)
        except json.JSONDecodeError:
            continue

    if best_result:
        return best_result

    # Last resort: find anything between [ and ] with proper nesting
    bracket_depth = 0
    start_idx = None
    for i, char in enumerate(response):
        if char == '[':
            if bracket_depth == 0:
                start_idx = i
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            if bracket_depth == 0 and start_idx is not None:
                try:
                    fragment = response[start_idx:i+1]
                    parsed = json.loads(fragment)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed
                except json.JSONDecodeError:
                    start_idx = None
                    continue

    # Absolute fallback - return single-item array from the query
    return [{"subtask": user_prompt, "type": "reasoning", "specialist": "owl"}]
```

---

## ALTERNATIVE APPROACH

If the model consistently struggles with JSON, consider using **guided generation** or switching to a model with better instruction following:

1. **vLLM guided_json parameter**: vLLM supports `guided_json` in the API to force valid JSON output
2. **Outlines integration**: Use the Outlines library for structured generation
3. **Model swap**: Consider using a model fine-tuned for structured output (e.g., Qwen2.5-Coder)

### vLLM Guided JSON Example:
```python
def query_llm_json_guided(system_prompt: str, user_prompt: str, schema: dict) -> Any:
    """Query LLM with guided JSON generation."""
    response = requests.post(
        VLLM_URL,
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
            "guided_json": schema  # Forces valid JSON matching schema
        }
    )
    return response.json()['choices'][0]['message']['content']

# Schema for subtasks:
SUBTASK_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "subtask": {"type": "string"},
            "type": {"type": "string", "enum": ["reasoning", "research", "validation", "synthesis", "seven_generations", "security"]},
            "specialist": {"type": "string", "enum": ["crawdad", "turtle", "bear", "eagle", "spider", "owl", "wolf", "raven"]}
        },
        "required": ["subtask", "type", "specialist"]
    },
    "minItems": 3,
    "maxItems": 5
}
```

---

## VALIDATION CHECKLIST

After implementing the fix:

- [ ] Run: `python3 -c "from lib.halo_council import PlanningAgent, PromptRefinementModule; r = PromptRefinementModule(); p = PlanningAgent(); refined = r.refine('How to optimize memory?'); tasks = p.decompose(refined); print(f'Got {len(tasks)} subtasks'); assert len(tasks) >= 3, 'Should have 3+ subtasks'"`
- [ ] Verify subtasks have different specialists assigned
- [ ] Test with a complex query requiring multiple perspectives
- [ ] Run full HALO query: `python3 -c "from lib.halo_council import halo_query; result = halo_query('Should we add caching?'); print(result)"`

---

## THERMAL MEMORY ENTRY

After successful fix, record:
```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
VALUES (
  'halo-json-fix-20251224',
  'HALO JSON Extraction Fixed - Dec 24, 2025

Problem: Nemotron-9B outputs verbose reasoning before JSON arrays
Solution: Enhanced query_llm_json() with multi-pass extraction:
1. Strip markdown code blocks
2. Find LARGEST valid JSON array in response
3. Handle nested bracket matching
4. Fallback to single-item array

Also documented vLLM guided_json option for future use.',
  85.0,
  '{"type": "bug_fix", "file": "halo_council.py", "function": "query_llm_json"}'::jsonb
);
```

---

For Seven Generations - clear instructions enable distributed execution.
