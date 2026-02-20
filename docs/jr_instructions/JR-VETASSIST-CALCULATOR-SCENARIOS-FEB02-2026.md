# Jr Instruction: Calculator Saved Scenarios (Phase B)

**Task ID:** VETASSIST-CALC-SCENARIOS-001
**Assigned:** Software Engineer Jr.
**Priority:** P2
**Created:** 2026-02-02
**TPM:** Claude Opus 4.5
**Depends on:** None (works independently of VA linking)

---

## Context

The VA Disability Calculator (`/calculator`) lets veterans enter conditions and calculate their combined disability rating. Phase A (localStorage persistence) is deployed — the form auto-saves to the browser so users don't lose work on page refresh.

Phase B adds **server-side saved scenarios**: veterans can name and save multiple "what if" calculations to their account. Example: "Current Rating", "If PTSD Approved", "If Back Claim Increase". This is the foundation for the scratchpad workflow where veterans explore how different claims would affect their compensation.

### Existing Patterns to Follow

The dashboard scratchpad (`/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`) uses this exact pattern:
- `psycopg2` with `RealDictCursor` (NOT SQLAlchemy)
- `get_db_connection()` from `app.core.database_config`
- Auth via `get_current_user` from `app.core.security`
- UPSERT pattern for saves

Follow this pattern for scenarios.

### Files to Read First

1. `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py` — current calculator endpoints
2. `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py` — scratchpad CRUD pattern (lines 194-230)
3. `/ganuda/vetassist/backend/app/core/database_config.py` — `get_db_connection()`
4. `/ganuda/vetassist/backend/app/core/security.py` — `get_current_user`

---

## Step 1: Create the Database Table

Run this SQL on bluefin (192.168.132.222) against `zammad_production`:

```sql
CREATE TABLE IF NOT EXISTS vetassist_calculator_scenarios (
    id SERIAL PRIMARY KEY,
    veteran_id VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL DEFAULT '[]',
    dependents JSONB NOT NULL DEFAULT '{}',
    aid_attendance BOOLEAN NOT NULL DEFAULT FALSE,
    housebound BOOLEAN NOT NULL DEFAULT FALSE,
    -- Cached calculation results (computed on save)
    combined_rating INTEGER,
    rounded_rating INTEGER,
    monthly_compensation DECIMAL(10,2),
    is_baseline BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calc_scenarios_veteran
    ON vetassist_calculator_scenarios(veteran_id);

CREATE INDEX IF NOT EXISTS idx_calc_scenarios_veteran_baseline
    ON vetassist_calculator_scenarios(veteran_id, is_baseline)
    WHERE is_baseline = TRUE;

COMMENT ON TABLE vetassist_calculator_scenarios IS 'Saved calculator scenarios for what-if analysis. Phase B of calculator persistence.';
COMMENT ON COLUMN vetassist_calculator_scenarios.is_baseline IS 'TRUE if this represents current actual rating (from VA data or manual entry). At most one baseline per veteran.';
COMMENT ON COLUMN vetassist_calculator_scenarios.conditions IS 'JSONB array matching CalculatorRequest.conditions schema: [{name, rating, is_bilateral, bilateral_side, diagnostic_code}]';
COMMENT ON COLUMN vetassist_calculator_scenarios.dependents IS 'JSONB matching CalculatorRequest.dependents schema: {has_spouse, num_children_under_18, ...}';
```

**Verify:** `\dt vetassist_calculator_scenarios` shows the table. `\d vetassist_calculator_scenarios` shows all columns.

---

## Step 2: Add Scenario CRUD Endpoints to calculator.py

Modify: `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

Add these imports near the top (after the existing imports):

```python
from psycopg2.extras import RealDictCursor
from app.core.database_config import get_db_connection
from app.core.security import get_current_user
import json
```

Add a Pydantic model for scenario requests after the existing `CalculatorRequest` model:

```python
class ScenarioSave(BaseModel):
    """Request to save a calculator scenario"""
    name: str = Field(..., min_length=1, max_length=100, description="Scenario name")
    description: Optional[str] = Field(None, max_length=500, description="Optional notes")
    conditions: List[Condition] = Field(..., min_items=1)
    dependents: Optional[Dependents] = None
    aid_attendance: bool = False
    housebound: bool = False
    is_baseline: bool = Field(default=False, description="Mark as current actual rating")
    # Cached results (computed by backend on save)
    combined_rating: Optional[int] = None
    rounded_rating: Optional[int] = None
    monthly_compensation: Optional[float] = None


class ScenarioResponse(BaseModel):
    """Saved scenario with cached results"""
    id: int
    name: str
    description: Optional[str]
    conditions: List[Dict]
    dependents: Optional[Dict]
    aid_attendance: bool
    housebound: bool
    combined_rating: Optional[int]
    rounded_rating: Optional[int]
    monthly_compensation: Optional[float]
    is_baseline: bool
    created_at: str
    updated_at: str
```

Add these 5 endpoints AFTER the existing endpoints (before the ML prediction section):

```python
# =============================================================================
# Saved Scenarios (Phase B)
# =============================================================================

@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
async def save_scenario(
    data: ScenarioSave,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a calculator scenario for the authenticated user.
    Automatically computes and caches the calculation result.
    Limit: 20 scenarios per user.
    """
    veteran_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Enforce 20-scenario limit
            cur.execute(
                "SELECT COUNT(*) as cnt FROM vetassist_calculator_scenarios WHERE veteran_id = %s",
                (veteran_id,)
            )
            if cur.fetchone()["cnt"] >= 20:
                raise HTTPException(status_code=400, detail="Maximum 20 saved scenarios. Delete one to save a new one.")

            # If marking as baseline, clear any existing baseline
            if data.is_baseline:
                cur.execute(
                    "UPDATE vetassist_calculator_scenarios SET is_baseline = FALSE WHERE veteran_id = %s AND is_baseline = TRUE",
                    (veteran_id,)
                )

            # Compute calculation result
            calc_result = None
            try:
                calculator = VACalculatorService(db)
                calc_result = calculator.calculate(
                    conditions=data.conditions,
                    dependents=data.dependents,
                    aid_attendance=data.aid_attendance,
                    housebound=data.housebound
                )
            except Exception:
                pass  # Save scenario even if calculation fails

            conditions_json = json.dumps([c.dict() for c in data.conditions])
            dependents_json = json.dumps(data.dependents.dict() if data.dependents else {})

            cur.execute("""
                INSERT INTO vetassist_calculator_scenarios
                    (veteran_id, name, description, conditions, dependents,
                     aid_attendance, housebound, is_baseline,
                     combined_rating, rounded_rating, monthly_compensation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                veteran_id,
                data.name,
                data.description,
                conditions_json,
                dependents_json,
                data.aid_attendance,
                data.housebound,
                data.is_baseline,
                calc_result["combined_rating"] if calc_result else data.combined_rating,
                calc_result["rounded_rating"] if calc_result else data.rounded_rating,
                calc_result["monthly_compensation"] if calc_result else data.monthly_compensation,
            ))
            row = cur.fetchone()
            conn.commit()

        return _row_to_response(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save scenario: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.get("/scenarios")
async def list_scenarios(current_user: dict = Depends(get_current_user)):
    """List all saved scenarios for the authenticated user."""
    veteran_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM vetassist_calculator_scenarios
                WHERE veteran_id = %s
                ORDER BY is_baseline DESC, updated_at DESC
            """, (veteran_id,))
            rows = cur.fetchall() or []

        return {
            "scenarios": [_row_to_response(r) for r in rows],
            "total": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific saved scenario."""
    veteran_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM vetassist_calculator_scenarios
                WHERE id = %s AND veteran_id = %s
            """, (scenario_id, veteran_id))
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found")

        return _row_to_response(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scenario: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    data: ScenarioSave,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a saved scenario. Re-computes calculation result."""
    veteran_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify ownership
            cur.execute(
                "SELECT id FROM vetassist_calculator_scenarios WHERE id = %s AND veteran_id = %s",
                (scenario_id, veteran_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Scenario not found")

            # If marking as baseline, clear any other baseline
            if data.is_baseline:
                cur.execute(
                    "UPDATE vetassist_calculator_scenarios SET is_baseline = FALSE WHERE veteran_id = %s AND is_baseline = TRUE AND id != %s",
                    (veteran_id, scenario_id)
                )

            # Re-compute calculation
            calc_result = None
            try:
                calculator = VACalculatorService(db)
                calc_result = calculator.calculate(
                    conditions=data.conditions,
                    dependents=data.dependents,
                    aid_attendance=data.aid_attendance,
                    housebound=data.housebound
                )
            except Exception:
                pass

            conditions_json = json.dumps([c.dict() for c in data.conditions])
            dependents_json = json.dumps(data.dependents.dict() if data.dependents else {})

            cur.execute("""
                UPDATE vetassist_calculator_scenarios SET
                    name = %s, description = %s, conditions = %s, dependents = %s,
                    aid_attendance = %s, housebound = %s, is_baseline = %s,
                    combined_rating = %s, rounded_rating = %s, monthly_compensation = %s,
                    updated_at = NOW()
                WHERE id = %s AND veteran_id = %s
                RETURNING *
            """, (
                data.name, data.description, conditions_json, dependents_json,
                data.aid_attendance, data.housebound, data.is_baseline,
                calc_result["combined_rating"] if calc_result else data.combined_rating,
                calc_result["rounded_rating"] if calc_result else data.rounded_rating,
                calc_result["monthly_compensation"] if calc_result else data.monthly_compensation,
                scenario_id, veteran_id
            ))
            row = cur.fetchone()
            conn.commit()

        return _row_to_response(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scenario: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a saved scenario."""
    veteran_id = str(current_user.id) if hasattr(current_user, 'id') else str(current_user)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "DELETE FROM vetassist_calculator_scenarios WHERE id = %s AND veteran_id = %s RETURNING id",
                (scenario_id, veteran_id)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Scenario not found")
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scenario: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


def _row_to_response(row: dict) -> dict:
    """Convert a database row to ScenarioResponse format."""
    conditions = row["conditions"]
    if isinstance(conditions, str):
        conditions = json.loads(conditions)
    dependents = row["dependents"]
    if isinstance(dependents, str):
        dependents = json.loads(dependents)
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row.get("description"),
        "conditions": conditions,
        "dependents": dependents,
        "aid_attendance": row["aid_attendance"],
        "housebound": row["housebound"],
        "combined_rating": row.get("combined_rating"),
        "rounded_rating": row.get("rounded_rating"),
        "monthly_compensation": float(row["monthly_compensation"]) if row.get("monthly_compensation") else None,
        "is_baseline": row["is_baseline"],
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }
```

---

## Step 3: Verify

After implementing, verify all endpoints work:

```bash
# Test save (requires auth token)
curl -X POST https://vetassist.ganuda.us/api/v1/calculator/scenarios \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Current Rating","conditions":[{"name":"Tinnitus","rating":10}],"is_baseline":true}'

# Test list
curl -X GET https://vetassist.ganuda.us/api/v1/calculator/scenarios \
  -H "Authorization: Bearer <token>"

# Test get by ID
curl -X GET https://vetassist.ganuda.us/api/v1/calculator/scenarios/1 \
  -H "Authorization: Bearer <token>"

# Test delete
curl -X DELETE https://vetassist.ganuda.us/api/v1/calculator/scenarios/1 \
  -H "Authorization: Bearer <token>"
```

---

## Acceptance Criteria

1. `vetassist_calculator_scenarios` table exists with all columns and indexes
2. POST /calculator/scenarios saves a scenario with auto-computed results
3. GET /calculator/scenarios returns all scenarios for the authenticated user, baseline first
4. GET /calculator/scenarios/{id} returns a single scenario with ownership check
5. PUT /calculator/scenarios/{id} updates and re-computes results
6. DELETE /calculator/scenarios/{id} removes with ownership check
7. 20-scenario limit enforced
8. Baseline uniqueness enforced (at most one per veteran)
9. Auth required on all scenario endpoints

---

## Frontend Note

Frontend work (Save Scenario button, scenarios list panel) will be deployed by the TPM separately since frontend files are outside the RLM override scope.

---

*For Seven Generations*
*Cherokee AI Federation — VetAssist Calculator Team*
