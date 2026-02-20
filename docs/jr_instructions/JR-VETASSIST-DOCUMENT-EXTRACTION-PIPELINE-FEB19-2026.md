# Jr Instruction: VetAssist Document Extraction Pipeline — Wire Upload → Extract → Profile

**Task ID**: VETASSIST-DOC-EXTRACT-001
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8
**use_rlm**: false
**Council Vote**: #103c5135086cf09f (PROCEED WITH CAUTION, 0.85)

## Context

VetAssist has OCR, VLM extraction, DD-214 parser, medical document processor, and evidence tracker — all already built but **not wired together**. When a veteran uploads a document, nothing happens beyond storing the file. This task connects the pipeline so uploads trigger extraction and populate the veteran's profile and claims.

**Flow**: Upload → Background extraction → Classify → Type-specific parse → Present results → User confirms → Update profile/claims

**Security**: PII stays in vetassist DB. User MUST confirm before any profile update. All extractions logged.

## Step 1: Add document processing endpoint to wizard.py

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

<<<<<<< SEARCH
@router.get("/{session_id}")
def get_wizard_state(session_id: str):
=======
@router.post("/{session_id}/process-documents")
def process_uploaded_documents(session_id: str, background_tasks: BackgroundTasks):
    """Trigger extraction pipeline on all unprocessed uploads for a session.

    Runs OCR/VLM extraction in background, classifies each document,
    extracts structured data, and stores results for user review.
    Council Vote #103c5135086cf09f.
    """
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get unprocessed files for this session
            cur.execute("""
                SELECT file_uuid, original_name, category, mime_type
                FROM vetassist_wizard_files
                WHERE session_id = %s AND deleted = false
                  AND file_uuid NOT IN (
                      SELECT COALESCE(metadata->>'file_uuid', '') FROM vetassist_documents
                      WHERE session_id = %s AND processing_status = 'completed'
                  )
            """, (session_id, session_id))
            files = cur.fetchall()
        conn.close()

        if not files:
            return {"message": "No unprocessed documents found", "count": 0}

        # Queue background processing for each file
        for f in files:
            file_path = os.path.join(UPLOAD_DIR, session_id, f['file_uuid'])
            background_tasks.add_task(
                _process_single_document,
                session_id=session_id,
                file_uuid=f['file_uuid'],
                file_path=file_path,
                original_name=f['original_name'],
                category=f['category'],
                mime_type=f['mime_type']
            )

        return {
            "message": f"Processing {len(files)} document(s) in background",
            "count": len(files),
            "files": [f['original_name'] for f in files]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/extracted-data")
def get_extracted_data(session_id: str):
    """Get all extracted data for a session, pending user confirmation."""
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, document_type, classification_confidence,
                       parsed_data, processing_status, processing_error,
                       metadata->>'original_name' as original_name,
                       metadata->>'file_uuid' as file_uuid,
                       created_at
                FROM vetassist_documents
                WHERE session_id = %s
                ORDER BY created_at DESC
            """, (session_id,))
            docs = cur.fetchall()
        conn.close()

        # Serialize datetime fields
        for doc in docs:
            if doc.get('created_at'):
                doc['created_at'] = doc['created_at'].isoformat()
            if doc.get('parsed_data') and isinstance(doc['parsed_data'], str):
                doc['parsed_data'] = json.loads(doc['parsed_data'])

        return {"documents": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConfirmExtractionRequest(BaseModel):
    document_id: int
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict, description="Fields the user confirmed/edited")
    update_profile: bool = Field(default=False, description="Whether to update veteran profile with this data")
    update_claims: bool = Field(default=False, description="Whether to update claims with extracted conditions")


@router.post("/{session_id}/confirm-extraction")
def confirm_extraction(session_id: str, request: ConfirmExtractionRequest):
    """User confirms extracted data — only then does it update profile/claims.

    Veterans must explicitly approve before any PII is written to their profile.
    Audit trail stored in metadata.
    """
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get the document's parsed data
            cur.execute("""
                SELECT id, document_type, parsed_data, metadata
                FROM vetassist_documents
                WHERE id = %s AND session_id = %s
            """, (request.document_id, session_id))
            doc = cur.fetchone()

            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")

            parsed = doc['parsed_data'] if isinstance(doc['parsed_data'], dict) else json.loads(doc['parsed_data'] or '{}')
            meta = doc['metadata'] if isinstance(doc['metadata'], dict) else json.loads(doc['metadata'] or '{}')

            # Merge user confirmations (user may have corrected fields)
            confirmed = {**parsed, **request.confirmed_fields}

            # Get veteran_id from session
            cur.execute("SELECT veteran_id FROM vetassist_wizard_sessions WHERE session_id = %s", (session_id,))
            session_row = cur.fetchone()
            veteran_id = session_row['veteran_id'] if session_row else None

            updates_applied = []

            if request.update_profile and veteran_id and doc['document_type'] == 'dd214':
                # Update veteran profile from DD-214 data
                profile_fields = {}
                field_map = {
                    'service_member_name': 'full_name',
                    'branch': 'branch',
                    'entry_date': 'service_start_date',
                    'separation_date': 'service_end_date',
                    'discharge_type': 'discharge_type',
                    'grade_rank': 'rank',
                }
                for src, dst in field_map.items():
                    if confirmed.get(src):
                        profile_fields[dst] = confirmed[src]

                if profile_fields:
                    # Store extracted profile data in wizard session answers
                    cur.execute("""
                        UPDATE vetassist_wizard_sessions
                        SET answers = COALESCE(answers, '{}'::jsonb) ||
                            jsonb_build_object('extracted_profile', %s::jsonb)
                        WHERE session_id = %s
                    """, (json.dumps(profile_fields), session_id))
                    updates_applied.append(f"Profile: {list(profile_fields.keys())}")

            if request.update_claims and veteran_id:
                # Extract conditions from medical records or VA decision letters
                conditions = confirmed.get('conditions', confirmed.get('diagnoses', []))
                if conditions:
                    cur.execute("""
                        UPDATE vetassist_wizard_sessions
                        SET answers = COALESCE(answers, '{}'::jsonb) ||
                            jsonb_build_object('extracted_conditions', %s::jsonb)
                        WHERE session_id = %s
                    """, (json.dumps(conditions), session_id))
                    updates_applied.append(f"Conditions: {len(conditions)} extracted")

            # Mark document as confirmed with audit trail
            meta['confirmed_at'] = datetime.now().isoformat()
            meta['confirmed_fields'] = list(request.confirmed_fields.keys())
            meta['updates_applied'] = updates_applied
            cur.execute("""
                UPDATE vetassist_documents
                SET metadata = %s::jsonb, processing_status = 'confirmed'
                WHERE id = %s
            """, (json.dumps(meta), request.document_id))

            conn.commit()
        conn.close()

        return {
            "status": "confirmed",
            "document_id": request.document_id,
            "updates_applied": updates_applied
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _process_single_document(session_id: str, file_uuid: str, file_path: str,
                              original_name: str, category: str, mime_type: str):
    """Background task: Run extraction pipeline on a single uploaded document."""
    import traceback

    try:
        # Step 1: Extract text via OCR pipeline
        extracted_text = ""
        try:
            import sys
            sys.path.insert(0, '/ganuda/vetassist/lib')
            from ocr_pipeline import extract_text
            extracted_text = extract_text(file_path)
        except Exception as ocr_err:
            print(f"[DOC-EXTRACT] OCR failed for {original_name}: {ocr_err}")

        # Step 2: Try VLM extraction for images/scanned PDFs
        vlm_result = None
        if mime_type and ('image' in mime_type or not extracted_text.strip()):
            try:
                from app.services.vlm_document_extractor import VLMDocumentExtractor
                extractor = VLMDocumentExtractor()
                vlm_result = extractor.extract(file_path, document_type=category)
            except Exception as vlm_err:
                print(f"[DOC-EXTRACT] VLM extraction failed for {original_name}: {vlm_err}")

        # Step 3: Classify document type
        doc_type = category  # Start with user-selected category
        confidence = 0.5
        try:
            from document_classifier import classify_document
            classification = classify_document(extracted_text)
            if classification and classification.get('confidence', 0) > confidence:
                doc_type = classification['type']
                confidence = classification['confidence']
        except Exception:
            pass

        # Step 4: Type-specific parsing
        parsed_data = {}

        if doc_type in ('dd214', 'service_records'):
            try:
                from dd214_parser import parse_dd214
                parsed_data = parse_dd214(extracted_text)
                parsed_data['_source'] = 'dd214_parser'
            except Exception as e:
                print(f"[DOC-EXTRACT] DD-214 parse failed: {e}")

        elif doc_type in ('medical', 'nexus_letter', 'buddy_statement'):
            try:
                from app.services.medical_document_processor import MedicalDocumentProcessor
                processor = MedicalDocumentProcessor()
                result = processor.process(file_path)
                parsed_data = {
                    'diagnoses': result.get('diagnoses', []),
                    'treatments': result.get('treatments', []),
                    'nexus_signals': result.get('nexus_signals', []),
                    'document_subtype': result.get('document_type', doc_type),
                    '_source': 'medical_processor'
                }
            except Exception as e:
                print(f"[DOC-EXTRACT] Medical parse failed: {e}")

        # Merge VLM results if available (higher confidence for structured fields)
        if vlm_result and vlm_result.get('fields'):
            parsed_data['vlm_fields'] = vlm_result['fields']
            parsed_data['vlm_confidence'] = vlm_result.get('confidence', 0)
            if not parsed_data.get('_source'):
                parsed_data['_source'] = 'vlm_extractor'

        # Step 5: Store results in vetassist_documents
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vetassist_documents
                    (session_id, document_type, classification_confidence,
                     parsed_data, ocr_text, processing_status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                doc_type,
                confidence,
                json.dumps(parsed_data),
                extracted_text[:10000],  # Cap stored OCR text
                'completed',
                json.dumps({
                    'file_uuid': file_uuid,
                    'original_name': original_name,
                    'category': category,
                    'mime_type': mime_type,
                    'processed_at': datetime.now().isoformat()
                })
            ))
            conn.commit()
        conn.close()
        print(f"[DOC-EXTRACT] Processed {original_name}: type={doc_type}, confidence={confidence:.2f}, fields={len(parsed_data)}")

    except Exception as e:
        # Store error state
        try:
            conn = get_db_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO vetassist_documents
                        (session_id, document_type, processing_status, processing_error, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    session_id,
                    category or 'unknown',
                    'error',
                    str(e),
                    json.dumps({'file_uuid': file_uuid, 'original_name': original_name})
                ))
                conn.commit()
            conn.close()
        except Exception:
            pass
        print(f"[DOC-EXTRACT] ERROR processing {original_name}: {traceback.format_exc()}")


@router.get("/{session_id}")
def get_wizard_state(session_id: str):
>>>>>>> REPLACE

## Step 2: Ensure vetassist_documents table exists

This is a manual step — the table may already exist. Run on bluefin (192.168.132.222):

```text
CREATE TABLE IF NOT EXISTS vetassist_documents (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    document_type VARCHAR(100),
    classification_confidence FLOAT DEFAULT 0,
    parsed_data JSONB DEFAULT '{}',
    ocr_text TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vetassist_docs_session ON vetassist_documents(session_id);
CREATE INDEX IF NOT EXISTS idx_vetassist_docs_status ON vetassist_documents(processing_status);
```

## Verification

1. Upload a PDF to a wizard session
2. Call `POST /api/v1/wizard/{session_id}/process-documents`
3. Wait a few seconds, then `GET /api/v1/wizard/{session_id}/extracted-data`
4. Verify parsed_data contains extracted fields
5. Call `POST /api/v1/wizard/{session_id}/confirm-extraction` with document_id and update_profile=true
6. Verify wizard session answers contain extracted_profile

## Manual Steps (TPM on redfin)

1. Create vetassist_documents table on bluefin if it doesn't exist
2. Restart VetAssist backend after Jr applies changes
3. Test with a sample DD-214 PDF upload
