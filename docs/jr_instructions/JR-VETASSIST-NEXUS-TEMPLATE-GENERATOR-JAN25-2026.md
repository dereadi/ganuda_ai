# JR Instruction: VetAssist Nexus Template Generator

**Task ID:** VETASSIST-NEXUS-002
**Priority:** P2
**Type:** backend
**Assigned:** Software Engineer Jr.
**Council Approval:** APPROVED 7-0 (2026-01-25)

---

## Objective

Create a nexus letter template generator that populates templates from medical entities and veteran profile data.

---

## Context

A nexus letter connects:
1. In-service event → Current condition
2. Must include "at least as likely as not" language
3. Requires medical provider signature

**We generate templates, NOT medical opinions.**

---

## Deliverables

### 1. Nexus Template Generator Service

Create `/ganuda/vetassist/backend/app/services/nexus_template_generator.py`:

```python
"""
Nexus Letter Template Generator for VetAssist.
Council Approved: 2026-01-25 (7-0)

IMPORTANT: This generates TEMPLATES for medical providers to review and sign.
We do NOT generate medical opinions - that requires a licensed provider.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
import json


@dataclass
class ServiceEvent:
    date: date
    description: str
    documentation: str
    confidence: float


@dataclass
class NexusTemplate:
    # Header
    veteran_name: str
    claimed_condition: str
    generated_date: date

    # Section 1: Service History
    service_dates: str  # e.g., "June 2014 - December 2018"
    duty_stations: List[str]
    mos_duties: str

    # Section 2: In-Service Events
    service_events: List[ServiceEvent]

    # Section 3: Current Condition
    current_diagnosis: str
    symptoms: List[str]
    functional_limitations: List[str]

    # Section 4: Suggested Rationale Points
    rationale_points: List[str]

    # Metadata
    completeness_score: float
    gaps_identified: List[str]

    # Disclaimers
    disclaimer: str = field(default="""
IMPORTANT DISCLAIMER:
This is a TEMPLATE to assist medical providers in writing a nexus letter.
This document does NOT constitute a medical opinion.
A licensed medical provider must review all evidence, conduct an examination
if appropriate, and provide their independent medical opinion.

The veteran should present this template to their treating physician or
obtain an Independent Medical Opinion (IMO) from a qualified provider.
""")


# Database configuration
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "vetassist_pii"
}


class NexusTemplateGenerator:
    """
    Generates nexus letter templates from medical entities.

    CRITICAL: We generate templates, not medical opinions.
    A licensed provider must sign the final letter.
    """

    def __init__(self):
        self.conn = None

    def _get_connection(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def _get_entities(self, session_id: str) -> List[dict]:
        """Fetch medical entities for session."""
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM medical_entities
                WHERE session_id = %s
                ORDER BY entity_date ASC NULLS LAST
            """, (session_id,))
            return cur.fetchall()

    def _get_timeline(self, session_id: str) -> Optional[dict]:
        """Fetch service connection timeline if exists."""
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM service_connection_timeline
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))
            return cur.fetchone()

    def generate(
        self,
        session_id: str,
        veteran_name: str,
        claimed_condition: str,
        service_dates: str,
        mos_duties: str = "",
        symptoms: List[str] = None,
        functional_limitations: List[str] = None
    ) -> NexusTemplate:
        """
        Generate a nexus letter template.

        Args:
            session_id: VetAssist session UUID
            veteran_name: Veteran's full name
            claimed_condition: The disability being claimed
            service_dates: Service period string (e.g., "2014-2018")
            mos_duties: Military occupational specialty and duties
            symptoms: Current symptoms reported by veteran
            functional_limitations: How condition affects daily life

        Returns:
            NexusTemplate ready for display/export
        """
        entities = self._get_entities(session_id)
        timeline = self._get_timeline(session_id)

        # Extract service events
        service_events = self._extract_service_events(entities)

        # Extract current diagnosis info
        current_dx = self._extract_current_diagnosis(entities, claimed_condition)

        # Extract duty stations from entities
        duty_stations = self._extract_duty_stations(entities)

        # Generate rationale points
        rationale_points = self._generate_rationale_points(
            service_events, current_dx, claimed_condition
        )

        # Identify gaps
        gaps = self._identify_gaps(service_events, current_dx)

        # Calculate completeness
        completeness = self._calculate_completeness(service_events, current_dx, gaps)

        return NexusTemplate(
            veteran_name=veteran_name,
            claimed_condition=claimed_condition,
            generated_date=date.today(),
            service_dates=service_dates,
            duty_stations=duty_stations,
            mos_duties=mos_duties,
            service_events=service_events,
            current_diagnosis=current_dx.get('diagnosis', claimed_condition),
            symptoms=symptoms or [],
            functional_limitations=functional_limitations or [],
            rationale_points=rationale_points,
            completeness_score=completeness,
            gaps_identified=gaps
        )

    def _extract_service_events(self, entities: List[dict]) -> List[ServiceEvent]:
        """Extract in-service events from entities."""
        events = []
        for e in entities:
            if e.get('service_connection_relevant'):
                events.append(ServiceEvent(
                    date=e.get('entity_date'),
                    description=e.get('entity_text', ''),
                    documentation=f"Document ID: {e.get('document_id', 'N/A')}",
                    confidence=e.get('confidence', 0.5)
                ))
        return events

    def _extract_current_diagnosis(self, entities: List[dict], condition: str) -> dict:
        """Extract current diagnosis information."""
        current_year = date.today().year

        for e in entities:
            if e.get('entity_type') == 'CONDITION':
                entity_date = e.get('entity_date')
                if entity_date and entity_date.year >= current_year - 1:
                    return {
                        'diagnosis': e.get('normalized_text') or e.get('entity_text'),
                        'date': entity_date,
                        'confidence': e.get('confidence', 0.5)
                    }

        return {'diagnosis': condition, 'date': None, 'confidence': 0.0}

    def _extract_duty_stations(self, entities: List[dict]) -> List[str]:
        """Extract duty stations/locations."""
        stations = []
        for e in entities:
            if e.get('entity_type') == 'PROVIDER':
                text = e.get('entity_text', '')
                if any(kw in text.lower() for kw in ['base', 'camp', 'fort', 'station']):
                    stations.append(text)
        return list(set(stations))[:5]  # Dedupe and limit

    def _generate_rationale_points(
        self,
        events: List[ServiceEvent],
        current_dx: dict,
        condition: str
    ) -> List[str]:
        """Generate suggested rationale points for the medical provider."""
        points = []

        if events:
            points.append(
                f"Service treatment records document {len(events)} relevant "
                f"event(s) during active duty service."
            )

            # Temporal proximity
            if events and current_dx.get('date'):
                first_event = min(e.date for e in events if e.date)
                years_diff = (current_dx['date'] - first_event).days / 365
                if years_diff > 0:
                    points.append(
                        f"The veteran's current {condition} diagnosis occurred "
                        f"approximately {int(years_diff)} years after the documented "
                        f"in-service event(s), consistent with the natural progression "
                        f"of this condition."
                    )

        # Standard nexus language suggestion
        points.append(
            f"Based on the documented in-service event(s) and current diagnosis, "
            f"it is at least as likely as not (50% or greater probability) that "
            f"the veteran's {condition} is related to their military service."
        )

        # No intervening cause
        points.append(
            "Review of available records does not reveal any significant "
            "intervening cause or injury that would better explain the "
            "veteran's current condition."
        )

        return points

    def _identify_gaps(self, events: List[ServiceEvent], current_dx: dict) -> List[str]:
        """Identify documentation gaps."""
        gaps = []

        if not events:
            gaps.append("No in-service events documented - STRs or buddy statements needed")

        if not current_dx.get('date'):
            gaps.append("No recent diagnosis documentation - current medical evaluation needed")

        if events and current_dx.get('date'):
            # Check for treatment continuity
            first_event = min((e.date for e in events if e.date), default=None)
            if first_event:
                years_gap = (current_dx['date'] - first_event).days / 365
                if years_gap > 10:
                    gaps.append(
                        f"Large gap ({int(years_gap)} years) between service and "
                        f"current diagnosis - continuity evidence would strengthen claim"
                    )

        return gaps

    def _calculate_completeness(
        self,
        events: List[ServiceEvent],
        current_dx: dict,
        gaps: List[str]
    ) -> float:
        """Calculate template completeness score."""
        score = 0.5  # Base score

        if events:
            score += 0.2
            if any(e.confidence > 0.8 for e in events):
                score += 0.1

        if current_dx.get('date'):
            score += 0.2

        # Deduct for gaps
        score -= len(gaps) * 0.1

        return max(0.0, min(1.0, score))

    def to_markdown(self, template: NexusTemplate) -> str:
        """Convert template to markdown format."""
        md = []

        md.append("# NEXUS LETTER TEMPLATE\n")
        md.append(template.disclaimer)
        md.append("\n---\n")

        md.append(f"**Veteran:** {template.veteran_name}\n")
        md.append(f"**Claimed Condition:** {template.claimed_condition}\n")
        md.append(f"**Date Generated:** {template.generated_date}\n")
        md.append(f"**Template Completeness:** {template.completeness_score:.0%}\n\n")

        md.append("## Section 1: Service History\n")
        md.append(f"**Service Period:** {template.service_dates}\n")
        if template.duty_stations:
            md.append(f"**Duty Stations:** {', '.join(template.duty_stations)}\n")
        if template.mos_duties:
            md.append(f"**MOS/Duties:** {template.mos_duties}\n")
        md.append("\n")

        md.append("## Section 2: In-Service Events\n")
        if template.service_events:
            for event in template.service_events:
                date_str = event.date.strftime('%Y-%m-%d') if event.date else 'Date unknown'
                md.append(f"- **{date_str}:** {event.description}\n")
                md.append(f"  - Source: {event.documentation}\n")
        else:
            md.append("*No in-service events documented. See gaps below.*\n")
        md.append("\n")

        md.append("## Section 3: Current Condition\n")
        md.append(f"**Diagnosis:** {template.current_diagnosis}\n")
        if template.symptoms:
            md.append("**Current Symptoms:**\n")
            for symptom in template.symptoms:
                md.append(f"- {symptom}\n")
        if template.functional_limitations:
            md.append("**Functional Limitations:**\n")
            for limitation in template.functional_limitations:
                md.append(f"- {limitation}\n")
        md.append("\n")

        md.append("## Section 4: Medical Opinion (FOR PROVIDER TO COMPLETE)\n")
        md.append("*The following section must be completed by a licensed medical provider:*\n\n")
        md.append('> "Based on my review of the veteran\'s medical records and ')
        md.append('examination, it is my medical opinion that ')
        md.append(f'**[{template.claimed_condition}]** ')
        md.append('is at least as likely as not (50% or greater probability) ')
        md.append('caused by or related to ')
        md.append('**[IN-SERVICE EVENT - see Section 2]**."\n\n')

        md.append("## Section 5: Suggested Rationale Points\n")
        md.append("*Consider including these points in your medical rationale:*\n\n")
        for point in template.rationale_points:
            md.append(f"- {point}\n")
        md.append("\n")

        if template.gaps_identified:
            md.append("## Evidence Gaps Identified\n")
            md.append("*The following gaps may weaken the claim:*\n\n")
            for gap in template.gaps_identified:
                md.append(f"- ⚠️ {gap}\n")
            md.append("\n")

        md.append("## Signature Block\n")
        md.append("Provider Name: _________________________\n\n")
        md.append("License/Credentials: _________________________\n\n")
        md.append("Signature: _________________________\n\n")
        md.append("Date: _________________________\n")

        return ''.join(md)


# API convenience function
def generate_nexus_template(
    session_id: str,
    veteran_name: str,
    claimed_condition: str,
    service_dates: str,
    **kwargs
) -> dict:
    """
    API-friendly wrapper for nexus template generation.

    Returns dict with template data and markdown.
    """
    generator = NexusTemplateGenerator()
    template = generator.generate(
        session_id=session_id,
        veteran_name=veteran_name,
        claimed_condition=claimed_condition,
        service_dates=service_dates,
        **kwargs
    )

    return {
        "veteran_name": template.veteran_name,
        "claimed_condition": template.claimed_condition,
        "completeness_score": round(template.completeness_score, 2),
        "gaps_identified": template.gaps_identified,
        "service_events_count": len(template.service_events),
        "rationale_points": template.rationale_points,
        "markdown": generator.to_markdown(template),
        "disclaimer": template.disclaimer.strip()
    }
```

---

## Success Criteria

- [ ] `nexus_template_generator.py` created
- [ ] Extracts service events from medical_entities
- [ ] Generates rationale points
- [ ] Identifies documentation gaps
- [ ] Produces markdown output
- [ ] Includes prominent disclaimer
- [ ] API wrapper function works

---

## Critical Safety Note

**We generate TEMPLATES, not medical opinions.**

The disclaimer must be prominent and clear that:
1. This is not a medical opinion
2. A licensed provider must review and sign
3. The veteran should seek professional help

---

## For Seven Generations

A well-prepared nexus letter can be the difference between approval and denial. We give veterans the template; their doctors provide the medical judgment.
