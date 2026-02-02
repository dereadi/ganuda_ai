# Jr Instruction: VetAssist VA Form Auto-Fill with PyPDFForm

**Date:** 2026-01-30
**Priority:** Tier 1 — High Impact
**Council Vote:** `23589699dd7b4a97` (confidence 0.873)
**Assigned To:** Software Engineer Jr.
**Depends On:** Existing wizard forms at `/wizard/`

## Objective

Integrate `PyPDFForm` to programmatically fill VA disability claim forms (21-526EZ, 21-0781, 21-4138) from wizard answers, so veterans download pre-filled PDFs ready for submission.

## Background

- VetAssist wizard currently guides veterans through form questions but produces instructions only
- `PyPDFForm` (MIT license) is a pure Python library for filling PDF form fields
- VA forms are available as fillable PDFs from va.gov
- `abd-vro` (VA's own CC0 repo) provides reference data for claims automation

## Steps

### Step 1: Install PyPDFForm

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install PyPDFForm
pip freeze > requirements.txt
```

### Step 2: Download VA form templates

**Directory to create:** `/ganuda/vetassist/backend/app/static/va_forms/`

Download these fillable PDFs from va.gov:
- `VA-21-526EZ.pdf` — Application for Disability Compensation
- `VA-21-0781.pdf` — Statement in Support of Claim for PTSD
- `VA-21-4138.pdf` — Statement in Support of Claim
- `VA-21-4142.pdf` — Authorization to Disclose Information

Store them in the static directory. These are public government forms.

### Step 3: Create form field mapping configuration

**File to create:** `/ganuda/vetassist/backend/app/services/va_form_mappings.py`

Map wizard answer keys to PDF form field names. Example structure:

```python
FORM_MAPPINGS = {
    "21-526EZ": {
        "veteran_name": "topmostSubform[0].Page1[0].VeteranName[0]",
        "ssn": "topmostSubform[0].Page1[0].SSN[0]",
        "date_of_birth": "topmostSubform[0].Page1[0].DOB[0]",
        "address_street": "topmostSubform[0].Page1[0].Address[0]",
        # ... map all fields
    },
    "21-0781": {
        # PTSD form field mappings
    },
    "21-4138": {
        # Statement in support field mappings
    }
}
```

To discover field names, use:
```python
from PyPDFForm import PdfWrapper
fields = PdfWrapper("VA-21-526EZ.pdf").schema
print(fields)  # Shows all field names and types
```

### Step 4: Create form filler service

**File to create:** `/ganuda/vetassist/backend/app/services/va_form_filler.py`

This service should:
1. Accept a form type (e.g., "21-526EZ") and a dict of wizard answers
2. Look up the form template PDF from static directory
3. Map wizard answers to PDF field names using the mapping config
4. Fill the PDF using PyPDFForm:
   ```python
   from PyPDFForm import PdfWrapper
   filled = PdfWrapper(template_path).fill(field_mapping)
   filled.stream.seek(0)
   return filled.stream.read()
   ```
5. Return the filled PDF as bytes
6. Log which fields were filled vs. left empty with `[FORMFILL]` prefix

### Step 5: Add form generation endpoint

**File to modify:** `/ganuda/vetassist/backend/app/api/endpoints/wizard.py`

Add new endpoint:
```
POST /api/wizard/generate-form
Body: { "form_type": "21-526EZ", "answers": { ... } }
Response: PDF file download
```

This endpoint should:
1. Validate form_type is in supported list
2. Call form filler service with answers
3. Return PDF as `StreamingResponse` with `application/pdf` content type
4. Set `Content-Disposition` header for download filename
5. Require authentication

### Step 6: Add frontend download button

**File to modify:** `/ganuda/vetassist/frontend/src/app/wizard/` (appropriate step component)

After wizard completion, show a "Download Pre-Filled Form" button that:
1. Calls the generate-form endpoint with collected answers
2. Triggers browser PDF download
3. Shows loading state while generating
4. Shows error message if generation fails

## Security Requirements (Crawdad)

- PII in wizard answers must be handled according to existing PII protection policies
- Pre-filled PDFs should NOT be stored on server — generate on-demand and stream to client
- All form generation happens on-premise (PyPDFForm is pure Python, no external calls)
- Authentication required for form generation endpoint

## Verification

1. Complete wizard for 21-526EZ → download PDF → verify fields are populated
2. Try generating with missing fields → verify partial fill works (empty fields left blank)
3. Try generating with invalid form type → verify 400 error
4. Verify PDF file is not cached on server after download

## For Seven Generations

Pre-filled VA forms reduce the most tedious part of claims filing — manually copying information into government paperwork. This directly increases claim completion rates.
