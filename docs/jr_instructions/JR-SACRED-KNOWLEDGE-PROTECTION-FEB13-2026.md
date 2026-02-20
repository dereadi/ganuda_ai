# Jr Instruction: Sacred Knowledge Protection — Auto-Detection System

**Task**: Build automatic detection system for sacred/sensitive content in thermal memories
**Council Vote**: #33e50dc466de520e (RC-2026-02C, Turtle's cultural pick)
**Kanban**: #35
**Priority**: 5
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5

## Context

The thermal_memory_archive has a `sacred_pattern` boolean field. Currently only the TPM manually sets this flag. We need an automatic detection system that:

1. Scans new memories for sacred/sensitive content patterns
2. Flags them with `sacred_pattern = true` (which prevents temperature from cooling below 40)
3. Optionally redacts sensitive content before it reaches external-facing APIs
4. Logs all detections for audit

This protects tribal knowledge, elder wisdom, ceremony details, and culturally sensitive information from accidental exposure through RAG retrieval or bot responses.

## Step 1: Create sacred knowledge detector module

Create `/ganuda/lib/sacred_knowledge_detector.py`

```python
"""
Sacred Knowledge Auto-Detection — Cherokee AI Federation

Scans thermal memories for sacred, ceremonial, culturally sensitive content.
Flags matching memories with sacred_pattern=true to protect from cooling
and optionally redact from external-facing outputs.

Turtle's Seven Generations pick — Council Vote #33e50dc466de520e.
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Pattern categories for sacred content detection
SACRED_PATTERNS = {
    "ceremony": [
        r"\bceremony\b", r"\bceremonial\b", r"\britual\b", r"\bstomp\s*dance\b",
        r"\bgreen\s*corn\b", r"\bgoing\s*to\s*water\b", r"\bsmudg(?:e|ing)\b",
        r"\bsweat\s*lodge\b", r"\bpipe\s*ceremony\b", r"\bsacred\s*fire\b",
        r"\bsun\s*dance\b", r"\bvision\s*quest\b",
    ],
    "medicine": [
        r"\bmedicine\s*(?:man|woman|person|wheel)\b", r"\bhealer\b",
        r"\btraditional\s*medicine\b", r"\bherbal\s*remed(?:y|ies)\b",
        r"\bsacred\s*plant\b", r"\btobacco\s*offering\b",
    ],
    "elder_wisdom": [
        r"\belder\b.*\b(?:said|taught|told|shared|spoke)\b",
        r"\bgrandfather\b.*\b(?:wisdom|story|teaching)\b",
        r"\bgrandmother\b.*\b(?:wisdom|story|teaching)\b",
        r"\boral\s*(?:history|tradition)\b", r"\bpassed\s*down\b",
    ],
    "language": [
        r"\bcherokee\s*(?:language|syllabary|word)\b",
        r"\btsalagi\b", r"\bsequoyah\b",
        r"[\u13A0-\u13F4]",  # Cherokee syllabary Unicode range
    ],
    "clan": [
        r"\bclan\s*(?:mother|father|system|membership)\b",
        r"\bwolf\s*clan\b", r"\bdeer\s*clan\b", r"\bbird\s*clan\b",
        r"\bpaint\s*clan\b", r"\bblue\s*clan\b", r"\blong\s*hair\s*clan\b",
        r"\bwild\s*potato\s*clan\b",
    ],
    "sacred_sites": [
        r"\bsacred\s*(?:site|ground|place|mountain|spring|cave)\b",
        r"\bburial\s*(?:ground|mound|site)\b",
        r"\bancestral\s*(?:land|home|territory)\b",
    ],
    "governance": [
        r"\bblood\s*law\b", r"\bclans?\s*council\b",
        r"\bpeace\s*chief\b.*\bdecision\b",
        r"\bwar\s*chief\b.*\bdecision\b",
    ],
}

# Confidence thresholds
HIGH_CONFIDENCE = 3   # >= 3 pattern matches → auto-flag
MEDIUM_CONFIDENCE = 1  # 1-2 matches → flag for review


def detect_sacred_content(content: str) -> Dict:
    """Scan content for sacred/sensitive patterns.

    Returns:
        Dict with:
            - is_sacred: bool (should flag as sacred_pattern)
            - confidence: HIGH | MEDIUM | NONE
            - categories: list of matched categories
            - match_count: total pattern matches
            - matches: list of (category, pattern) tuples
    """
    content_lower = content.lower()
    matches = []
    categories = set()

    for category, patterns in SACRED_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower):
                matches.append((category, pattern))
                categories.add(category)

    match_count = len(matches)

    if match_count >= HIGH_CONFIDENCE:
        confidence = "HIGH"
        is_sacred = True
    elif match_count >= MEDIUM_CONFIDENCE:
        confidence = "MEDIUM"
        is_sacred = True
    else:
        confidence = "NONE"
        is_sacred = False

    return {
        "is_sacred": is_sacred,
        "confidence": confidence,
        "categories": sorted(categories),
        "match_count": match_count,
        "matches": matches[:10],
    }


def scan_and_flag_memory(memory_hash: str, content: str, conn=None) -> Dict:
    """Scan a memory and flag as sacred if detected.

    Args:
        memory_hash: The memory's hash
        content: The memory content to scan
        conn: Optional existing DB connection

    Returns:
        Detection result dict
    """
    result = detect_sacred_content(content)

    if result["is_sacred"]:
        import psycopg2
        from lib.secrets_loader import get_db_config

        close_conn = False
        if conn is None:
            conn = psycopg2.connect(**get_db_config())
            close_conn = True

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET sacred_pattern = true,
                        metadata = COALESCE(metadata, '{}'::jsonb) ||
                            jsonb_build_object(
                                'sacred_detection', jsonb_build_object(
                                    'confidence', %s,
                                    'categories', %s::jsonb,
                                    'match_count', %s,
                                    'detected_at', NOW()::text
                                )
                            )
                    WHERE memory_hash = %s AND sacred_pattern IS NOT TRUE
                """, (
                    result["confidence"],
                    json.dumps(result["categories"]),
                    result["match_count"],
                    memory_hash,
                ))
            conn.commit()
            if cur.rowcount > 0:
                logger.info("Sacred content detected in %s: %s (%s)",
                           memory_hash[:12], result["categories"], result["confidence"])
        except Exception as e:
            logger.error("Failed to flag sacred memory: %s", e)
            conn.rollback()
        finally:
            if close_conn:
                conn.close()

    return result


def backfill_sacred_scan(batch_size: int = 500) -> Dict:
    """Scan existing memories that haven't been checked for sacred content."""
    import psycopg2
    from lib.secrets_loader import get_db_config

    conn = psycopg2.connect(**get_db_config())
    flagged = 0
    scanned = 0

    try:
        with conn.cursor() as cur:
            # Find memories not yet scanned (no sacred_detection in metadata)
            cur.execute("""
                SELECT memory_hash, original_content
                FROM thermal_memory_archive
                WHERE sacred_pattern IS NOT TRUE
                AND (metadata IS NULL OR NOT metadata ? 'sacred_detection')
                ORDER BY temperature_score DESC
                LIMIT %s
            """, (batch_size,))
            rows = cur.fetchall()

        for memory_hash, content in rows:
            result = scan_and_flag_memory(memory_hash, content, conn)
            scanned += 1
            if result["is_sacred"]:
                flagged += 1

    finally:
        conn.close()

    return {"scanned": scanned, "flagged": flagged, "batch_size": batch_size}


# Need json import for the jsonb building
import json
```

## Manual Steps

Test sacred content detection:

```text
cd /ganuda && python3 -c "
from lib.sacred_knowledge_detector import detect_sacred_content

# Should detect
r1 = detect_sacred_content('The elder taught us about the stomp dance ceremony and going to water')
print(f'Test 1: {r1}')

# Should not detect
r2 = detect_sacred_content('Deployed vLLM service on redfin with Qwen 72B model')
print(f'Test 2: {r2}')
"
```

Run backfill scan on existing memories (hottest first):

```text
cd /ganuda && python3 -c "from lib.sacred_knowledge_detector import backfill_sacred_scan; print(backfill_sacred_scan(1000))"
```

## Success Criteria

- [ ] `detect_sacred_content()` identifies 7 categories of sacred content
- [ ] HIGH confidence (3+ matches) auto-flags without review
- [ ] Detection metadata stored in memory's `metadata` jsonb
- [ ] Sacred memories get `sacred_pattern = true` (never cool below 40)
- [ ] Backfill scans existing memories without duplicating work
- [ ] No false positives on infrastructure/technical memories

---

*For Seven Generations - Cherokee AI Federation*
