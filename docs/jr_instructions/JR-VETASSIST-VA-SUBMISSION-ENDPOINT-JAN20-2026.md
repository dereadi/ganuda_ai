# Jr Instruction: VetAssist VA Submission Endpoint
## Task ID: VetAssist Sprint 4 - Task 1
## Priority: P1
## Estimated Complexity: High

---

## Objective

Implement direct claim submission to VA via the Lighthouse Benefits Intake API. Veterans should be able to submit their completed claims directly to the VA instead of downloading and mailing PDFs.

---

## Prerequisites

- VetAssist backend running (port 8001)
- PDF generation working (pdf_service.py)
- VA Lighthouse sandbox API key (to be obtained from developer.va.gov)

---

## Implementation Steps

### Step 1: Create Database Table

```sql
CREATE TABLE IF NOT EXISTS vetassist_va_submissions (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES vetassist_wizard_sessions(session_id),

    -- VA API tracking
    va_guid VARCHAR(64),
    va_status VARCHAR(50) DEFAULT 'pending',
    va_status_updated_at TIMESTAMP,

    -- Submission details
    form_type VARCHAR(20),
    pdf_path VARCHAR(255),
    pdf_size_bytes INT,

    -- Retry logic
    attempt_count INT DEFAULT 0,
    last_attempt_at TIMESTAMP,
    next_retry_at TIMESTAMP,
    error_message TEXT,

    -- Audit
    submitted_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_va_submissions_session ON vetassist_va_submissions(session_id);
CREATE INDEX idx_va_submissions_status ON vetassist_va_submissions(va_status);
CREATE INDEX idx_va_submissions_retry ON vetassist_va_submissions(next_retry_at)
    WHERE va_status IN ('pending', 'error');
```

### Step 2: Create VA API Service

Create `/ganuda/vetassist/backend/app/services/va_api_service.py`:

```python
"""
VA Lighthouse API Service
Direct submission to Veterans Benefits Administration
Cherokee AI Federation - For Seven Generations
"""
import os
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# VA API Configuration
VA_API_BASE = os.environ.get('VA_API_BASE', 'https://sandbox-api.va.gov')
VA_API_KEY = os.environ.get('VA_LIGHTHOUSE_API_KEY', '')

# Timeouts
UPLOAD_TIMEOUT = 60.0
STATUS_TIMEOUT = 30.0


class VAAPIService:
    """Service for interacting with VA Lighthouse Benefits Intake API"""

    def __init__(self):
        if not VA_API_KEY:
            logger.warning("VA_LIGHTHOUSE_API_KEY not set - submissions will fail")

        self.headers = {
            'apikey': VA_API_KEY,
            'Content-Type': 'application/json'
        }

    async def get_upload_location(self) -> Dict[str, Any]:
        """
        Step 1: Get a pre-signed upload URL from VA.
        URL is valid for 15 minutes.

        Returns: {guid, location_url, expires_at}
        """
        async with httpx.AsyncClient(timeout=STATUS_TIMEOUT) as client:
            response = await client.post(
                f"{VA_API_BASE}/services/vba_documents/v1/",
                headers=self.headers
            )

            if response.status_code != 200:
                raise VAAPIError(f"Failed to get upload location: {response.status_code} - {response.text}")

            data = response.json()
            return {
                'guid': data['data']['id'],
                'location_url': data['data']['attributes']['location'],
                'expires_at': data['data']['attributes']['expiration_date']
            }

    async def upload_pdf(self, location_url: str, pdf_path: str, metadata: Dict) -> bool:
        """
        Step 2: Upload PDF to the pre-signed URL.

        Args:
            location_url: URL from get_upload_location()
            pdf_path: Path to PDF file
            metadata: Form metadata (veteran info, form type)

        Returns: True if successful
        """
        async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
            with open(pdf_path, 'rb') as f:
                files = {
                    'content': (os.path.basename(pdf_path), f, 'application/pdf'),
                    'metadata': (None, self._build_metadata(metadata), 'application/json')
                }

                response = await client.put(
                    location_url,
                    files=files
                )

                if response.status_code not in (200, 201):
                    raise VAAPIError(f"PDF upload failed: {response.status_code}")

                return True

    async def check_status(self, guid: str) -> Dict[str, Any]:
        """
        Step 3: Check submission status.

        Status progression:
        pending -> uploaded -> received -> processing -> success -> vbms

        Returns: {status, updated_at, error_message}
        """
        async with httpx.AsyncClient(timeout=STATUS_TIMEOUT) as client:
            response = await client.get(
                f"{VA_API_BASE}/services/vba_documents/v1/uploads/{guid}",
                headers=self.headers
            )

            if response.status_code != 200:
                raise VAAPIError(f"Status check failed: {response.status_code}")

            data = response.json()
            attrs = data['data']['attributes']

            return {
                'status': attrs['status'],
                'updated_at': attrs.get('updated_at'),
                'error_message': attrs.get('detail', {}).get('message')
            }

    async def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Optional: Pre-validate PDF before submission.
        Catches format issues early.

        Returns: {valid, errors}
        """
        async with httpx.AsyncClient(timeout=STATUS_TIMEOUT) as client:
            with open(pdf_path, 'rb') as f:
                files = {'document': (os.path.basename(pdf_path), f, 'application/pdf')}

                response = await client.post(
                    f"{VA_API_BASE}/services/vba_documents/v1/uploads/validate_document",
                    headers={'apikey': VA_API_KEY},
                    files=files
                )

                if response.status_code == 200:
                    return {'valid': True, 'errors': []}
                else:
                    data = response.json()
                    return {
                        'valid': False,
                        'errors': data.get('errors', [response.text])
                    }

    def _build_metadata(self, metadata: Dict) -> str:
        """Build metadata JSON for VA submission"""
        import json
        return json.dumps({
            'veteranFirstName': metadata.get('first_name', ''),
            'veteranLastName': metadata.get('last_name', ''),
            'fileNumber': metadata.get('file_number', ''),
            'zipCode': metadata.get('zip_code', ''),
            'source': 'VetAssist Cherokee AI',
            'docType': metadata.get('form_type', '21-526EZ'),
            'businessLine': 'CMP'  # Compensation
        })


class VAAPIError(Exception):
    """Exception for VA API errors"""
    pass


# Singleton instance
va_api_service = VAAPIService()
```

### Step 3: Create Submission Endpoint

Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`:

```python
from fastapi import BackgroundTasks
from app.services.va_api_service import va_api_service, VAAPIError

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

### Step 4: Add Environment Variable

The Jr should NOT create the API key - this is a manual step.

Add to `/ganuda/vetassist/backend/.env`:
```
VA_LIGHTHOUSE_API_KEY=<to-be-obtained-from-developer.va.gov>
VA_API_BASE=https://sandbox-api.va.gov
```

---

## Testing

```bash
# Create a completed session first, then:

# Submit to VA
curl -X POST "http://localhost:8001/api/v1/wizard/{session_id}/submit-to-va"

# Check status
curl "http://localhost:8001/api/v1/wizard/{session_id}/va-status"
```

---

## Acceptance Criteria

1. Database table created for tracking submissions
2. VA API service handles upload location, PDF upload, status check
3. Endpoint queues submission as background task
4. Error handling with retry logic
5. Status endpoint returns current VA status

---

## Security Notes

- API key stored in environment, not code
- Transmission over HTTPS only
- Veteran data validated before submission

---

*Cherokee AI Federation - For Seven Generations*
