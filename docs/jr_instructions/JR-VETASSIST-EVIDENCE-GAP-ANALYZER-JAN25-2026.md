# JR Instruction: VetAssist Evidence Gap Analyzer

**Task ID:** VETASSIST-NEXUS-001
**Priority:** P1
**Type:** backend
**Assigned:** Software Engineer Jr.
**Council Approval:** APPROVED 7-0 (2026-01-25)

---

## Objective

Create an evidence gap analyzer that identifies missing documentation for nexus letters by examining the medical_entities table.

---

## Context

Veterans need complete evidence chains for service connection:
1. **In-service event** (documented incident during military service)
2. **Current diagnosis** (recent medical documentation)
3. **Nexus** (medical opinion linking the two)

Missing any piece weakens or defeats the claim.

---

## Deliverables

### 1. Evidence Gap Analyzer Service

Create `/ganuda/vetassist/backend/app/services/evidence_gap_analyzer.py`:

```python
"""
Evidence Gap Analyzer for VetAssist Nexus Letter Assistant.
Council Approved: 2026-01-25 (7-0)

Analyzes medical_entities to identify missing evidence for service connection.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import date, timedelta
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor


class GapSeverity(Enum):
    CRITICAL = "critical"      # Claim likely to fail without this
    IMPORTANT = "important"    # Significantly weakens claim
    SUGGESTED = "suggested"    # Would strengthen claim


class EvidenceType(Enum):
    IN_SERVICE_EVENT = "in_service_event"
    CURRENT_DIAGNOSIS = "current_diagnosis"
    CONTINUITY_OF_CARE = "continuity_of_care"
    NEXUS_OPINION = "nexus_opinion"
    BUDDY_STATEMENT = "buddy_statement"
    SERVICE_RECORDS = "service_records"


@dataclass
class EvidenceGap:
    gap_type: EvidenceType
    severity: GapSeverity
    description: str
    suggestion: str
    evidence_needed: List[str]


@dataclass
class GapAnalysis:
    session_id: str
    condition_claimed: str
    gaps: List[EvidenceGap]
    completeness_score: float  # 0-1
    nexus_strength: float      # 0-1 likelihood of approval
    has_critical_gaps: bool
    summary: str


# Database configuration
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "vetassist_pii"
}


class EvidenceGapAnalyzer:
    """
    Analyzes medical entities for evidence completeness.

    Uses the medical_entities table to identify:
    1. Missing in-service event documentation
    2. Missing current diagnosis
    3. Gaps in continuity of care
    4. Need for nexus opinion
    """

    def __init__(self):
        self.conn = None

    def _get_connection(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def _get_entities(self, session_id: str) -> List[dict]:
        """Fetch all medical entities for a session."""
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id, entity_type, entity_text, normalized_text,
                    confidence, entity_date, date_precision,
                    service_connection_relevant, military_service_period,
                    linked_entity_id, link_type
                FROM medical_entities
                WHERE session_id = %s
                ORDER BY entity_date ASC NULLS LAST
            """, (session_id,))
            return cur.fetchall()

    def _get_service_dates(self, session_id: str) -> Optional[dict]:
        """Get DD-214 service dates if available."""
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT military_service_period
                FROM medical_entities
                WHERE session_id = %s
                AND military_service_period IS NOT NULL
                LIMIT 1
            """, (session_id,))
            row = cur.fetchone()
            return row if row else None

    def analyze(self, session_id: str, condition_claimed: str) -> GapAnalysis:
        """
        Analyze evidence completeness for a claimed condition.

        Args:
            session_id: VetAssist session UUID
            condition_claimed: The disability condition being claimed

        Returns:
            GapAnalysis with identified gaps and recommendations
        """
        entities = self._get_entities(session_id)
        gaps = []

        # Categorize entities
        service_events = [e for e in entities if e['service_connection_relevant']]
        conditions = [e for e in entities if e['entity_type'] == 'CONDITION']
        current_conditions = [e for e in conditions
                            if e['entity_date'] and e['entity_date'].year >= date.today().year - 1]
        treatments = [e for e in entities if e['entity_type'] in ('PROCEDURE', 'MEDICATION')]

        # Check 1: In-service event documentation
        if not service_events:
            gaps.append(EvidenceGap(
                gap_type=EvidenceType.IN_SERVICE_EVENT,
                severity=GapSeverity.CRITICAL,
                description="No documented in-service event found in your records",
                suggestion="Upload service treatment records (STRs), incident reports, or buddy statements documenting the event during your military service.",
                evidence_needed=[
                    "Service Treatment Records (STRs)",
                    "Line of Duty (LOD) determination",
                    "Incident/accident report",
                    "Buddy/lay statement from fellow service member"
                ]
            ))

        # Check 2: Current diagnosis
        if not current_conditions:
            gaps.append(EvidenceGap(
                gap_type=EvidenceType.CURRENT_DIAGNOSIS,
                severity=GapSeverity.CRITICAL,
                description=f"No recent diagnosis documentation found for {condition_claimed}",
                suggestion="Obtain a current medical evaluation that documents your diagnosis. A Disability Benefits Questionnaire (DBQ) is ideal.",
                evidence_needed=[
                    "Recent medical examination (within 1 year)",
                    "Disability Benefits Questionnaire (DBQ)",
                    "Specialist evaluation report",
                    "Current treatment records"
                ]
            ))

        # Check 3: Continuity of care
        if service_events and current_conditions:
            # Check for treatment gap
            earliest_service = min((e['entity_date'] for e in service_events if e['entity_date']), default=None)
            latest_current = max((e['entity_date'] for e in current_conditions if e['entity_date']), default=None)

            if earliest_service and latest_current:
                years_gap = (latest_current - earliest_service).days / 365

                if years_gap > 5 and len(treatments) < 3:
                    gaps.append(EvidenceGap(
                        gap_type=EvidenceType.CONTINUITY_OF_CARE,
                        severity=GapSeverity.IMPORTANT,
                        description=f"Limited documentation of ongoing treatment over {int(years_gap)} years",
                        suggestion="Provide records showing continuous treatment or explain gaps with lay statements.",
                        evidence_needed=[
                            "Medical records spanning the gap period",
                            "Pharmacy records showing ongoing medication",
                            "Personal statement explaining lack of treatment",
                            "Buddy statements about observed symptoms"
                        ]
                    ))

        # Check 4: Nexus opinion
        # Look for existing nexus-like statements
        nexus_keywords = ['related to', 'caused by', 'result of', 'service-connected', 'at least as likely']
        has_nexus = any(
            any(kw in (e.get('entity_text', '') or '').lower() for kw in nexus_keywords)
            for e in entities
        )

        if not has_nexus and service_events and current_conditions:
            gaps.append(EvidenceGap(
                gap_type=EvidenceType.NEXUS_OPINION,
                severity=GapSeverity.IMPORTANT,
                description="No medical nexus opinion found linking your condition to service",
                suggestion="Obtain a nexus letter from a qualified medical provider stating the connection between your service and current condition.",
                evidence_needed=[
                    "Independent Medical Opinion (IMO)",
                    "Nexus letter from treating physician",
                    "Medical literature supporting connection",
                    "DBQ with nexus opinion section completed"
                ]
            ))

        # Check 5: Service records verification
        service_dates = self._get_service_dates(session_id)
        if not service_dates:
            gaps.append(EvidenceGap(
                gap_type=EvidenceType.SERVICE_RECORDS,
                severity=GapSeverity.SUGGESTED,
                description="Service period not documented in uploaded records",
                suggestion="Upload your DD-214 or other service verification documents.",
                evidence_needed=[
                    "DD-214 (Certificate of Release)",
                    "Service personnel records",
                    "Orders or deployment records"
                ]
            ))

        # Calculate scores
        completeness_score = self._calculate_completeness(gaps, entities)
        nexus_strength = self._calculate_nexus_strength(gaps, entities)
        has_critical = any(g.severity == GapSeverity.CRITICAL for g in gaps)

        # Generate summary
        summary = self._generate_summary(gaps, completeness_score, condition_claimed)

        return GapAnalysis(
            session_id=session_id,
            condition_claimed=condition_claimed,
            gaps=gaps,
            completeness_score=completeness_score,
            nexus_strength=nexus_strength,
            has_critical_gaps=has_critical,
            summary=summary
        )

    def _calculate_completeness(self, gaps: List[EvidenceGap], entities: List[dict]) -> float:
        """Calculate evidence completeness score (0-1)."""
        if not entities:
            return 0.0

        # Deduct points for gaps
        score = 1.0
        for gap in gaps:
            if gap.severity == GapSeverity.CRITICAL:
                score -= 0.3
            elif gap.severity == GapSeverity.IMPORTANT:
                score -= 0.15
            else:
                score -= 0.05

        return max(0.0, min(1.0, score))

    def _calculate_nexus_strength(self, gaps: List[EvidenceGap], entities: List[dict]) -> float:
        """Estimate likelihood of successful service connection (0-1)."""
        # Start with base score
        score = 0.5

        # Critical gaps severely reduce chances
        critical_count = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL)
        score -= critical_count * 0.25

        # Service-connected evidence boosts
        service_relevant = sum(1 for e in entities if e.get('service_connection_relevant'))
        score += min(0.3, service_relevant * 0.1)

        # High confidence entities boost
        high_confidence = sum(1 for e in entities if e.get('confidence', 0) > 0.8)
        score += min(0.2, high_confidence * 0.05)

        return max(0.0, min(1.0, score))

    def _generate_summary(self, gaps: List[EvidenceGap], score: float, condition: str) -> str:
        """Generate human-readable summary."""
        if not gaps:
            return f"Your evidence for {condition} appears complete. Review the nexus letter template to ensure all sections are addressed."

        critical = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        important = [g for g in gaps if g.severity == GapSeverity.IMPORTANT]

        if critical:
            return f"Your claim for {condition} is missing critical evidence: {', '.join(g.gap_type.value for g in critical)}. Address these gaps before submitting."
        elif important:
            return f"Your evidence for {condition} has some important gaps that could weaken your claim. Consider addressing: {', '.join(g.gap_type.value for g in important)}."
        else:
            return f"Your evidence for {condition} is mostly complete with minor suggested improvements."


# API convenience function
def analyze_evidence_gaps(session_id: str, condition_claimed: str) -> dict:
    """
    API-friendly wrapper for evidence gap analysis.

    Returns dict suitable for JSON serialization.
    """
    analyzer = EvidenceGapAnalyzer()
    analysis = analyzer.analyze(session_id, condition_claimed)

    return {
        "session_id": analysis.session_id,
        "condition_claimed": analysis.condition_claimed,
        "completeness_score": round(analysis.completeness_score, 2),
        "nexus_strength": round(analysis.nexus_strength, 2),
        "has_critical_gaps": analysis.has_critical_gaps,
        "summary": analysis.summary,
        "gaps": [
            {
                "type": gap.gap_type.value,
                "severity": gap.severity.value,
                "description": gap.description,
                "suggestion": gap.suggestion,
                "evidence_needed": gap.evidence_needed
            }
            for gap in analysis.gaps
        ]
    }
```

---

## Testing

Create `/ganuda/vetassist/backend/tests/test_evidence_gap_analyzer.py`:

```python
"""Tests for Evidence Gap Analyzer."""

import pytest
from unittest.mock import patch, MagicMock
from app.services.evidence_gap_analyzer import (
    EvidenceGapAnalyzer, GapSeverity, EvidenceType, analyze_evidence_gaps
)


class TestEvidenceGapAnalyzer:

    @patch.object(EvidenceGapAnalyzer, '_get_entities')
    @patch.object(EvidenceGapAnalyzer, '_get_service_dates')
    def test_empty_entities_returns_critical_gaps(self, mock_dates, mock_entities):
        """No entities should return critical gaps for event and diagnosis."""
        mock_entities.return_value = []
        mock_dates.return_value = None

        analyzer = EvidenceGapAnalyzer()
        result = analyzer.analyze("test-session", "PTSD")

        assert result.has_critical_gaps
        assert len([g for g in result.gaps if g.severity == GapSeverity.CRITICAL]) >= 2

    @patch.object(EvidenceGapAnalyzer, '_get_entities')
    @patch.object(EvidenceGapAnalyzer, '_get_service_dates')
    def test_complete_evidence_no_critical_gaps(self, mock_dates, mock_entities):
        """Complete evidence chain should have no critical gaps."""
        from datetime import date

        mock_entities.return_value = [
            {
                'id': 1,
                'entity_type': 'MILITARY_EVENT',
                'entity_text': 'IED explosion exposure',
                'entity_date': date(2015, 6, 15),
                'service_connection_relevant': True,
                'confidence': 0.9
            },
            {
                'id': 2,
                'entity_type': 'CONDITION',
                'entity_text': 'Post-traumatic stress disorder',
                'entity_date': date.today(),
                'service_connection_relevant': True,
                'confidence': 0.95
            }
        ]
        mock_dates.return_value = {'military_service_period': '2014-2018'}

        analyzer = EvidenceGapAnalyzer()
        result = analyzer.analyze("test-session", "PTSD")

        critical_gaps = [g for g in result.gaps if g.severity == GapSeverity.CRITICAL]
        assert len(critical_gaps) == 0
        assert result.completeness_score > 0.5
```

---

## Success Criteria

- [ ] `evidence_gap_analyzer.py` created
- [ ] Connects to vetassist_pii database
- [ ] Detects missing in-service events (critical)
- [ ] Detects missing current diagnosis (critical)
- [ ] Detects continuity gaps (important)
- [ ] Detects missing nexus opinion (important)
- [ ] Calculates completeness score
- [ ] Calculates nexus strength
- [ ] Generates human-readable summary
- [ ] API wrapper function works

---

## Integration Notes

- Uses `medical_entities` table created in P0
- Will be called by nexus letter template generator
- Results displayed in EvidenceGapPanel.tsx (already exists)

---

## For Seven Generations

Every gap we identify helps a veteran strengthen their claim. Every missed gap could cost them benefits they deserve.
