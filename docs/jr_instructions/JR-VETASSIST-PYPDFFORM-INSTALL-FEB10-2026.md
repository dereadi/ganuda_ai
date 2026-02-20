# Jr Instruction: VetAssist PyPDFForm Integration
*Kanban: #1749 | Priority: P1 | Estimated: 3-4 hours*
*Reference: https://github.com/chinapandaman/PyPDFForm*

## Objective
Install PyPDFForm and create a form-filling API endpoint in the VetAssist backend so veterans can auto-fill VA PDF forms from wizard data.

## Step 1: Install PyPDFForm

File: `/ganuda/vetassist/requirements.txt`

Add `pypdfform` to the end of the requirements file. Then install:

```text
pip install pypdfform
```

## Step 2: Create Form Filler Service

Create `/ganuda/vetassist/services/form_filler.py`

```python
"""
VA Form Auto-Filler using PyPDFForm
Reference: https://chinapandaman.github.io/PyPDFForm/fill/
For Seven Generations
"""

import os
from PyPDFForm import PdfWrapper

# Directory containing blank VA form templates
FORMS_DIR = os.path.join(os.path.dirname(__file__), '..', 'forms', 'templates')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'forms', 'filled')


def fill_va_form(form_name: str, field_data: dict) -> str:
    """Fill a VA PDF form with provided field data.

    Args:
        form_name: Template filename (e.g., '21-0966.pdf')
        field_data: Dict mapping PDF field names to values

    Returns:
        Path to the filled PDF file
    """
    template_path = os.path.join(FORMS_DIR, form_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Form template not found: {form_name}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filled = PdfWrapper(template_path).fill(field_data)

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_name = f"{form_name.replace('.pdf', '')}_{timestamp}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    with open(output_path, 'wb') as f:
        f.write(filled.read())

    return output_path


def inspect_form_fields(form_name: str) -> dict:
    """Return the fillable field names and types for a VA form template."""
    template_path = os.path.join(FORMS_DIR, form_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Form template not found: {form_name}")

    wrapper = PdfWrapper(template_path)
    return wrapper.schema
```

## Step 3: Create Form Templates Directory

Create `/ganuda/vetassist/forms/templates/` directory.

```text
mkdir -p /ganuda/vetassist/forms/templates
mkdir -p /ganuda/vetassist/forms/filled
```

## Step 4: Add API Endpoint

This step depends on the existing VetAssist backend routing structure. Find the main Flask/FastAPI app file and add:

```python
@app.route('/api/forms/inspect/<form_name>', methods=['GET'])
def inspect_form(form_name):
    """Return fillable field names for a VA form template."""
    try:
        from services.form_filler import inspect_form_fields
        fields = inspect_form_fields(form_name)
        return jsonify({'form': form_name, 'fields': fields})
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/forms/fill', methods=['POST'])
def fill_form():
    """Fill a VA form with provided data. Expects JSON: {form_name, field_data}"""
    try:
        from services.form_filler import fill_va_form
        data = request.get_json()
        form_name = data.get('form_name')
        field_data = data.get('field_data', {})

        if not form_name:
            return jsonify({'error': 'form_name required'}), 400

        output_path = fill_va_form(form_name, field_data)
        return send_file(output_path, as_attachment=True)
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Validation
- `pip show pypdfform` returns version info
- `/api/forms/inspect/<form_name>` returns field schema
- `/api/forms/fill` with valid data returns filled PDF

## Notes
- VA form PDFs must be downloaded separately and placed in templates dir
- PII: filled forms contain veteran data — stored in /ganuda only, never /tmp
- Future: integrate with Presidio (#1703) to redact PII from logs
