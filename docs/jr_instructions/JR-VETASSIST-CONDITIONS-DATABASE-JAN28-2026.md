# JR Instruction: VetAssist Conditions Database

**JR ID:** JR-VETASSIST-CONDITIONS-DATABASE-JAN28-2026
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Depends On:** Existing VetAssist backend
**Ultrathink:** ULTRATHINK-VETASSIST-SPRINT3-LLMD-AMEM-JAN24-2026.md

---

## Objective

Create the conditions database from CFR 38 (800+ conditions) with service-connection requirements to power the claim wizard condition selection step.

---

## Files to Create/Modify

| File | Description |
|------|-------------|
| `/ganuda/vetassist/backend/app/models/conditions.py` | SQLAlchemy model for conditions |
| `/ganuda/vetassist/backend/app/api/v1/conditions.py` | REST endpoints |
| `/ganuda/vetassist/backend/data/cfr38_conditions.json` | Seed data |
| `/ganuda/vetassist/database/migrations/002_conditions.sql` | DB migration |

---

## Database Schema

Create migration `/ganuda/vetassist/database/migrations/002_conditions.sql`:

```sql
-- Conditions table from CFR 38
CREATE TABLE IF NOT EXISTS conditions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,  -- CFR code like "7100"
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,  -- "mental_health", "musculoskeletal", etc.
    subcategory VARCHAR(100),

    -- Rating criteria
    min_rating INTEGER DEFAULT 0,
    max_rating INTEGER DEFAULT 100,
    rating_criteria JSONB,  -- {10: "criteria", 30: "criteria", ...}

    -- Service connection requirements
    nexus_required BOOLEAN DEFAULT true,
    presumptive_conditions JSONB,  -- {"agent_orange": true, "gulf_war": false, ...}
    in_service_events TEXT[],  -- ["noise_exposure", "combat", "TBI"]

    -- Evidence requirements
    required_evidence JSONB,  -- {"current_diagnosis": true, "in_service_treatment": false, ...}
    supporting_evidence JSONB,  -- Nice to have evidence

    -- Metadata
    cfr_section VARCHAR(20),
    common_names TEXT[],  -- Alternative names for search
    search_keywords TEXT[],

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Category lookup
CREATE TABLE IF NOT EXISTS condition_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0
);

-- Seed categories
INSERT INTO condition_categories (code, name, description, icon, sort_order) VALUES
('mental_health', 'Mental Health', 'PTSD, depression, anxiety, etc.', 'brain', 1),
('musculoskeletal', 'Musculoskeletal', 'Back, joints, bones', 'bone', 2),
('hearing', 'Hearing', 'Tinnitus, hearing loss', 'ear', 3),
('respiratory', 'Respiratory', 'Lungs, breathing conditions', 'lungs', 4),
('cardiovascular', 'Cardiovascular', 'Heart, blood vessels', 'heart', 5),
('neurological', 'Neurological', 'TBI, nerve damage', 'brain', 6),
('digestive', 'Digestive', 'GI conditions', 'stomach', 7),
('skin', 'Skin', 'Dermatological conditions', 'shield', 8),
('endocrine', 'Endocrine', 'Diabetes, thyroid', 'flask', 9),
('other', 'Other', 'Other conditions', 'file', 100)
ON CONFLICT (code) DO NOTHING;

-- Indexes for search
CREATE INDEX idx_conditions_name ON conditions USING gin(to_tsvector('english', name));
CREATE INDEX idx_conditions_category ON conditions(category);
CREATE INDEX idx_conditions_search ON conditions USING gin(search_keywords);
```

---

## Model

Create `/ganuda/vetassist/backend/app/models/conditions.py`:

```python
"""
VA Disability Conditions from CFR 38
"""

from sqlalchemy import Column, Integer, String, Boolean, ARRAY, Text
from sqlalchemy.dialects.postgresql import JSONB
from ..db.base import Base

class Condition(Base):
    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))

    min_rating = Column(Integer, default=0)
    max_rating = Column(Integer, default=100)
    rating_criteria = Column(JSONB)

    nexus_required = Column(Boolean, default=True)
    presumptive_conditions = Column(JSONB)
    in_service_events = Column(ARRAY(Text))

    required_evidence = Column(JSONB)
    supporting_evidence = Column(JSONB)

    cfr_section = Column(String(20))
    common_names = Column(ARRAY(Text))
    search_keywords = Column(ARRAY(Text))


class ConditionCategory(Base):
    __tablename__ = "condition_categories"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
```

---

## API Endpoints

Create `/ganuda/vetassist/backend/app/api/v1/conditions.py`:

```python
"""
Conditions API endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from ...db.base import get_db
from ...models.conditions import Condition, ConditionCategory
from pydantic import BaseModel

router = APIRouter(prefix="/conditions", tags=["conditions"])


class ConditionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    subcategory: Optional[str]
    min_rating: int
    max_rating: int
    nexus_required: bool
    common_names: Optional[List[str]]

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    code: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    condition_count: int


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """Get all condition categories with counts."""
    categories = db.query(
        ConditionCategory,
        func.count(Condition.id).label('condition_count')
    ).outerjoin(
        Condition, Condition.category == ConditionCategory.code
    ).group_by(
        ConditionCategory.id
    ).order_by(
        ConditionCategory.sort_order
    ).all()

    return [
        CategoryResponse(
            code=cat.ConditionCategory.code,
            name=cat.ConditionCategory.name,
            description=cat.ConditionCategory.description,
            icon=cat.ConditionCategory.icon,
            condition_count=cat.condition_count
        )
        for cat in categories
    ]


@router.get("/search", response_model=List[ConditionResponse])
async def search_conditions(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Search conditions by name or keywords."""
    query = db.query(Condition)

    # Full-text search
    search_filter = func.to_tsvector('english', Condition.name).match(
        func.plainto_tsquery('english', q)
    ) | Condition.common_names.contains([q.lower()])

    query = query.filter(search_filter)

    if category:
        query = query.filter(Condition.category == category)

    conditions = query.limit(limit).all()
    return conditions


@router.get("/{condition_id}", response_model=ConditionResponse)
async def get_condition(
    condition_id: int,
    db: Session = Depends(get_db)
):
    """Get condition details by ID."""
    condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    return condition


@router.get("/{condition_id}/evidence")
async def get_evidence_requirements(
    condition_id: int,
    db: Session = Depends(get_db)
):
    """Get evidence requirements for a condition."""
    condition = db.query(Condition).filter(Condition.id == condition_id).first()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")

    return {
        "condition_id": condition.id,
        "condition_name": condition.name,
        "nexus_required": condition.nexus_required,
        "required_evidence": condition.required_evidence or {},
        "supporting_evidence": condition.supporting_evidence or {},
        "presumptive_conditions": condition.presumptive_conditions or {},
        "in_service_events": condition.in_service_events or []
    }
```

---

## Seed Data (Top 20 Common Conditions)

Create `/ganuda/vetassist/backend/data/cfr38_conditions_seed.json`:

```json
[
  {
    "code": "9411",
    "name": "Post-Traumatic Stress Disorder (PTSD)",
    "category": "mental_health",
    "subcategory": "trauma",
    "min_rating": 0,
    "max_rating": 100,
    "nexus_required": true,
    "in_service_events": ["combat", "military_sexual_trauma", "accident", "witness_death"],
    "required_evidence": {
      "current_diagnosis": true,
      "stressor_verification": true,
      "nexus_opinion": true
    },
    "common_names": ["ptsd", "post traumatic stress", "combat stress"],
    "search_keywords": ["ptsd", "trauma", "nightmares", "anxiety", "combat", "mst"]
  },
  {
    "code": "6260",
    "name": "Tinnitus",
    "category": "hearing",
    "subcategory": "hearing_loss",
    "min_rating": 0,
    "max_rating": 10,
    "nexus_required": true,
    "in_service_events": ["noise_exposure", "artillery", "aircraft", "combat"],
    "required_evidence": {
      "current_diagnosis": true,
      "audiogram": true,
      "nexus_opinion": true
    },
    "common_names": ["ringing in ears", "ear ringing"],
    "search_keywords": ["tinnitus", "ringing", "ears", "hearing", "noise"]
  },
  {
    "code": "5237",
    "name": "Lumbosacral Strain",
    "category": "musculoskeletal",
    "subcategory": "spine",
    "min_rating": 0,
    "max_rating": 100,
    "nexus_required": true,
    "in_service_events": ["heavy_lifting", "injury", "jump", "vehicle_accident"],
    "required_evidence": {
      "current_diagnosis": true,
      "imaging": true,
      "range_of_motion": true
    },
    "common_names": ["low back pain", "lower back", "back strain"],
    "search_keywords": ["back", "spine", "lumbar", "sciatica", "pain"]
  },
  {
    "code": "5003",
    "name": "Degenerative Arthritis",
    "category": "musculoskeletal",
    "subcategory": "joints",
    "min_rating": 10,
    "max_rating": 100,
    "nexus_required": true,
    "in_service_events": ["repetitive_stress", "injury", "wear_and_tear"],
    "required_evidence": {
      "current_diagnosis": true,
      "x_ray": true,
      "range_of_motion": true
    },
    "common_names": ["arthritis", "joint pain", "degenerative joint disease"],
    "search_keywords": ["arthritis", "joints", "knee", "hip", "shoulder", "pain"]
  },
  {
    "code": "8100",
    "name": "Migraine Headaches",
    "category": "neurological",
    "subcategory": "headache",
    "min_rating": 0,
    "max_rating": 50,
    "nexus_required": true,
    "in_service_events": ["TBI", "stress", "blast_exposure"],
    "required_evidence": {
      "current_diagnosis": true,
      "headache_log": true,
      "neurological_exam": true
    },
    "common_names": ["migraines", "severe headaches"],
    "search_keywords": ["migraine", "headache", "head pain", "aura"]
  }
]
```

---

## Register Router

Update `/ganuda/vetassist/backend/app/main.py` to include:

```python
from app.api.v1.conditions import router as conditions_router
app.include_router(conditions_router, prefix="/api/v1")
```

---

## Verification

```bash
# Run migration
cd /ganuda/vetassist/backend
psql -h 192.168.132.224 -U vetassist -d vetassist -f database/migrations/002_conditions.sql

# Seed data
python3 -c "
from app.db.base import SessionLocal
from app.models.conditions import Condition
import json

db = SessionLocal()
with open('data/cfr38_conditions_seed.json') as f:
    conditions = json.load(f)
    for c in conditions:
        db.merge(Condition(**c))
    db.commit()
print('Seeded conditions')
"

# Test API
curl http://localhost:8000/api/v1/conditions/categories
curl "http://localhost:8000/api/v1/conditions/search?q=ptsd"
```

---

FOR SEVEN GENERATIONS
