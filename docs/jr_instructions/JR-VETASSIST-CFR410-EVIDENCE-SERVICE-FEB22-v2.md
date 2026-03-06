# Jr Instruction: VetAssist 38 CFR 4.10 — Add Medication Impact Category to Evidence Service (v2)

**Task ID:** CFR410-EVIDENCE-v2
**Kanban:** #1843
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

The new 38 CFR 4.10 medication impact rule (effective Feb 17, 2026) means the VA rates veterans based on function WHILE ON medication. Veterans must document medication side effects, residual symptoms, and dosage history. The evidence_service.py needs a new category for this.

NOTE: The article content in expand_articles.py was already partially updated (Step 1 of original #800). The corruption there has been fixed by TPM. This instruction handles only the evidence_service.py addition.

---

## Step 1: Add medication impact evidence category after severity_evidence

File: `/ganuda/vetassist/backend/app/services/evidence_service.py`

```python
<<<<<<< SEARCH
    "severity_evidence": {
        "name": "Severity Evidence",
        "description": "Documentation showing how your condition affects daily life and work",
        "priority": 4,
        "items": [
=======
    "medication_impact": {
        "name": "Medication Impact Evidence (38 CFR 4.10)",
        "description": "Documentation of how medications affect your daily functioning — required under the Feb 2026 rule change",
        "priority": 5,
        "items": [
            {
                "id": "medication_list",
                "name": "Current Medication List with Side Effects",
                "description": "Complete list of all medications for this condition, dosages, and every side effect you experience",
                "how_to_obtain": "Ask your pharmacist for a printout, or list them yourself including OTC medications",
                "required": True
            },
            {
                "id": "residual_symptoms",
                "name": "Residual Symptoms Statement",
                "description": "Written statement describing symptoms that PERSIST despite taking medication as prescribed",
                "how_to_obtain": "Write a personal statement detailing what daily life is like even while medicated",
                "required": True
            },
            {
                "id": "dosage_history",
                "name": "Dosage History and Changes",
                "description": "Record of medication changes, dose increases, and why adjustments were made",
                "how_to_obtain": "Request pharmacy records or VA medication history from My HealtheVet",
                "required": False
            },
            {
                "id": "side_effect_impact",
                "name": "Functional Impact of Side Effects",
                "description": "How medication side effects (drowsiness, weight gain, cognitive fog, etc.) limit your work and daily activities",
                "how_to_obtain": "Write a statement, or ask your doctor to document side effects in your medical record",
                "required": False
            }
        ]
    },
    "severity_evidence": {
        "name": "Severity Evidence",
        "description": "Documentation showing how your condition affects daily life and work",
        "priority": 4,
        "items": [
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/vetassist/backend && python3 -c "
from app.services.evidence_service import EVIDENCE_CATEGORIES
assert 'medication_impact' in EVIDENCE_CATEGORIES, 'medication_impact category missing'
assert EVIDENCE_CATEGORIES['medication_impact']['priority'] == 5
print(f'Evidence categories: {list(EVIDENCE_CATEGORIES.keys())}')
print('CFR 4.10 medication impact category: OK')
"
```

## What NOT to Change

- Do NOT modify existing evidence categories (service_connection, current_diagnosis, nexus_evidence, severity_evidence)
- Do NOT change priority numbers of existing categories
- Do NOT modify expand_articles.py (corruption already fixed by TPM)
- Do NOT add new imports
