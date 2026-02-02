# Jr Instruction: VA Rated Disabilities API Integration (v2 — SEARCH/REPLACE format)

**Task ID:** VETASSIST-VA-RATINGS-API-002
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Votes:** #8362 (GitHub tools eval), #8363 (research approval)
**Replaces:** Task #518 (failed — wrong instruction format)

## Background

Add `disability_rating.read` scope to VA OAuth and build a service to pull rated disabilities from VA Lighthouse API. See the full API spec in `JR-VETASSIST-VA-RATED-DISABILITIES-API-FEB01-2026.md`.

## Changes

### Change 1: Add OAuth scope

**File:** `/ganuda/vetassist/backend/app/services/va_oauth_service.py`

<<<<<<< SEARCH
# Scopes needed for Benefits Claims API
VA_SCOPES = [
    'openid',
    'profile',
    'claim.read',
    'claim.write'
]
=======
# Scopes needed for Benefits Claims API + Disability Ratings
VA_SCOPES = [
    'openid',
    'profile',
    'claim.read',
    'claim.write',
    'disability_rating.read',
]
>>>>>>> REPLACE

### Change 2: Create disability rating service

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

logger = logging.getLogger(__name__)

VA_DISABILITY_RATING_URL = f"{settings.VA_API_BASE}/services/veteran_verification/v2/disability_rating"


class VADisabilityRatingService:
    """Fetch and transform rated disabilities from VA Lighthouse API."""

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
                continue
            if rating.get("rating_percentage", 0) == 0:
                continue

            # Detect bilateral from diagnostic_text
            diagnostic_text = rating.get("diagnostic_text", "")
            is_bilateral = bool(re.search(r'bilateral', diagnostic_text, re.IGNORECASE))

            conditions.append({
                "name": rating.get("diagnostic_type_name", diagnostic_text),
                "rating": rating.get("rating_percentage", 0),
                "is_bilateral": is_bilateral,
                "bilateral_side": "both" if is_bilateral else None,
                "diagnostic_code": rating.get("diagnostic_type_code"),
                "effective_date": rating.get("effective_date"),
                "static": rating.get("static_ind", False),
                "va_source": True,
            })

        return {
            "va_combined_rating": attributes.get("combined_disability_rating"),
            "combined_effective_date": attributes.get("combined_effective_date"),
            "conditions": conditions,
        }
```

### Change 3: Add API endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

<<<<<<< SEARCH
from app.core.database import get_db
from app.services.va_calculator import VACalculatorService

router = APIRouter()
=======
from app.core.database import get_db
from app.services.va_calculator import VACalculatorService
from app.services.va_disability_rating_service import VADisabilityRatingService

router = APIRouter()
>>>>>>> REPLACE

Then add the new endpoint. Find the `@router.get("/test-cases")` endpoint and add the va-ratings endpoint BEFORE it:

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

<<<<<<< SEARCH
@router.get("/test-cases")
async def get_test_cases():
=======
@router.get("/va-ratings")
async def get_va_ratings(db: Session = Depends(get_db)):
    """
    Fetch the authenticated veteran's rated disabilities from VA.
    Requires the user to have a linked VA account with a valid access token.
    """
    from app.api.v1.endpoints.auth import get_current_user
    from fastapi import status

    # This endpoint requires auth — placeholder until VA account linking is complete
    # For now, return a helpful message
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="VA account linking required. This endpoint will be available after Phase 4 (account linking) is deployed."
    )


@router.get("/test-cases")
async def get_test_cases():
>>>>>>> REPLACE

## Verification

1. Backend starts without import errors
2. `GET /api/v1/calculator/va-ratings` returns 501 with helpful message (until account linking is ready)
3. VA OAuth scope list includes `disability_rating.read`
4. New service file exists at `app/services/va_disability_rating_service.py`

## Dependencies

- Phase A (localStorage) should be deployed first — task VETASSIST-CALC-PERSIST-002
- VA Account Linking (from the linking plan) must be complete before this endpoint is functional
- The `disability_rating.read` scope must be added to our VA Developer Portal sandbox app

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `app/services/va_oauth_service.py` | MODIFY | Add `disability_rating.read` to scopes |
| `app/services/va_disability_rating_service.py` | CREATE | New service to fetch/transform rated disabilities |
| `app/api/v1/endpoints/calculator.py` | MODIFY | Add import + `GET /calculator/va-ratings` endpoint |
