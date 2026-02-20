# Jr Instruction: VetAssist API Routing Fix

**Task ID:** VETASSIST-API-ROUTING-FIX-001
**Priority:** P0
**Assigned To:** Software Engineer Jr.
**Kanban:** #1730
**Date:** February 9, 2026

## Background

Regression testing shows several VetAssist API endpoints returning unexpected errors. Investigation reveals:
- 2 endpoints missing root handlers (health, conditions)
- 1 endpoint with route collision causing 500 (content/{content_id} catches "educational" as UUID)
- 6 routers mounted twice in main.py (duplicate registration)
- 1 forms endpoint working correctly (403 = auth required, not a bug)
- 1 test was wrong (calculator/combined-rating never existed)

Backend runs on port 8001 via uvicorn. Frontend proxies /api/v1/* from port 3000.

## Edit 1: Add root health endpoint

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/health.py`

<<<<<<< SEARCH
router = APIRouter()


@router.get("/db")
=======
router = APIRouter()


@router.get("")
async def health_root(db: Session = Depends(get_db)):
    """Root health check — aggregates all subsystems"""
    checks = {}
    try:
        db.execute(text("SELECT 1")).scalar()
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/db")
>>>>>>> REPLACE

## Edit 2: Add root conditions list endpoint

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py`

<<<<<<< SEARCH
@router.post("/map", response_model=List[ConditionMatch])
=======
@router.get("")
def list_conditions():
    """List available body systems and condition count"""
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT body_system, COUNT(*) as condition_count
                FROM vetassist_cfr_conditions
                GROUP BY body_system
                ORDER BY body_system
            """)
            systems = cur.fetchall()
            return {
                "total_systems": len(systems),
                "body_systems": [dict(s) for s in systems]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/map", response_model=List[ConditionMatch])
>>>>>>> REPLACE

## Edit 3: Add UUID validation to content endpoint to prevent 500 on non-UUID paths

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/content.py`

<<<<<<< SEARCH
@router.get("/{content_id}")
async def get_content(
    content_id: str,
    db: Session = Depends(get_db),
    increment_views: bool = Query(True, description="Increment view count")
):
    """
    Get a single educational content item by ID

    **Path Parameters:**
    - content_id: UUID of the content item

    **Query Parameters:**
    - increment_views: Whether to increment view counter (default: true)

    **Returns:** Full content item details
    """
=======
@router.get("/{content_id}")
async def get_content(
    content_id: str,
    db: Session = Depends(get_db),
    increment_views: bool = Query(True, description="Increment view count")
):
    """
    Get a single educational content item by ID

    **Path Parameters:**
    - content_id: UUID of the content item

    **Query Parameters:**
    - increment_views: Whether to increment view counter (default: true)

    **Returns:** Full content item details
    """
    import uuid as _uuid
    try:
        _uuid.UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Content '{content_id}' not found. Use GET /api/v1/content for listing or ?content_type= for filtering.")
>>>>>>> REPLACE

## Edit 4: Remove duplicate router registrations in main.py

File: `/ganuda/vetassist/backend/app/main.py`

<<<<<<< SEARCH
# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(workbench.router, prefix="/api/v1/workbench", tags=["workbench"])
app.include_router(wizard.router, prefix="/api/v1/wizard", tags=["wizard"])
app.include_router(readiness.router, prefix="/api/v1/readiness", tags=["readiness"])
app.include_router(family.router, prefix="/api/v1/family", tags=["family"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
app.include_router(forms.router, prefix="/api/v1/forms", tags=["forms"])
=======
# Include API routes (all routers registered via api_router in __init__.py)
app.include_router(api_router, prefix="/api/v1")
>>>>>>> REPLACE

## Do NOT

- Do not modify auth logic or security on any endpoint
- Do not change the forms/available endpoint — 403 is correct (requires auth)
- Do not create a /calculator/combined-rating endpoint — the existing POST /calculate is correct
- Do not modify the frontend
- Do not change database schemas
- Do not remove any existing endpoints

## Success Criteria

1. `GET /api/v1/health` returns 200 with status and checks
2. `GET /api/v1/health/db` still returns 200 (existing, unchanged)
3. `GET /api/v1/health/system` still returns 200 (existing, unchanged)
4. `GET /api/v1/conditions` returns 200 with body systems list
5. `GET /api/v1/conditions/body-systems` still returns 200 (existing, unchanged)
6. `GET /api/v1/content/educational` returns 404 with helpful message (not 500)
7. `GET /api/v1/content` still returns 200 with content list (existing, unchanged)
8. `GET /api/v1/forms/available` still returns 403 without auth token (existing, unchanged)
9. No duplicate routes in OpenAPI schema (`/docs`)
10. Python syntax valid after all edits

## Manual Steps After Jr Completes

Restart the backend to pick up changes:

    sudo systemctl restart vetassist-backend.service

Then verify:

    curl -s http://localhost:8001/api/v1/health | python3 -m json.tool
    curl -s http://localhost:8001/api/v1/conditions | python3 -m json.tool
    curl -s http://localhost:8001/api/v1/content/educational
