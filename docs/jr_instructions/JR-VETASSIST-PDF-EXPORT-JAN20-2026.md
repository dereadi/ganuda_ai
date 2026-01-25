# Jr Instruction: VetAssist PDF Generation/Export

**Priority**: 2 of 3
**Council Audit**: 3b690ed593a16433
**Estimated Complexity**: Medium
**Parent ULTRATHINK**: ULTRATHINK-VETASSIST-SPRINT2-JAN20-2026.md

## Objective

Generate filled PDF forms from completed wizard sessions, allowing veterans to download ready-to-submit VA forms.

## Prerequisites

- VetAssist backend running
- Wizard sessions with completed data
- Auth integration (Priority 1) completed

## Tasks

### Task 1: Install PDF Dependencies

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install reportlab PyPDF2 pdfrw
```

### Task 2: Download VA Form Templates

Download official VA form PDFs and store in `/ganuda/vetassist/backend/templates/forms/`:

- 21-526EZ: https://www.va.gov/vaforms/va/pdf/VA21-526EZ.pdf
- 21-0995: https://www.va.gov/vaforms/va/pdf/VA21-0995.pdf
- 20-0996: https://www.va.gov/vaforms/va/pdf/VA20-0996.pdf
- 10182: https://www.va.gov/vaforms/va/pdf/VA10182.pdf

```bash
mkdir -p /ganuda/vetassist/backend/templates/forms
cd /ganuda/vetassist/backend/templates/forms
curl -O https://www.va.gov/vaforms/va/pdf/VA21-526EZ.pdf
curl -O https://www.va.gov/vaforms/va/pdf/VA21-0995.pdf
curl -O https://www.va.gov/vaforms/va/pdf/VA20-0996.pdf
curl -O https://www.va.gov/vaforms/va/pdf/VA10182.pdf
```

### Task 3: Create PDF Service

Create `/ganuda/vetassist/backend/app/services/pdf_service.py`:

```python
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from pdfrw import PdfReader as PdfrwReader, PdfWriter as PdfrwWriter, PageMerge
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

TEMPLATES_DIR = "/ganuda/vetassist/backend/templates/forms"
EXPORTS_DIR = "/ganuda/vetassist/exports"

os.makedirs(EXPORTS_DIR, exist_ok=True)

# Field mappings: wizard field -> PDF form field name
FIELD_MAPPINGS = {
    "21-526EZ": {
        "full_name": "form1[0].#subform[0].VeteransLastName[0]",
        "ssn": "form1[0].#subform[0].VeteransSocialSecurityNumber[0]",
        "date_of_birth": "form1[0].#subform[0].VeteransDateOfBirth[0]",
        "branch": "form1[0].#subform[0].BranchOfService[0]",
        "service_start": "form1[0].#subform[0].DateEnteredActiveService[0]",
        "service_end": "form1[0].#subform[0].DateReleasedFromActiveService[0]",
        # Add more mappings as discovered
    },
    "21-0995": {
        "prior_claim_id": "form1[0].#subform[0].PriorClaimNumber[0]",
        "decision_date": "form1[0].#subform[0].DateOfDecision[0]",
        # Add mappings
    },
    "20-0996": {
        "decision_date": "form1[0].#subform[0].DateOfDecision[0]",
        "error_type": "form1[0].#subform[0].ErrorType[0]",
        # Add mappings
    },
    "10182": {
        "appeal_lane": "form1[0].#subform[0].AppealLane[0]",
        # Add mappings
    }
}


class PDFService:
    def __init__(self):
        self.templates_dir = TEMPLATES_DIR
        self.exports_dir = EXPORTS_DIR

    def fill_form(self, wizard_type: str, session_id: str, form_data: Dict[str, Any]) -> str:
        """
        Fill a VA form template with wizard data and save to exports.

        Returns: Path to generated PDF
        """
        template_path = os.path.join(self.templates_dir, f"VA{wizard_type}.pdf")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        output_path = os.path.join(self.exports_dir, f"{session_id}_{wizard_type}.pdf")

        # Get field mappings for this form type
        mappings = FIELD_MAPPINGS.get(wizard_type, {})

        try:
            # Read template
            reader = PdfReader(template_path)
            writer = PdfWriter()

            # Fill form fields
            for page in reader.pages:
                writer.add_page(page)

            # Update form fields
            field_values = {}
            for wizard_field, pdf_field in mappings.items():
                if wizard_field in form_data:
                    field_values[pdf_field] = form_data[wizard_field]

            writer.update_page_form_field_values(writer.pages[0], field_values)

            # Write output
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            logger.info(f"Generated PDF: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise

    def generate_summary(self, wizard_type: str, session_id: str, form_data: Dict[str, Any]) -> str:
        """
        Generate a summary document with all claim information.

        Returns: Path to generated PDF
        """
        output_path = os.path.join(self.exports_dir, f"{session_id}_summary.pdf")

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, f"VetAssist Claim Summary")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Form: {wizard_type}")
        c.drawString(50, height - 85, f"Session: {session_id}")

        # Form data
        y = height - 120
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Claim Information")
        y -= 20

        c.setFont("Helvetica", 11)
        for key, value in form_data.items():
            if y < 50:  # New page if needed
                c.showPage()
                y = height - 50

            # Format key nicely
            label = key.replace("_", " ").title()
            c.drawString(50, y, f"{label}: {value}")
            y -= 15

        c.save()

        # Write to file
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())

        return output_path


pdf_service = PDFService()
```

### Task 4: Create Export Endpoint

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`:

```python
from fastapi.responses import FileResponse
from app.services.pdf_service import pdf_service

@router.get("/{session_id}/export/pdf")
def export_pdf(session_id: str):
    """Generate and download filled VA form PDF"""
    # Get session data
    conn = get_db_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT wizard_type, answers FROM vetassist_wizard_sessions
            WHERE session_id = %s AND status = 'completed'
        """, (session_id,))
        session = cur.fetchone()
    conn.close()

    if not session:
        raise HTTPException(status_code=404, detail="Completed session not found")

    wizard_type = session['wizard_type']
    form_data = session['answers'] if isinstance(session['answers'], dict) else json.loads(session['answers'])

    try:
        pdf_path = pdf_service.fill_form(wizard_type, session_id, form_data)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"VA{wizard_type}_{session_id[:8]}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{session_id}/export/summary")
def export_summary(session_id: str):
    """Generate and download claim summary PDF"""
    # Similar implementation
    pass
```

### Task 5: Frontend Download Button

Update `/ganuda/vetassist/frontend/app/wizard/[sessionId]/complete/page.tsx` to add real download functionality:

```tsx
const downloadPDF = async () => {
  try {
    const response = await fetch(`${apiUrl}/wizard/${sessionId}/export/pdf`);
    if (!response.ok) throw new Error('Download failed');

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `VA_Claim_${sessionId.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    setError('Failed to download PDF');
  }
};
```

### Task 6: Field Mapping Discovery

For each form type, use a PDF inspection tool to discover actual field names:

```python
from PyPDF2 import PdfReader

reader = PdfReader("/ganuda/vetassist/backend/templates/forms/VA21-526EZ.pdf")
fields = reader.get_fields()
for name, field in fields.items():
    print(f"{name}: {field}")
```

Document discovered field names in `/ganuda/docs/vetassist/VA-FORM-FIELD-MAPPINGS.md`.

## Validation

1. Complete a 21-526EZ wizard session
2. Call `/api/v1/wizard/{session_id}/export/pdf`
3. Verify PDF opens and contains entered data
4. Test download from completion page
5. Verify all 4 form types generate correctly

## Files to Create/Modify

- `backend/app/services/pdf_service.py` (NEW)
- `backend/app/api/v1/endpoints/wizard.py` (MODIFY - add export endpoints)
- `backend/templates/forms/` (NEW - VA form PDFs)
- `frontend/app/wizard/[sessionId]/complete/page.tsx` (MODIFY - real download)

## Notes

- VA forms may have complex nested field structures
- Some forms may need flattening after fill
- Consider watermark "DRAFT - NOT FOR SUBMISSION" until user confirms

## Report Back

When complete, update Jr work queue with:
- Field mappings discovered per form
- Test results for each form type
- Any forms that need special handling
