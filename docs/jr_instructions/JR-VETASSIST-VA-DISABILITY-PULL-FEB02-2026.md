# Jr Instruction: VA Disability Pull + Calculator Pre-Populate

**Task ID:** VETASSIST-VA-PULL-001
**Assigned:** Software Engineer Jr.
**Priority:** P2
**Created:** 2026-02-02
**TPM:** Claude Opus 4.5
**Depends on:** VETASSIST-VA-LINK-VERIFY-001 (VA account linking must work)

---

## Context

The calculator has a stub endpoint at `GET /calculator/va-ratings` (calculator.py:155) that returns 501 Not Implemented. This task replaces that stub with a real implementation that:

1. Reads the authenticated user's linked VA account
2. Retrieves their rated disabilities from the VA API
3. Returns them in the calculator's `Condition` format so the frontend can pre-populate the form

### The VA API

VA provides disability rating data through the **Veterans Health API — Disability Rating** endpoint. In sandbox mode:

- Base URL: `https://sandbox-api.va.gov/services/veteran_verification/v2`
- Endpoint: `GET /disability_rating`
- Auth: Bearer token (the VA access_token from OAuth)
- Returns: `{ "data": { "id": "...", "type": "disability_ratings", "attributes": { "combined_disability_rating": 40, "combined_effective_date": "...", "individual_ratings": [...] } } }`

Each `individual_rating` contains:
```json
{
  "decision": "Service Connected",
  "effective_date": "2020-01-01",
  "rating_percentage": 30,
  "diagnostic_type_name": "Post-Traumatic Stress Disorder",
  "diagnostic_type_code": "9411",
  "static_ind": false
}
```

### Existing Code to Read

1. `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py` — the stub at line 155
2. `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py` — `get_current_user` dependency
3. `/ganuda/vetassist/backend/app/api/v1/endpoints/va_auth.py` — VA OAuth service
4. `/ganuda/vetassist/backend/app/services/va_oauth_service.py` — VA OAuth token management
5. `/ganuda/vetassist/backend/app/services/va_session_service.py` — VA session/token storage

---

## Step 1: Create VA Disability Rating Service

Create: `/ganuda/vetassist/backend/app/services/va_disability_rating_service.py`

This service fetches and transforms VA disability data:

```python
"""
VA Disability Rating Service
Fetches rated disabilities from VA API for linked veterans.
"""

import logging
import httpx
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

VA_API_BASE = "https://sandbox-api.va.gov/services/veteran_verification/v2"


class VADisabilityRatingService:
    """Fetch and transform VA disability rating data."""

    @staticmethod
    async def get_disability_ratings(va_access_token: str) -> Dict[str, Any]:
        """
        Fetch disability ratings from VA API.

        Args:
            va_access_token: OAuth access token from VA.gov

        Returns:
            Dict with combined_rating and individual conditions list

        Raises:
            Exception on API errors
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VA_API_BASE}/disability_rating",
                headers={
                    "Authorization": f"Bearer {va_access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 401:
                raise ValueError("VA access token expired or invalid")
            if response.status_code != 200:
                logger.error(f"[VA API] Disability rating fetch failed: {response.status_code} {response.text[:200]}")
                raise Exception(f"VA API returned {response.status_code}")

            data = response.json()

        attrs = data.get("data", {}).get("attributes", {})

        # Transform individual ratings into calculator Condition format
        conditions = []
        for rating in attrs.get("individual_ratings", []):
            # Only include service-connected ratings
            if rating.get("decision") != "Service Connected":
                continue

            pct = rating.get("rating_percentage", 0)
            # VA ratings are multiples of 10
            # Some edge cases exist (e.g., 15% rounded to 20%), normalize
            rounded_pct = round(pct / 10) * 10

            conditions.append({
                "name": rating.get("diagnostic_type_name", "Unknown Condition"),
                "rating": rounded_pct,
                "is_bilateral": False,  # VA API doesn't flag bilateral directly
                "bilateral_side": None,
                "diagnostic_code": rating.get("diagnostic_type_code"),
                "effective_date": rating.get("effective_date"),
                "static": rating.get("static_ind", False),
                "va_source": True  # Flag that this came from VA data
            })

        return {
            "combined_disability_rating": attrs.get("combined_disability_rating"),
            "combined_effective_date": attrs.get("combined_effective_date"),
            "conditions": conditions,
            "conditions_count": len(conditions),
            "source": "va_api",
            "note": "Bilateral conditions may need manual flagging. VA API does not distinguish bilateral pairs."
        }
```

---

## Step 2: Replace the Stub Endpoint

Modify: `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

Replace the stub `GET /va-ratings` endpoint (lines 155-169) with:

```python
@router.get("/va-ratings")
async def get_va_ratings(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch the authenticated veteran's rated disabilities from VA.
    Requires the user to have a linked VA account with a valid access token.

    Returns conditions in CalculatorRequest format for direct form pre-population.
    """
    from app.services.va_disability_rating_service import VADisabilityRatingService

    # Check if user has linked VA account
    if not current_user.va_icn:
        raise HTTPException(
            status_code=400,
            detail="No VA account linked. Link your VA.gov account from Settings first."
        )

    # Get VA access token from session storage
    va_token = _get_va_access_token(current_user.va_icn)
    if not va_token:
        raise HTTPException(
            status_code=401,
            detail="VA session expired. Please re-authenticate with VA.gov."
        )

    try:
        result = await VADisabilityRatingService.get_disability_ratings(va_token)
        return result
    except ValueError as e:
        # Token expired
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VA API error: {str(e)}")


def _get_va_access_token(va_icn: str) -> Optional[str]:
    """
    Look up the VA access token for a linked veteran.
    Checks vetassist_users table where VA tokens are stored.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT access_token, token_expires_at
                FROM vetassist_users
                WHERE va_icn = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (va_icn,))
            row = cur.fetchone()
        conn.close()

        if row and row.get("access_token"):
            # Check expiry if available
            from datetime import datetime, timezone
            expires = row.get("token_expires_at")
            if expires and expires < datetime.now(timezone.utc):
                return None  # Token expired
            return row["access_token"]
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[VA Token] Lookup failed: {e}")

    return None
```

**Important:** Add these imports if not already present at the top of calculator.py:

```python
from app.core.security import get_current_user
from app.core.database_config import get_db_connection
from psycopg2.extras import RealDictCursor
```

---

## Step 3: Verify the vetassist_users Table Schema

The VA token storage table needs to have the right columns. Check:

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "\d vetassist_users"
```

Look for: `va_icn`, `access_token`, `token_expires_at` columns.

If `token_expires_at` doesn't exist (the session service may store expiry differently), adapt the `_get_va_access_token` function to match the actual column names. Document the actual schema in your task output.

---

## Step 4: Test the Endpoint

### Without VA Linking (should get 400):
```bash
curl -s https://vetassist.ganuda.us/api/v1/calculator/va-ratings \
  -H "Authorization: Bearer <auth_token_for_unlinked_user>" | python3 -m json.tool
```
Expected: `400` with "No VA account linked"

### Without Auth (should get 401):
```bash
curl -s https://vetassist.ganuda.us/api/v1/calculator/va-ratings | python3 -m json.tool
```
Expected: `401` with "Not authenticated"

### Full test requires a VA-linked user with valid VA access token, which can only be done through the VA sandbox OAuth flow.

---

## Acceptance Criteria

1. `va_disability_rating_service.py` created with `get_disability_ratings()` method
2. `GET /calculator/va-ratings` no longer returns 501
3. Unlinked users get 400 with helpful message
4. Unauthenticated requests get 401
5. VA API response correctly transformed to calculator `Condition` format
6. `_get_va_access_token()` correctly queries `vetassist_users` table
7. Service handles VA API errors gracefully (502 for upstream failures)

---

## Frontend Note

Frontend pre-population of the calculator form with VA data will be handled by the TPM separately. The frontend will call `GET /calculator/va-ratings` and map the response into the form's conditions array. The `va_source: true` flag on each condition lets the UI distinguish VA-sourced conditions from manually entered ones.

---

## Architecture Note — How the Pieces Fit Together

```
User links VA account (POST /auth/link-va)
    → va_icn stored in users table
    → VA access token stored in vetassist_users table

User visits calculator page
    → Frontend calls GET /calculator/va-ratings
    → Backend checks va_icn on user → looks up access_token
    → Calls VA API → transforms to Condition format
    → Frontend pre-fills form with VA conditions
    → User can add speculative conditions ("What if I file for PTSD?")
    → User saves as scenario (POST /calculator/scenarios)
```

---

*For Seven Generations*
*Cherokee AI Federation — VetAssist Calculator Team*
