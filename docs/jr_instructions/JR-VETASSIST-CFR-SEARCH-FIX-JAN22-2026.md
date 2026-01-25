# JR Instruction: VetAssist CFR Condition Search Fix

**Priority:** P1
**Assigned To:** Software Engineer Jr
**Date:** January 22, 2026

## Problem Statement

The `/api/v1/conditions/map` endpoint returns empty results for natural language queries like "bad knee from running" even though knee-related conditions exist in the database. The current SQL query searches for the entire phrase literally instead of tokenizing and matching individual keywords.

## Root Cause

The current implementation in `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py` passes the full description to LIKE clauses:
```sql
WHERE LOWER(condition_name) LIKE '%bad knee from running%'
```

This never matches because no condition name contains that exact phrase.

## Required Fix

Tokenize the input and search for ANY relevant keyword match.

## Implementation Steps

### Step 1: Create tokenization helper

**File:** /ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py

Add after line 23 (after `get_db_conn` function):

```python
# Stopwords to filter from search
STOPWORDS = {'a', 'an', 'the', 'from', 'with', 'and', 'or', 'in', 'on', 'my', 'for', 'to', 'is', 'was', 'been', 'have', 'has', 'had', 'of', 'at', 'by'}

def tokenize_description(description: str) -> list:
    """Extract meaningful search terms from description."""
    words = description.lower().split()
    # Filter stopwords and short words
    tokens = [w for w in words if w not in STOPWORDS and len(w) >= 3]
    return tokens if tokens else words[:3]  # Fallback to first 3 words
```

### Step 2: Replace the search query in map_condition function

Replace lines 46-99 with:

```python
def map_condition(request: MappingRequest):
    """
    Map veteran's description to CFR diagnostic codes.
    Returns matched conditions sorted by relevance.
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Tokenize search terms
            tokens = tokenize_description(request.description)

            if not tokens:
                return []

            # Build dynamic WHERE clause for each token
            where_clauses = []
            params = []

            for token in tokens:
                pattern = f"%{token}%"
                where_clauses.append("""
                    (LOWER(condition_name) LIKE %s
                     OR EXISTS (SELECT 1 FROM unnest(synonyms) s WHERE LOWER(s) LIKE %s)
                     OR EXISTS (SELECT 1 FROM unnest(common_names) c WHERE LOWER(c) LIKE %s))
                """)
                params.extend([pattern, pattern, pattern])

            # Join with OR - match ANY token
            where_sql = " OR ".join(where_clauses)

            # Calculate match score based on number of matching tokens
            score_clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                score_clauses.append(f"""
                    CASE WHEN LOWER(condition_name) LIKE %s THEN 0.4 ELSE 0 END +
                    CASE WHEN EXISTS (SELECT 1 FROM unnest(synonyms) s WHERE LOWER(s) LIKE %s) THEN 0.3 ELSE 0 END +
                    CASE WHEN EXISTS (SELECT 1 FROM unnest(common_names) c WHERE LOWER(c) LIKE %s) THEN 0.3 ELSE 0 END
                """)
                params.extend([pattern, pattern, pattern])

            score_sql = " + ".join(score_clauses)

            query = f"""
                SELECT
                    diagnostic_code,
                    condition_name,
                    body_system,
                    rating_criteria,
                    evidence_requirements,
                    dbq_form,
                    ({score_sql}) as match_score
                FROM vetassist_cfr_conditions
                WHERE {where_sql}
            """

            if request.body_system:
                query += " AND body_system = %s"
                params.append(request.body_system)

            query += " ORDER BY match_score DESC LIMIT 5"

            cur.execute(query, params)
            results = cur.fetchall()

        matches = []
        for r in results:
            if r['match_score'] > 0:
                matches.append(ConditionMatch(
                    diagnostic_code=r['diagnostic_code'],
                    condition_name=r['condition_name'],
                    body_system=r['body_system'],
                    match_score=min(r['match_score'], 1.0),
                    rating_criteria=r['rating_criteria'] or {},
                    evidence_requirements=r['evidence_requirements'] or [],
                    dbq_form=r['dbq_form']
                ))

        return matches

    finally:
        conn.close()
```

## Test Cases

After implementation, these should return results:

```bash
# Should match knee conditions
curl -X POST "http://localhost:8001/api/v1/conditions/map" \
  -H "Content-Type: application/json" \
  -d '{"description": "bad knee from running"}'

# Should match back conditions
curl -X POST "http://localhost:8001/api/v1/conditions/map" \
  -H "Content-Type: application/json" \
  -d '{"description": "my back hurts all the time"}'

# Should match PTSD
curl -X POST "http://localhost:8001/api/v1/conditions/map" \
  -H "Content-Type: application/json" \
  -d '{"description": "nightmares and flashbacks from deployment"}'
```

## Expected Behavior

- "bad knee from running" -> Matches knee conditions (tokens: ["bad", "knee", "running"])
- "my back hurts all the time" -> Matches back conditions (tokens: ["back", "hurts", "time"])
- "nightmares and flashbacks" -> Matches PTSD (tokens: ["nightmares", "flashbacks"])

## Completion Criteria

1. All test queries return non-empty results
2. Match scores reflect relevance (more keyword matches = higher score)
3. Existing single-word queries still work
