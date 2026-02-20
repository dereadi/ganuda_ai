# Jr Instruction: PyPDFForm Part 2 — Form Generator Service

**ID:** JR-VETASSIST-PYPDF-PART2-SERVICE-FEB06-2026
**Priority:** P0
**Part:** 2 of 4

---

## Objective

Create the form generator service.

---

## Step 1: Create form_generator.py

**file: /ganuda/vetassist/backend/app/services/form_generator.py**
```python
"""VA Form Generator Service"""

import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pypdfform import PdfWrapper

logger = logging.getLogger(__name__)

TEMPLATE_DIR = "/ganuda/vetassist/templates/va_forms"
TEMPLATES = {
    "21-526EZ": os.path.join(TEMPLATE_DIR, "21-526EZ.pdf"),
    "21-0781": os.path.join(TEMPLATE_DIR, "21-0781.pdf"),
    "21-0781a": os.path.join(TEMPLATE_DIR, "21-0781a.pdf"),
}

class FormGeneratorError(Exception):
    pass

class VAFormGenerator:
    def __init__(self):
        for form_id, path in TEMPLATES.items():
            if not os.path.exists(path):
                logger.warning(f"Template missing: {form_id}")

    def get_available_forms(self):
        return [f for f, p in TEMPLATES.items() if os.path.exists(p)]

    def generate_form(self, form_type: str, user_data: Dict, wizard_data: Dict) -> bytes:
        if form_type not in TEMPLATES:
            raise FormGeneratorError(f"Unknown form: {form_type}")
        template_path = TEMPLATES[form_type]
        if not os.path.exists(template_path):
            raise FormGeneratorError(f"Template not found: {form_type}")
        try:
            pdf = PdfWrapper(template_path)
            field_data = {
                "VeteranFirstName": user_data.get("first_name", ""),
                "VeteranLastName": user_data.get("last_name", ""),
                "SSN": user_data.get("ssn", ""),
                "Email": user_data.get("email", ""),
            }
            pdf.fill(field_data)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name
            pdf.draw().save(tmp_path)
            with open(tmp_path, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(tmp_path)
            return pdf_bytes
        except Exception as e:
            raise FormGeneratorError(str(e))

_generator = None

def get_form_generator():
    global _generator
    if _generator is None:
        _generator = VAFormGenerator()
    return _generator
```

---

## Step 2: Verify service loads

```bash
/ganuda/vetassist/backend/venv/bin/python -c "import sys; sys.path.insert(0, '/ganuda/vetassist/backend'); from app.services.form_generator import get_form_generator; print(get_form_generator().get_available_forms())"
```

---

*Part 2 of 4*
