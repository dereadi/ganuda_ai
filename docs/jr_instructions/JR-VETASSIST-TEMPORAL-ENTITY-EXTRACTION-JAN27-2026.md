# JR Instruction: Temporal Entity Extraction (LLMD Phase 3.1a)

**JR ID:** JR-AI-007
**Priority:** P1 (Deferred - Phase 3)
**Sprint:** VetAssist AI Enhancements Phase 3
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Assigned To:** research_jr
**Effort:** High (broken into phases per Turtle's guidance)

## Problem Statement

Veterans have 10+ years of medical records across multiple VA facilities and civilian providers. Establishing service connection requires mapping symptoms to service dates, which currently requires manual timeline construction.

Research shows LLMD (Language Models for Medical Documents) approaches can automate temporal parsing with high accuracy.

## Council Guidance

**Turtle's 7GEN Concern:** High effort may divert resources. Break into phases for sustainable implementation.

**Approved Phased Approach:**
- Phase 3.1a: Temporal Entity Extraction (THIS JR)
- Phase 3.1b: Service Period Mapping (future JR)
- Phase 3.1c: Continuity Analysis (future JR)

## Required Implementation - Phase 3.1a

### 1. Temporal Entity Schema

ADD migration: `/ganuda/vetassist/backend/migrations/temporal_entities.sql`

```sql
-- Temporal Entity Extraction Schema
-- Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)
-- Phase 3.1a of LLMD implementation

CREATE TABLE IF NOT EXISTS vetassist_temporal_entities (
    id SERIAL PRIMARY KEY,

    -- Session linkage
    session_id UUID NOT NULL,
    document_id VARCHAR(100),

    -- Entity information
    entity_type VARCHAR(50) NOT NULL,  -- 'symptom', 'diagnosis', 'treatment', 'procedure', 'medication', 'event'
    entity_text TEXT NOT NULL,
    normalized_text TEXT,  -- Normalized form (e.g., ICD code description)

    -- Temporal information
    date_mentioned DATE,
    date_range_start DATE,
    date_range_end DATE,
    temporal_expression TEXT,  -- Original expression: "in 2019", "after deployment", etc.
    temporal_precision VARCHAR(20),  -- 'exact', 'month', 'year', 'approximate'

    -- Context
    context_snippet TEXT,  -- Surrounding text (500 chars)
    source_page INT,
    source_location VARCHAR(50),

    -- Extraction metadata
    confidence FLOAT,
    extracted_by VARCHAR(100),
    extracted_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT fk_temporal_session FOREIGN KEY (session_id)
        REFERENCES vetassist_wizard_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_temporal_session ON vetassist_temporal_entities(session_id);
CREATE INDEX idx_temporal_type ON vetassist_temporal_entities(entity_type);
CREATE INDEX idx_temporal_date ON vetassist_temporal_entities(date_mentioned);

COMMENT ON TABLE vetassist_temporal_entities IS 'Extracted temporal entities from medical documents for timeline construction';
```

### 2. Temporal Extraction Service

CREATE: `/ganuda/vetassist/backend/app/services/temporal_parser.py`

```python
"""
Temporal Entity Extraction for VetAssist.
Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)

Phase 3.1a of LLMD-inspired temporal parsing implementation.
Extracts dates, symptoms, diagnoses from medical records and stores as structured timeline.
"""

import logging
import re
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json
import httpx
import os

logger = logging.getLogger(__name__)


@dataclass
class TemporalEntity:
    """A temporal entity extracted from medical text."""
    entity_type: str  # symptom, diagnosis, treatment, procedure, medication, event
    entity_text: str
    normalized_text: Optional[str] = None
    date_mentioned: Optional[date] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    temporal_expression: Optional[str] = None
    temporal_precision: str = "approximate"  # exact, month, year, approximate
    context_snippet: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 0.0


class TemporalParser:
    """
    Extracts temporal entities from medical documents.

    Uses a combination of:
    1. LLM extraction for complex temporal reasoning
    2. Regex patterns for date normalization
    3. Heuristics for relative date resolution
    """

    # Patterns for date extraction
    DATE_PATTERNS = [
        # MM/DD/YYYY, MM-DD-YYYY
        (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'exact'),
        # YYYY-MM-DD (ISO)
        (r'\b(\d{4})-(\d{2})-(\d{2})\b', 'exact'),
        # Month DD, YYYY
        (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b', 'exact'),
        # Month YYYY
        (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', 'month'),
        # YYYY only
        (r'\b(19|20)\d{2}\b', 'year'),
    ]

    EXTRACTION_PROMPT = '''Extract all medical events with dates from this text.
For each event, identify:
1. entity_type: symptom, diagnosis, treatment, procedure, medication, or event
2. entity_text: the exact text describing the entity
3. temporal_expression: any date or time reference
4. confidence: 0.0-1.0

Return as JSON array:
[
  {
    "entity_type": "diagnosis",
    "entity_text": "PTSD",
    "temporal_expression": "diagnosed in 2019",
    "confidence": 0.9
  }
]

Medical Text:
{text}

JSON Output:'''

    def __init__(self):
        self.api_url = os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        self.model = os.getenv("VLLM_MODEL", "/ganuda/models/qwen2.5-coder-32b-awq")

    async def extract_entities(
        self,
        text: str,
        reference_date: Optional[date] = None,
        document_id: Optional[str] = None
    ) -> List[TemporalEntity]:
        """
        Extract temporal entities from medical text.

        Args:
            text: Medical document text
            reference_date: Reference date for resolving relative expressions
            document_id: Source document identifier

        Returns:
            List of extracted TemporalEntity objects
        """
        logger.info(f"[TemporalParser] Extracting entities from {len(text)} chars")

        # Use LLM for entity extraction
        raw_entities = await self._llm_extract(text)

        # Resolve temporal expressions to dates
        entities = []
        for raw in raw_entities:
            entity = self._resolve_temporal(raw, reference_date)
            if entity:
                entity.context_snippet = self._get_context(text, raw.get("entity_text", ""))
                entities.append(entity)

        logger.info(f"[TemporalParser] Extracted {len(entities)} temporal entities")
        return entities

    async def _llm_extract(self, text: str) -> List[Dict]:
        """Use LLM to extract entities from text."""
        # Chunk text if too long
        max_chunk = 4000
        if len(text) > max_chunk:
            text = text[:max_chunk]

        prompt = self.EXTRACTION_PROMPT.format(text=text)

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500,
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            result = response.json()

        content = result["choices"][0]["message"]["content"]
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> List[Dict]:
        """Extract JSON from LLM response."""
        try:
            # Find JSON array in response
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                content = content[start:end].strip()
            elif "[" in content:
                start = content.index("[")
                end = content.rindex("]") + 1
                content = content[start:end]

            return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[TemporalParser] JSON parse error: {e}")
            return []

    def _resolve_temporal(
        self,
        raw_entity: Dict,
        reference_date: Optional[date]
    ) -> Optional[TemporalEntity]:
        """Resolve temporal expressions to actual dates."""
        temporal_expr = raw_entity.get("temporal_expression", "")
        entity_text = raw_entity.get("entity_text", "")

        if not entity_text:
            return None

        entity = TemporalEntity(
            entity_type=raw_entity.get("entity_type", "event"),
            entity_text=entity_text,
            temporal_expression=temporal_expr,
            confidence=raw_entity.get("confidence", 0.5)
        )

        # Try to extract date from temporal expression
        if temporal_expr:
            extracted_date, precision = self._extract_date(temporal_expr, reference_date)
            entity.date_mentioned = extracted_date
            entity.temporal_precision = precision

        return entity

    def _extract_date(
        self,
        expression: str,
        reference_date: Optional[date]
    ) -> Tuple[Optional[date], str]:
        """Extract a date from a temporal expression."""
        expression = expression.lower()

        # Try regex patterns
        for pattern, precision in self.DATE_PATTERNS:
            match = re.search(pattern, expression, re.IGNORECASE)
            if match:
                try:
                    return self._parse_match(match, precision), precision
                except ValueError:
                    continue

        # Handle relative expressions
        if reference_date:
            if "last year" in expression:
                return date(reference_date.year - 1, 1, 1), "year"
            if "this year" in expression:
                return date(reference_date.year, 1, 1), "year"

        return None, "approximate"

    def _parse_match(self, match, precision: str) -> date:
        """Parse a regex match into a date object."""
        groups = match.groups()

        if precision == "exact" and len(groups) == 3:
            # Handle different formats
            if groups[0].isdigit() and len(groups[0]) == 4:
                # YYYY-MM-DD
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            elif groups[0].isdigit():
                # MM/DD/YYYY
                return date(int(groups[2]), int(groups[0]), int(groups[1]))
            else:
                # Month DD, YYYY
                month_map = {
                    "january": 1, "february": 2, "march": 3, "april": 4,
                    "may": 5, "june": 6, "july": 7, "august": 8,
                    "september": 9, "october": 10, "november": 11, "december": 12
                }
                month = month_map.get(groups[0].lower(), 1)
                return date(int(groups[2]), month, int(groups[1]))

        elif precision == "month" and len(groups) == 2:
            month_map = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12
            }
            month = month_map.get(groups[0].lower(), 1)
            return date(int(groups[1]), month, 1)

        elif precision == "year":
            year = int(match.group())
            return date(year, 1, 1)

        raise ValueError("Could not parse date")

    def _get_context(self, full_text: str, entity_text: str, window: int = 250) -> str:
        """Get surrounding context for an entity."""
        idx = full_text.lower().find(entity_text.lower())
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(full_text), idx + len(entity_text) + window)
        return full_text[start:end]


class TemporalEntityStore:
    """Persistence layer for temporal entities."""

    def __init__(self):
        from app.core.database_config import get_db_connection
        self.get_connection = get_db_connection

    def save_entities(
        self,
        session_id: str,
        entities: List[TemporalEntity],
        document_id: Optional[str] = None
    ) -> int:
        """Save extracted entities to database."""
        conn = self.get_connection()
        saved = 0

        try:
            with conn.cursor() as cur:
                for entity in entities:
                    cur.execute("""
                        INSERT INTO vetassist_temporal_entities (
                            session_id, document_id, entity_type, entity_text,
                            normalized_text, date_mentioned, date_range_start,
                            date_range_end, temporal_expression, temporal_precision,
                            context_snippet, confidence, extracted_by
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        session_id,
                        document_id,
                        entity.entity_type,
                        entity.entity_text,
                        entity.normalized_text,
                        entity.date_mentioned,
                        entity.date_range_start,
                        entity.date_range_end,
                        entity.temporal_expression,
                        entity.temporal_precision,
                        entity.context_snippet,
                        entity.confidence,
                        "temporal_parser_v1"
                    ))
                    saved += 1

                conn.commit()

        finally:
            conn.close()

        logger.info(f"[TemporalEntityStore] Saved {saved} entities for session {session_id}")
        return saved

    def get_timeline(self, session_id: str) -> List[Dict]:
        """Get all temporal entities for a session as timeline."""
        conn = self.get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM vetassist_temporal_entities
                    WHERE session_id = %s
                    ORDER BY COALESCE(date_mentioned, date_range_start, '1900-01-01')
                """, (session_id,))

                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

        finally:
            conn.close()
```

## Verification

```bash
cd /ganuda/vetassist/backend

# 1. Apply migration
psql -h 192.168.132.222 -U claude -d zammad_production -f migrations/temporal_entities.sql

# 2. Test parser import
python3 -c "
from app.services.temporal_parser import TemporalParser, TemporalEntity, TemporalEntityStore
print('✓ TemporalParser imported')

parser = TemporalParser()
print(f'✓ Parser initialized with {len(parser.DATE_PATTERNS)} date patterns')

store = TemporalEntityStore()
print('✓ TemporalEntityStore initialized')
"

# 3. Test date extraction
python3 -c "
from app.services.temporal_parser import TemporalParser
from datetime import date

parser = TemporalParser()

# Test various date formats
test_expressions = [
    '01/15/2020',
    '2019-03-22',
    'March 2018',
    'diagnosed in 2019',
]

for expr in test_expressions:
    extracted, precision = parser._extract_date(expr, date.today())
    print(f'  \"{expr}\" -> {extracted} ({precision})')
"
```

## Future Phases (Not This JR)

**Phase 3.1b - Service Period Mapping:**
- Map extracted events to DD-214 service dates
- Classify as IN_SERVICE, POST_SERVICE_1YR, POST_SERVICE

**Phase 3.1c - Continuity Analysis:**
- Identify treatment gaps
- Flag chronic vs acute conditions
- Generate service-connection strength score

---

FOR SEVEN GENERATIONS
