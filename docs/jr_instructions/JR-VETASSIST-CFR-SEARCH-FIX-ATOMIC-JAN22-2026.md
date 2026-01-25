# JR Instruction: VetAssist CFR Condition Search Fix

**Priority:** P1
**Assigned To:** Software Engineer Jr
**Date:** January 22, 2026

## Problem

The `/api/v1/conditions/map` endpoint returns empty results for "bad knee from running" even though knee conditions exist. The search looks for full phrase matches instead of tokenizing into keywords.

## Solution

Tokenize input and match individual keywords.

---

## Step 1: Add tokenization helper function

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/tokenize_helper.py`:

```python
# VetAssist - Tokenization helper for CFR condition search
# Cherokee AI Federation

# Stopwords to filter from search
STOPWORDS = {'a', 'an', 'the', 'from', 'with', 'and', 'or', 'in', 'on', 'my', 'for', 'to', 'is', 'was', 'been', 'have', 'has', 'had', 'of', 'at', 'by'}

def tokenize_description(description: str) -> list:
    """Extract meaningful search terms from description."""
    words = description.lower().split()
    tokens = [w for w in words if w not in STOPWORDS and len(w) >= 3]
    return tokens if tokens else words[:3]
```

---

## Step 2: Replace map_condition function

**File:** /ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py

**Action:** REPLACE lines 40-114 with the following:

```python
@router.post("/map", response_model=List[ConditionMatch])
def map_condition(request: MappingRequest):
    """Map veteran's description to CFR diagnostic codes."""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            tokens = tokenize_description(request.description)
            if not tokens:
                return []

            # Build WHERE clause matching any token
            where_parts = []
            params = []
            for token in tokens:
                pattern = f"%{token}%"
                where_parts.append("""(
                    LOWER(condition_name) LIKE %s
                    OR EXISTS (SELECT 1 FROM unnest(synonyms) s WHERE LOWER(s) LIKE %s)
                    OR EXISTS (SELECT 1 FROM unnest(common_names) c WHERE LOWER(c) LIKE %s)
                )""")
                params.extend([pattern, pattern, pattern])

            where_sql = " OR ".join(where_parts)

            # Build score calculation
            score_parts = []
            for token in tokens:
                pattern = f"%{token}%"
                score_parts.append("""(
                    CASE WHEN LOWER(condition_name) LIKE %s THEN 0.4 ELSE 0 END +
                    CASE WHEN EXISTS (SELECT 1 FROM unnest(synonyms) s WHERE LOWER(s) LIKE %s) THEN 0.3 ELSE 0 END +
                    CASE WHEN EXISTS (SELECT 1 FROM unnest(common_names) c WHERE LOWER(c) LIKE %s) THEN 0.3 ELSE 0 END
                )""")
                params.extend([pattern, pattern, pattern])

            score_sql = " + ".join(score_parts)

            query = f"""
                SELECT diagnostic_code, condition_name, body_system,
                       rating_criteria, evidence_requirements, dbq_form,
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

---

## Test After Implementation

```bash
curl -X POST "http://localhost:8001/api/v1/conditions/map" \
  -H "Content-Type: application/json" \
  -d '{"description": "bad knee from running"}'
```

Expected: Non-empty array with knee conditions matched.
