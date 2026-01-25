# JR Instruction: CFR Search Improvement
## Task ID: CFR-SEARCH-001
## Priority: P2
## Estimated Complexity: Medium

---

## Objective

Improve the CFR condition mapping search to handle multi-word phrases and partial matches. Currently single words like "PTSD" work, but phrases like "knee pain" or "PTSD post traumatic stress" return empty results.

---

## Current Issue

```bash
# Works
curl -X POST .../conditions/map -d '{"description": "PTSD"}'
# Returns 9411

# Fails (returns empty)
curl -X POST .../conditions/map -d '{"description": "PTSD post traumatic stress"}'
curl -X POST .../conditions/map -d '{"description": "knee pain"}'
```

---

## Root Cause

The SQL query in `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py` uses exact matching on synonyms/common_names arrays. Multi-word inputs don't match single-word array elements.

---

## Solution Options

### Option A: Word Tokenization (Recommended)
Split input into words and match ANY word against synonyms/common_names.

```python
# In conditions.py map_condition()
search_terms = request.description.lower().split()

# Match if ANY search term appears in synonyms or common_names
query = """
SELECT ... FROM vetassist_cfr_conditions
WHERE
    -- Any search term in condition name
    (SELECT bool_or(LOWER(condition_name) LIKE '%' || term || '%')
     FROM unnest(%s::text[]) term)
    OR
    -- Any search term in synonyms
    (SELECT bool_or(syn ILIKE '%' || term || '%')
     FROM unnest(synonyms) syn, unnest(%s::text[]) term)
    OR
    -- Any search term in common_names
    (SELECT bool_or(cn ILIKE '%' || term || '%')
     FROM unnest(common_names) cn, unnest(%s::text[]) term)
"""
params = [search_terms, search_terms, search_terms]
```

### Option B: Full-Text Search
Add PostgreSQL tsvector column for full-text search.

```sql
ALTER TABLE vetassist_cfr_conditions ADD COLUMN search_vector tsvector;

UPDATE vetassist_cfr_conditions SET search_vector =
    to_tsvector('english',
        condition_name || ' ' ||
        array_to_string(synonyms, ' ') || ' ' ||
        array_to_string(common_names, ' ')
    );

CREATE INDEX idx_cfr_fts ON vetassist_cfr_conditions USING GIN(search_vector);
```

Then query with:
```python
query = """
SELECT * FROM vetassist_cfr_conditions
WHERE search_vector @@ plainto_tsquery('english', %s)
"""
```

### Option C: Trigram Similarity
Use pg_trgm extension for fuzzy matching.

---

## Implementation Steps

1. Read current conditions.py implementation
2. Implement Option A (word tokenization)
3. Test with various search phrases
4. If insufficient, add Option B (full-text search)
5. Update tests in test_sprint3_integration.py

---

## Test Cases

```python
# Should all return results
test_searches = [
    ("PTSD", "9411"),
    ("post traumatic stress", "9411"),
    ("knee pain", ["5256", "5257", "5260", "5261"]),
    ("back pain lower", ["5237", "5242"]),
    ("ringing ears", "6260"),
    ("cant sleep", "6847"),
    ("sugar diabetes", "7913"),
    ("hand numbness carpal", "8515"),
]
```

---

## Acceptance Criteria

1. Multi-word phrases return relevant conditions
2. Partial word matches work (e.g., "diabet" matches diabetes)
3. Performance remains under 100ms for queries
4. All existing tests still pass

---

## Files to Modify

- `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py`
- `/ganuda/vetassist/backend/tests/integration/sprint3/test_sprint3_integration.py`

---

*Cherokee AI Federation - For Seven Generations*
