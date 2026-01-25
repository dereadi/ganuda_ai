# Jr Instructions: VetAssist Combined Rating Calculator

**Task ID**: VETASSIST-CALC-001
**Priority**: HIGH
**Target**: redfin (API endpoint) + Web UI
**Requires**: No PII, no goldfin - can build now
**Council Approval**: Part of VetAssist Phase 1 MVP (APPROVED 5-0-2)

---

## Executive Summary

Build a VA Combined Disability Rating Calculator that implements the exact formula from 38 CFR 4.25. This is the first VetAssist feature to ship - no PII required, pure math.

**Why This First**:
- Zero PII concerns (just numbers)
- Validates our understanding of VA rules
- High value to veterans (most don't understand the math)
- Can ship before goldfin exists

---

## The VA Combined Rating Formula

### Core Formula (38 CFR 4.25)

VA ratings are NOT additive. They use the "whole person" theory:

```
Combined = 100 - [(100 - Rating1) × (100 - Rating2) / 100]
```

Or equivalently:
```
efficiency_remaining = 100
for each rating (sorted highest to lowest):
    efficiency_remaining = efficiency_remaining × (100 - rating) / 100
combined = 100 - efficiency_remaining
```

### Step-by-Step Example

Veteran has three ratings: 50%, 30%, 20%

1. Start with 100% efficiency (whole person)
2. Apply 50%: `100 × 0.50 = 50` lost → 50% remaining
3. Apply 30%: `50 × 0.30 = 15` lost → 35% remaining
4. Apply 20%: `35 × 0.20 = 7` lost → 28% remaining
5. Combined = `100 - 28 = 72%`
6. Round to nearest 10% = **70%**

**Key Insight**: 50% + 30% + 20% = 100% (simple math), but VA combined = 70%

### Rounding Rules

- Combined ratings round to nearest 10%
- 0.5 rounds UP (e.g., 75% → 80%)
- Exact formula for rounding: `Math.round(combined / 10) * 10`

### Bilateral Factor

When a veteran has the same condition affecting both sides (left and right limbs), they get a 10% boost on those paired ratings:

1. Calculate the combined rating for the bilateral conditions
2. Add 10% of that combined value
3. Then combine with remaining ratings

**Example**: 30% left knee + 20% right knee
1. Combine bilateral: `100 - [(100-30) × (100-20) / 100] = 44%`
2. Apply bilateral factor: `44 × 1.10 = 48.4%` (round to 48%)
3. Combine with other ratings normally

---

## API Specification

### Endpoint

```
POST /v1/vetassist/rating-calculator
```

### Request Schema

```json
{
  "ratings": [
    {
      "condition": "Knee strain",
      "percentage": 30,
      "side": "left",
      "diagnostic_code": "5260"
    },
    {
      "condition": "Knee strain",
      "percentage": 20,
      "side": "right",
      "diagnostic_code": "5260"
    },
    {
      "condition": "PTSD",
      "percentage": 50,
      "side": null,
      "diagnostic_code": "9411"
    }
  ],
  "show_steps": true,
  "include_compensation": true,
  "dependents": {
    "spouse": true,
    "children": 2,
    "parents": 0
  }
}
```

### Response Schema

```json
{
  "combined_rating": 70,
  "combined_exact": 72.4,
  "bilateral_conditions": [
    {
      "conditions": ["Knee strain (left)", "Knee strain (right)"],
      "combined": 44,
      "with_bilateral_factor": 48
    }
  ],
  "calculation_steps": [
    {
      "step": 1,
      "description": "Start with 100% efficiency",
      "efficiency_remaining": 100
    },
    {
      "step": 2,
      "description": "Apply PTSD (50%)",
      "rating": 50,
      "efficiency_lost": 50,
      "efficiency_remaining": 50
    },
    {
      "step": 3,
      "description": "Apply bilateral knee conditions (48% after factor)",
      "rating": 48,
      "efficiency_lost": 24,
      "efficiency_remaining": 26
    },
    {
      "step": 4,
      "description": "Final calculation",
      "exact_combined": 74,
      "rounded_combined": 70
    }
  ],
  "compensation": {
    "year": 2025,
    "monthly_amount": 1716.28,
    "spouse_included": true,
    "children_included": 2,
    "effective_date_note": "Rates effective December 1, 2024"
  },
  "explanation": "Your 3 conditions combine to a 70% VA disability rating. This is lower than simply adding them (100%) because VA uses the 'whole person' theory - each condition affects your remaining efficiency, not your whole body.",
  "audit_hash": "abc123"
}
```

---

## Implementation

### Core Calculator Function

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib

# Valid VA rating percentages (VA only issues these values)
VALID_VA_RATINGS = {0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100}

@dataclass
class Rating:
    condition: str
    percentage: int
    side: Optional[str] = None  # "left", "right", or None
    diagnostic_code: Optional[str] = None

    def __post_init__(self):
        """Validate rating percentage is a valid VA rating."""
        if self.percentage not in VALID_VA_RATINGS:
            raise ValueError(
                f"Invalid rating {self.percentage}%. "
                f"VA only issues ratings at: {sorted(VALID_VA_RATINGS)}"
            )

@dataclass
class CalculationStep:
    step: int
    description: str
    rating: Optional[int] = None
    efficiency_lost: Optional[float] = None
    efficiency_remaining: float = 100

def calculate_combined_rating(
    ratings: List[Rating],
    apply_bilateral: bool = True
) -> Dict:
    """
    Calculate VA combined disability rating per 38 CFR 4.25.

    Returns:
        Dict with combined_rating, steps, bilateral_info, etc.
    """
    if not ratings:
        return {"combined_rating": 0, "calculation_steps": []}

    steps = []
    step_num = 1

    # Step 1: Identify bilateral conditions
    bilateral_groups = {}
    non_bilateral = []

    if apply_bilateral:
        for r in ratings:
            if r.side in ("left", "right"):
                key = (r.condition.lower(), r.diagnostic_code)
                if key not in bilateral_groups:
                    bilateral_groups[key] = []
                bilateral_groups[key].append(r)
            else:
                non_bilateral.append(r)
    else:
        non_bilateral = ratings

    # Step 2: Process bilateral conditions
    bilateral_info = []
    processed_ratings = []

    for key, group in bilateral_groups.items():
        if len(group) >= 2:
            # Has both sides - apply bilateral factor
            left = [r for r in group if r.side == "left"]
            right = [r for r in group if r.side == "right"]

            if left and right:
                # Combine the bilateral ratings
                bilateral_combined = combine_ratings([r.percentage for r in group])

                # Apply 10% bilateral factor
                with_factor = bilateral_combined * 1.10
                with_factor_rounded = int(round(with_factor))

                bilateral_info.append({
                    "conditions": [f"{r.condition} ({r.side})" for r in group],
                    "combined": bilateral_combined,
                    "with_bilateral_factor": with_factor_rounded
                })

                # Add as single rating for final calculation
                processed_ratings.append(with_factor_rounded)
            else:
                # Only one side, treat as normal
                for r in group:
                    processed_ratings.append(r.percentage)
        else:
            # Only one side present
            for r in group:
                processed_ratings.append(r.percentage)

    # Add non-bilateral ratings
    for r in non_bilateral:
        processed_ratings.append(r.percentage)

    # Step 3: Sort ratings highest to lowest
    processed_ratings.sort(reverse=True)

    # Step 4: Calculate combined using VA formula
    steps.append(CalculationStep(
        step=step_num,
        description="Start with 100% efficiency (whole person)",
        efficiency_remaining=100
    ))
    step_num += 1

    efficiency_remaining = 100.0

    for rating in processed_ratings:
        efficiency_lost = efficiency_remaining * (rating / 100)
        efficiency_remaining = efficiency_remaining - efficiency_lost

        steps.append(CalculationStep(
            step=step_num,
            description=f"Apply {rating}% rating",
            rating=rating,
            efficiency_lost=round(efficiency_lost, 2),
            efficiency_remaining=round(efficiency_remaining, 2)
        ))
        step_num += 1

    # Step 5: Calculate final combined
    exact_combined = 100 - efficiency_remaining
    rounded_combined = round(exact_combined / 10) * 10

    steps.append(CalculationStep(
        step=step_num,
        description=f"Final: {exact_combined:.1f}% rounds to {rounded_combined}%",
        efficiency_remaining=round(efficiency_remaining, 2)
    ))

    return {
        "combined_rating": rounded_combined,
        "combined_exact": round(exact_combined, 2),
        "bilateral_conditions": bilateral_info,
        "calculation_steps": [vars(s) for s in steps]
    }


def combine_ratings(percentages: List[int]) -> int:
    """Combine multiple ratings using VA formula (no rounding)."""
    if not percentages:
        return 0

    percentages = sorted(percentages, reverse=True)
    efficiency = 100.0

    for pct in percentages:
        efficiency = efficiency * (100 - pct) / 100

    return int(round(100 - efficiency))
```

### 2025 Compensation Rates

```python
# VA Disability Compensation Rates - Effective December 1, 2024
# Source: https://www.va.gov/disability/compensation-rates/

COMPENSATION_2025 = {
    # Base rates (veteran alone, no dependents)
    "base": {
        10: 175.51,
        20: 347.28,
        30: 537.81,
        40: 774.57,
        50: 1102.04,
        60: 1395.08,
        70: 1759.96,
        80: 2044.93,
        90: 2298.27,
        100: 3832.06
    },
    # Additional amounts for dependents (30%+ only)
    "spouse": {
        30: 64.00,
        40: 85.00,
        50: 107.00,
        60: 128.00,
        70: 149.00,
        80: 171.00,
        90: 192.00,
        100: 213.81
    },
    "child_under_18": {
        30: 32.00,
        40: 43.00,
        50: 53.00,
        60: 64.00,
        70: 75.00,
        80: 85.00,
        90: 96.00,
        100: 106.92
    },
    "child_18_school": {
        30: 103.00,
        40: 137.00,
        50: 172.00,
        60: 206.00,
        70: 240.00,
        80: 274.00,
        90: 309.00,
        100: 343.67
    },
    "parent_one": {
        30: 51.00,
        40: 68.00,
        50: 85.00,
        60: 102.00,
        70: 119.00,
        80: 136.00,
        90: 153.00,
        100: 170.45
    },
    "parent_two": {
        30: 96.00,
        40: 127.00,
        50: 159.00,
        60: 191.00,
        70: 223.00,
        80: 255.00,
        90: 286.00,
        100: 318.87
    }
}

def get_monthly_compensation(
    rating: int,
    spouse: bool = False,
    children: int = 0,
    children_18_school: int = 0,
    parents: int = 0
) -> Dict:
    """Calculate monthly compensation based on rating and dependents."""

    if rating < 10 or rating > 100:
        return {"error": "Rating must be between 10 and 100"}

    # Round to nearest 10
    rating = round(rating / 10) * 10

    base = COMPENSATION_2025["base"][rating]
    total = base
    breakdown = [{"type": "Base rate", "amount": base}]

    # Dependents only apply at 30%+
    if rating >= 30:
        if spouse:
            spouse_add = COMPENSATION_2025["spouse"][rating]
            total += spouse_add
            breakdown.append({"type": "Spouse", "amount": spouse_add})

        for _ in range(children):
            child_add = COMPENSATION_2025["child_under_18"][rating]
            total += child_add
            breakdown.append({"type": "Child under 18", "amount": child_add})

        for _ in range(children_18_school):
            child_add = COMPENSATION_2025["child_18_school"][rating]
            total += child_add
            breakdown.append({"type": "Child 18+ in school", "amount": child_add})

        if parents == 1:
            parent_add = COMPENSATION_2025["parent_one"][rating]
            total += parent_add
            breakdown.append({"type": "One dependent parent", "amount": parent_add})
        elif parents >= 2:
            parent_add = COMPENSATION_2025["parent_two"][rating]
            total += parent_add
            breakdown.append({"type": "Two dependent parents", "amount": parent_add})

    return {
        "rating": rating,
        "monthly_total": round(total, 2),
        "annual_total": round(total * 12, 2),
        "breakdown": breakdown,
        "effective_date": "December 1, 2024",
        "note": "Rates are tax-free" if rating < 100 else "100% rating includes Special Monthly Compensation eligibility"
    }
```

---

## Test Cases

### Test 1: Simple Addition Comparison

```python
# Input: 50%, 30%
# Expected: 65% (not 80%)
# Math: 100 - [(100-50) × (100-30) / 100] = 100 - [50 × 70 / 100] = 100 - 35 = 65%
```

### Test 2: Three Ratings

```python
# Input: 50%, 30%, 20%
# Expected: 70%
# Math:
#   After 50%: 50% remaining
#   After 30%: 50 × 0.70 = 35% remaining
#   After 20%: 35 × 0.80 = 28% remaining
#   Combined: 72%, rounds to 70%
```

### Test 3: Bilateral Factor

```python
# Input: 30% left knee, 20% right knee
# Expected: ~48% (bilateral), then use in overall calculation
# Math:
#   Bilateral combined: 100 - [(100-30) × (100-20) / 100] = 44%
#   With factor: 44 × 1.10 = 48.4% → 48%
```

### Test 4: Match VA Table

The calculator must match the official VA Combined Ratings Table exactly:

| Rating 1 | Rating 2 | Expected Combined |
|----------|----------|-------------------|
| 10 | 10 | 20 |
| 20 | 10 | 30 |
| 30 | 20 | 40 |
| 40 | 30 | 60 |
| 50 | 30 | 70 |
| 50 | 40 | 70 |
| 50 | 50 | 80 |
| 60 | 40 | 80 |
| 70 | 30 | 80 |
| 70 | 50 | 90 |
| 80 | 50 | 90 |
| 90 | 50 | 100 |

---

## Web UI Requirements

### Calculator Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  VA Combined Disability Rating Calculator                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Add your disability ratings:                                   │
│                                                                  │
│  ┌─────────────────┬──────────┬─────────────┬─────────┐        │
│  │ Condition       │ Rating % │ Side        │ Remove  │        │
│  ├─────────────────┼──────────┼─────────────┼─────────┤        │
│  │ PTSD            │ 50%  ▼   │ N/A         │   ✕     │        │
│  │ Knee strain     │ 30%  ▼   │ Left    ▼   │   ✕     │        │
│  │ Knee strain     │ 20%  ▼   │ Right   ▼   │   ✕     │        │
│  └─────────────────┴──────────┴─────────────┴─────────┘        │
│                                                                  │
│  [+ Add Another Rating]                                         │
│                                                                  │
│  Dependents (affects compensation at 30%+):                     │
│  ☑ Spouse   Children: [2]   Dependent parents: [0]             │
│                                                                  │
│  [Calculate Combined Rating]                                    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  RESULTS                                                         │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Combined Rating: 70%                                     │  │
│  │  Monthly Compensation: $1,716.28                          │  │
│  │  Annual Compensation: $20,595.36 (tax-free)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  How we calculated this:                                        │
│                                                                  │
│  1. Start with 100% efficiency (whole person)                  │
│  2. Apply PTSD (50%): 50% efficiency lost → 50% remaining      │
│  3. Apply bilateral knee (48% after 10% factor):               │
│     24% efficiency lost → 26% remaining                         │
│  4. Combined: 74% → rounds to 70%                              │
│                                                                  │
│  💡 Why isn't it 100%?                                          │
│  VA uses "whole person" theory. Each condition affects your    │
│  remaining capacity, not your whole body. Learn more →         │
│                                                                  │
│  ⚠️ Bilateral Factor Applied                                    │
│  Your left and right knee conditions were combined (44%)       │
│  and boosted 10% (→ 48%) before calculating the total.         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Plain Language Explanations

Always explain in veteran-friendly terms:

- "Combined" not "total" (VA terminology)
- Explain why 50% + 30% ≠ 80%
- Show step-by-step math
- Highlight bilateral factor when applied
- Include compensation amounts (motivating!)

---

## Gateway Integration

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
from vetassist_calculator import calculate_combined_rating, get_monthly_compensation

@app.route('/v1/vetassist/rating-calculator', methods=['POST'])
def rating_calculator():
    """Calculate VA combined disability rating."""
    data = request.get_json()

    # Parse ratings
    ratings = []
    for r in data.get('ratings', []):
        ratings.append(Rating(
            condition=r.get('condition', 'Unknown'),
            percentage=r.get('percentage', 0),
            side=r.get('side'),
            diagnostic_code=r.get('diagnostic_code')
        ))

    # Calculate
    result = calculate_combined_rating(ratings)

    # Add compensation if requested
    if data.get('include_compensation'):
        deps = data.get('dependents', {})
        comp = get_monthly_compensation(
            rating=result['combined_rating'],
            spouse=deps.get('spouse', False),
            children=deps.get('children', 0),
            children_18_school=deps.get('children_18_school', 0),
            parents=deps.get('parents', 0)
        )
        result['compensation'] = comp

    # Add explanation
    result['explanation'] = generate_explanation(result)

    # Audit (use SHA-256, not MD5 - MD5 is cryptographically broken)
    result['audit_hash'] = hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()[:16]

    return jsonify(result)
```

---

## Validation Checklist

- [ ] Calculator matches VA Combined Ratings Table for all combinations
- [ ] Bilateral factor applies correctly (10% boost)
- [ ] Rounding to nearest 10% works (0.5 rounds up)
- [ ] 2025 compensation rates are accurate
- [ ] Dependent calculations correct at each rating level
- [ ] Step-by-step explanations are clear
- [ ] API endpoint returns proper JSON schema
- [ ] Error handling for invalid inputs (negative ratings, >100%, etc.)
- [ ] Council validation for edge cases

---

## Files to Create

| File | Location | Purpose |
|------|----------|---------|
| `vetassist_calculator.py` | `/ganuda/lib/` | Core calculation logic |
| `compensation_rates_2025.py` | `/ganuda/lib/` | Rate tables |
| `test_calculator.py` | `/ganuda/scripts/` | Validation tests |
| Gateway route | `/ganuda/services/llm_gateway/gateway.py` | API endpoint |

---

## Related Documents

- VetAssist PRD v2.0
- [38 CFR 4.25 - Combined Ratings Table](https://www.ecfr.gov/current/title-38/chapter-I/part-4)
- [VA Compensation Rates 2025](https://www.va.gov/disability/compensation-rates/)

---

*For Seven Generations*
