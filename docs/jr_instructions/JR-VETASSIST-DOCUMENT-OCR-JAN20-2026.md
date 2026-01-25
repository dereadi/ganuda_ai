# Jr Instruction: VetAssist Document OCR/AI Extraction
## Task ID: VetAssist Sprint 3 - Task 1
## Priority: P1
## Estimated Complexity: High

---

## Objective

Implement document OCR and AI extraction for uploaded veteran documents. System should extract structured data from DD-214s, medical records, buddy statements, and nexus letters.

---

## Prerequisites

- VetAssist backend running on redfin (port 8001)
- vLLM running on redfin (port 8000) with Qwen2.5-Coder-32B
- PostgreSQL on bluefin (zammad_production database)
- Python OCR libraries installed

---

## Implementation Steps

### Step 1: Install OCR Dependencies

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install pytesseract pdf2image Pillow
```

On system (if not installed):
```bash
sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils
```

### Step 2: Create Database Table

Connect to bluefin PostgreSQL and create:

```sql
CREATE TABLE IF NOT EXISTS vetassist_extracted_documents (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    document_type VARCHAR(50),
    original_file_id INT,
    extracted_text TEXT,
    extracted_data JSONB,
    confidence_score FLOAT,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES vetassist_wizard_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_extracted_docs_session ON vetassist_extracted_documents(session_id);
```

### Step 3: Create OCR Service

Create `/ganuda/vetassist/backend/app/services/ocr_service.py`:

```python
"""
VetAssist OCR Service - Document extraction
Cherokee AI Federation
"""
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)

VLLM_URL = "http://localhost:8000/v1/chat/completions"

class OCRService:
    def __init__(self):
        self.temp_dir = "/ganuda/vetassist/temp_ocr"
        os.makedirs(self.temp_dir, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Convert PDF to images and OCR each page"""
        images = convert_from_path(pdf_path)
        full_text = []
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            full_text.append(f"--- Page {i+1} ---\n{text}")
        return "\n".join(full_text)

    def extract_text_from_image(self, image_path: str) -> str:
        """OCR a single image"""
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)

    async def extract_structured_data(self, text: str, doc_type: str) -> dict:
        """Use LLM to extract structured data from OCR text"""
        prompts = {
            "dd214": """Extract the following from this DD-214 document:
- full_name: Veteran's full name
- ssn_last4: Last 4 of SSN (if visible)
- branch: Branch of service
- service_start_date: Date entered active duty
- service_end_date: Date separated
- discharge_type: Type of discharge
- mos: Military Occupational Specialty
- decorations: List of decorations/medals

Return JSON only.""",

            "medical": """Extract from this medical record:
- diagnoses: List of diagnoses with ICD codes if present
- treatment_dates: List of treatment dates
- provider_name: Treating physician/provider
- facility: Medical facility name
- medications: List of medications mentioned
- findings: Key medical findings

Return JSON only.""",

            "buddy": """Extract from this buddy statement:
- author_name: Person who wrote the statement
- relationship: Relationship to veteran
- observations: What they observed (list)
- dates_observed: When they observed it
- contact_info: Author's contact if provided

Return JSON only.""",

            "nexus": """Extract from this nexus/IMO letter:
- doctor_name: Physician's name
- credentials: Doctor's credentials
- opinion: Medical opinion stated
- rationale: Reasoning for opinion
- conditions_addressed: Conditions discussed

Return JSON only."""
        }

        prompt = prompts.get(doc_type, prompts["medical"])

        async with httpx.AsyncClient() as client:
            response = await client.post(
                VLLM_URL,
                json={
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                    "messages": [
                        {"role": "system", "content": "You extract structured data from documents. Return only valid JSON."},
                        {"role": "user", "content": f"{prompt}\n\nDocument text:\n{text[:8000]}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=60.0
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                # Parse JSON from response
                try:
                    # Handle markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    return json.loads(content.strip())
                except:
                    return {"raw_extraction": content}
            else:
                logger.error(f"LLM extraction failed: {response.status_code}")
                return {"error": "Extraction failed"}

ocr_service = OCRService()
```

### Step 4: Create Extraction Endpoint

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`:

```python
from app.services.ocr_service import ocr_service

@router.post("/{session_id}/extract")
async def extract_document(
    session_id: str,
    document_type: str,  # dd214, medical, buddy, nexus
    file_id: int
):
    """Extract structured data from uploaded document using OCR + AI"""
    conn = get_db_conn()
    try:
        # Get file info
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT file_path, file_name FROM vetassist_wizard_files
                WHERE id = %s AND session_id = %s AND NOT deleted
            """, (file_id, session_id))
            file_info = cur.fetchone()

        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = file_info['file_path']

        # OCR extraction
        if file_path.lower().endswith('.pdf'):
            text = ocr_service.extract_text_from_pdf(file_path)
        else:
            text = ocr_service.extract_text_from_image(file_path)

        # AI extraction
        extracted_data = await ocr_service.extract_structured_data(text, document_type)

        # Calculate confidence (simple heuristic)
        confidence = 0.8 if len(extracted_data) > 2 else 0.5

        # Store results
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO vetassist_extracted_documents
                (session_id, document_type, original_file_id, extracted_text, extracted_data, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, extracted_data, confidence_score
            """, (session_id, document_type, file_id, text[:50000], json.dumps(extracted_data), confidence))
            result = cur.fetchone()
            conn.commit()

        return {
            "extraction_id": result['id'],
            "document_type": document_type,
            "extracted_data": extracted_data,
            "confidence": confidence,
            "text_length": len(text)
        }

    finally:
        conn.close()
```

### Step 5: Register Endpoint

Ensure the endpoint is included in the router registration in `app/api/v1/__init__.py`.

---

## Testing

```bash
# Upload a document first, note the file_id returned

# Then extract
curl -X POST "http://localhost:8001/api/v1/wizard/{session_id}/extract?document_type=dd214&file_id={file_id}"
```

---

## Acceptance Criteria

1. OCR extracts text from PDF and image uploads
2. AI parses extracted text into structured JSON
3. Results stored in `vetassist_extracted_documents` table
4. Confidence score calculated for each extraction
5. Handles errors gracefully (unreadable documents, OCR failures)

---

## Security Notes (Turtle 7-Gen Concern)

- Extracted PII must be encrypted at rest
- Temp OCR files should be deleted after processing
- Consider PII redaction logging for audit trail

---

*Cherokee AI Federation - For Seven Generations*
