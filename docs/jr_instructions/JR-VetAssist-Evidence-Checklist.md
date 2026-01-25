# Jr Instructions: VetAssist Evidence Checklist System

**Task ID**: VETASSIST-EVID-001
**Priority**: HIGH
**Target**: bluefin (PostgreSQL) + redfin (API)
**Requires**: No PII, no goldfin - can build now
**Council Approval**: Part of VetAssist Phase 1 MVP (APPROVED 5-0-2)
**Depends On**: VETASSIST-COND-001 (Condition Database)

---

## Executive Summary

Build an evidence checklist system that tells veterans exactly what documentation they need for each claimed condition. This is the #1 blocker identified in VA's own research - 40% of veterans abandon claims at the documentation step.

**Why This Matters**:
- Veterans don't know what records are needed
- Confusion between VA vs. private medical records
- No clear guidance on nexus letters vs. buddy statements
- Evidence requirements vary by condition type

---

## Evidence Types

### Core Evidence Categories

| ID | Type | Description | Priority |
|----|------|-------------|----------|
| STR | Service Treatment Records | Medical records from active duty | Required |
| VMR | VA Medical Records | Records from VA healthcare | Required (if applicable) |
| PMR | Private Medical Records | Records from civilian doctors | Helpful |
| DBQ | Disability Benefits Questionnaire | Standardized medical exam form | Highly Recommended |
| NEX | Nexus Letter | Doctor's statement linking condition to service | Critical for most claims |
| BUD | Buddy Statement | Witness statement from fellow service member | Helpful |
| PER | Personal Statement (21-4138) | Veteran's own account | Required |
| DIS | Discharge Papers (DD-214) | Proof of service dates/locations | Required |
| MED | Medical Evidence | Current diagnosis documentation | Required |
| PHO | Photos/Documentation | Visual evidence of condition | Helpful |

### Evidence Priority Levels

```python
class EvidencePriority:
    REQUIRED = "required"        # Claim likely denied without this
    CRITICAL = "critical"        # Strongly impacts decision
    RECOMMENDED = "recommended"  # Improves chances significantly
    HELPFUL = "helpful"          # Nice to have, not decisive
    OPTIONAL = "optional"        # Only for specific circumstances
```

---

## Database Schema

### PostgreSQL Schema (on bluefin)

```sql
-- Evidence types reference table
CREATE TABLE IF NOT EXISTS vetassist_evidence_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,    -- STR, VMR, DBQ, etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    how_to_obtain TEXT,                   -- Instructions for veteran
    typical_wait_time VARCHAR(50),        -- "2-4 weeks", "Same day", etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Condition to evidence mapping
CREATE TABLE IF NOT EXISTS vetassist_evidence_requirements (
    id SERIAL PRIMARY KEY,
    condition_id INTEGER REFERENCES vetassist_conditions(id),
    evidence_type_code VARCHAR(10) REFERENCES vetassist_evidence_types(code),
    priority VARCHAR(20) NOT NULL,        -- required, critical, recommended, etc.
    notes TEXT,                           -- Condition-specific guidance
    alternative_if_unavailable TEXT,      -- What to do if can't get this
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(condition_id, evidence_type_code)
);

-- Veteran's evidence tracking (non-PII - just status)
-- Note: Actual documents stored on goldfin when available
CREATE TABLE IF NOT EXISTS vetassist_evidence_tracking (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,             -- Anonymous session reference
    condition_id INTEGER REFERENCES vetassist_conditions(id),
    evidence_type_code VARCHAR(10) REFERENCES vetassist_evidence_types(code),
    status VARCHAR(20) NOT NULL,          -- have, need, not_applicable, pending
    notes TEXT,                           -- Veteran's notes (non-PII)
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, condition_id, evidence_type_code)
);

-- Indexes
CREATE INDEX idx_evidence_req_condition ON vetassist_evidence_requirements(condition_id);
CREATE INDEX idx_evidence_tracking_session ON vetassist_evidence_tracking(session_id);
```

---

## Seed Data

### Evidence Types

```sql
INSERT INTO vetassist_evidence_types (code, name, description, how_to_obtain, typical_wait_time)
VALUES
('STR', 'Service Treatment Records',
 'Medical records from your time in service, including sick call visits, hospitalizations, and treatments.',
 'Request from National Personnel Records Center (NPRC) via SF-180 form, or through VA.gov.',
 '2-4 weeks (longer for older records)'),

('VMR', 'VA Medical Records',
 'Records from any VA healthcare facility visits.',
 'Request through MyHealtheVet, VA.gov, or your local VA medical center.',
 '1-2 weeks'),

('PMR', 'Private Medical Records',
 'Records from civilian doctors, hospitals, and specialists.',
 'Contact each healthcare provider directly. You may need to sign a release form.',
 'Varies by provider'),

('DBQ', 'Disability Benefits Questionnaire',
 'Standardized VA form completed by a doctor documenting your condition severity.',
 'Ask your doctor to complete the DBQ for your condition. Forms available at VA.gov.',
 'Depends on doctor availability'),

('NEX', 'Nexus Letter',
 'A letter from a doctor stating your condition is "at least as likely as not" connected to your service.',
 'Request from your treating physician or a medical specialist. May require an appointment.',
 '1-4 weeks'),

('BUD', 'Buddy Statement',
 'Written statement from someone who witnessed your condition or its cause during service.',
 'Ask fellow service members, family, or friends who have knowledge of your condition.',
 'Immediate (if contact available)'),

('PER', 'Personal Statement (VA Form 21-4138)',
 'Your own written account describing your condition, its onset, and impact on your life.',
 'Write using the VetAssist Personal Statement Builder or VA Form 21-4138.',
 'Immediate'),

('DIS', 'Discharge Papers (DD-214)',
 'Your Certificate of Release or Discharge from Active Duty.',
 'Request from NPRC if you do not have a copy. Veterans can also access via VA.gov.',
 '1-2 weeks'),

('MED', 'Current Medical Diagnosis',
 'Documentation from a doctor confirming your current diagnosis.',
 'Schedule an appointment with your doctor for evaluation and diagnosis.',
 'Varies by appointment availability'),

('PHO', 'Photos/Documentation',
 'Visual evidence such as photos of scars, skin conditions, or equipment.',
 'Take clear photos with good lighting. Include a ruler for scale if applicable.',
 'Immediate')

ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    how_to_obtain = EXCLUDED.how_to_obtain,
    typical_wait_time = EXCLUDED.typical_wait_time;
```

---

## Condition-Specific Evidence Maps

### Evidence Requirements by Condition Category

```python
# Default evidence requirements by category
EVIDENCE_BY_CATEGORY = {
    "Mental Health": {
        "required": ["STR", "PER", "MED"],
        "critical": ["NEX", "DBQ"],
        "recommended": ["VMR", "PMR", "BUD"],
        "notes": {
            "STR": "Include any mental health visits, counseling, or medication records",
            "NEX": "Nexus letters are critical for PTSD claims without combat documentation",
            "BUD": "Buddy statements can document behavior changes observed by others"
        }
    },
    "Musculoskeletal": {
        "required": ["STR", "PER", "MED"],
        "critical": ["DBQ", "NEX"],
        "recommended": ["VMR", "PMR"],
        "helpful": ["PHO"],
        "notes": {
            "DBQ": "Use the appropriate joint DBQ (knee, shoulder, etc.)",
            "PHO": "Photos of scars, swelling, or limited range of motion can help"
        }
    },
    "Respiratory": {
        "required": ["STR", "PER", "MED"],
        "critical": ["DBQ", "NEX"],
        "recommended": ["VMR"],
        "notes": {
            "DBQ": "Pulmonary function test (PFT) results are essential",
            "NEX": "Critical for toxic exposure claims (burn pits, Agent Orange)"
        }
    },
    "Hearing/Vision": {
        "required": ["STR", "PER", "MED"],
        "critical": ["DBQ"],
        "recommended": ["VMR"],
        "notes": {
            "STR": "Entry and exit audiograms are highly valuable",
            "DBQ": "Audiogram and speech discrimination test required"
        }
    },
    "Skin": {
        "required": ["STR", "PER", "MED"],
        "recommended": ["DBQ", "PMR"],
        "helpful": ["PHO"],
        "notes": {
            "PHO": "Document affected areas with clear photos during flare-ups"
        }
    },
    "Toxic Exposure": {
        "required": ["STR", "PER", "MED", "DIS"],
        "critical": ["NEX"],
        "recommended": ["DBQ", "VMR"],
        "notes": {
            "DIS": "DD-214 proves service dates/locations for presumptive eligibility",
            "NEX": "Less critical if condition is presumptive under PACT Act"
        }
    }
}

# Special case: Presumptive conditions require less evidence
PRESUMPTIVE_REQUIREMENTS = {
    "required": ["DIS", "PER", "MED"],
    "recommended": ["DBQ"],
    "notes": {
        "NEX": "Nexus letter NOT required for presumptive conditions",
        "DIS": "DD-214 proves service during qualifying period/location"
    }
}
```

### Load Evidence Requirements

```python
import psycopg2

def load_evidence_requirements(conn_string: str):
    """Load condition-to-evidence mappings based on category."""
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Get all conditions
    cur.execute("SELECT id, va_name, category, presumptive_eligible FROM vetassist_conditions")
    conditions = cur.fetchall()

    for cond_id, name, category, is_presumptive in conditions:
        # Use presumptive requirements if applicable
        if is_presumptive:
            evidence_map = PRESUMPTIVE_REQUIREMENTS
        else:
            evidence_map = EVIDENCE_BY_CATEGORY.get(category, EVIDENCE_BY_CATEGORY["Musculoskeletal"])

        # Insert evidence requirements for each priority level
        for priority, evidence_codes in evidence_map.items():
            if priority == "notes":
                continue
            for code in evidence_codes:
                notes = evidence_map.get("notes", {}).get(code, None)
                cur.execute("""
                    INSERT INTO vetassist_evidence_requirements
                    (condition_id, evidence_type_code, priority, notes)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (condition_id, evidence_type_code) DO UPDATE SET
                        priority = EXCLUDED.priority,
                        notes = EXCLUDED.notes
                """, (cond_id, code, priority, notes))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded evidence requirements for {len(conditions)} conditions")
```

---

## API Endpoints

### Get Evidence Checklist

```
POST /v1/vetassist/evidence-checklist
```

#### Request

```json
{
  "conditions": [
    {"condition_id": 142, "side": "left"},
    {"condition_id": 89}
  ],
  "session_id": "optional-uuid-for-tracking"
}
```

#### Response

```json
{
  "checklist": [
    {
      "condition": "Knee strain, left",
      "condition_id": 142,
      "is_presumptive": false,
      "evidence": [
        {
          "type": "STR",
          "name": "Service Treatment Records",
          "priority": "required",
          "status": null,
          "description": "Medical records from your time in service",
          "how_to_obtain": "Request from NPRC via SF-180 form",
          "typical_wait_time": "2-4 weeks",
          "notes": "Include any knee-related visits, injuries, or complaints"
        },
        {
          "type": "DBQ",
          "name": "Disability Benefits Questionnaire",
          "priority": "critical",
          "status": null,
          "description": "Standardized VA form documenting condition severity",
          "how_to_obtain": "Ask your doctor to complete the DBQ",
          "notes": "Use the Knee and Lower Leg DBQ form"
        }
      ]
    }
  ],
  "summary": {
    "total_conditions": 2,
    "total_evidence_items": 14,
    "required_items": 6,
    "critical_items": 4,
    "recommended_items": 4
  },
  "audit_hash": "abc123def456"
}
```

### Update Evidence Status

```
POST /v1/vetassist/evidence-status
```

#### Request

```json
{
  "session_id": "uuid",
  "updates": [
    {"condition_id": 142, "evidence_type": "STR", "status": "have"},
    {"condition_id": 142, "evidence_type": "DBQ", "status": "pending"}
  ]
}
```

#### Response

```json
{
  "updated": 2,
  "progress": {
    "condition_id": 142,
    "condition": "Knee strain, left",
    "have": 2,
    "need": 4,
    "pending": 1,
    "not_applicable": 0,
    "completion_percentage": 33
  }
}
```

---

## Implementation

### Gateway Integration

```python
from flask import Flask, request, jsonify
import psycopg2
import hashlib
import json

@app.route('/v1/vetassist/evidence-checklist', methods=['POST'])
def evidence_checklist():
    """Get evidence requirements for selected conditions."""
    data = request.get_json()
    conditions = data.get('conditions', [])
    session_id = data.get('session_id')

    if not conditions:
        return jsonify({"error": "At least one condition required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    checklist = []
    for cond in conditions:
        cond_id = cond.get('condition_id')

        # Get condition info
        cur.execute("""
            SELECT va_name, category, presumptive_eligible
            FROM vetassist_conditions WHERE id = %s
        """, (cond_id,))
        cond_info = cur.fetchone()

        if not cond_info:
            continue

        va_name, category, is_presumptive = cond_info

        # Get evidence requirements
        cur.execute("""
            SELECT
                er.evidence_type_code,
                et.name,
                er.priority,
                et.description,
                et.how_to_obtain,
                et.typical_wait_time,
                er.notes,
                er.alternative_if_unavailable
            FROM vetassist_evidence_requirements er
            JOIN vetassist_evidence_types et ON er.evidence_type_code = et.code
            WHERE er.condition_id = %s
            ORDER BY
                CASE er.priority
                    WHEN 'required' THEN 1
                    WHEN 'critical' THEN 2
                    WHEN 'recommended' THEN 3
                    WHEN 'helpful' THEN 4
                    ELSE 5
                END
        """, (cond_id,))
        evidence = cur.fetchall()

        # Get tracking status if session provided
        status_map = {}
        if session_id:
            cur.execute("""
                SELECT evidence_type_code, status
                FROM vetassist_evidence_tracking
                WHERE session_id = %s AND condition_id = %s
            """, (session_id, cond_id))
            for row in cur.fetchall():
                status_map[row[0]] = row[1]

        evidence_list = []
        for row in evidence:
            evidence_list.append({
                "type": row[0],
                "name": row[1],
                "priority": row[2],
                "description": row[3],
                "how_to_obtain": row[4],
                "typical_wait_time": row[5],
                "notes": row[6],
                "alternative": row[7],
                "status": status_map.get(row[0])
            })

        checklist.append({
            "condition": va_name,
            "condition_id": cond_id,
            "is_presumptive": is_presumptive,
            "evidence": evidence_list
        })

    # Calculate summary
    total_items = sum(len(c["evidence"]) for c in checklist)
    required = sum(1 for c in checklist for e in c["evidence"] if e["priority"] == "required")
    critical = sum(1 for c in checklist for e in c["evidence"] if e["priority"] == "critical")
    recommended = sum(1 for c in checklist for e in c["evidence"] if e["priority"] == "recommended")

    cur.close()
    conn.close()

    return jsonify({
        "checklist": checklist,
        "summary": {
            "total_conditions": len(checklist),
            "total_evidence_items": total_items,
            "required_items": required,
            "critical_items": critical,
            "recommended_items": recommended
        },
        "audit_hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    })


@app.route('/v1/vetassist/evidence-status', methods=['POST'])
def evidence_status():
    """Update evidence tracking status for a session."""
    data = request.get_json()
    session_id = data.get('session_id')
    updates = data.get('updates', [])

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    updated = 0
    for update in updates:
        cur.execute("""
            INSERT INTO vetassist_evidence_tracking
            (session_id, condition_id, evidence_type_code, status, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (session_id, condition_id, evidence_type_code) DO UPDATE SET
                status = EXCLUDED.status,
                updated_at = NOW()
        """, (
            session_id,
            update.get('condition_id'),
            update.get('evidence_type'),
            update.get('status')
        ))
        updated += 1

    conn.commit()

    # Get progress for first condition
    first_cond = updates[0].get('condition_id') if updates else None
    progress = None
    if first_cond:
        cur.execute("""
            SELECT
                c.va_name,
                COUNT(*) FILTER (WHERE t.status = 'have') as have,
                COUNT(*) FILTER (WHERE t.status = 'need') as need,
                COUNT(*) FILTER (WHERE t.status = 'pending') as pending,
                COUNT(*) FILTER (WHERE t.status = 'not_applicable') as na
            FROM vetassist_evidence_tracking t
            JOIN vetassist_conditions c ON t.condition_id = c.id
            WHERE t.session_id = %s AND t.condition_id = %s
            GROUP BY c.va_name
        """, (session_id, first_cond))
        row = cur.fetchone()
        if row:
            total = row[1] + row[2] + row[3]
            progress = {
                "condition_id": first_cond,
                "condition": row[0],
                "have": row[1],
                "need": row[2],
                "pending": row[3],
                "not_applicable": row[4],
                "completion_percentage": int((row[1] / total * 100) if total > 0 else 0)
            }

    cur.close()
    conn.close()

    return jsonify({
        "updated": updated,
        "progress": progress
    })
```

---

## UI Component Specification

### Evidence Checklist Card

```
┌─────────────────────────────────────────────────────────────────┐
│  Evidence Checklist for: Knee strain, left                      │
│  Progress: ████████░░░░░░░░ 47% Complete                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REQUIRED (must have for claim)                                  │
│                                                                  │
│  ☑ Service Treatment Records                    [Have]          │
│    Include any knee-related visits or injuries                  │
│    How to get: Request from NPRC via SF-180 (2-4 weeks)        │
│                                                                  │
│  ☑ Personal Statement (21-4138)                 [Have]          │
│    Your written account of the injury and impact               │
│    How to get: Use VetAssist Statement Builder                 │
│                                                                  │
│  ☐ Current Medical Diagnosis                    [Need]          │
│    Documentation confirming your current diagnosis              │
│    How to get: Schedule appointment with your doctor           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CRITICAL (strongly recommended)                                 │
│                                                                  │
│  ⏳ Disability Benefits Questionnaire           [Pending]        │
│    Use the Knee and Lower Leg DBQ form                         │
│    How to get: Ask your doctor to complete                     │
│                                                                  │
│  ☐ Nexus Letter                                 [Need]          │
│    Doctor's statement linking condition to service              │
│    How to get: Request from treating physician                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RECOMMENDED (improves your claim)                               │
│                                                                  │
│  ☐ VA Medical Records                           [Need]          │
│  ☐ Buddy Statement                              [N/A]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Status Options

| Status | Icon | Meaning |
|--------|------|---------|
| `have` | ☑ | Veteran has this document |
| `need` | ☐ | Still needs to obtain |
| `pending` | ⏳ | Requested, waiting to receive |
| `not_applicable` | N/A | Doesn't apply to this claim |

---

## Validation Checklist

- [ ] Evidence types table seeded with all 10 types
- [ ] Evidence requirements mapped for all condition categories
- [ ] Presumptive conditions have reduced requirements (no nexus)
- [ ] API returns sorted by priority (required first)
- [ ] Session tracking works across multiple requests
- [ ] Progress percentage calculates correctly
- [ ] SHA-256 audit hash on all responses
- [ ] "How to obtain" instructions are clear and actionable
- [ ] Wait times are realistic

---

## Files to Create

| File | Location | Purpose |
|------|----------|---------|
| `evidence_schema.sql` | `/ganuda/sql/` | Database schema |
| `seed_evidence_types.sql` | `/ganuda/sql/` | Evidence type seed data |
| `load_evidence_requirements.py` | `/ganuda/scripts/` | Load condition mappings |
| Gateway routes | `/ganuda/services/llm_gateway/gateway.py` | API endpoints |

---

## Related Documents

- JR-VetAssist-Condition-Database.md (dependency)
- VetAssist PRD v2.0 (feature spec)
- [VA Evidence Requirements](https://www.va.gov/disability/how-to-file-claim/evidence-needed/)

---

*For Seven Generations*
