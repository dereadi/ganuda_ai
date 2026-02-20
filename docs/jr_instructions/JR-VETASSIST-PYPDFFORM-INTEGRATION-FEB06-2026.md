# Jr Instruction: VetAssist PyPDFForm VA Form Automation

**ID:** JR-VETASSIST-PYPDFFORM-INTEGRATION-FEB06-2026
**Priority:** P0-B (Phase 1)
**Estimated Effort:** 4-6 hours
**Council Approval:** Conditional Approve (79.4%, audit hash: 0cc1c5d0138a8d6d)
**Ultrathink Reference:** ULTRATHINK-VETASSIST-PHASE1-ENHANCEMENTS-FEB06-2026.md

---

## Objective

Integrate PyPDFForm library to auto-fill VA disability forms (21-526EZ, 21-0781) from data veterans have already entered in the VetAssist wizard. This eliminates manual re-entry and reduces errors.

---

## Context

Veterans currently must manually fill 13+ page VA forms. VetAssist already collects this data during the wizard flow. PyPDFForm (MIT license) can populate PDF form fields programmatically.

**Security Note (Crawdad approved):**
- We provide blank VA form templates — users cannot upload their own
- Generated PDFs are temporary, not stored server-side
- PII handled per existing VetAssist security patterns

---

## Prerequisites

1. VetAssist backend running on redfin (192.168.132.223)
2. Access to `/ganuda/vetassist/backend/` directory
3. Blank VA form PDFs downloaded from va.gov

---

## Step 1: Install PyPDFForm

**On redfin:**

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install pypdfform
pip freeze | grep -i pypdfform  # Verify installation
```

---

## Step 2: Download VA Form Templates

**Create templates directory:**

```bash
mkdir -p /ganuda/vetassist/templates/va_forms
cd /ganuda/vetassist/templates/va_forms
```

**Download current VA forms:**

```bash
# VA Form 21-526EZ (Application for Disability Compensation)
curl -L "https://www.vba.va.gov/pubs/forms/VBA-21-526EZ-ARE.pdf" -o 21-526EZ.pdf

# VA Form 21-0781 (Statement in Support of Claim for PTSD)
curl -L "https://www.vba.va.gov/pubs/forms/VBA-21-0781-ARE.pdf" -o 21-0781.pdf

# VA Form 21-0781a (Statement in Support of Claim for PTSD Secondary to Personal Assault)
curl -L "https://www.vba.va.gov/pubs/forms/VBA-21-0781a-ARE.pdf" -o 21-0781a.pdf
```

**Verify downloads:**

```bash
ls -la /ganuda/vetassist/templates/va_forms/
# Should show 3 PDF files
```

---

## Step 3: Inspect Form Fields

Before mapping, inspect available form fields:

```python
# Run in Python to get field names
from pypdfform import PdfWrapper

# Inspect 21-526EZ
pdf = PdfWrapper("/ganuda/vetassist/templates/va_forms/21-526EZ.pdf")
print("21-526EZ Fields:")
for field in pdf.schema:
    print(f"  {field}")

# Inspect 21-0781
pdf = PdfWrapper("/ganuda/vetassist/templates/va_forms/21-0781.pdf")
print("21-0781 Fields:")
for field in pdf.schema:
    print(f"  {field}")
```

**Document the actual field names** — VA form field IDs may differ from display labels.

---

## Step 4: Create Form Generator Service

**Path:** `/ganuda/vetassist/backend/app/services/form_generator.py`

```python
"""
VA Form Generator Service
Generates pre-filled VA disability forms from VetAssist data.

Security:
- Templates are read-only, provided by us
- Generated PDFs are temporary, cleaned up after response
- PII is never logged
"""

import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pypdfform import PdfWrapper

logger = logging.getLogger(__name__)

# Template paths
TEMPLATE_DIR = "/ganuda/vetassist/templates/va_forms"
TEMPLATES = {
    "21-526EZ": os.path.join(TEMPLATE_DIR, "21-526EZ.pdf"),
    "21-0781": os.path.join(TEMPLATE_DIR, "21-0781.pdf"),
    "21-0781a": os.path.join(TEMPLATE_DIR, "21-0781a.pdf"),
}


class FormGeneratorError(Exception):
    """Raised when form generation fails."""
    pass


class VAFormGenerator:
    """Generates pre-filled VA forms from VetAssist data."""

    def __init__(self):
        self._validate_templates()

    def _validate_templates(self):
        """Ensure all template files exist."""
        for form_id, path in TEMPLATES.items():
            if not os.path.exists(path):
                logger.error(f"Template missing: {form_id} at {path}")
                raise FormGeneratorError(f"Template not found: {form_id}")

    def get_available_forms(self) -> list[str]:
        """Return list of available form types."""
        return list(TEMPLATES.keys())

    def generate_form(
        self,
        form_type: str,
        user_data: Dict[str, Any],
        wizard_data: Dict[str, Any],
    ) -> bytes:
        """
        Generate a filled VA form.

        Args:
            form_type: Form identifier (e.g., "21-526EZ")
            user_data: User profile data (name, SSN, DOB, etc.)
            wizard_data: Wizard session data (conditions, stressors, etc.)

        Returns:
            Filled PDF as bytes

        Raises:
            FormGeneratorError: If generation fails
        """
        if form_type not in TEMPLATES:
            raise FormGeneratorError(f"Unknown form type: {form_type}")

        template_path = TEMPLATES[form_type]

        try:
            # Load template
            pdf = PdfWrapper(template_path)

            # Map data to form fields based on form type
            if form_type == "21-526EZ":
                field_data = self._map_526ez_fields(user_data, wizard_data)
            elif form_type == "21-0781":
                field_data = self._map_0781_fields(user_data, wizard_data)
            elif form_type == "21-0781a":
                field_data = self._map_0781a_fields(user_data, wizard_data)
            else:
                raise FormGeneratorError(f"No field mapping for: {form_type}")

            # Fill the form
            pdf.fill(field_data)

            # Generate to temp file (PyPDFForm requires file output)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name

            pdf.draw().save(tmp_path)

            # Read back as bytes
            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()

            # Clean up temp file
            os.unlink(tmp_path)

            logger.info(f"Generated {form_type} form successfully")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Form generation failed: {e}")
            raise FormGeneratorError(f"Failed to generate {form_type}: {str(e)}")

    def _map_526ez_fields(
        self, user_data: Dict[str, Any], wizard_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map VetAssist data to VA Form 21-526EZ fields.

        NOTE: Field names below are examples. Run field inspection
        to get actual field IDs from the PDF.
        """
        # Format dates as MM/DD/YYYY for VA forms
        def format_date(date_str: Optional[str]) -> str:
            if not date_str:
                return ""
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%m/%d/%Y")
            except:
                return date_str

        # Build field mapping
        # TODO: Update these field names after running field inspection
        return {
            # Section I - Veteran Identification
            "F[0].Page_1[0].VeteransFirstName[0]": user_data.get("first_name", ""),
            "F[0].Page_1[0].VeteransMiddleName[0]": user_data.get("middle_name", ""),
            "F[0].Page_1[0].VeteransLastName[0]": user_data.get("last_name", ""),
            "F[0].Page_1[0].SSN[0]": user_data.get("ssn", ""),
            "F[0].Page_1[0].DateOfBirth[0]": format_date(user_data.get("dob")),
            "F[0].Page_1[0].VAFileNumber[0]": user_data.get("va_file_number", ""),

            # Contact Information
            "F[0].Page_1[0].MailingAddress_Street[0]": user_data.get("address_street", ""),
            "F[0].Page_1[0].MailingAddress_City[0]": user_data.get("address_city", ""),
            "F[0].Page_1[0].MailingAddress_State[0]": user_data.get("address_state", ""),
            "F[0].Page_1[0].MailingAddress_Zip[0]": user_data.get("address_zip", ""),
            "F[0].Page_1[0].Phone[0]": user_data.get("phone", ""),
            "F[0].Page_1[0].Email[0]": user_data.get("email", ""),

            # Service Information
            "F[0].Page_2[0].BranchOfService[0]": user_data.get("branch", ""),
            "F[0].Page_2[0].ServiceEntryDate[0]": format_date(user_data.get("service_start")),
            "F[0].Page_2[0].ServiceExitDate[0]": format_date(user_data.get("service_end")),

            # Claimed Conditions (up to 8 on first page)
            # These would be populated from wizard_data["claimed_conditions"]
        }

    def _map_0781_fields(
        self, user_data: Dict[str, Any], wizard_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map VetAssist data to VA Form 21-0781 (PTSD Stressor Statement).
        """
        stressor = wizard_data.get("stressor", {})

        return {
            # Veteran Info (repeated on this form)
            "VeteranName": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            "SSN": user_data.get("ssn", ""),

            # Stressor Information
            "DateOfIncident": stressor.get("date", ""),
            "LocationOfIncident": stressor.get("location", ""),
            "UnitAssignment": stressor.get("unit", ""),
            "StressorDescription": stressor.get("description", ""),

            # Witnesses (if provided)
            "WitnessName1": stressor.get("witness_1_name", ""),
            "WitnessAddress1": stressor.get("witness_1_address", ""),
        }

    def _map_0781a_fields(
        self, user_data: Dict[str, Any], wizard_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map VetAssist data to VA Form 21-0781a (PTSD Personal Assault).
        """
        # Similar structure to 0781 but with assault-specific fields
        stressor = wizard_data.get("stressor", {})

        return {
            "VeteranName": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}",
            "SSN": user_data.get("ssn", ""),
            "IncidentDescription": stressor.get("description", ""),
            "DateOfIncident": stressor.get("date", ""),
            "LocationOfIncident": stressor.get("location", ""),
            # Behavioral changes section
            "BehavioralChanges": stressor.get("behavioral_changes", ""),
        }


# Singleton instance
_generator: Optional[VAFormGenerator] = None


def get_form_generator() -> VAFormGenerator:
    """Get or create the form generator instance."""
    global _generator
    if _generator is None:
        _generator = VAFormGenerator()
    return _generator
```

---

## Step 5: Create API Endpoint

**Path:** `/ganuda/vetassist/backend/app/api/v1/endpoints/forms.py`

```python
"""
VA Form Generation API Endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.form_generator import get_form_generator, FormGeneratorError

logger = logging.getLogger(__name__)
router = APIRouter()


class FormGenerateRequest(BaseModel):
    form_type: str  # "21-526EZ", "21-0781", "21-0781a"
    session_id: Optional[str] = None  # If not provided, use current session


@router.get("/available")
async def list_available_forms(current_user=Depends(get_current_user)):
    """List available VA form types."""
    generator = get_form_generator()
    return {
        "forms": [
            {
                "id": "21-526EZ",
                "name": "Application for Disability Compensation",
                "description": "Main disability benefits application form",
            },
            {
                "id": "21-0781",
                "name": "Statement in Support of Claim for PTSD",
                "description": "PTSD stressor statement form",
            },
            {
                "id": "21-0781a",
                "name": "Statement in Support of Claim for PTSD (Personal Assault)",
                "description": "PTSD personal assault stressor form",
            },
        ]
    }


@router.post("/generate")
async def generate_form(
    request: FormGenerateRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Generate a pre-filled VA form.

    Returns the filled PDF as a downloadable file.
    """
    try:
        generator = get_form_generator()

        # Get user profile data
        user_data = {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "middle_name": getattr(current_user, "middle_name", ""),
            "ssn": current_user.ssn,  # Encrypted at rest
            "dob": str(current_user.dob) if current_user.dob else "",
            "email": current_user.email,
            "phone": getattr(current_user, "phone", ""),
            "address_street": getattr(current_user, "address_street", ""),
            "address_city": getattr(current_user, "address_city", ""),
            "address_state": getattr(current_user, "address_state", ""),
            "address_zip": getattr(current_user, "address_zip", ""),
            "branch": getattr(current_user, "branch_of_service", ""),
            "service_start": getattr(current_user, "service_start_date", ""),
            "service_end": getattr(current_user, "service_end_date", ""),
            "va_file_number": getattr(current_user, "va_file_number", ""),
        }

        # Get wizard session data
        # TODO: Implement session retrieval based on your session storage
        wizard_data = {}
        if request.session_id:
            # Query wizard session from database
            # wizard_data = await get_wizard_session(db, request.session_id, current_user.id)
            pass

        # Generate the form
        pdf_bytes = generator.generate_form(
            form_type=request.form_type,
            user_data=user_data,
            wizard_data=wizard_data,
        )

        # Log generation (no PII)
        logger.info(
            f"Form generated: type={request.form_type}, user_id={current_user.id}"
        )

        # Return PDF as downloadable file
        filename = f"VA_Form_{request.form_type}_{current_user.id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except FormGeneratorError as e:
        logger.error(f"Form generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating form: {e}")
        raise HTTPException(status_code=500, detail="Form generation failed")
```

---

## Step 6: Register Router

**Path:** `/ganuda/vetassist/backend/app/api/v1/api.py` (or main router file)

Add the forms router:

```python
from app.api.v1.endpoints import forms

api_router.include_router(
    forms.router,
    prefix="/forms",
    tags=["forms"],
)
```

---

## Step 7: Frontend Integration

**Add "Generate Form" button to wizard completion page.**

**Path:** Update the wizard completion component (e.g., `/ganuda/vetassist/frontend/app/wizard/complete/page.tsx`)

```tsx
'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'

interface FormOption {
  id: string
  name: string
  description: string
}

const AVAILABLE_FORMS: FormOption[] = [
  {
    id: '21-526EZ',
    name: 'VA Form 21-526EZ',
    description: 'Application for Disability Compensation and Related Benefits',
  },
  {
    id: '21-0781',
    name: 'VA Form 21-0781',
    description: 'Statement in Support of Claim for PTSD',
  },
]

export function FormGenerator({ sessionId }: { sessionId?: string }) {
  const { token } = useAuth()
  const [generating, setGenerating] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerateForm(formType: string) {
    setGenerating(formType)
    setError(null)

    try {
      const response = await fetch('/api/v1/forms/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          form_type: formType,
          session_id: sessionId,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate form')
      }

      // Download the PDF
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `VA_Form_${formType}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate form')
    } finally {
      setGenerating(null)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Generate Pre-Filled VA Forms
      </h2>
      <p className="text-gray-600 mb-6">
        Based on the information you provided, we can pre-fill your VA forms.
        Review the generated forms carefully before submitting to the VA.
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {AVAILABLE_FORMS.map((form) => (
          <div
            key={form.id}
            className="flex items-center justify-between border border-gray-200 rounded-lg p-4"
          >
            <div>
              <h3 className="font-medium text-gray-900">{form.name}</h3>
              <p className="text-sm text-gray-500">{form.description}</p>
            </div>
            <button
              onClick={() => handleGenerateForm(form.id)}
              disabled={generating !== null}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                generating === form.id
                  ? 'bg-gray-400 text-white cursor-wait'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {generating === form.id ? 'Generating...' : 'Generate PDF'}
            </button>
          </div>
        ))}
      </div>

      <p className="text-sm text-gray-500 mt-6">
        <strong>Note:</strong> Generated forms are pre-filled with your information
        but may require additional details. Always review before submission.
      </p>
    </div>
  )
}
```

---

## Verification Checklist

- [ ] PyPDFForm installed in venv (`pip list | grep pypdfform`)
- [ ] VA form templates downloaded to `/ganuda/vetassist/templates/va_forms/`
- [ ] Field inspection script run, field names documented
- [ ] `form_generator.py` created and tested standalone
- [ ] API endpoint `/api/v1/forms/generate` responds
- [ ] Frontend "Generate Form" button works
- [ ] Generated PDF opens correctly in PDF reader
- [ ] User data appears in correct form fields
- [ ] No PII logged in application logs
- [ ] Temp files cleaned up after generation

---

## Security Verification (Crawdad)

- [ ] Template PDFs are read-only (not user-uploadable)
- [ ] Generated PDFs not stored server-side (temp only)
- [ ] API endpoint requires authentication
- [ ] No SSN or sensitive data in logs
- [ ] File path validation prevents traversal

---

## Test Cases

1. **Happy path:** Generate 21-526EZ with full user data
2. **Partial data:** Generate form with some fields empty
3. **Invalid form type:** Request unknown form type → 400 error
4. **Unauthenticated:** Request without token → 401 error
5. **Missing template:** Remove template file → appropriate error

---

## Maintenance Notes

- **On VA form update:** Download new template, run field inspection, update mappings
- **Monitor:** VA form revision dates at https://www.va.gov/find-forms/
- **Template versions:** Store version metadata for audit trail

---

## Related Documents

- Ultrathink: ULTRATHINK-VETASSIST-PHASE1-ENHANCEMENTS-FEB06-2026.md
- Council Vote: Audit hash 0cc1c5d0138a8d6d
- PyPDFForm docs: https://github.com/chinapandaman/PyPDFForm

---

*For Seven Generations*
