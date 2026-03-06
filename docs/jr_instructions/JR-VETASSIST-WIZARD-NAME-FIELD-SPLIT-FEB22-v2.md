# Jr Instruction: VetAssist Wizard Name Field Split — Remaining Steps (v2)

**Task ID:** WIZARD-NAME-SPLIT-v2
**Kanban:** #1846
**Priority:** 4
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

The wizard field_map in wizard.py was already updated to use split name fields (first_name, middle_initial, last_name). Two remaining files still reference the old `full_name` field and need updating: OCR extraction prompts and PDF form field mappings.

---

## Step 1: Update DD-214 OCR extraction prompt to use split name fields

File: `/ganuda/vetassist/backend/app/services/ocr_service.py`

```python
<<<<<<< SEARCH
            "dd214": """Extract the following from this DD-214 document:
- full_name: Veteran's full name
- ssn_last4: Last 4 of SSN (if visible)
- branch: Branch of service
=======
            "dd214": """Extract the following from this DD-214 document:
- first_name: Veteran's first name
- middle_initial: Veteran's middle initial (single letter, if present)
- last_name: Veteran's last name
- ssn_last4: Last 4 of SSN (if visible)
- branch: Branch of service
>>>>>>> REPLACE
```

---

## Step 2: Update PDF form field mappings for 21-526EZ

File: `/ganuda/vetassist/backend/app/services/pdf_service.py`

```python
<<<<<<< SEARCH
    "21-526EZ": {
        "full_name": "form1[0].#subform[0].VeteransLastName[0]",
        "ssn": "form1[0].#subform[0].VeteransSocialSecurityNumber[0]",
        "date_of_birth": "form1[0].#subform[0].VeteransDateOfBirth[0]",
        "branch": "form1[0].#subform[0].BranchOfService[0]",
        "service_start": "form1[0].#subform[0].DateEnteredActiveService[0]",
        "service_end": "form1[0].#subform[0].DateReleasedFromActiveService[0]",
        # Add more mappings as discovered
    },
=======
    "21-526EZ": {
        "first_name": "form1[0].#subform[0].VeteransFirstName[0]",
        "middle_initial": "form1[0].#subform[0].VeteransMiddleInitial[0]",
        "last_name": "form1[0].#subform[0].VeteransLastName[0]",
        "ssn": "form1[0].#subform[0].VeteransSocialSecurityNumber[0]",
        "date_of_birth": "form1[0].#subform[0].VeteransDateOfBirth[0]",
        "branch": "form1[0].#subform[0].BranchOfService[0]",
        "service_start": "form1[0].#subform[0].DateEnteredActiveService[0]",
        "service_end": "form1[0].#subform[0].DateReleasedFromActiveService[0]",
        # Add more mappings as discovered
    },
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda && python3 -c "from vetassist.backend.app.services.ocr_service import OCRService; print('OCR service OK')"
```

```text
cd /ganuda && python3 -c "from vetassist.backend.app.services.pdf_service import PDFService; print('PDF service OK')"
```

## What NOT to Change

- Do NOT modify wizard.py field_map — it's already correct
- Do NOT modify the frontend step components
- Do NOT change medical/buddy/nexus extraction prompts — only DD-214 needs split names
