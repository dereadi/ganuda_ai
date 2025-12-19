# KB-RES-001: Resonance-Memory Integration

**Category:** AI / Metacognition
**Created:** December 17, 2025
**Author:** TPM with Council Input
**Status:** Implemented (Phase 1)

---

## Summary

Implemented lookup-first architecture for Council deliberations. Recognized patterns skip expensive LLM analysis by matching against stored resonance fingerprints.

## Problem

Every council vote was doing full 7-specialist analysis (~500ms, high token cost) even for questions we'd seen before. No institutional memory of what worked.

## Solution

Three-tier lookup system:
1. **Hot Cache** (in-memory): ~0.1ms - instant recognition
2. **Thermal Memory** (PostgreSQL): ~5ms - indexed lookup
3. **Full Analysis** (LLM): ~500ms - only when needed

### Fingerprint-Based Matching

Each deliberation generates a compact fingerprint:
- Theme hash (security, performance, data, governance, etc.)
- Tone vector (confident, cautious, positive, negative)
- Specialist mask (which specialists involved)
- Confidence band (low/medium/high)
- Question semantic hash

Similar questions → similar fingerprints → cache hits.

## Implementation

### Database Schema (bluefin)

```sql
-- Main patterns table
CREATE TABLE resonance_patterns (
    id SERIAL PRIMARY KEY,
    fingerprint_hash BIGINT NOT NULL UNIQUE,
    theme_hash INTEGER,
    tone_vector SMALLINT[4],
    specialist_mask SMALLINT,
    confidence_band SMALLINT,
    pattern_type VARCHAR(20),  -- 'harmony', 'creative_tension', 'mixed'
    resonance_score REAL,
    temperature REAL DEFAULT 70.0,
    access_count INTEGER DEFAULT 1,
    original_question TEXT,
    ...
);

-- Indexes for fast lookup
CREATE INDEX idx_resonance_fingerprint ON resonance_patterns(fingerprint_hash);
CREATE INDEX idx_resonance_temperature ON resonance_patterns(temperature DESC);
```

### Python Modules (redfin)

**Location:** `/ganuda/lib/metacognition/`

- `resonance_fingerprint.py` - Generates fingerprints without LLM
- `resonance_lookup.py` - Queries thermal memory for matches

### Usage

```python
from metacognition.resonance_lookup import lookup_resonance

result = lookup_resonance(
    question="Should we add caching?",
    specialists=["gecko", "crawdad"],
    confidence=0.85
)

if result["found"]:
    if result["match_type"] == "exact":
        # Skip full analysis - use cached resonance
        return result["resonance_data"]
    else:
        # Fuzzy match - inform deliberation but still analyze
        context = result["original_question"]
```

## Current State

- **28 patterns seeded** from council vote history
- **17 harmony patterns** (high agreement)
- **2 creative tension patterns** (productive disagreement)
- **9 mixed patterns** (multiple concerns)
- **Average resonance score:** 0.78
- **Average temperature:** 89 (hot, frequently accessed)

## Resonance Health View

```sql
SELECT * FROM resonance_health;

   pattern_type   | outcome | count | avg_score | avg_temp
------------------+---------+-------+-----------+----------
 harmony          | unknown |    17 |      0.79 |     89.6
 mixed            | unknown |     9 |      0.75 |     87.4
 creative_tension | unknown |     2 |      0.82 |     90.9
```

## Expected Benefits

After 100+ deliberations:
- **60-70% cache hit rate** expected
- **~400ms saved** per cache hit
- **Token cost reduction** - skip LLM for known patterns
- **Institutional memory** - learn from past decisions

## Future Enhancements

1. **Outcome tracking** - Mark patterns as positive/negative based on results
2. **Anti-pattern detection** - Warn when approaching known-bad patterns
3. **ResonanceLock** - High-confidence patterns skip analysis entirely
4. **Temperature decay** - Cold patterns fade, hot patterns persist

## Related Files

- `/ganuda/docs/jr_instructions/JR_BUILD_RESONANCE_MEMORY_INTEGRATION.md` - Full Jr instructions
- `/ganuda/lib/metacognition/` - Python modules
- `resonance_patterns` table on bluefin

---

*For Seven Generations - Cherokee AI Federation*
*"Once it hits the right resonance, it should be optimal"*
