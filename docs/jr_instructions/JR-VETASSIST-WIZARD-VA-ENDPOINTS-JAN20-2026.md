# Jr Instruction: Add VA Submission Endpoints to Wizard
## Task ID: VetAssist Sprint 4 - Task 1B (Focused)
## Priority: P1
## Estimated Complexity: Low

---

## Objective

Add submit-to-va and va-status endpoints to the existing wizard.py file. The va_api_service.py and database table already exist.

---

## Prerequisites (Already Done)

- va_api_service.py exists at `/ganuda/vetassist/backend/app/services/va_api_service.py`
- vetassist_va_submissions table exists in database
- wizard.py exists at `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

---

## Implementation

### Step 1: Add Imports to wizard.py

Add these imports at the top of `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`:

```python
from fastapi import BackgroundTasks
from app.services.va_api_service import va_api_service, VAAPIError
```

### Step 2: Add Endpoints to wizard.py

Append these endpoints to the end of `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`:

```python
# ============ VA Direct Submission Endpoints ============

@router.post("/{session_id}/submit-to-va")
async def submit_to_va(
    session_id: str,
    background_tasks: BackgroundTasks
):
    """
    Submit completed claim to VA via Benefits Intake API.

    Flow:
    1. Validate session is complete
    2. Generate PDF if needed
    3. Validate PDF with VA
    4. Queue background submission
    5. Return tracking info
    """
    conn = get_db_conn()
    try:
        # Get session
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT session_id, wizard_type, answers, status, veteran_id
                FROM vetassist_wizard_sessions WHERE session_id = %s
            """, (session_id,))
            session = cur.fetchone()

        if not session:
            raise HTTPException(404, "Session not found")

        if session['status'] != 'completed':
            raise HTTPException(400, "Session must be completed before VA submission")

        # Generate PDF
        from app.services.pdf_service import pdf_service
        answers = session['answers'] if isinstance(session['answers'], dict) else json.loads(session['answers'] or '{}')
        pdf_path = pdf_service.generate_summary(session['wizard_type'], session_id, answers)

        # Validate PDF with VA (optional but recommended)
        try:
            validation = await va_api_service.validate_pdf(pdf_path)
            if not validation['valid']:
                raise HTTPException(400, f"PDF validation failed: {validation['errors']}")
        except Exception as e:
            # Log but don't fail if validation endpoint unavailable
            print(f"[VA] PDF validation skipped: {e}")

        # Create submission record
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO vetassist_va_submissions
                (session_id, form_type, pdf_path, pdf_size_bytes, va_status)
                VALUES (%s, %s, %s, %s, 'queued')
                RETURNING id
            """, (session_id, session['wizard_type'], pdf_path, os.path.getsize(pdf_path)))
            submission_id = cur.fetchone()['id']
            conn.commit()

        # Queue background submission
        background_tasks.add_task(process_va_submission, submission_id)

        return {
            "submission_id": submission_id,
            "status": "queued",
            "message": "Your claim has been queued for submission to the VA. You will receive status updates."
        }

    finally:
        conn.close()


async def process_va_submission(submission_id: int):
    """Background task to submit to VA"""
    conn = get_db_conn()
    try:
        # Get submission details
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.*, w.answers, w.wizard_type
                FROM vetassist_va_submissions s
                JOIN vetassist_wizard_sessions w ON s.session_id = w.session_id
                WHERE s.id = %s
            """, (submission_id,))
            submission = cur.fetchone()

        if not submission:
            return

        try:
            # Step 1: Get upload location
            location = await va_api_service.get_upload_location()

            # Update with GUID
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE vetassist_va_submissions
                    SET va_guid = %s, va_status = 'uploading', last_attempt_at = NOW()
                    WHERE id = %s
                """, (location['guid'], submission_id))
                conn.commit()

            # Step 2: Upload PDF
            answers = submission['answers'] if isinstance(submission['answers'], dict) else {}
            metadata = {
                'first_name': answers.get('first_name', ''),
                'last_name': answers.get('last_name', ''),
                'zip_code': answers.get('zip_code', ''),
                'form_type': submission['wizard_type']
            }

            await va_api_service.upload_pdf(
                location['location_url'],
                submission['pdf_path'],
                metadata
            )

            # Update status
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE vetassist_va_submissions
                    SET va_status = 'uploaded', va_status_updated_at = NOW()
                    WHERE id = %s
                """, (submission_id,))
                conn.commit()

            print(f"[VA] Submission {submission_id} uploaded successfully. GUID: {location['guid']}")

        except VAAPIError as e:
            # Record error for retry
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE vetassist_va_submissions
                    SET va_status = 'error',
                        error_message = %s,
                        attempt_count = attempt_count + 1,
                        next_retry_at = NOW() + INTERVAL '5 minutes'
                    WHERE id = %s
                """, (str(e), submission_id))
                conn.commit()
            print(f"[VA] Submission {submission_id} failed: {e}")

    finally:
        conn.close()


@router.get("/{session_id}/va-status")
async def get_va_status(session_id: str):
    """Get VA submission status for a session"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, va_guid, va_status, va_status_updated_at,
                       attempt_count, error_message, created_at
                FROM vetassist_va_submissions
                WHERE session_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (session_id,))
            submission = cur.fetchone()

        if not submission:
            raise HTTPException(404, "No VA submission found for this session")

        # Optionally refresh status from VA
        if submission['va_guid'] and submission['va_status'] not in ('success', 'vbms', 'error'):
            try:
                status = await va_api_service.check_status(submission['va_guid'])
                # Update local status
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE vetassist_va_submissions
                        SET va_status = %s, va_status_updated_at = NOW()
                        WHERE id = %s
                    """, (status['status'], submission['id']))
                    conn.commit()
                submission['va_status'] = status['status']
            except Exception as e:
                print(f"[VA] Status refresh failed: {e}")

        return {
            "submission_id": submission['id'],
            "va_guid": submission['va_guid'],
            "status": submission['va_status'],
            "status_updated_at": submission['va_status_updated_at'],
            "attempts": submission['attempt_count'],
            "error": submission['error_message'],
            "submitted_at": submission['created_at']
        }

    finally:
        conn.close()
```

---

## Verification (Required before marking complete)

```bash
# 1. Check imports added
grep -n "BackgroundTasks\|va_api_service" /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py

# 2. Check endpoints added
grep -n "submit-to-va\|va-status" /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py

# 3. Restart backend
pkill -f "uvicorn.*8001" && cd /ganuda/vetassist/backend && source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 2>&1 &

# 4. Test endpoints appear in OpenAPI
sleep 5 && curl -s http://localhost:8001/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([p for p in d.get('paths',{}) if 'va' in p.lower()])"
```

---

## Acceptance Criteria

1. BackgroundTasks and va_api_service imports added to wizard.py
2. POST /{session_id}/submit-to-va endpoint exists
3. GET /{session_id}/va-status endpoint exists
4. Endpoints appear in OpenAPI spec
5. Backend restarts without errors

---

*Cherokee AI Federation - For Seven Generations*
