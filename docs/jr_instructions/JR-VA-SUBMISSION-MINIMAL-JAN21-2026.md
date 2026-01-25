# JR Instruction: VA Submission Endpoint - Minimal
## Task ID: VA-SUBMIT-MINI-001
## Priority: P1

---

## Objective

Add VA submission endpoint to wizard routes. Minimal implementation.

---

## Implementation

Modify: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```python
# Add this import at top of file
from datetime import datetime
import httpx

# Add this endpoint after existing routes

@router.post("/sessions/{session_id}/submit-va")
async def submit_to_va(
    session_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit completed wizard session to VA.
    Requires VA OAuth tokens to be linked.
    """
    # Get session
    session = db.execute(
        "SELECT * FROM vetassist_wizard_sessions WHERE id = %s AND user_id = %s",
        [session_id, current_user.id]
    ).fetchone()

    if not session:
        raise HTTPException(404, "Session not found")

    if session['status'] != 'ready_to_submit':
        raise HTTPException(400, "Session not ready for submission")

    # Get user's VA tokens
    va_tokens = db.execute(
        "SELECT access_token, refresh_token FROM vetassist_va_tokens WHERE user_id = %s",
        [current_user.id]
    ).fetchone()

    if not va_tokens:
        raise HTTPException(400, "VA account not linked. Please connect your VA.gov account.")

    # Build submission payload
    payload = {
        "form526": {
            "veteran": session['veteran_info'],
            "disabilities": session['conditions'],
            "serviceHistory": session['service_info'],
        }
    }

    # Submit to VA API (sandbox for now)
    VA_API_URL = "https://sandbox-api.va.gov/services/claims/v1/forms/526"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                VA_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {va_tokens['access_token']}",
                    "Content-Type": "application/json",
                },
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            # Update session with confirmation
            db.execute(
                """UPDATE vetassist_wizard_sessions
                   SET status = 'submitted',
                       va_confirmation_number = %s,
                       submitted_at = %s
                   WHERE id = %s""",
                [result.get('confirmationNumber'), datetime.utcnow(), session_id]
            )
            db.commit()

            return {
                "success": True,
                "confirmation_number": result.get('confirmationNumber'),
                "message": "Claim submitted successfully to VA"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }

    except Exception as e:
        raise HTTPException(500, f"VA submission failed: {str(e)}")
```

---

## Verification

```bash
# Check endpoint was added
grep -n "submit-va" /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py
```

---

*Cherokee AI Federation - For Seven Generations*
