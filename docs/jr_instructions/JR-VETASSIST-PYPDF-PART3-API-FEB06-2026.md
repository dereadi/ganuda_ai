# Jr Instruction: PyPDFForm Part 3 — API Endpoint

**ID:** JR-VETASSIST-PYPDF-PART3-API-FEB06-2026
**Priority:** P0
**Part:** 3 of 4

---

## Objective

Create the API endpoint for form generation.

---

## Step 1: Create forms.py endpoint

**file: /ganuda/vetassist/backend/app/api/v1/endpoints/forms.py**
```python
"""VA Form Generation API"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

class FormRequest(BaseModel):
    form_type: str
    session_id: Optional[str] = None

@router.get("/available")
async def list_forms():
    from app.services.form_generator import get_form_generator
    gen = get_form_generator()
    return {"forms": gen.get_available_forms()}

@router.post("/generate")
async def generate_form(request: FormRequest):
    from app.services.form_generator import get_form_generator, FormGeneratorError
    try:
        gen = get_form_generator()
        user_data = {"first_name": "Test", "last_name": "User"}
        pdf_bytes = gen.generate_form(request.form_type, user_data, {})
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="VA_Form_{request.form_type}.pdf"'}
        )
    except FormGeneratorError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Step 2: Verify endpoint loads

```bash
/ganuda/vetassist/backend/venv/bin/python -c "import sys; sys.path.insert(0, '/ganuda/vetassist/backend'); from app.api.v1.endpoints.forms import router; print('Routes:', [r.path for r in router.routes])"
```

---

*Part 3 of 4*
