# JR INSTRUCTION: Self-Hosted Docling Document AI Integration

**Task ID:** ASSIST-INTEGRATE-DOCLING
**Priority:** P1 — Document intelligence for all verticals
**Assigned To:** Any available Jr
**Created By:** TPM + Council (7/7 APPROVE with conditions)
**Date:** 2026-02-04
**Council Vote:** COUNCIL-VOTE-ASSIST-TECH-STACK-FEB04-2026.md
**Estimated Effort:** 8-10 hours
**Dependencies:** None

---

## MISSION CONTEXT

Veterans, SSID applicants, and Cherokee Nation citizens must submit documents to prove eligibility:
- **VetAssist:** DD-214, medical records, C&P exams, VA forms
- **SSIDAssist:** Medical records, work history, SSA forms
- **TribeAssist:** Enrollment applications, eligibility documentation

Current OCR pipeline (Tesseract + custom logic) is brittle:
- Poor table extraction
- Misses form field structure
- Requires extensive manual cleanup
- No understanding of document semantics

**Docling is IBM's open-source document AI:**
- Extracts text, tables, headings, metadata
- Understands document structure (forms, reports, letters)
- MIT license, LF AI Foundation hosted
- 52k stars, active development

**Critical Council Conditions:**
1. **Self-host ONLY** — No IBM cloud API calls
2. **No telemetry** — Verify Docling sends nothing external
3. **FPIC consent** — Users must explicitly consent to document processing
4. **Crawdad audit** — Verify no phone-home behavior in dependency chain
5. **Abstraction layer** — Must be swappable (escape velocity)
6. **On-premises processing** — Documents never leave our infrastructure

This is not optional. Veterans' medical records contain PHI. Cherokee Nation documents contain sovereign data. We do not send this to external services.

---

## TECHNICAL CONTEXT

**What is Docling?**
- Document understanding and conversion library
- Extracts: text, tables, headings, images, metadata
- Inputs: PDF, DOCX, images (JPEG, PNG, TIFF)
- Outputs: Structured JSON, Markdown
- Models: Runs locally, no API required
- License: MIT (Council-approved)

**Why Docling over Tesseract?**
- Tesseract: OCR only (pixels → text)
- Docling: Document understanding (structure, semantics, relationships)
- Example: Tesseract sees "Name: ____", Docling sees "Form field 'Name' with empty value"

**Why not cloud Document AI (Google, AWS, Azure)?**
- Sends PHI/PII to external servers (HIPAA violation, sovereignty violation)
- Creates dependency on external service (availability, cost)
- Data extraction (trains their models on our data)

**Deployment Target:**
- **Server:** greenfin (192.168.132.224)
- **Why greenfin:** External-facing node, has GPU capacity
- **Database:** bluefin (192.168.132.222), zammad_production
- **Network:** Must verify all traffic stays within 192.168.132.x

---

## SCOPE OF WORK

### Phase 1: Installation & Security Audit (2 hours)

**Location:** greenfin (192.168.132.224)

**Install Docling:**
```bash
# SSH to greenfin
ssh greenfin.ganuda.local

# Create virtual environment for isolation
mkdir -p /ganuda/assist/core/backend/services/document_ai
cd /ganuda/assist/core/backend/services/document_ai
python3 -m venv docling_venv
source docling_venv/bin/activate

# Install Docling
pip install docling

# Verify version
pip show docling
# Expected: docling>=2.0.0
```

**Offline test (Council requirement: must work without network):**
```bash
# Disconnect network
sudo ip link set eth0 down

# Test document processing
python3 << EOF
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("/tmp/test.pdf")
print(result.document.export_to_dict())
EOF

# If this fails, Docling requires network. STOP and report to Council.
# If this succeeds, Docling is truly local. Proceed.

# Reconnect network
sudo ip link set eth0 up
```

**Dependency chain audit (Council requirement: Crawdad must verify):**
```bash
# List all dependencies
pip show docling
pip list --format=freeze > /tmp/docling-dependencies.txt

# Audit each dependency for telemetry
# Check for: analytics, telemetry, tracking, phone-home

# Common culprits:
# - transformers (HuggingFace) — may download models from internet
# - torch (PyTorch) — telemetry in some versions
# - pillow (PIL) — usually clean
# - pdfminer — usually clean

# For each dependency, check for network calls:
python3 << EOF
import sys
import docling

# Hook into socket to detect network calls
import socket
original_socket = socket.socket

def tracked_socket(*args, **kwargs):
    print(f"NETWORK CALL DETECTED: {args}, {kwargs}")
    return original_socket(*args, **kwargs)

socket.socket = tracked_socket

# Process a document
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
result = converter.convert("/tmp/test.pdf")
print("Processing complete")
EOF

# If you see NETWORK CALL DETECTED (other than localhost), investigate.
# Acceptable: localhost connections (127.0.0.1)
# NOT acceptable: External IPs, domain names
```

**Verify with tcpdump (Council requirement: zero external traffic):**
```bash
# Start packet capture on greenfin
sudo tcpdump -i eth0 -w /tmp/docling-traffic.pcap &
TCPDUMP_PID=$!

# Process a document
python3 << EOF
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
result = converter.convert("/tmp/test.pdf")
EOF

# Stop packet capture
sudo kill $TCPDUMP_PID

# Analyze capture
tcpdump -r /tmp/docling-traffic.pcap

# Expected: Only local traffic (192.168.132.x)
# NOT acceptable: External IPs, DNS queries to non-local domains

# If external traffic detected: STOP. Report to Crawdad. Do not proceed.
```

**Download models locally (prevent internet dependency):**
```bash
# Docling may download models on first run
# Pre-download all models to ensure offline capability

python3 << EOF
from docling.document_converter import DocumentConverter

# This will download models if not present
converter = DocumentConverter()
print("Models downloaded")
EOF

# Verify models are cached locally
ls -la ~/.cache/docling/  # or wherever Docling caches models

# Test offline processing again
sudo ip link set eth0 down
python3 -c "from docling.document_converter import DocumentConverter; DocumentConverter().convert('/tmp/test.pdf')"
# This must succeed. If it fails, models are not cached correctly.
sudo ip link set eth0 up
```

---

### Phase 2: Document Processing Service (3 hours)

**Create abstraction layer (Council requirement: must be swappable).**

File: `/ganuda/assist/core/backend/services/document_ai/base_processor.py`

```python
"""
Base document processor interface.

Council requirement: Abstraction layer for escape velocity.
We can swap Docling for another backend without changing API.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, BinaryIO
from dataclasses import dataclass
from enum import Enum

class DocumentType(Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"  # JPEG, PNG, TIFF

@dataclass
class DocumentExtractionResult:
    """Structured document extraction result."""
    text: str  # Full extracted text
    tables: list[Dict[str, Any]]  # Extracted tables (list of dicts)
    headings: list[Dict[str, str]]  # Headings with levels
    metadata: Dict[str, Any]  # Document metadata (author, date, etc.)
    fields: Dict[str, str]  # Form fields (if document is a form)
    images: list[Dict[str, Any]]  # Embedded images
    confidence: float  # Extraction confidence (0.0-1.0)
    processor: str  # Which processor was used (docling, tesseract, etc.)

class BaseDocumentProcessor(ABC):
    """
    Abstract base class for document processors.

    All document processors must implement this interface.
    This allows us to swap backends (Docling → Tesseract → future tool).
    """

    @abstractmethod
    def process_document(
        self,
        file_path: str = None,
        file_bytes: BinaryIO = None,
        document_type: DocumentType = None,
    ) -> DocumentExtractionResult:
        """
        Process a document and extract structured data.

        Args:
            file_path: Path to document file
            file_bytes: Document bytes (if not using file_path)
            document_type: Type of document (auto-detected if None)

        Returns:
            DocumentExtractionResult with extracted data

        Raises:
            ValueError: If neither file_path nor file_bytes provided
            RuntimeError: If processing fails
        """
        pass

    @abstractmethod
    def supports_document_type(self, document_type: DocumentType) -> bool:
        """Check if this processor supports a document type."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get processor name (for logging/debugging)."""
        pass
```

**Create Docling implementation:**

File: `/ganuda/assist/core/backend/services/document_ai/docling_processor.py`

```python
"""
Docling document processor implementation.

Council conditions:
- Self-hosted ONLY (no cloud API calls)
- No telemetry
- Processes in memory (no persistent storage)
- All processing on-premises
"""

import logging
from typing import Dict, Any, BinaryIO
from pathlib import Path
import tempfile

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import ConversionStatus

from .base_processor import (
    BaseDocumentProcessor,
    DocumentExtractionResult,
    DocumentType,
)

logger = logging.getLogger(__name__)

class DoclingProcessor(BaseDocumentProcessor):
    """Docling-based document processor."""

    def __init__(self):
        """Initialize Docling converter."""
        # Initialize converter (models must be pre-downloaded)
        self.converter = DocumentConverter()
        logger.info("Docling processor initialized")

    def process_document(
        self,
        file_path: str = None,
        file_bytes: BinaryIO = None,
        document_type: DocumentType = None,
    ) -> DocumentExtractionResult:
        """
        Process document with Docling.

        Council requirement: Process in memory, no persistent storage.
        """
        if not file_path and not file_bytes:
            raise ValueError("Must provide either file_path or file_bytes")

        # If bytes provided, write to temp file (Docling requires file path)
        temp_file = None
        try:
            if file_bytes:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(file_bytes.read())
                temp_file.close()
                process_path = temp_file.name
            else:
                process_path = file_path

            logger.info(f"Processing document: {process_path}")

            # Convert document
            result = self.converter.convert(process_path)

            # Check conversion status
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Docling conversion failed: {result.status}")

            # Extract structured data
            doc = result.document
            doc_dict = doc.export_to_dict()

            # Parse extraction result
            extraction = DocumentExtractionResult(
                text=doc.export_to_markdown(),  # Full text as markdown
                tables=self._extract_tables(doc_dict),
                headings=self._extract_headings(doc_dict),
                metadata=self._extract_metadata(doc_dict),
                fields=self._extract_form_fields(doc_dict),
                images=self._extract_images(doc_dict),
                confidence=self._calculate_confidence(result),
                processor="docling",
            )

            logger.info(f"Extraction complete: {len(extraction.text)} chars, {len(extraction.tables)} tables")
            return extraction

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise RuntimeError(f"Docling processing error: {e}")

        finally:
            # Clean up temp file (Council requirement: no persistent storage)
            if temp_file:
                Path(temp_file.name).unlink(missing_ok=True)

    def _extract_tables(self, doc_dict: Dict) -> list[Dict[str, Any]]:
        """Extract tables from document."""
        tables = []
        for item in doc_dict.get("items", []):
            if item.get("type") == "table":
                tables.append({
                    "rows": item.get("rows", []),
                    "columns": item.get("columns", []),
                    "data": item.get("data", []),
                })
        return tables

    def _extract_headings(self, doc_dict: Dict) -> list[Dict[str, str]]:
        """Extract headings with levels."""
        headings = []
        for item in doc_dict.get("items", []):
            if item.get("type") == "heading":
                headings.append({
                    "text": item.get("text", ""),
                    "level": item.get("level", 1),
                })
        return headings

    def _extract_metadata(self, doc_dict: Dict) -> Dict[str, Any]:
        """Extract document metadata."""
        return doc_dict.get("metadata", {})

    def _extract_form_fields(self, doc_dict: Dict) -> Dict[str, str]:
        """
        Extract form fields (if document is a form).

        Example: VA Form 21-526EZ has fields like "veteran_name", "claim_date"
        """
        fields = {}
        for item in doc_dict.get("items", []):
            if item.get("type") == "form_field":
                field_name = item.get("name", "")
                field_value = item.get("value", "")
                fields[field_name] = field_value
        return fields

    def _extract_images(self, doc_dict: Dict) -> list[Dict[str, Any]]:
        """Extract embedded images."""
        images = []
        for item in doc_dict.get("items", []):
            if item.get("type") == "image":
                images.append({
                    "caption": item.get("caption", ""),
                    "alt_text": item.get("alt_text", ""),
                })
        return images

    def _calculate_confidence(self, result) -> float:
        """
        Calculate extraction confidence.

        Docling doesn't provide confidence score directly.
        We estimate based on conversion status and data completeness.
        """
        if result.status == ConversionStatus.SUCCESS:
            return 0.95
        elif result.status == ConversionStatus.PARTIAL:
            return 0.70
        else:
            return 0.50

    def supports_document_type(self, document_type: DocumentType) -> bool:
        """Check if Docling supports this document type."""
        return document_type in [DocumentType.PDF, DocumentType.DOCX, DocumentType.IMAGE]

    def get_name(self) -> str:
        """Get processor name."""
        return "docling"
```

**Create Tesseract fallback:**

File: `/ganuda/assist/core/backend/services/document_ai/tesseract_processor.py`

```python
"""
Tesseract fallback processor.

Used if Docling fails or for simple OCR tasks.
Council requirement: Abstraction layer allows swapping backends.
"""

import logging
from typing import Dict, Any, BinaryIO
import pytesseract
from PIL import Image
import tempfile
from pathlib import Path

from .base_processor import (
    BaseDocumentProcessor,
    DocumentExtractionResult,
    DocumentType,
)

logger = logging.getLogger(__name__)

class TesseractProcessor(BaseDocumentProcessor):
    """Tesseract OCR fallback processor."""

    def process_document(
        self,
        file_path: str = None,
        file_bytes: BinaryIO = None,
        document_type: DocumentType = None,
    ) -> DocumentExtractionResult:
        """Process document with Tesseract OCR."""
        if not file_path and not file_bytes:
            raise ValueError("Must provide either file_path or file_bytes")

        temp_file = None
        try:
            if file_bytes:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(file_bytes.read())
                temp_file.close()
                process_path = temp_file.name
            else:
                process_path = file_path

            logger.info(f"OCR processing: {process_path}")

            # Load image
            image = Image.open(process_path)

            # Extract text
            text = pytesseract.image_to_string(image)

            # Tesseract only does OCR, no structure
            extraction = DocumentExtractionResult(
                text=text,
                tables=[],  # No table extraction
                headings=[],  # No heading detection
                metadata={},  # No metadata
                fields={},  # No form field detection
                images=[],  # No image extraction
                confidence=0.70,  # Lower confidence than Docling
                processor="tesseract",
            )

            logger.info(f"OCR complete: {len(text)} chars")
            return extraction

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise RuntimeError(f"Tesseract processing error: {e}")

        finally:
            if temp_file:
                Path(temp_file.name).unlink(missing_ok=True)

    def supports_document_type(self, document_type: DocumentType) -> bool:
        """Tesseract supports images only."""
        return document_type == DocumentType.IMAGE

    def get_name(self) -> str:
        return "tesseract"
```

**Create processor factory:**

File: `/ganuda/assist/core/backend/services/document_ai/processor_factory.py`

```python
"""
Document processor factory.

Council requirement: Abstraction layer allows swapping backends.
"""

from .base_processor import BaseDocumentProcessor, DocumentType
from .docling_processor import DoclingProcessor
from .tesseract_processor import TesseractProcessor

class DocumentProcessorFactory:
    """Factory for creating document processors."""

    @staticmethod
    def get_processor(
        document_type: DocumentType = None,
        prefer_docling: bool = True,
    ) -> BaseDocumentProcessor:
        """
        Get appropriate document processor.

        Args:
            document_type: Type of document to process
            prefer_docling: Prefer Docling over Tesseract (default True)

        Returns:
            Document processor instance
        """
        if prefer_docling:
            try:
                processor = DoclingProcessor()
                if not document_type or processor.supports_document_type(document_type):
                    return processor
            except Exception:
                # Docling initialization failed, fall back to Tesseract
                pass

        # Fallback to Tesseract
        return TesseractProcessor()
```

---

### Phase 3: API Endpoint & FPIC Consent (2 hours)

**Create document processing API endpoint.**

File: `/ganuda/assist/core/backend/routes/documents.py`

```python
"""
Document processing API.

Council requirements:
- FPIC consent required
- Authentication required
- Rate limiting
- No data leaves cluster
- All processing logged in audit table
"""

from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from services.document_ai.processor_factory import DocumentProcessorFactory
from services.document_ai.base_processor import DocumentType
from lib.auth import require_auth
from lib.pii_detection import detect_pii

logger = logging.getLogger(__name__)

documents_bp = Blueprint('documents', __name__)
limiter = Limiter(key_func=get_remote_address)

@documents_bp.route('/api/v1/documents/process', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")  # Council requirement: rate limiting
def process_document():
    """
    Process uploaded document with AI extraction.

    Council requirements:
    - User must provide FPIC consent flag
    - User must be authenticated
    - Rate limited to 10 requests/minute
    - Max file size: 50MB
    - Processing logged in audit table
    """
    user = request.user  # Set by @require_auth decorator

    # Council requirement: FPIC consent
    consent = request.form.get('consent', 'false').lower() == 'true'
    if not consent:
        logger.warning(f"User {user.id} attempted document processing without consent")
        return jsonify({
            "error": "FPIC consent required",
            "message": "You must consent to AI document processing. This processes your document using machine learning to extract text and structure. Your document stays on our servers and is not shared externally.",
        }), 403

    # Check file upload
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Council requirement: Max file size 50MB
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to start

    if file_size > 50 * 1024 * 1024:  # 50MB
        return jsonify({"error": "File too large (max 50MB)"}), 413

    # Determine document type
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        doc_type = DocumentType.PDF
    elif filename.endswith('.docx'):
        doc_type = DocumentType.DOCX
    elif filename.endswith(('.jpg', '.jpeg', '.png', '.tiff')):
        doc_type = DocumentType.IMAGE
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        # Get processor
        processor = DocumentProcessorFactory.get_processor(doc_type)
        logger.info(f"Processing document with {processor.get_name()}")

        # Process document (in memory, no persistent storage)
        result = processor.process_document(file_bytes=file, document_type=doc_type)

        # Council requirement: PII detection before returning
        pii_found = detect_pii(result.text)

        # Log to audit table
        from lib.audit import log_audit_event
        log_audit_event(
            user_id=user.id,
            action="document_processed",
            details={
                "filename": file.filename,
                "file_size": file_size,
                "processor": result.processor,
                "confidence": result.confidence,
                "pii_detected": len(pii_found) > 0,
            },
        )

        # Return extraction result
        return jsonify({
            "success": True,
            "text": result.text,
            "tables": result.tables,
            "headings": result.headings,
            "metadata": result.metadata,
            "fields": result.fields,
            "confidence": result.confidence,
            "processor": result.processor,
            "pii_warning": len(pii_found) > 0,
            "pii_types": list(pii_found) if pii_found else [],
        }), 200

    except Exception as e:
        logger.error(f"Document processing failed: {e}")

        # Council requirement: Don't expose document contents in error messages
        return jsonify({
            "error": "Document processing failed",
            "message": "Unable to process document. Please try again or contact support.",
        }), 500

@documents_bp.route('/api/v1/documents/consent', methods=['GET'])
@require_auth
def get_consent_info():
    """
    Get FPIC consent information for document processing.

    This endpoint explains what consent means and why it's required.
    """
    return jsonify({
        "fpic_required": True,
        "purpose": "Extract text and structure from your documents using machine learning",
        "data_handling": {
            "processing_location": "On our secure servers (never sent to external services)",
            "storage": "Documents are processed in memory and not stored permanently",
            "sharing": "Your documents are never shared with third parties",
            "ai_training": "Your documents are NOT used to train AI models",
        },
        "your_rights": {
            "withdraw_consent": "You can withdraw consent at any time",
            "delete_data": "You can request deletion of all your data",
            "access_data": "You can request a copy of all your data",
        },
        "consent_text": "I consent to processing my documents with AI to extract text and structure. I understand my documents stay on your servers and are not shared externally.",
    })
```

**Create FPIC consent UI component:**

File: `/ganuda/assist/core/frontend/src/components/DocumentUploadConsent.tsx`

```typescript
import React, { useState } from 'react';
import { Checkbox, Alert } from '@trussworks/react-uswds';

interface DocumentUploadConsentProps {
  onConsentChange: (consented: boolean) => void;
}

const DocumentUploadConsent: React.FC<DocumentUploadConsentProps> = ({ onConsentChange }) => {
  const [consented, setConsented] = useState(false);

  const handleConsentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newConsent = e.target.checked;
    setConsented(newConsent);
    onConsentChange(newConsent);
  };

  return (
    <div className="document-consent">
      <Alert type="info" headingLevel="h4" slim>
        <strong>Document Processing Consent</strong>
        <p>
          We use AI to extract text and structure from your documents. This helps us
          auto-fill forms and identify relevant information for your claim.
        </p>

        <h5>What we do:</h5>
        <ul>
          <li>Process your documents on our secure servers (not cloud services)</li>
          <li>Extract text, tables, and form fields automatically</li>
          <li>Help you complete applications faster</li>
        </ul>

        <h5>What we DON'T do:</h5>
        <ul>
          <li>Send your documents to external companies (Google, AWS, etc.)</li>
          <li>Store your documents permanently (processed in memory only)</li>
          <li>Use your documents to train AI models</li>
          <li>Share your documents with third parties</li>
        </ul>
      </Alert>

      <Checkbox
        id="fpic-consent"
        name="fpic-consent"
        label="I consent to AI processing of my documents. I understand my documents stay on your servers and are not shared externally."
        checked={consented}
        onChange={handleConsentChange}
      />

      {!consented && (
        <p className="text-secondary" style={{ marginTop: '0.5rem' }}>
          You must provide consent to upload and process documents.
        </p>
      )}
    </div>
  );
};

export default DocumentUploadConsent;
```

---

### Phase 4: Real-World Testing (2 hours)

**Test on actual document types.**

Create test script:

File: `/ganuda/assist/core/backend/tests/document_ai/test_real_documents.py`

```python
"""
Test Docling on real document types.

Council requirement: Validate on actual VA forms, medical records, etc.
"""

import pytest
from services.document_ai.processor_factory import DocumentProcessorFactory
from services.document_ai.base_processor import DocumentType

class TestRealDocuments:
    """Test document processing on real document types."""

    def test_va_form_21_526ez(self):
        """Test VA disability claim form processing."""
        # Path to sample VA Form 21-526EZ
        form_path = "/ganuda/assist/test-data/va-form-21-526ez-sample.pdf"

        processor = DocumentProcessorFactory.get_processor()
        result = processor.process_document(file_path=form_path, document_type=DocumentType.PDF)

        # Verify extraction
        assert len(result.text) > 100  # Should extract significant text
        assert "veteran" in result.text.lower()
        assert result.confidence > 0.8

        # Check for form fields
        # VA Form 21-526EZ has fields like: veteran_name, ssn, claim_date
        assert len(result.fields) > 0  # Should detect form fields

    def test_dd214_discharge_record(self):
        """Test DD-214 military discharge record."""
        dd214_path = "/ganuda/assist/test-data/dd214-sample.pdf"

        processor = DocumentProcessorFactory.get_processor()
        result = processor.process_document(file_path=dd214_path, document_type=DocumentType.PDF)

        # DD-214 contains: dates, military service info, discharge type
        assert "discharge" in result.text.lower() or "separation" in result.text.lower()
        assert result.confidence > 0.7

    def test_medical_records_cp_exam(self):
        """Test C&P examination medical records."""
        cp_exam_path = "/ganuda/assist/test-data/cp-exam-sample.pdf"

        processor = DocumentProcessorFactory.get_processor()
        result = processor.process_document(file_path=cp_exam_path, document_type=DocumentType.PDF)

        # Medical records contain diagnosis, symptoms, examination findings
        assert len(result.text) > 200
        assert len(result.headings) > 0  # Medical records have structured headings

    def test_ssa_earnings_statement(self):
        """Test SSA earnings statement."""
        ssa_path = "/ganuda/assist/test-data/ssa-earnings-sample.pdf"

        processor = DocumentProcessorFactory.get_processor()
        result = processor.process_document(file_path=ssa_path, document_type=DocumentType.PDF)

        # Earnings statement contains tables
        assert len(result.tables) > 0  # Should extract earnings table

    def test_cherokee_enrollment_application(self):
        """Test Cherokee Nation enrollment application."""
        # This may not exist yet, but placeholder for future
        enrollment_path = "/ganuda/assist/test-data/cherokee-enrollment-sample.pdf"

        try:
            processor = DocumentProcessorFactory.get_processor()
            result = processor.process_document(file_path=enrollment_path, document_type=DocumentType.PDF)

            # Cherokee documents may contain syllabary
            # Docling should preserve Cherokee characters
            assert len(result.text) > 0
        except FileNotFoundError:
            pytest.skip("Cherokee enrollment sample not available")

    def test_faxed_medical_record(self):
        """Test low-quality faxed medical record (TIFF image)."""
        fax_path = "/ganuda/assist/test-data/faxed-medical-record.tiff"

        processor = DocumentProcessorFactory.get_processor()
        result = processor.process_document(file_path=fax_path, document_type=DocumentType.IMAGE)

        # Faxed images are low quality, confidence may be lower
        assert len(result.text) > 50  # Should extract some text
        # Confidence may be lower for faxed images, but should still process
```

---

### Phase 5: Network Security Verification (1 hour)

**Verify no data leaves cluster during processing.**

Create verification script:

File: `/ganuda/assist/core/backend/tests/security/test_network_isolation.sh`

```bash
#!/bin/bash
# Network isolation test for Docling
# Council requirement: Verify no external network calls during processing

set -e

echo "=== Docling Network Isolation Test ==="
echo "Council requirement: All traffic must stay within 192.168.132.x"
echo ""

# Start tcpdump on greenfin
ssh greenfin.ganuda.local "sudo tcpdump -i eth0 -w /tmp/docling-test.pcap not host 192.168.132.222" &
TCPDUMP_PID=$!
sleep 2  # Let tcpdump start

echo "Processing test document..."

# Process a test document via API
curl -X POST http://greenfin.ganuda.local:5000/api/v1/documents/process \
  -F "file=@/ganuda/assist/test-data/va-form-21-526ez-sample.pdf" \
  -F "consent=true" \
  -H "Authorization: Bearer test-token"

sleep 2  # Let packets finish

# Stop tcpdump
kill $TCPDUMP_PID

# Download and analyze packet capture
scp greenfin.ganuda.local:/tmp/docling-test.pcap /tmp/

echo ""
echo "=== Analyzing packet capture ==="
tcpdump -r /tmp/docling-test.pcap

# Check for external traffic
EXTERNAL_PACKETS=$(tcpdump -r /tmp/docling-test.pcap | grep -v "192.168.132" | wc -l)

if [ $EXTERNAL_PACKETS -gt 0 ]; then
  echo ""
  echo "❌ FAILURE: External network traffic detected!"
  echo "Council condition violated: Docling is calling external services"
  echo ""
  echo "External packets:"
  tcpdump -r /tmp/docling-test.pcap | grep -v "192.168.132"
  exit 1
else
  echo ""
  echo "✅ SUCCESS: No external network traffic detected"
  echo "All traffic stayed within 192.168.132.x network"
  exit 0
fi
```

---

## VERIFICATION CHECKLIST

Before marking this task complete:

- [ ] Docling installed on greenfin (192.168.132.224)
- [ ] Offline test passes (network disconnected, processing succeeds)
- [ ] Dependency chain audited (Crawdad approval required)
- [ ] tcpdump test passes (zero external traffic)
- [ ] Models downloaded and cached locally
- [ ] Base processor interface created
- [ ] Docling processor implemented
- [ ] Tesseract fallback implemented
- [ ] Processor factory created
- [ ] API endpoint created with FPIC consent requirement
- [ ] FPIC consent UI component created
- [ ] Rate limiting configured (10/minute)
- [ ] Audit logging implemented
- [ ] Real document tests pass (VA form, DD-214, medical records, SSA form)
- [ ] Network isolation test passes (no external traffic)
- [ ] All tests documented and passing

---

## SUCCESS CRITERIA

1. **Docling processes documents offline** (network disconnected test passes)
2. **Zero external network calls** (tcpdump shows only 192.168.132.x traffic)
3. **FPIC consent required** (API returns 403 without consent flag)
4. **Real documents extract correctly** (VA forms, medical records, etc.)
5. **Abstraction layer works** (can swap Docling for Tesseract fallback)
6. **All processing logged** (audit table contains document processing events)

---

## NOTES FOR JR EXECUTOR

- **Server:** greenfin (192.168.132.224)
- **Database:** bluefin (192.168.132.222), zammad_production
- **Dependencies:** Python 3.9+, pip, tcpdump (for network testing)
- **Council Oversight:** Crawdad must approve dependency audit
- **FPIC Context:** Cherokee Nation requires FPIC (Free, Prior, and Informed Consent) for data processing
- **PHI/PII:** Medical records contain protected health information
- **Blocked By:** None
- **Blocks:** Future document auto-fill features

---

## CULTURAL NOTE

Council member Spider: "Veterans must be informed their documents are processed by AI and must consent explicitly (FPIC compliance)."

FPIC (Free, Prior, and Informed Consent) is an Indigenous data sovereignty principle from the CARE Principles for Indigenous Data Governance.

- **Free:** No coercion (user can decline and still use service)
- **Prior:** Consent before processing (not after)
- **Informed:** Clear explanation of what AI does with their data

This is not GDPR checkbox theater. This is meaningful consent. Users must understand:
1. What happens to their documents
2. Where processing occurs (on our servers, not cloud)
3. What we don't do (no external sharing, no AI training)

Council member Raven: "Redaction must be user-controlled, not automatic. Veterans choose what gets protected. Default should be 'protect' not 'erase.'"

Document processing is not about hiding data from users. It's about helping users understand and use their own data.

---

**Council Verdict:** 7/7 APPROVE — With conditions (self-host, no telemetry, FPIC consent, abstraction layer)
**Next Steps After Completion:** Integrate document extraction with VA form auto-fill (future task)

ᏩᏙ (It is finished.)
