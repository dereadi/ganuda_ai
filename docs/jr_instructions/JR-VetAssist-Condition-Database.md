# Jr Instructions: VetAssist Condition Database

**Task ID**: VETASSIST-COND-001
**Priority**: HIGH
**Target**: bluefin (PostgreSQL) + redfin (API)
**Requires**: No PII, no goldfin - can build now
**Council Approval**: Part of VetAssist Phase 1 MVP (APPROVED 5-0-2)

---

## Executive Summary

Extract and enhance the 400+ condition list from VA's vets-website repository. This enables veterans to search for conditions using plain language and get mapped to official VA terminology.

**Source Files (from vets-website repo):**
- `conditionOptions.js` - 400+ conditions with laterality flags
- `disabilityLabelsRevised.js` - 580 labeled conditions (legacy IDs)

---

## Step 1: Extract Conditions from VA GitHub

### Option A: Direct Fetch (Recommended)

**IMPORTANT**: Write to `/ganuda/data/vetassist/`, NOT `/tmp/`. Files in /tmp are deleted on reboot.

```bash
# Create data directory
mkdir -p /ganuda/data/vetassist

# Fetch conditionOptions.js
curl -s "https://raw.githubusercontent.com/department-of-veterans-affairs/vets-website/main/src/applications/disability-benefits/all-claims/content/conditionOptions.js" > /ganuda/data/vetassist/conditionOptions.js

# Fetch disabilityLabelsRevised.js
curl -s "https://raw.githubusercontent.com/department-of-veterans-affairs/vets-website/main/src/applications/disability-benefits/all-claims/content/disabilityLabelsRevised.js" > /ganuda/data/vetassist/disabilityLabelsRevised.js
```

### Option B: Clone Repository

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/department-of-veterans-affairs/vets-website.git
cd vets-website
git sparse-checkout set src/applications/disability-benefits/all-claims/content
```

---

## Step 2: Parse and Transform

### Condition Structure

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class VACondition:
    id: int                          # Sequential ID
    name: str                        # Full VA name: "PTSD (post-traumatic stress disorder)"
    display_name: str                # Short display: "PTSD"
    medical_term: Optional[str]      # Medical: "post-traumatic stress disorder"
    category: str                    # Category: "Mental Health", "Musculoskeletal", etc.
    has_laterality: bool             # True if left/right/bilateral applies
    side: Optional[str]              # "left", "right", "bilateral", or None
    diagnostic_codes: List[str]      # VASRD codes: ["9411"]
    synonyms: List[str]              # Plain language: ["shell shock", "combat stress"]
    dbq_form: Optional[str]          # Related DBQ: "DBQ - PTSD"
    presumptive_eligible: bool       # Auto-eligible under certain conditions
    pact_act_condition: bool         # PACT Act toxic exposure condition
```

### Parsing Script

```python
#!/usr/bin/env python3
"""Parse VA condition files into structured database."""

import re
import json
from pathlib import Path

def parse_condition_options(js_content: str) -> list:
    """Parse conditionOptions.js format."""
    conditions = []

    # Extract array content
    match = re.search(r'const conditionObjects = \[(.*?)\];', js_content, re.DOTALL)
    if not match:
        return conditions

    # Parse each object
    objects = re.findall(r"\{\s*option:\s*['\"](.+?)['\"](?:,\s*sideOfBody:\s*(true|false))?\s*\}", match.group(1))

    for i, (option, side_of_body) in enumerate(objects):
        condition = {
            "id": i,
            "name": option,
            "has_laterality": side_of_body == "true",
            "side": extract_side(option),
            "display_name": extract_display_name(option),
            "medical_term": extract_medical_term(option),
            "category": categorize_condition(option),
            "synonyms": [],
            "diagnostic_codes": [],
        }
        conditions.append(condition)

    return conditions


def extract_side(name: str) -> str:
    """Extract laterality from condition name."""
    name_lower = name.lower()
    if ", bilateral" in name_lower or "bilateral" in name_lower:
        return "bilateral"
    elif ", left" in name_lower:
        return "left"
    elif ", right" in name_lower:
        return "right"
    return None


def extract_display_name(name: str) -> str:
    """Extract short display name."""
    # "PTSD (post-traumatic stress disorder)" -> "PTSD"
    # "ACL tear (anterior cruciate ligament tear), left" -> "ACL tear, left"
    match = re.match(r'^([^(]+)', name)
    if match:
        display = match.group(1).strip()
        # Re-add laterality if present
        if ", left" in name:
            display += ", left"
        elif ", right" in name:
            display += ", right"
        elif ", bilateral" in name:
            display += ", bilateral"
        return display
    return name


def extract_medical_term(name: str) -> str:
    """Extract medical terminology from parentheses."""
    match = re.search(r'\(([^)]+)\)', name)
    return match.group(1) if match else None


def categorize_condition(name: str) -> str:
    """Categorize condition by keywords."""
    name_lower = name.lower()

    categories = {
        "Mental Health": ["ptsd", "depression", "anxiety", "bipolar", "schizophrenia", "mood", "mental"],
        "Musculoskeletal": ["knee", "back", "spine", "shoulder", "hip", "ankle", "wrist", "arthritis", "strain", "tear"],
        "Respiratory": ["asthma", "copd", "lung", "bronchitis", "sleep apnea", "respiratory"],
        "Cardiovascular": ["heart", "hypertension", "blood pressure", "coronary", "cardiac"],
        "Neurological": ["migraine", "headache", "neuropathy", "tbi", "traumatic brain", "seizure"],
        "Skin": ["dermatitis", "eczema", "psoriasis", "skin", "scar"],
        "Digestive": ["gerd", "ibs", "colitis", "stomach", "gastro"],
        "Endocrine": ["diabetes", "thyroid", "hormone"],
        "Hearing/Vision": ["tinnitus", "hearing", "vision", "blind", "deaf", "eye"],
        "Cancer": ["cancer", "carcinoma", "tumor", "leukemia", "lymphoma"],
        "Toxic Exposure": ["agent orange", "burn pit", "radiation", "gulf war"],
    }

    for category, keywords in categories.items():
        if any(kw in name_lower for kw in keywords):
            return category

    return "Other"


if __name__ == "__main__":
    # Read and parse
    with open("/ganuda/data/vetassist/conditionOptions.js") as f:
        content = f.read()

    conditions = parse_condition_options(content)

    # Output
    print(f"Parsed {len(conditions)} conditions")
    with open("/ganuda/data/vetassist/va_conditions.json", "w") as f:
        json.dump(conditions, f, indent=2)
```

---

## Step 3: Enhance with Synonyms

Add plain-language synonyms so veterans can search naturally:

```python
SYNONYM_MAP = {
    "ptsd": ["shell shock", "combat stress", "nightmares", "flashbacks", "war trauma"],
    "tinnitus": ["ringing in ears", "ear ringing", "buzzing ears"],
    "sleep apnea": ["snoring", "stop breathing sleep", "cpap"],
    "degenerative disc disease": ["bad back", "back pain", "herniated disc", "bulging disc"],
    "migraine": ["bad headaches", "severe headache", "chronic headache"],
    "gerd": ["acid reflux", "heartburn", "stomach acid"],
    "plantar fasciitis": ["heel pain", "foot pain", "sore feet"],
    "carpal tunnel": ["wrist pain", "numb hands", "hand tingling"],
    "depression": ["sad", "hopeless", "can't get out of bed", "mental health"],
    "anxiety": ["panic attacks", "nervous", "worry", "anxious"],
    "hypertension": ["high blood pressure", "hbp"],
    "diabetes": ["blood sugar", "insulin", "diabetic"],
    "acl tear": ["knee injury", "knee gave out", "torn knee"],
    "meniscus tear": ["knee cartilage", "torn cartilage"],
    "rotator cuff": ["shoulder injury", "can't raise arm", "shoulder pain"],
    "traumatic brain injury": ["tbi", "head injury", "concussion", "brain damage"],
    "radiculopathy": ["pinched nerve", "shooting pain", "nerve pain"],
    "sciatica": ["leg pain", "back to leg pain", "shooting leg pain"],
    "eczema": ["itchy skin", "skin rash", "dry skin"],
    "erectile dysfunction": ["ed", "impotence", "can't perform"],
    "irritable bowel": ["ibs", "stomach problems", "bathroom issues"],
    "gulf war syndrome": ["gulf war illness", "gws", "unexplained illness"],
}

def add_synonyms(conditions: list) -> list:
    """Add synonyms to conditions based on keywords."""
    for condition in conditions:
        name_lower = condition["name"].lower()
        condition["synonyms"] = []

        for key, synonyms in SYNONYM_MAP.items():
            if key in name_lower:
                condition["synonyms"].extend(synonyms)

    return conditions
```

---

## Step 4: Database Schema

### PostgreSQL Schema (on bluefin)

```sql
-- Create conditions table
CREATE TABLE IF NOT EXISTS vetassist_conditions (
    id SERIAL PRIMARY KEY,
    va_name VARCHAR(500) NOT NULL UNIQUE,     -- Full VA name (unique for upsert)
    display_name VARCHAR(200) NOT NULL,       -- Short display name
    medical_term VARCHAR(300),                -- Medical terminology
    category VARCHAR(100) NOT NULL,           -- Condition category
    has_laterality BOOLEAN DEFAULT FALSE,     -- Left/right applies
    side VARCHAR(20),                         -- left, right, bilateral, NULL
    diagnostic_codes TEXT[],                  -- VASRD codes
    synonyms TEXT[],                          -- Plain language synonyms
    dbq_form VARCHAR(100),                    -- Related DBQ
    presumptive_eligible BOOLEAN DEFAULT FALSE,
    pact_act_condition BOOLEAN DEFAULT FALSE,
    search_vector TSVECTOR,                   -- Full-text search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Full-text search index
CREATE INDEX idx_conditions_search ON vetassist_conditions USING GIN(search_vector);

-- Category index
CREATE INDEX idx_conditions_category ON vetassist_conditions(category);

-- Laterality index
CREATE INDEX idx_conditions_laterality ON vetassist_conditions(has_laterality, side);

-- Trigger to update search vector
CREATE OR REPLACE FUNCTION update_condition_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.va_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.display_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.medical_term, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.synonyms, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER condition_search_update
    BEFORE INSERT OR UPDATE ON vetassist_conditions
    FOR EACH ROW EXECUTE FUNCTION update_condition_search_vector();
```

### Load Data

```python
import psycopg2
import json
import os

# Presumptive condition lists (from Step 6)
ALL_PRESUMPTIVES = set(
    PACT_ACT_CONDITIONS + GULF_WAR_PRESUMPTIVES + AGENT_ORANGE_PRESUMPTIVES
)


def is_presumptive(condition_name: str) -> bool:
    """Check if condition matches any presumptive list."""
    name_lower = condition_name.lower()
    for presumptive in ALL_PRESUMPTIVES:
        if presumptive.lower() in name_lower:
            return True
    return False


def is_pact_act(condition_name: str) -> bool:
    """Check if condition is a PACT Act toxic exposure condition."""
    name_lower = condition_name.lower()
    for condition in PACT_ACT_CONDITIONS:
        if condition.lower() in name_lower:
            return True
    return False


def load_conditions_to_db(conditions: list, conn_string: str = None):
    """Load conditions into PostgreSQL with presumptive flags."""
    # Use environment variable or provided connection string
    if conn_string is None:
        conn_string = os.getenv(
            'VETASSIST_DB_URL',
            'postgresql://claude:jawaseatlasers2@192.168.132.222/zammad_production'
        )

    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    loaded = 0
    for c in conditions:
        # Check presumptive status based on condition name
        presumptive = is_presumptive(c["name"])
        pact_act = is_pact_act(c["name"])

        cur.execute("""
            INSERT INTO vetassist_conditions
            (va_name, display_name, medical_term, category, has_laterality,
             side, diagnostic_codes, synonyms, presumptive_eligible, pact_act_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (va_name) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                medical_term = EXCLUDED.medical_term,
                category = EXCLUDED.category,
                has_laterality = EXCLUDED.has_laterality,
                side = EXCLUDED.side,
                synonyms = EXCLUDED.synonyms,
                presumptive_eligible = EXCLUDED.presumptive_eligible,
                pact_act_condition = EXCLUDED.pact_act_condition,
                updated_at = NOW()
        """, (
            c["name"],
            c["display_name"],
            c.get("medical_term"),
            c["category"],
            c["has_laterality"],
            c.get("side"),
            c.get("diagnostic_codes", []),
            c.get("synonyms", []),
            presumptive,
            pact_act,
        ))
        loaded += 1

    conn.commit()
    cur.close()
    conn.close()

    # Report presumptive counts
    presumptive_count = sum(1 for c in conditions if is_presumptive(c["name"]))
    pact_count = sum(1 for c in conditions if is_pact_act(c["name"]))
    print(f"Loaded {loaded} conditions")
    print(f"  - {presumptive_count} presumptive conditions flagged")
    print(f"  - {pact_count} PACT Act conditions flagged")
```

---

## Step 5: Search API

### Endpoint

```
POST /v1/vetassist/condition-search
```

### Request

```json
{
  "query": "bad knee",
  "limit": 10,
  "include_laterality": true,
  "category": null
}
```

### Response

```json
{
  "query": "bad knee",
  "results": [
    {
      "id": 142,
      "va_name": "Knee strain, left",
      "display_name": "Knee strain, left",
      "category": "Musculoskeletal",
      "has_laterality": true,
      "side": "left",
      "relevance_score": 0.95
    },
    {
      "id": 143,
      "va_name": "Knee strain, right",
      "display_name": "Knee strain, right",
      "category": "Musculoskeletal",
      "has_laterality": true,
      "side": "right",
      "relevance_score": 0.95
    },
    {
      "id": 156,
      "va_name": "Meniscus tear (knee cartilage tear), left",
      "display_name": "Meniscus tear, left",
      "medical_term": "knee cartilage tear",
      "category": "Musculoskeletal",
      "has_laterality": true,
      "side": "left",
      "relevance_score": 0.82
    }
  ],
  "total_matches": 24,
  "suggestion": "Did you mean 'knee injury'? Related: ACL tear, Meniscus tear, Patellofemoral syndrome"
}
```

### Implementation

```python
@app.route('/v1/vetassist/condition-search', methods=['POST'])
def condition_search():
    """Search conditions with fuzzy matching and synonyms."""
    data = request.get_json()
    query = data.get('query', '').strip()
    limit = min(data.get('limit', 10), 50)
    category = data.get('category')

    if not query:
        return jsonify({"error": "Query required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Build search query
    sql = """
        SELECT
            id, va_name, display_name, medical_term, category,
            has_laterality, side, diagnostic_codes, synonyms,
            ts_rank(search_vector, plainto_tsquery('english', %s)) AS rank
        FROM vetassist_conditions
        WHERE search_vector @@ plainto_tsquery('english', %s)
    """
    params = [query, query]

    if category:
        sql += " AND category = %s"
        params.append(category)

    sql += " ORDER BY rank DESC LIMIT %s"
    params.append(limit)

    cur.execute(sql, params)
    results = cur.fetchall()

    # Format response
    conditions = []
    for row in results:
        conditions.append({
            "id": row[0],
            "va_name": row[1],
            "display_name": row[2],
            "medical_term": row[3],
            "category": row[4],
            "has_laterality": row[5],
            "side": row[6],
            "relevance_score": round(row[9], 2)
        })

    cur.close()
    conn.close()

    return jsonify({
        "query": query,
        "results": conditions,
        "total_matches": len(conditions)
    })
```

---

## Step 6: Presumptive Conditions

### PACT Act Conditions (Toxic Exposure)

Add these flags for automatic presumptive eligibility:

```python
PACT_ACT_CONDITIONS = [
    "Asthma",
    "Head cancer",
    "Neck cancer",
    "Respiratory cancer",
    "Gastrointestinal cancer",
    "Reproductive cancer",
    "Lymphoma",
    "Lymphomatic cancer",
    "Kidney cancer",
    "Brain cancer",
    "Melanoma",
    "Pancreatic cancer",
    "Chronic bronchitis",
    "COPD",
    "Constrictive bronchiolitis",
    "Interstitial lung disease",
    "Pleuritis",
    "Pulmonary fibrosis",
    "Sarcoidosis",
    "Chronic sinusitis",
    "Chronic rhinitis",
    "Glioblastoma",
    "Hypertension",  # Added 2024
]

GULF_WAR_PRESUMPTIVES = [
    "Chronic fatigue syndrome",
    "Fibromyalgia",
    "Functional gastrointestinal disorders",
    "Undiagnosed illnesses",
]

AGENT_ORANGE_PRESUMPTIVES = [
    "AL amyloidosis",
    "Bladder cancer",
    "Chronic B-cell leukemias",
    "Chloracne",
    "Diabetes mellitus type 2",
    "Hodgkin's disease",
    "Hypertension",
    "Ischemic heart disease",
    "Multiple myeloma",
    "Non-Hodgkin's lymphoma",
    "Parkinson's disease",
    "Peripheral neuropathy",
    "Porphyria cutanea tarda",
    "Prostate cancer",
    "Respiratory cancers",
    "Soft tissue sarcomas",
]
```

---

## Validation Checklist

- [ ] Fetch latest conditionOptions.js from VA GitHub
- [ ] Parse all 400+ conditions correctly
- [ ] Extract laterality (left/right/bilateral) flags
- [ ] Categorize all conditions
- [ ] Add synonym mappings for common searches
- [ ] Load into PostgreSQL on bluefin
- [ ] Full-text search working
- [ ] API endpoint returning ranked results
- [ ] PACT Act conditions flagged
- [ ] Agent Orange presumptives flagged
- [ ] Gulf War presumptives flagged

---

## Files to Create

| File | Location | Purpose |
|------|----------|---------|
| `condition_parser.py` | `/ganuda/scripts/` | Parse VA condition files |
| `conditions_schema.sql` | `/ganuda/sql/` | Database schema |
| `load_conditions.py` | `/ganuda/scripts/` | Load data to PostgreSQL |
| `synonyms.json` | `/ganuda/data/vetassist/` | Plain language synonyms |
| `presumptives.json` | `/ganuda/data/vetassist/` | Presumptive condition lists |

---

## Related Documents

- VA-Vets-Website-Analysis.md (source research)
- VetAssist PRD v2.0
- [VA PACT Act Presumptive Conditions](https://www.va.gov/resources/the-pact-act-and-your-va-benefits/)

---

*For Seven Generations*
