# JR-VETASSIST-CALCULATOR-API-JAN30-2026
## Build VA Disability Rating Calculator API

**Priority:** P0 - High Value (standalone, no auth dependency for MVP)
**Target Node:** bluefin (192.168.132.222)
**File to Create:** `/ganuda/vetassist/backend/app/api/calculator_routes.py`
**Wire into:** `/ganuda/vetassist/backend/main.py`

### Context

The VA Combined Ratings Calculator uses the formula from 38 CFR 4.25. This is a pure computation endpoint — no database needed. The frontend sends conditions with ratings and gets back the combined rating, compensation amounts, and step-by-step calculation.

### The 38 CFR 4.25 Combined Ratings Formula

Veterans' disability ratings are NOT simply added. They use a "whole person" method:

1. Sort ratings from highest to lowest
2. Start with the highest rating as a percentage of the "whole person" (100%)
3. Apply each subsequent rating to the REMAINING ability
4. Round to nearest 10%

**Example:** 50% + 30% + 20%
- Start: 100% whole person
- After 50%: remaining = 50%, combined = 50%
- After 30%: 30% of 50% = 15%, combined = 65%, remaining = 35%
- After 20%: 20% of 35% = 7%, combined = 72%, remaining = 28%
- Round 72% to nearest 10% = **70%**

### Bilateral Factor (38 CFR 4.26)

When a veteran has paired extremities affected (both arms, both legs, etc.):
1. Add the bilateral conditions using the combined formula
2. Add 10% of the bilateral combined value
3. Use this adjusted value in the overall combination

### Endpoint

#### POST /api/v1/calculator/calculate

**Request (matches frontend `CalculatorRequest`):**
```json
{
  "conditions": [
    {
      "name": "PTSD",
      "rating": 50,
      "is_bilateral": false,
      "bilateral_side": null,
      "diagnostic_code": "9411"
    },
    {
      "name": "Left Knee Strain",
      "rating": 30,
      "is_bilateral": true,
      "bilateral_side": "left"
    },
    {
      "name": "Right Knee Strain",
      "rating": 20,
      "is_bilateral": true,
      "bilateral_side": "right"
    }
  ],
  "dependents": {
    "has_spouse": true,
    "num_children_under_18": 2,
    "num_children_over_18_in_school": 0,
    "num_dependent_parents": 0,
    "spouse_aid_attendance": false
  },
  "aid_attendance": false,
  "housebound": false
}
```

**Response (matches frontend `CalculationResult`):**
```json
{
  "combined_rating": 72,
  "rounded_rating": 70,
  "monthly_compensation": 1716.28,
  "annual_compensation": 20595.36,
  "bilateral_factor_applied": true,
  "bilateral_factor_value": 4.4,
  "calculation_steps": [
    {
      "step_number": 1,
      "description": "Bilateral factor: Left Knee (30%) + Right Knee (20%)",
      "calculation": "Combined bilateral: 44% + 10% bilateral factor = 48.4%",
      "result": 48.4
    },
    {
      "step_number": 2,
      "description": "Combine PTSD (50%) with bilateral group (48.4%)",
      "calculation": "50% + (48.4% × 50% remaining) = 74.2%",
      "result": 74.2
    },
    {
      "step_number": 3,
      "description": "Round to nearest 10%",
      "calculation": "74.2% rounds to 70%",
      "result": 70
    }
  ],
  "conditions_summary": [
    {"name": "PTSD", "rating": 50, "is_bilateral": false, "bilateral_side": null},
    {"name": "Left Knee Strain", "rating": 30, "is_bilateral": true, "bilateral_side": "left"},
    {"name": "Right Knee Strain", "rating": 20, "is_bilateral": true, "bilateral_side": "right"}
  ],
  "dependents_summary": {
    "spouse": true,
    "children_under_18": 2,
    "children_over_18_in_school": 0,
    "dependent_parents": 0,
    "spouse_aid_attendance": false
  },
  "timestamp": "2026-01-30T12:00:00Z"
}
```

### 2026 VA Compensation Rates

Use this lookup table for monthly compensation. Store as a Python dict.

**Base rates (veteran alone, no dependents):**
| Rating | Monthly |
|--------|---------|
| 10% | $171.23 |
| 20% | $338.49 |
| 30% | $524.31 |
| 40% | $755.28 |
| 50% | $1,075.16 |
| 60% | $1,361.88 |
| 70% | $1,716.28 |
| 80% | $1,995.01 |
| 90% | $2,241.91 |
| 100% | $3,737.85 |

**Dependent additions (added to base for 30%+ ratings):**
See https://www.va.gov/disability/compensation-rates/veteran-rates/ for full table.

For MVP, use base rates only and add a note that dependent adjustments are approximate. The full 2026 rate tables with all dependent combinations can be added in a follow-up.

### Implementation Notes

- This endpoint requires NO database access — pure computation
- No authentication required for MVP (calculator is a public tool)
- Validate ratings are in {0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100}
- Bilateral factor only applies to paired extremities (left/right pairs)
- Return `timestamp` as ISO 8601 UTC string

### Wire into main.py

```python
from app.api.calculator_routes import router as calculator_router
app.include_router(calculator_router)
```

### Verification

```bash
# Simple: single condition
curl -X POST http://192.168.132.222:8001/api/v1/calculator/calculate \
  -H "Content-Type: application/json" \
  -d '{"conditions":[{"name":"PTSD","rating":70,"is_bilateral":false}]}'

# Complex: bilateral + dependents
curl -X POST http://192.168.132.222:8001/api/v1/calculator/calculate \
  -H "Content-Type: application/json" \
  -d '{"conditions":[{"name":"PTSD","rating":50,"is_bilateral":false},{"name":"Left Knee","rating":30,"is_bilateral":true,"bilateral_side":"left"},{"name":"Right Knee","rating":20,"is_bilateral":true,"bilateral_side":"right"}],"dependents":{"has_spouse":true,"num_children_under_18":2,"num_children_over_18_in_school":0,"num_dependent_parents":0,"spouse_aid_attendance":false}}'
```

### Test Cases

1. **Single 70%** → combined 70%, rounded 70%
2. **50% + 30%** → 65%, rounded 70%
3. **50% + 30% + 20%** → 72%, rounded 70%
4. **Bilateral 30% left + 20% right** → combined 44%, bilateral factor +4.4% = 48.4%
5. **100%** → $3,737.85/month
6. **Empty conditions** → 0% rating, $0 compensation
