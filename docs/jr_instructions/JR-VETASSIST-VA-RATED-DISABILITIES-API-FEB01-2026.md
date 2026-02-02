# Jr Instruction: VA Rated Disabilities API Integration (Phase C Research + Implementation)

**Task ID:** VETASSIST-VA-RATINGS-API-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Votes:** #8362 (GitHub tools eval), #8363 (research approval)

## Background

VetAssist already has VA OAuth sandbox working with scopes `openid profile claim.read claim.write`. We need to add the `disability_rating.read` scope and build a service to pull a veteran's existing rated disabilities from the VA Lighthouse API. This data pre-populates the calculator with their **Current Rating** so they can add What-If conditions to explore potential changes.

## API Specification (from VA OpenAPI v2)

### Endpoint

```
GET https://sandbox-api.va.gov/services/veteran_verification/v2/disability_rating
```

Production: `https://api.va.gov/services/veteran_verification/v2/disability_rating`

### Authentication

- OAuth 2.0 Authorization Code Grant (same flow we already use)
- Required scope: `disability_rating.read`
- ICN automatically provided via the OAuth token context (no query params needed)

### Response Schema

```json
{
  "data": {
    "id": "string",
    "type": "disability-rating",
    "attributes": {
      "combined_disability_rating": 70,
      "combined_effective_date": "2019-01-01",
      "legal_effective_date": "2019-06-15",
      "individual_ratings": [
        {
          "decision": "Service Connected",
          "disability_rating_id": "string",
          "effective_date": "2018-03-27",
          "rating_end_date": null,
          "rating_percentage": 50,
          "diagnostic_type_code": "9411",
          "hyph_diagnostic_type_code": null,
          "diagnostic_type_name": "Post-traumatic stress disorder",
          "diagnostic_text": "PTSD",
          "static_ind": false
        },
        {
          "decision": "Service Connected",
          "disability_rating_id": "string",
          "effective_date": "2018-03-27",
          "rating_end_date": null,
          "rating_percentage": 10,
          "diagnostic_type_code": "6260",
          "hyph_diagnostic_type_code": null,
          "diagnostic_type_name": "Tinnitus",
          "diagnostic_text": "Tinnitus, bilateral",
          "static_ind": true
        }
      ]
    }
  }
}
```

### Key Fields and Calculator Mapping

| VA API Field | Calculator Form Field | Notes |
|-------------|----------------------|-------|
| `diagnostic_type_name` | `conditions[].name` | Use as condition name |
| `rating_percentage` | `conditions[].rating` | Direct percentage value |
| `diagnostic_text` | — | Contains bilateral info (e.g., "bilateral hearing loss") |
| `static_ind` | — | Display as badge: "Static" (no future re-exam) or "Scheduled for review" |
| `effective_date` | — | Display as info but not a calculator input |
| `decision` | — | Filter: only include "Service Connected" ratings |
| `combined_disability_rating` | Result comparison | Compare VA's combined vs our calculator's result |
| `diagnostic_type_code` | — | Store for reference, link to 38 CFR schedule |

### Bilateral Detection

The VA API does NOT have an explicit `is_bilateral` boolean. Bilateral must be inferred from `diagnostic_text`:
- Look for "bilateral" in the text (case-insensitive)
- Examples: "bilateral hearing loss", "Tinnitus, bilateral", "bilateral knee strain"
- If bilateral is detected, set `conditions[].is_bilateral = true`

## Changes Required

### Step 1: Add OAuth Scope

**File:** `/ganuda/vetassist/backend/app/services/va_oauth_service.py`

Find the `VA_SCOPES` list and add `disability_rating.read`:

```python
VA_SCOPES = [
    'openid',
    'profile',
    'claim.read',
    'claim.write',
    'disability_rating.read',  # NEW: Pull rated disabilities for calculator
]
```

### Step 2: Create Rated Disabilities Service

**Create:** `/ganuda/vetassist/backend/app/services/va_disability_rating_service.py`

```python
"""
VA Disability Rating Service
Fetches veteran's rated disabilities from VA Lighthouse API.
Cherokee AI Federation - For the Seven Generations
"""

import logging
import re
from typing import Optional
from app.core.config import settings
from app.services.va_oauth_service import VAOAuthService

logger = logging.getLogger(__name__)

VA_DISABILITY_RATING_URL = f"{settings.VA_API_BASE}/services/veteran_verification/v2/disability_rating"


class VADisabilityRatingService:
    """Fetch and transform rated disabilities from VA Lighthouse API."""

    def __init__(self):
        self.oauth_service = VAOAuthService()

    async def get_rated_disabilities(self, access_token: str) -> Optional[dict]:
        """
        Fetch rated disabilities for the authenticated veteran.

        Args:
            access_token: Valid VA OAuth access token with disability_rating.read scope

        Returns:
            Dict with combined_rating and conditions array mapped to calculator format,
            or None if the request fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    VA_DISABILITY_RATING_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                    timeout=15.0,
                )

            if response.status_code != 200:
                logger.error(f"VA disability rating API returned {response.status_code}: {response.text[:200]}")
                return None

            data = response.json()
            attributes = data.get("data", {}).get("attributes", {})

            return self._transform_to_calculator_format(attributes)

        except Exception as e:
            logger.error(f"Failed to fetch VA disability ratings: {e}")
            return None

    def _transform_to_calculator_format(self, attributes: dict) -> dict:
        """
        Transform VA API response into calculator form data structure.

        Only includes "Service Connected" ratings with active percentages.
        Detects bilateral conditions from diagnostic_text.
        """
        conditions = []
        individual_ratings = attributes.get("individual_ratings", [])

        for rating in individual_ratings:
            # Only include service-connected, active ratings
            if rating.get("decision") != "Service Connected":
                continue
            if rating.get("rating_end_date") is not None:
                continue  # Rating has ended
            if rating.get("rating_percentage", 0) == 0:
                continue  # 0% ratings don't affect combined

            # Detect bilateral from diagnostic_text
            diagnostic_text = rating.get("diagnostic_text", "")
            is_bilateral = bool(re.search(r'bilateral', diagnostic_text, re.IGNORECASE))

            conditions.append({
                "name": rating.get("diagnostic_type_name", diagnostic_text),
                "rating": rating.get("rating_percentage", 0),
                "is_bilateral": is_bilateral,
                "bilateral_side": "both" if is_bilateral else None,
                # Extra fields for display (not used in calculation)
                "diagnostic_code": rating.get("diagnostic_type_code"),
                "effective_date": rating.get("effective_date"),
                "static": rating.get("static_ind", False),
                "va_source": True,  # Flag: this came from VA, not user-entered
            })

        return {
            "va_combined_rating": attributes.get("combined_disability_rating"),
            "combined_effective_date": attributes.get("combined_effective_date"),
            "conditions": conditions,
        }
```

### Step 3: Add API Endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

Add a new endpoint that fetches the veteran's rated disabilities:

```python
@router.get("/calculator/va-ratings")
async def get_va_ratings(current_user = Depends(get_current_user)):
    """
    Fetch the authenticated veteran's rated disabilities from VA.
    Requires the user to have a linked VA account with a valid access token.
    """
    if not current_user.va_icn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No VA account linked. Link your VA.gov account in Settings first."
        )

    # Get the user's stored VA access token
    from app.services.token_encryption import TokenEncryptionService
    token_service = TokenEncryptionService()
    va_token = token_service.get_decrypted_token(current_user.id)

    if not va_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="VA session expired. Please re-link your VA.gov account in Settings."
        )

    # Fetch rated disabilities
    from app.services.va_disability_rating_service import VADisabilityRatingService
    rating_service = VADisabilityRatingService()
    result = await rating_service.get_rated_disabilities(va_token.access_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not retrieve ratings from VA.gov. Please try again later."
        )

    return result
```

### Step 4: Frontend — "Load My VA Ratings" Button

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

Add a button that appears only for users with linked VA accounts. When clicked, it calls `/api/v1/calculator/va-ratings` and populates the form.

**Add near the top of the form, after the title area:**

```tsx
{user?.va_linked && (
  <button
    type="button"
    onClick={async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE}/calculator/va-ratings`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const err = await response.json();
          setError(err.detail || 'Could not load VA ratings');
          return;
        }
        const data = await response.json();
        // Map VA conditions to form fields
        const formConditions = data.conditions.map((c: any) => ({
          name: c.name,
          rating: c.rating,
          is_bilateral: c.is_bilateral,
          bilateral_side: c.bilateral_side,
        }));
        reset({
          conditions: formConditions.length > 0 ? formConditions : [{ name: '', rating: 0, is_bilateral: false, bilateral_side: null }],
          dependents: getValues('dependents'),
          aid_attendance: getValues('aid_attendance'),
          housebound: getValues('housebound'),
        });
        // Save to localStorage
        localStorage.setItem(CALC_STORAGE_KEY, JSON.stringify(getValues()));
      } catch (e) {
        setError('Failed to connect to VA.gov');
      } finally {
        setLoading(false);
      }
    }}
    className="w-full px-4 py-3 bg-blue-50 border border-blue-300 text-blue-800 rounded-lg hover:bg-blue-100 transition-colors font-medium"
  >
    Load My VA Ratings
  </button>
)}
```

**Add `getValues` to the `useForm` destructuring:**
```tsx
const { register, control, handleSubmit, watch, reset, getValues, formState: { errors } } = useForm<...>(...);
```

**Note:** This button only appears if `user.va_linked === true`. Veterans without a linked VA account won't see it — they enter conditions manually.

## Dependencies

- Phase A (localStorage persistence) should be deployed first — task #516
- VA Account Linking (Phases 2-4 from the linking plan) must be complete
- The `disability_rating.read` scope must be added to our VA Developer Portal sandbox app configuration

## Verification

### Sandbox Testing

1. Log in with a test VA account from [VA test users page](https://developer.va.gov/explore/api/veteran-service-history-and-eligibility/test-users)
2. Link the VA account to a local VetAssist account
3. Go to Calculator, click "Load My VA Ratings"
4. Verify conditions populate with correct names, percentages, and bilateral flags
5. Verify our calculated combined rating matches the VA's `combined_disability_rating`
6. Add a What-If condition and recalculate — the VA conditions plus the new one should combine correctly

### Error Cases

- User without linked VA account: button should not appear
- Expired VA token: should show "VA session expired" message
- VA API down: should show "Could not retrieve ratings" message
- Veteran with 0 rated disabilities: should show empty form with message

## Security Notes

- VA access tokens are encrypted at rest (AES-256-GCM) — existing infrastructure handles this
- The `/calculator/va-ratings` endpoint requires authentication (JWT)
- No PII is cached — ratings are fetched fresh each time
- `va_source: true` flag lets the frontend distinguish VA-sourced conditions from user-entered ones (prevents accidental modification of official ratings)

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `app/services/va_oauth_service.py` | MODIFY | Add `disability_rating.read` to scopes |
| `app/services/va_disability_rating_service.py` | CREATE | New service to fetch and transform rated disabilities |
| `app/api/v1/endpoints/calculator.py` | MODIFY | Add `GET /calculator/va-ratings` endpoint |
| `frontend/app/calculator/page.tsx` | MODIFY | Add "Load My VA Ratings" button |

## References

- [VA Lighthouse Disability Rating API (OpenAPI v2)](https://api.va.gov/internal/docs/veteran-verification/v2/openapi.json)
- [Veteran Service History and Eligibility API Test Data](https://developer.va.gov/explore/api/veteran-service-history-and-eligibility/test-users)
- [VA Developer Portal](https://developer.va.gov/)
- [Rated Disabilities Product Docs](https://github.com/department-of-veterans-affairs/va.gov-team/blob/master/products/disability/rated-disabilities/README.md)
- [disability-max-ratings-api](https://github.com/department-of-veterans-affairs/disability-max-ratings-api) — maps diagnostic codes to max possible ratings
