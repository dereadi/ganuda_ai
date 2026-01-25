# Jr Instruction: VetAssist CFR Code Auto-Mapping
## Task ID: VetAssist Sprint 3 - Task 2
## Priority: P1
## Estimated Complexity: Medium

---

## Objective

Build a condition-to-CFR-code mapping system. When veterans describe their conditions in plain language, the system suggests matching 38 CFR diagnostic codes with rating criteria.

---

## Background

The VA rates disabilities using 38 CFR Part 4 - Schedule for Rating Disabilities. Each condition has:
- Diagnostic Code (e.g., 5237 for lumbosacral strain)
- Rating Criteria (0%, 10%, 20%, ... 100%)
- Evidence Requirements
- Associated DBQ form

Veterans often describe conditions differently than medical terminology (e.g., "bad back" vs "lumbosacral strain").

---

## Implementation Steps

### Step 1: Create CFR Conditions Database Table

```sql
CREATE TABLE IF NOT EXISTS vetassist_cfr_conditions (
    id SERIAL PRIMARY KEY,
    diagnostic_code VARCHAR(10) UNIQUE NOT NULL,
    condition_name VARCHAR(255) NOT NULL,
    body_system VARCHAR(100),
    synonyms TEXT[],
    common_names TEXT[],
    rating_criteria JSONB,
    evidence_requirements TEXT[],
    dbq_form VARCHAR(50),
    icd10_codes TEXT[],
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cfr_diagnostic_code ON vetassist_cfr_conditions(diagnostic_code);
CREATE INDEX idx_cfr_body_system ON vetassist_cfr_conditions(body_system);
CREATE INDEX idx_cfr_synonyms ON vetassist_cfr_conditions USING GIN(synonyms);
CREATE INDEX idx_cfr_common_names ON vetassist_cfr_conditions USING GIN(common_names);
```

### Step 2: Seed Initial CFR Data

Create `/ganuda/vetassist/backend/scripts/seed_cfr_conditions.py`:

```python
"""
Seed CFR conditions database with common VA disability codes
Cherokee AI Federation
"""
import psycopg2
import json

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

# Common VA disability conditions with CFR codes
CFR_CONDITIONS = [
    # Musculoskeletal - Back
    {
        "diagnostic_code": "5237",
        "condition_name": "Lumbosacral or Cervical Strain",
        "body_system": "Musculoskeletal",
        "synonyms": ["back strain", "neck strain", "spinal strain"],
        "common_names": ["back pain", "bad back", "lower back pain", "neck pain"],
        "rating_criteria": {
            "0": "No symptoms",
            "10": "Forward flexion greater than 60 degrees but not greater than 85 degrees, or combined range of motion greater than 120 degrees but not greater than 235 degrees",
            "20": "Forward flexion greater than 30 degrees but not greater than 60 degrees",
            "40": "Forward flexion 30 degrees or less, or favorable ankylosis",
            "50": "Unfavorable ankylosis of the entire thoracolumbar spine",
            "100": "Unfavorable ankylosis of the entire spine"
        },
        "evidence_requirements": [
            "Current diagnosis from medical provider",
            "Range of motion testing",
            "X-rays or MRI (if available)",
            "Service treatment records showing onset",
            "Nexus letter linking to service"
        ],
        "dbq_form": "DBQ-BACK",
        "icd10_codes": ["M54.5", "M54.2", "S39.012A"]
    },
    {
        "diagnostic_code": "5242",
        "condition_name": "Degenerative Arthritis of the Spine",
        "body_system": "Musculoskeletal",
        "synonyms": ["spinal arthritis", "degenerative disc disease", "DDD"],
        "common_names": ["arthritis in back", "degenerative spine", "disc degeneration"],
        "rating_criteria": {
            "10": "X-ray evidence with occasional incapacitating exacerbations",
            "20": "X-ray evidence with 1 or 2 incapacitating episodes per year requiring bed rest",
            "40": "X-ray evidence with 2 to 4 incapacitating episodes per year",
            "60": "X-ray evidence with 6 or more incapacitating episodes per year"
        },
        "evidence_requirements": [
            "X-ray or MRI showing arthritis",
            "Documentation of incapacitating episodes",
            "Treatment records",
            "Service connection evidence"
        ],
        "dbq_form": "DBQ-BACK",
        "icd10_codes": ["M47.816", "M47.817"]
    },
    # Mental Health - PTSD
    {
        "diagnostic_code": "9411",
        "condition_name": "Post-Traumatic Stress Disorder (PTSD)",
        "body_system": "Mental Disorders",
        "synonyms": ["PTSD", "post traumatic stress"],
        "common_names": ["ptsd", "combat stress", "trauma", "nightmares", "flashbacks"],
        "rating_criteria": {
            "0": "Diagnosed but symptoms not severe enough to interfere with occupational and social functioning",
            "10": "Occupational and social impairment due to mild or transient symptoms",
            "30": "Occasional decrease in work efficiency and intermittent periods of inability to perform occupational tasks",
            "50": "Reduced reliability and productivity due to symptoms like: flattened affect, circumstantial speech, panic attacks more than once a week",
            "70": "Occupational and social impairment with deficiencies in most areas",
            "100": "Total occupational and social impairment"
        },
        "evidence_requirements": [
            "Current PTSD diagnosis from mental health provider",
            "Stressor verification (combat, MST, etc.)",
            "C&P exam or private DBQ",
            "Buddy statements describing symptoms",
            "Treatment records"
        ],
        "dbq_form": "DBQ-MENTAL-DISORDERS",
        "icd10_codes": ["F43.10", "F43.11", "F43.12"]
    },
    # Hearing
    {
        "diagnostic_code": "6260",
        "condition_name": "Tinnitus",
        "body_system": "Auditory",
        "synonyms": ["ringing in ears", "ear ringing"],
        "common_names": ["ringing ears", "buzzing in ears", "tinnitus", "hearing ringing"],
        "rating_criteria": {
            "10": "Recurrent tinnitus (maximum schedular rating)"
        },
        "evidence_requirements": [
            "Current diagnosis",
            "Statement of onset during service",
            "Audiogram",
            "Noise exposure documentation"
        ],
        "dbq_form": "DBQ-EAR",
        "icd10_codes": ["H93.11", "H93.12", "H93.19"]
    },
    {
        "diagnostic_code": "6100",
        "condition_name": "Hearing Loss",
        "body_system": "Auditory",
        "synonyms": ["hearing impairment", "auditory impairment"],
        "common_names": ["hearing loss", "can't hear", "deaf", "hard of hearing"],
        "rating_criteria": {
            "0": "Level I hearing in both ears",
            "10": "Level II-IV hearing combinations",
            "20": "Level IV-V hearing combinations",
            "30": "Level V-VI hearing combinations",
            "40": "Level VI-VII hearing combinations",
            "50": "Level VII-VIII hearing combinations",
            "60": "Level VIII-IX hearing combinations",
            "70": "Level IX-X hearing combinations",
            "80": "Level X-XI hearing combinations",
            "100": "Total deafness in both ears"
        },
        "evidence_requirements": [
            "Audiogram (puretone and speech discrimination)",
            "Service audiograms for comparison",
            "Noise exposure documentation",
            "Medical nexus opinion"
        ],
        "dbq_form": "DBQ-EAR",
        "icd10_codes": ["H90.3", "H91.90"]
    },
    # Knee
    {
        "diagnostic_code": "5260",
        "condition_name": "Limitation of Flexion of the Knee",
        "body_system": "Musculoskeletal",
        "synonyms": ["knee flexion limitation", "knee bending problem"],
        "common_names": ["bad knee", "knee pain", "can't bend knee", "knee injury"],
        "rating_criteria": {
            "0": "Flexion limited to 60 degrees",
            "10": "Flexion limited to 45 degrees",
            "20": "Flexion limited to 30 degrees",
            "30": "Flexion limited to 15 degrees"
        },
        "evidence_requirements": [
            "Range of motion testing",
            "X-rays or MRI",
            "Service treatment records",
            "Nexus opinion"
        ],
        "dbq_form": "DBQ-KNEE",
        "icd10_codes": ["M25.661", "M25.662"]
    },
    # Sleep Apnea
    {
        "diagnostic_code": "6847",
        "condition_name": "Sleep Apnea Syndromes (Obstructive, Central, Mixed)",
        "body_system": "Respiratory",
        "synonyms": ["OSA", "sleep apnea", "obstructive sleep apnea"],
        "common_names": ["sleep apnea", "can't sleep", "stop breathing at night", "cpap"],
        "rating_criteria": {
            "0": "Asymptomatic but with documented disorder",
            "30": "Persistent day-time hypersomnolence",
            "50": "Requires use of breathing assistance device such as CPAP",
            "100": "Chronic respiratory failure with CO2 retention or cor pulmonale, or requires tracheostomy"
        },
        "evidence_requirements": [
            "Sleep study (polysomnography)",
            "CPAP prescription",
            "Service connection evidence",
            "Nexus for secondary conditions"
        ],
        "dbq_form": "DBQ-SLEEP-APNEA",
        "icd10_codes": ["G47.33"]
    },
    # TBI
    {
        "diagnostic_code": "8045",
        "condition_name": "Residuals of Traumatic Brain Injury (TBI)",
        "body_system": "Neurological",
        "synonyms": ["TBI", "traumatic brain injury", "head injury", "concussion"],
        "common_names": ["tbi", "brain injury", "head trauma", "concussion", "brain damage"],
        "rating_criteria": {
            "0": "No residuals",
            "10": "Level 1 impairment in one or more facets",
            "40": "Level 2 impairment in one or more facets",
            "70": "Level 3 impairment in one or more facets",
            "100": "Total impairment requiring constant supervision"
        },
        "evidence_requirements": [
            "TBI diagnosis documentation",
            "Neuropsychological testing",
            "Service records of head injury",
            "Current symptom documentation"
        ],
        "dbq_form": "DBQ-TBI",
        "icd10_codes": ["S06.0X0A", "F07.81"]
    },
    # Migraine
    {
        "diagnostic_code": "8100",
        "condition_name": "Migraine",
        "body_system": "Neurological",
        "synonyms": ["migraines", "migraine headaches"],
        "common_names": ["migraines", "bad headaches", "chronic headaches", "migraine"],
        "rating_criteria": {
            "0": "Less frequent attacks",
            "10": "Characteristic prostrating attacks averaging one in 2 months",
            "30": "Characteristic prostrating attacks averaging once a month",
            "50": "Very frequent completely prostrating and prolonged attacks productive of severe economic inadaptability"
        },
        "evidence_requirements": [
            "Migraine diagnosis",
            "Headache diary/frequency documentation",
            "Treatment records",
            "Work impact documentation"
        ],
        "dbq_form": "DBQ-HEADACHES",
        "icd10_codes": ["G43.909"]
    }
]

def seed_conditions():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for condition in CFR_CONDITIONS:
        cur.execute("""
            INSERT INTO vetassist_cfr_conditions
            (diagnostic_code, condition_name, body_system, synonyms, common_names,
             rating_criteria, evidence_requirements, dbq_form, icd10_codes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (diagnostic_code) DO UPDATE SET
                condition_name = EXCLUDED.condition_name,
                synonyms = EXCLUDED.synonyms,
                common_names = EXCLUDED.common_names,
                rating_criteria = EXCLUDED.rating_criteria,
                evidence_requirements = EXCLUDED.evidence_requirements
        """, (
            condition['diagnostic_code'],
            condition['condition_name'],
            condition['body_system'],
            condition.get('synonyms', []),
            condition.get('common_names', []),
            json.dumps(condition.get('rating_criteria', {})),
            condition.get('evidence_requirements', []),
            condition.get('dbq_form'),
            condition.get('icd10_codes', [])
        ))

    conn.commit()
    print(f"Seeded {len(CFR_CONDITIONS)} conditions")
    cur.close()
    conn.close()

if __name__ == "__main__":
    seed_conditions()
```

Run: `cd /ganuda/vetassist/backend && source venv/bin/activate && python scripts/seed_cfr_conditions.py`

### Step 3: Create Condition Mapping API

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py`:

```python
"""
VetAssist Condition Mapping - CFR Code lookup
Cherokee AI Federation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(tags=["conditions"])

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)


class ConditionMatch(BaseModel):
    diagnostic_code: str
    condition_name: str
    body_system: str
    match_score: float
    rating_criteria: dict
    evidence_requirements: List[str]
    dbq_form: Optional[str]


class MappingRequest(BaseModel):
    description: str
    body_system: Optional[str] = None


@router.post("/map", response_model=List[ConditionMatch])
def map_condition(request: MappingRequest):
    """
    Map veteran's description to CFR diagnostic codes.
    Returns matched conditions sorted by relevance.
    """
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build search query - check synonyms and common names
            search_terms = request.description.lower().split()

            query = """
                SELECT
                    diagnostic_code,
                    condition_name,
                    body_system,
                    rating_criteria,
                    evidence_requirements,
                    dbq_form,
                    -- Calculate match score
                    (
                        CASE WHEN LOWER(condition_name) LIKE %s THEN 1.0 ELSE 0 END +
                        CASE WHEN %s = ANY(LOWER(synonyms::text)::text[]) THEN 0.9 ELSE 0 END +
                        CASE WHEN %s = ANY(LOWER(common_names::text)::text[]) THEN 0.8 ELSE 0 END +
                        CASE WHEN LOWER(condition_name) LIKE %s THEN 0.5 ELSE 0 END
                    ) as match_score
                FROM vetassist_cfr_conditions
                WHERE
                    LOWER(condition_name) LIKE %s
                    OR %s = ANY(synonyms)
                    OR %s = ANY(common_names)
                    OR EXISTS (
                        SELECT 1 FROM unnest(synonyms) s WHERE LOWER(s) LIKE %s
                    )
                    OR EXISTS (
                        SELECT 1 FROM unnest(common_names) c WHERE LOWER(c) LIKE %s
                    )
            """

            params = [
                f"%{request.description.lower()}%",  # exact name match
                request.description.lower(),  # synonym exact
                request.description.lower(),  # common name exact
                f"%{search_terms[0] if search_terms else ''}%",  # partial name
                f"%{request.description.lower()}%",  # WHERE name like
                request.description.lower(),  # WHERE synonym
                request.description.lower(),  # WHERE common name
                f"%{request.description.lower()}%",  # WHERE synonym like
                f"%{request.description.lower()}%",  # WHERE common name like
            ]

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


@router.get("/body-systems")
def list_body_systems():
    """List all body systems in the CFR schedule"""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT body_system FROM vetassist_cfr_conditions
                WHERE body_system IS NOT NULL
                ORDER BY body_system
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


@router.get("/{diagnostic_code}")
def get_condition_details(diagnostic_code: str):
    """Get full details for a specific diagnostic code"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM vetassist_cfr_conditions
                WHERE diagnostic_code = %s
            """, (diagnostic_code,))
            result = cur.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Diagnostic code not found")

        return result
    finally:
        conn.close()
```

### Step 4: Register Router

In `/ganuda/vetassist/backend/app/api/v1/__init__.py`, add:

```python
from .endpoints import conditions
api_router.include_router(conditions.router, prefix="/conditions")
```

---

## Testing

```bash
# Map a condition description
curl -X POST http://localhost:8001/api/v1/conditions/map \
  -H "Content-Type: application/json" \
  -d '{"description": "back pain"}'

# Get body systems
curl http://localhost:8001/api/v1/conditions/body-systems

# Get specific code details
curl http://localhost:8001/api/v1/conditions/5237
```

---

## Acceptance Criteria

1. CFR conditions table created with initial seed data
2. Mapping endpoint returns relevant matches for common descriptions
3. Body system filtering works
4. Rating criteria and evidence requirements returned
5. Search handles synonyms and common names

---

## Peace Chief Concern

Per Council guidance: Veterans can override auto-suggestions. The mapping provides recommendations but does not force categorization. Frontend should allow "other" selection with manual entry.

---

*Cherokee AI Federation - For Seven Generations*
