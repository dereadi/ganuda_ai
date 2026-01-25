# Jr Instruction: VetAssist Claim Status Tracker
## Task ID: VetAssist Sprint 4 - Task 4
## Priority: P2
## Estimated Complexity: Medium-High

---

## Objective

Create a claim status tracking feature that uses the VA Benefits Claims API to show veterans their real claim status. Requires VA OAuth authentication (completed in Sprint 4 Task 2-3).

---

## Background

With VA OAuth now implemented, veterans can authenticate with VA.gov and we can access the Benefits Claims API on their behalf. This task adds:
1. Backend endpoint to fetch claim status from VA
2. Frontend claim status component on dashboard
3. Automatic status refresh

---

## Prerequisites

- VA OAuth backend endpoints working (`/api/v1/auth/va/*`)
- VA OAuth frontend pages working (`/va-success`, `/va-error`)
- `vetassist_va_tokens` table has valid tokens after login

---

## Implementation Steps

### Step 1: Create VA Claims Service

Create `/ganuda/vetassist/backend/app/services/va_claims_service.py`:

```python
"""
VA Claims Service
Fetches claim status from VA Benefits Claims API
Cherokee AI Federation - For Seven Generations
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

VA_CLAIMS_API_BASE = "https://sandbox-api.va.gov/services/claims/v2"


class VAClaimsService:
    """Service for interacting with VA Benefits Claims API"""

    async def get_claims(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get all claims for the authenticated veteran.

        Args:
            access_token: VA OAuth access token

        Returns:
            List of claim objects
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VA_CLAIMS_API_BASE}/veterans/claims",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code != 200:
                logger.error(f"VA Claims API error: {response.status_code}")
                raise VAClaimsError(f"Failed to fetch claims: {response.status_code}")

            data = response.json()
            return data.get("data", [])

    async def get_claim_detail(self, access_token: str, claim_id: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific claim.

        Args:
            access_token: VA OAuth access token
            claim_id: The claim ID

        Returns:
            Claim detail object
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{VA_CLAIMS_API_BASE}/veterans/claims/{claim_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )

            if response.status_code != 200:
                logger.error(f"VA Claim detail error: {response.status_code}")
                raise VAClaimsError(f"Failed to fetch claim detail: {response.status_code}")

            data = response.json()
            return data.get("data", {})

    def format_claim_for_display(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a VA claim object for frontend display.

        Args:
            claim: Raw claim from VA API

        Returns:
            Formatted claim object
        """
        attributes = claim.get("attributes", {})

        # Map VA status to user-friendly status
        status_map = {
            "PENDING": {"label": "Pending Review", "color": "yellow"},
            "INITIAL_REVIEW": {"label": "Initial Review", "color": "blue"},
            "EVIDENCE_GATHERING": {"label": "Gathering Evidence", "color": "blue"},
            "RATING_DECISION": {"label": "Rating Decision", "color": "purple"},
            "COMPLETE": {"label": "Complete", "color": "green"},
            "ERRORED": {"label": "Error", "color": "red"},
        }

        va_status = attributes.get("status", "UNKNOWN")
        status_info = status_map.get(va_status, {"label": va_status, "color": "gray"})

        return {
            "id": claim.get("id"),
            "type": attributes.get("claimType", "Unknown"),
            "status": status_info["label"],
            "status_color": status_info["color"],
            "date_filed": attributes.get("claimDate"),
            "contention_list": attributes.get("contentionList", []),
            "development_letter_sent": attributes.get("developmentLetterSent"),
            "decision_letter_sent": attributes.get("decisionLetterSent"),
            "phase_dates": attributes.get("phaseDates", {}),
            "estimated_completion": attributes.get("maxEstClaimDate"),
            "last_updated": datetime.now().isoformat()
        }


class VAClaimsError(Exception):
    """Exception for VA Claims API errors"""
    pass


# Singleton instance
va_claims_service = VAClaimsService()
```

### Step 2: Create Claims Status Endpoint

Create `/ganuda/vetassist/backend/app/api/v1/endpoints/claims.py`:

```python
"""
Claims Status Endpoints
Cherokee AI Federation - For Seven Generations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from app.services.va_claims_service import va_claims_service, VAClaimsError
from app.services.va_oauth_service import va_oauth_service, VAOAuthError
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_va_token_from_session(session_id: str, db) -> Optional[str]:
    """Get VA access token from database for a session"""
    # Query the vetassist_va_tokens table
    result = db.execute("""
        SELECT access_token, expires_at, refresh_token
        FROM vetassist_va_tokens
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (session_id,))
    row = result.fetchone()

    if not row:
        return None

    access_token, expires_at, refresh_token = row

    # TODO: Check if token expired and refresh if needed

    return access_token


@router.get("/status")
async def get_claim_status(
    session_id: str,
    db=Depends(get_db)
):
    """
    Get all claims for the authenticated veteran.

    Requires valid VA OAuth session.
    """
    # Get token from database
    access_token = await get_va_token_from_session(session_id, db)

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="VA authentication required. Please login with VA.gov first."
        )

    try:
        # Fetch claims from VA API
        claims = await va_claims_service.get_claims(access_token)

        # Format for display
        formatted_claims = [
            va_claims_service.format_claim_for_display(claim)
            for claim in claims
        ]

        return {
            "success": True,
            "claims": formatted_claims,
            "count": len(formatted_claims)
        }

    except VAClaimsError as e:
        logger.error(f"VA Claims API error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch claim status")


@router.get("/status/{claim_id}")
async def get_claim_detail(
    claim_id: str,
    session_id: str,
    db=Depends(get_db)
):
    """
    Get detailed status for a specific claim.

    Requires valid VA OAuth session.
    """
    access_token = await get_va_token_from_session(session_id, db)

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="VA authentication required"
        )

    try:
        claim = await va_claims_service.get_claim_detail(access_token, claim_id)
        formatted = va_claims_service.format_claim_for_display(claim)

        return {
            "success": True,
            "claim": formatted
        }

    except VAClaimsError as e:
        raise HTTPException(status_code=502, detail=str(e))
```

### Step 3: Register Claims Router

Add to `/ganuda/vetassist/backend/app/api/v1/__init__.py`:

```python
from app.api.v1.endpoints import claims

api_router.include_router(
    claims.router,
    prefix="/claims",
    tags=["claims"]
)
```

### Step 4: Create Frontend Claim Status Component

Create `/ganuda/vetassist/frontend/components/ClaimStatusCard.tsx`:

```tsx
'use client';

/**
 * Claim Status Card Component
 * Displays VA claim status with visual progress
 */

interface Claim {
  id: string;
  type: string;
  status: string;
  status_color: string;
  date_filed: string;
  contention_list: string[];
  estimated_completion: string | null;
}

interface ClaimStatusCardProps {
  claim: Claim;
  onClick?: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  blue: 'bg-blue-100 text-blue-800 border-blue-300',
  purple: 'bg-purple-100 text-purple-800 border-purple-300',
  green: 'bg-green-100 text-green-800 border-green-300',
  red: 'bg-red-100 text-red-800 border-red-300',
  gray: 'bg-gray-100 text-gray-800 border-gray-300',
};

export default function ClaimStatusCard({ claim, onClick }: ClaimStatusCardProps) {
  const colorClasses = STATUS_COLORS[claim.status_color] || STATUS_COLORS.gray;

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 border hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {claim.type}
          </h3>
          <p className="text-sm text-gray-500">
            Filed: {new Date(claim.date_filed).toLocaleDateString()}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${colorClasses}`}>
          {claim.status}
        </span>
      </div>

      {claim.contention_list.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Claimed Conditions:</p>
          <div className="flex flex-wrap gap-2">
            {claim.contention_list.slice(0, 3).map((condition, idx) => (
              <span
                key={idx}
                className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
              >
                {condition}
              </span>
            ))}
            {claim.contention_list.length > 3 && (
              <span className="text-gray-500 text-xs">
                +{claim.contention_list.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {claim.estimated_completion && (
        <div className="text-sm text-gray-500">
          Est. completion: {new Date(claim.estimated_completion).toLocaleDateString()}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
        <span className="text-xs text-gray-400">
          ID: {claim.id.slice(0, 8)}...
        </span>
        <span className="text-indigo-600 text-sm font-medium">
          View Details →
        </span>
      </div>
    </div>
  );
}
```

### Step 5: Add Claims Section to Dashboard

Edit `/ganuda/vetassist/frontend/app/dashboard/page.tsx` to add claims section.

Add the claims section after existing dashboard content:

```tsx
{/* VA Claims Status Section */}
{vaAuthenticated && (
  <section className="mt-8">
    <div className="flex justify-between items-center mb-4">
      <h2 className="text-xl font-bold text-gray-900">
        Your VA Claims
      </h2>
      <button
        onClick={refreshClaims}
        className="text-sm text-indigo-600 hover:text-indigo-800"
      >
        Refresh Status
      </button>
    </div>

    {claimsLoading ? (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    ) : claims.length > 0 ? (
      <div className="grid gap-4 md:grid-cols-2">
        {claims.map((claim) => (
          <ClaimStatusCard
            key={claim.id}
            claim={claim}
            onClick={() => router.push(`/claims/${claim.id}`)}
          />
        ))}
      </div>
    ) : (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-600">No claims found in your VA account.</p>
        <Link
          href="/wizard"
          className="mt-4 inline-block text-indigo-600 font-medium"
        >
          Start a new claim →
        </Link>
      </div>
    )}
  </section>
)}

{!vaAuthenticated && (
  <section className="mt-8 bg-blue-50 rounded-lg p-6">
    <h2 className="text-lg font-semibold text-blue-900 mb-2">
      Track Your VA Claims
    </h2>
    <p className="text-blue-800 mb-4">
      Connect your VA.gov account to see your real claim status here.
    </p>
    <a
      href="/api/v1/auth/va/login"
      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
    >
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
      </svg>
      Connect VA.gov Account
    </a>
  </section>
)}
```

---

## Verification (Required before marking complete)

```bash
# 1. Check claims service exists
ls -la /ganuda/vetassist/backend/app/services/va_claims_service.py

# 2. Check claims endpoint exists
ls -la /ganuda/vetassist/backend/app/api/v1/endpoints/claims.py

# 3. Check router registered
grep -n "claims" /ganuda/vetassist/backend/app/api/v1/__init__.py

# 4. Build frontend
cd /ganuda/vetassist/frontend && npm run build

# 5. Test claims endpoint (should return 401 without auth)
curl -s http://localhost:8001/api/v1/claims/status?session_id=test
```

---

## Acceptance Criteria

1. [ ] `va_claims_service.py` created with get_claims and get_claim_detail
2. [ ] `/api/v1/claims/status` endpoint returns claims for authenticated veterans
3. [ ] `/api/v1/claims/status/{claim_id}` endpoint returns claim details
4. [ ] ClaimStatusCard component created
5. [ ] Dashboard shows claims section for VA-authenticated users
6. [ ] Dashboard shows "Connect VA.gov" prompt for non-authenticated users
7. [ ] Frontend builds without errors

---

## Notes

- Sandbox API has test claims data for sandbox test accounts
- Production will require separate API credentials
- Consider caching claims for 5 minutes to reduce API calls

---

*Cherokee AI Federation - For Seven Generations*
