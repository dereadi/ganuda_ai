# Jr Instruction: VetAssist Evidence Checklist Generator
## Task ID: VetAssist Sprint 3 - Task 3
## Priority: P2
## Estimated Complexity: Medium

---

## Objective

Build an evidence checklist generator that creates personalized evidence requirements for each claimed condition. Help veterans understand exactly what documentation they need to submit a strong claim.

---

## Background

Each VA disability claim requires specific evidence:
1. **Service Connection**: Proof condition is related to military service
2. **Current Diagnosis**: Medical proof the condition exists now
3. **Nexus**: Medical opinion linking current condition to service
4. **Severity**: Evidence of how bad the condition is (for rating %)

Veterans often don't know what evidence to submit, leading to denied claims that could have been approved with proper documentation.

---

## Implementation Steps

### Step 1: Create Checklist Table

```sql
CREATE TABLE IF NOT EXISTS vetassist_evidence_checklists (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    generated_at TIMESTAMP DEFAULT NOW(),
    conditions_analyzed JSONB,
    checklist_items JSONB,
    completion_status JSONB,
    FOREIGN KEY (session_id) REFERENCES vetassist_wizard_sessions(session_id) ON DELETE CASCADE
);
```

### Step 2: Create Evidence Service

Create `/ganuda/vetassist/backend/app/services/evidence_service.py`:

```python
"""
VetAssist Evidence Checklist Service
Cherokee AI Federation - For Seven Generations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

# Evidence categories and their importance
EVIDENCE_CATEGORIES = {
    "service_connection": {
        "name": "Service Connection Evidence",
        "description": "Documents proving your condition is related to military service",
        "priority": 1,
        "items": [
            {
                "id": "dd214",
                "name": "DD-214 (Certificate of Release)",
                "description": "Shows service dates, MOS, and discharge type",
                "how_to_obtain": "Request from National Personnel Records Center (NPRC) or access via eBenefits",
                "required": True
            },
            {
                "id": "service_treatment_records",
                "name": "Service Treatment Records (STRs)",
                "description": "Medical records from during your service showing treatment for this condition",
                "how_to_obtain": "Request from NPRC or VA Regional Office",
                "required": True
            },
            {
                "id": "personnel_records",
                "name": "Service Personnel Records",
                "description": "Records showing duties, deployments, and assignments relevant to your condition",
                "how_to_obtain": "Request from NPRC",
                "required": False
            }
        ]
    },
    "current_diagnosis": {
        "name": "Current Diagnosis Evidence",
        "description": "Medical documentation proving you have this condition today",
        "priority": 2,
        "items": [
            {
                "id": "current_medical_records",
                "name": "Current Medical Records",
                "description": "Recent treatment records showing ongoing diagnosis and treatment",
                "how_to_obtain": "Request from your healthcare provider or VA Medical Center",
                "required": True
            },
            {
                "id": "dbq",
                "name": "Disability Benefits Questionnaire (DBQ)",
                "description": "Standardized VA form completed by a medical professional documenting your condition",
                "how_to_obtain": "Request from your doctor or VA examiner. Forms at va.gov/disability/get-help-filing-claim/",
                "required": True
            },
            {
                "id": "diagnosis_letter",
                "name": "Diagnosis Letter",
                "description": "Letter from doctor confirming your diagnosis with ICD code",
                "how_to_obtain": "Request from your treating physician",
                "required": False
            }
        ]
    },
    "nexus_evidence": {
        "name": "Nexus (Medical Link) Evidence",
        "description": "Medical opinion connecting your current condition to military service",
        "priority": 3,
        "items": [
            {
                "id": "nexus_letter",
                "name": "Nexus Letter / Independent Medical Opinion (IMO)",
                "description": "A doctor's opinion stating 'at least as likely as not' your condition is related to service",
                "how_to_obtain": "Request from your doctor, or hire a medical professional specializing in VA claims",
                "required": True
            },
            {
                "id": "buddy_statements",
                "name": "Buddy/Lay Statements",
                "description": "Statements from fellow service members or family describing your condition and its connection to service",
                "how_to_obtain": "Ask friends, family, or fellow veterans to write statements using VA Form 21-10210",
                "required": False
            },
            {
                "id": "continuity_evidence",
                "name": "Continuity of Symptom Evidence",
                "description": "Documentation showing your condition has been continuous since service",
                "how_to_obtain": "Gather old medical records, pharmacy records, or personal documentation",
                "required": False
            }
        ]
    },
    "severity_evidence": {
        "name": "Severity Evidence",
        "description": "Documentation showing how your condition affects daily life and work",
        "priority": 4,
        "items": [
            {
                "id": "functional_impact",
                "name": "Functional Impact Statement",
                "description": "Your description of how the condition affects daily activities and work",
                "how_to_obtain": "Write a detailed personal statement about limitations",
                "required": True
            },
            {
                "id": "work_records",
                "name": "Employment/Work Impact Records",
                "description": "Documentation of missed work, accommodations, or job loss due to condition",
                "how_to_obtain": "Request from employer HR department or gather pay stubs, FMLA records",
                "required": False
            },
            {
                "id": "photos_documentation",
                "name": "Photos/Video Documentation",
                "description": "Visual evidence of visible conditions or mobility limitations",
                "how_to_obtain": "Take photos/videos yourself or ask family to document",
                "required": False
            }
        ]
    }
}

# Condition-specific evidence additions
CONDITION_SPECIFIC = {
    "PTSD": {
        "stressor_evidence": {
            "id": "stressor_statement",
            "name": "Stressor Statement",
            "description": "Detailed account of the traumatic event(s) that caused your PTSD",
            "how_to_obtain": "Complete VA Form 21-0781 (PTSD Stressor Statement)",
            "required": True,
            "category": "service_connection"
        },
        "combat_records": {
            "id": "combat_records",
            "name": "Combat Records/Unit History",
            "description": "Unit records, combat history, or deployment orders",
            "how_to_obtain": "Request from NPRC or unit association",
            "required": False,
            "category": "service_connection"
        }
    },
    "Tinnitus": {
        "noise_exposure": {
            "id": "noise_exposure",
            "name": "Noise Exposure Documentation",
            "description": "Evidence of exposure to loud noises during service (weapons, machinery, aircraft)",
            "how_to_obtain": "MOS documentation, deployment records, buddy statements",
            "required": True,
            "category": "service_connection"
        }
    },
    "Sleep Apnea": {
        "sleep_study": {
            "id": "sleep_study",
            "name": "Sleep Study (Polysomnography)",
            "description": "Medical sleep study diagnosing sleep apnea and its severity",
            "how_to_obtain": "Request from sleep clinic or ask doctor for referral",
            "required": True,
            "category": "current_diagnosis"
        }
    },
    "TBI": {
        "incident_records": {
            "id": "tbi_incident",
            "name": "Head Injury Incident Documentation",
            "description": "Records of the event causing head injury (blast exposure, accident, assault)",
            "how_to_obtain": "Service records, incident reports, medical records from time of injury",
            "required": True,
            "category": "service_connection"
        }
    }
}


class EvidenceService:
    def generate_checklist(self, session_id: str, conditions: List[str]) -> Dict[str, Any]:
        """
        Generate personalized evidence checklist based on claimed conditions.
        """
        checklist = {
            "session_id": session_id,
            "conditions": conditions,
            "categories": {}
        }

        # Add base evidence categories
        for cat_id, category in EVIDENCE_CATEGORIES.items():
            checklist["categories"][cat_id] = {
                "name": category["name"],
                "description": category["description"],
                "priority": category["priority"],
                "items": [item.copy() for item in category["items"]]
            }

        # Add condition-specific evidence
        for condition in conditions:
            condition_upper = condition.upper().strip()
            for cond_key, specific_items in CONDITION_SPECIFIC.items():
                if cond_key.upper() in condition_upper or condition_upper in cond_key.upper():
                    for item_id, item in specific_items.items():
                        cat = item["category"]
                        if cat in checklist["categories"]:
                            # Check if not already added
                            existing_ids = [i["id"] for i in checklist["categories"][cat]["items"]]
                            if item["id"] not in existing_ids:
                                checklist["categories"][cat]["items"].append({
                                    "id": item["id"],
                                    "name": item["name"],
                                    "description": item["description"],
                                    "how_to_obtain": item["how_to_obtain"],
                                    "required": item["required"],
                                    "condition_specific": condition
                                })

        # Calculate statistics
        total_items = 0
        required_items = 0
        for cat in checklist["categories"].values():
            total_items += len(cat["items"])
            required_items += sum(1 for i in cat["items"] if i.get("required"))

        checklist["statistics"] = {
            "total_items": total_items,
            "required_items": required_items,
            "optional_items": total_items - required_items
        }

        return checklist

    def save_checklist(self, session_id: str, checklist: Dict) -> int:
        """Save generated checklist to database"""
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vetassist_evidence_checklists
                    (session_id, conditions_analyzed, checklist_items, completion_status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    session_id,
                    json.dumps(checklist.get("conditions", [])),
                    json.dumps(checklist.get("categories", {})),
                    json.dumps({})  # Empty completion status initially
                ))
                checklist_id = cur.fetchone()[0]
                conn.commit()
                return checklist_id
        finally:
            conn.close()

    def update_completion(self, session_id: str, item_id: str, completed: bool) -> bool:
        """Update completion status for a checklist item"""
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get current status
                cur.execute("""
                    SELECT completion_status FROM vetassist_evidence_checklists
                    WHERE session_id = %s ORDER BY generated_at DESC LIMIT 1
                """, (session_id,))
                row = cur.fetchone()
                if not row:
                    return False

                status = row['completion_status'] or {}
                status[item_id] = completed

                cur.execute("""
                    UPDATE vetassist_evidence_checklists
                    SET completion_status = %s
                    WHERE session_id = %s
                """, (json.dumps(status), session_id))
                conn.commit()
                return True
        finally:
            conn.close()


evidence_service = EvidenceService()
```

### Step 3: Create Evidence Checklist Endpoint

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py` or create new file:

```python
from app.services.evidence_service import evidence_service

@router.get("/{session_id}/evidence-checklist")
def get_evidence_checklist(session_id: str):
    """Generate personalized evidence checklist for claimed conditions"""
    conn = get_db_conn()
    try:
        # Get session and conditions
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT wizard_type, answers FROM vetassist_wizard_sessions
                WHERE session_id = %s
            """, (session_id,))
            session = cur.fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract conditions from answers
        answers = session['answers'] if isinstance(session['answers'], dict) else json.loads(session['answers'] or '{}')
        conditions = []

        # Check various places conditions might be stored
        if 'conditions' in answers:
            conditions = answers['conditions'] if isinstance(answers['conditions'], list) else [answers['conditions']]
        elif 'step_3' in answers and 'conditions' in answers['step_3']:
            conditions = answers['step_3']['conditions']

        if not conditions:
            # Return generic checklist
            conditions = ["General Disability"]

        # Generate checklist
        checklist = evidence_service.generate_checklist(session_id, conditions)

        # Check for existing uploaded evidence
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, category, file_name FROM vetassist_wizard_files
                WHERE session_id = %s AND NOT deleted
            """, (session_id,))
            uploaded_files = cur.fetchall()

        # Mark uploaded evidence as available
        uploaded_categories = {f['category'] for f in uploaded_files if f.get('category')}
        checklist["uploaded_evidence"] = [
            {"id": f['id'], "name": f['file_name'], "category": f.get('category')}
            for f in uploaded_files
        ]

        return checklist

    finally:
        conn.close()


@router.post("/{session_id}/evidence-checklist/update")
def update_checklist_item(
    session_id: str,
    item_id: str,
    completed: bool = True
):
    """Mark a checklist item as completed or not"""
    success = evidence_service.update_completion(session_id, item_id, completed)
    if not success:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return {"status": "updated", "item_id": item_id, "completed": completed}
```

---

## Testing

```bash
# Create session and add conditions
SESSION_ID="test-session-id"

# Get evidence checklist
curl "http://localhost:8001/api/v1/wizard/$SESSION_ID/evidence-checklist"

# Mark item complete
curl -X POST "http://localhost:8001/api/v1/wizard/$SESSION_ID/evidence-checklist/update?item_id=dd214&completed=true"
```

---

## Acceptance Criteria

1. Generates checklist based on claimed conditions
2. Includes condition-specific evidence requirements
3. Shows priority and required vs optional items
4. Tracks what's been uploaded vs missing
5. Provides guidance on how to obtain each document

---

## Frontend Display Suggestions

Display checklist grouped by category with:
- Checkboxes for tracking
- Color coding (red=required missing, yellow=optional, green=completed)
- Expandable "how to obtain" guidance
- Link to upload for each item

---

*Cherokee AI Federation - For Seven Generations*
