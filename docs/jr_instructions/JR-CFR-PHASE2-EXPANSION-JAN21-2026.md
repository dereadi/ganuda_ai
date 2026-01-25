# JR Instruction: CFR Phase 2 Expansion
## Task ID: CFR-EXPAND-002
## Priority: P2
## Estimated Complexity: Medium

---

## Objective

Continue CFR database expansion from 49 conditions to 800+ diagnostic codes. Phase 1 completed 49 conditions across 11 body systems. Phase 2 focuses on completing remaining high-volume conditions.

---

## Current State

```
Body System       | Current | Target
------------------|---------|--------
Musculoskeletal   |    16   |  ~150
Neurological      |     6   |  ~100
Mental Disorders  |     5   |   ~50
Digestive         |     4   |   ~70
Cardiovascular    |     3   |   ~80
Respiratory       |     3   |   ~60
Skin              |     3   |   ~40
Genitourinary     |     3   |   ~60
Endocrine         |     2   |   ~40
Eye               |     2   |   ~40
Auditory          |     2   |   ~50
------------------|---------|--------
TOTAL             |    49   |  ~800
```

---

## Phase 2 Priority Order

### Batch 1: Complete Top 100 Claimed Conditions
Focus on conditions with highest claim frequency:
- Remaining musculoskeletal (spine, foot, wrist, elbow)
- Sleep disorders (insomnia, narcolepsy)
- Headaches (tension, cluster)
- Sinusitis, rhinitis
- Fibromyalgia
- Chronic fatigue syndrome
- Gulf War presumptives

### Batch 2: Complete Body Systems
Add remaining codes per body system using 38 CFR Part 4.

---

## Data Source

Primary: https://www.ecfr.gov/current/title-38/chapter-I/part-4

For each condition extract:
- diagnostic_code (e.g., "5237")
- condition_name
- body_system
- rating_criteria (JSON with percentages)
- evidence_requirements (array)
- dbq_form (if applicable)

---

## SQL Template

```sql
INSERT INTO vetassist_cfr_conditions (
    diagnostic_code, condition_name, body_system, synonyms, common_names,
    rating_criteria, evidence_requirements, dbq_form, icd10_codes, description,
    claim_frequency_rank
) VALUES
('XXXX', 'Condition Name', 'Body System',
 ARRAY['synonym1', 'synonym2'],
 ARRAY['common term 1', 'common term 2'],
 '{"0": "criteria", "10": "criteria", "20": "criteria"}'::jsonb,
 ARRAY['Evidence 1', 'Evidence 2'],
 'DBQ-FORM', ARRAY['ICD10'], 'Description', NULL)
ON CONFLICT (diagnostic_code) DO UPDATE SET
    condition_name = EXCLUDED.condition_name,
    synonyms = EXCLUDED.synonyms,
    common_names = EXCLUDED.common_names,
    rating_criteria = EXCLUDED.rating_criteria,
    last_verified = NOW();
```

---

## Acceptance Criteria

1. Database contains 200+ conditions (Batch 1)
2. All 15 body systems have at least 10 conditions each
3. Top 100 claimed conditions all present
4. Search returns results for common veteran terms

---

## Verification

```bash
# Count by body system
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT body_system, COUNT(*) FROM vetassist_cfr_conditions GROUP BY body_system ORDER BY COUNT(*) DESC;"

# Test searches
curl -s -X POST http://localhost:8001/api/v1/conditions/map \
  -H "Content-Type: application/json" \
  -d '{"description": "fibromyalgia"}' | python3 -m json.tool
```

---

*Cherokee AI Federation - For Seven Generations*
