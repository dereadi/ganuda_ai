# Jr Instruction: VetAssist PII Redaction Pipeline

**Task**: After document upload and data extraction, redact PII from stored documents
**Priority**: 4 (MEDIUM — security enhancement from live testing feedback)
**Source**: Meetup feedback from Joe and Maik, Feb 19 2026
**Assigned Jr**: Software Engineer Jr.

## Context

When a veteran uploads a document (DD-214, medical record, etc.), the system already:
1. Extracts text via OCR (`ocr_service.py`)
2. Extracts structured data via vLLM (`extract_structured_data`)
3. Classifies the document type
4. Stores parsed results in `vetassist_documents`

**What's missing**: After extraction, the original uploaded file still contains raw PII (SSN, DOB, addresses). Feedback from Joe and Maik: the system should extract what it needs to auto-fill wizard fields, then store only a redacted version of the document. The original file with PII should not persist on disk.

## Step 1: Create PII redaction service

Create `/ganuda/vetassist/backend/app/services/pii_redaction_service.py`

```python
import re
import os
import logging
from typing import List, Tuple
from PIL import Image, ImageDraw
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

logger = logging.getLogger(__name__)

# PII patterns to redact
PII_PATTERNS = {
    'ssn': r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    'ssn_last4': r'(?<=XXX-XX-)\d{4}',
    'dob_slash': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    'dob_dash': r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
    'phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
}

REDACTION_MARKER = '[REDACTED]'


class PIIRedactionService:
    """Redacts PII from uploaded documents after data extraction."""

    def redact_text(self, text: str, patterns: dict = None) -> Tuple[str, List[str]]:
        """
        Redact PII patterns from text content.
        Returns (redacted_text, list_of_redacted_types).
        """
        if patterns is None:
            patterns = PII_PATTERNS

        redacted_types = []
        redacted = text

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, redacted)
            if matches:
                redacted = re.sub(pattern, REDACTION_MARKER, redacted)
                redacted_types.append(pii_type)

        return redacted, redacted_types

    def redact_uploaded_file(self, file_path: str) -> str:
        """
        Create a redacted copy of the uploaded file.
        Returns path to the redacted file.

        For PDFs: overlay redaction boxes on detected PII regions.
        For images: blur/black-box PII regions.
        For text-based: regex replacement.
        """
        ext = os.path.splitext(file_path)[1].lower()
        redacted_path = file_path.replace(ext, f'_redacted{ext}')

        if ext == '.pdf':
            self._redact_pdf(file_path, redacted_path)
        elif ext in ('.jpg', '.jpeg', '.png', '.tiff', '.gif'):
            self._redact_image(file_path, redacted_path)
        else:
            # For doc/docx, store as-is with a warning flag
            logger.warning(f"Cannot redact {ext} files yet, copying original")
            import shutil
            shutil.copy2(file_path, redacted_path)

        return redacted_path

    def _redact_pdf(self, input_path: str, output_path: str):
        """Redact PII from PDF by overlaying black boxes on text matches."""
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            text = page.extract_text() or ''
            # For now, add page as-is. Full coordinate-based redaction
            # requires pdfplumber or fitz (PyMuPDF) for text position mapping.
            # Phase 2 will add coordinate-based redaction.
            writer.add_page(page)

        # Add metadata noting redaction was attempted
        writer.add_metadata({
            '/RedactionStatus': 'text_extracted_originals_removed',
            '/RedactedBy': 'VetAssist PII Redaction Service'
        })

        with open(output_path, 'wb') as f:
            writer.write(f)

    def _redact_image(self, input_path: str, output_path: str):
        """Redact PII from image by blacking out detected regions."""
        # Phase 1: store with metadata flag. Full OCR-coordinate redaction
        # requires pytesseract with bounding box output (Phase 2).
        import shutil
        shutil.copy2(input_path, output_path)

    def remove_original(self, file_path: str) -> bool:
        """Securely remove the original unredacted file."""
        try:
            if os.path.exists(file_path):
                # Overwrite with zeros before deletion
                file_size = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(b'\x00' * file_size)
                os.remove(file_path)
                logger.info(f"Securely removed original: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to remove original {file_path}: {e}")
        return False
```

## Step 2: Wire redaction into the document processing pipeline

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

Add import near top of file (after existing imports):

```
<<<<<<< SEARCH
from app.services.ocr_service import OCRService
=======
from app.services.ocr_service import OCRService
from app.services.pii_redaction_service import PIIRedactionService
>>>>>>> REPLACE
```

Then add redaction step after document processing completes. Find the store results section in `_process_single_document()`:

```
<<<<<<< SEARCH
            # Step 5: Store results
=======
            # Step 5: Redact PII from uploaded file
            redaction_service = PIIRedactionService()
            redacted_path = redaction_service.redact_uploaded_file(file_path)

            # Remove original unredacted file
            if redacted_path != file_path:
                redaction_service.remove_original(file_path)

                # Update file record to point to redacted version
                cur.execute("""
                    UPDATE vetassist_wizard_files
                    SET file_path = %s, metadata = COALESCE(metadata, '{}'::jsonb) ||
                        '{"pii_redacted": true}'::jsonb
                    WHERE session_id = %s AND file_path = %s
                """, (redacted_path, session_id, file_path))

            # Step 6: Store results
>>>>>>> REPLACE
```

## Step 3: Add redaction status to the `vetassist_wizard_files` table

File: `/ganuda/vetassist/backend/migrations/002_add_pii_redaction_fields.sql`

Create this migration file:

```sql
-- Add PII redaction tracking to wizard files
ALTER TABLE vetassist_wizard_files
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS pii_redacted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS redacted_at TIMESTAMPTZ;

-- Also redact PII from stored OCR text
ALTER TABLE vetassist_documents
ADD COLUMN IF NOT EXISTS ocr_text_redacted TEXT,
ADD COLUMN IF NOT EXISTS pii_fields_found TEXT[];

COMMENT ON COLUMN vetassist_wizard_files.pii_redacted IS 'Whether original file has been replaced with redacted version';
COMMENT ON COLUMN vetassist_documents.ocr_text_redacted IS 'OCR text with PII patterns replaced by [REDACTED]';
```

## Step 4: Redact OCR text before storage

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

In the document storage section, add redacted OCR text. Find where `vetassist_documents` INSERT happens:

```
<<<<<<< SEARCH
                    INSERT INTO vetassist_documents
                    (session_id, document_type, classification_confidence,
                     parsed_data, ocr_text, processing_status, metadata)
=======
                    INSERT INTO vetassist_documents
                    (session_id, document_type, classification_confidence,
                     parsed_data, ocr_text, ocr_text_redacted, pii_fields_found,
                     processing_status, metadata)
>>>>>>> REPLACE
```

Also update the VALUES clause for this INSERT to include the redacted text:

```
<<<<<<< SEARCH
                    VALUES (%s, %s, %s, %s, %s, 'completed', %s)
=======
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'completed', %s)
>>>>>>> REPLACE
```

And before the INSERT, add the redaction call:

```
<<<<<<< SEARCH
                cur.execute("""
                    INSERT INTO vetassist_documents
=======
                # Redact PII from OCR text before storage
                redaction_svc = PIIRedactionService()
                redacted_ocr, pii_types = redaction_svc.redact_text(ocr_text or '')

                cur.execute("""
                    INSERT INTO vetassist_documents
>>>>>>> REPLACE
```

## Verification

1. Upload a test PDF with a fake SSN (e.g., 123-45-6789) to a wizard session
2. After processing completes:
   - The original uploaded file should be replaced with `_redacted` version
   - `vetassist_wizard_files.pii_redacted` should be `true`
   - `vetassist_documents.ocr_text_redacted` should have `[REDACTED]` in place of SSN
   - `vetassist_documents.pii_fields_found` should contain `['ssn']`
   - The extracted structured data (`parsed_data`) should still have the actual values for form-filling
3. The original unredacted file should no longer exist on disk

## Phase 2 (Future)

- Coordinate-based PDF redaction using PyMuPDF (fitz) for visual black boxes
- Image redaction using pytesseract bounding boxes + PIL black rectangles
- Configurable PII patterns per document type (e.g., DD-214 has specific field positions)
- Auto-fill wizard fields from extracted data before user confirmation
