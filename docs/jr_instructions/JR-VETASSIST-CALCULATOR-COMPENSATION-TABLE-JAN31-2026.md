# Jr Instruction: Create VA Compensation Rates Table

**Date:** January 31, 2026
**Priority:** High
**Assigned To:** Software Engineer Jr.
**Council Vote:** 30c3f0f3c835aa2a

## Problem

The VA combined rating calculator at `POST /api/v1/calculator/calculate` correctly computes the combined bilateral rating (e.g., 70+10+30 = 80%) but fails with `relation "va_compensation_rates" does not exist` when looking up monthly compensation dollar amounts.

## Required Changes

### Step 1 (sql): Create the va_compensation_rates table on zammad_production database at 192.168.132.222

```sql
CREATE TABLE IF NOT EXISTS va_compensation_rates (
    id SERIAL PRIMARY KEY,
    disability_rating INTEGER NOT NULL CHECK (disability_rating BETWEEN 0 AND 100),
    effective_date DATE NOT NULL DEFAULT '2024-12-01',
    veteran_alone NUMERIC(10,2) NOT NULL,
    veteran_with_spouse NUMERIC(10,2),
    veteran_spouse_1_child NUMERIC(10,2),
    veteran_spouse_2_children NUMERIC(10,2),
    veteran_spouse_3_children NUMERIC(10,2),
    additional_child_under_18 NUMERIC(10,2),
    additional_child_over_18_school NUMERIC(10,2),
    additional_spouse_aid_attendance NUMERIC(10,2),
    aid_attendance NUMERIC(10,2),
    housebound NUMERIC(10,2),
    UNIQUE(disability_rating, effective_date)
);
CREATE INDEX IF NOT EXISTS idx_comp_rates_rating ON va_compensation_rates(disability_rating);
```

### Step 2 (sql): Seed with 2025 VA compensation rates

The current VA compensation rates (effective December 1, 2024) are:

```sql
INSERT INTO va_compensation_rates (disability_rating, effective_date, veteran_alone, veteran_with_spouse) VALUES
(10, '2024-12-01', 175.51, 175.51),
(20, '2024-12-01', 347.83, 347.83),
(30, '2024-12-01', 538.78, 601.78),
(40, '2024-12-01', 775.72, 855.72),
(50, '2024-12-01', 1103.77, 1200.77),
(60, '2024-12-01', 1397.35, 1511.35),
(70, '2024-12-01', 1762.19, 1893.19),
(80, '2024-12-01', 2048.88, 2196.88),
(90, '2024-12-01', 2303.28, 2468.28),
(100, '2024-12-01', 3834.59, 4042.17)
ON CONFLICT (disability_rating, effective_date) DO NOTHING;
```

Note: These rates are approximate. The Jr should verify the exact 2025 rates from the VA website (https://www.va.gov/disability/compensation-rates/) and update all columns including dependent children rates.

### Step 3 (bash): Verify the calculator works end-to-end

```bash
curl -s -X POST http://192.168.132.223:8001/api/v1/calculator/calculate \
  -H "Content-Type: application/json" \
  -d '{"conditions": [{"name": "PTSD", "rating": 70}, {"name": "Tinnitus", "rating": 10}, {"name": "Lumbar Strain", "rating": 30}]}' | python3 -m json.tool
```

Expected: Combined rating of 80% and monthly compensation of ~$2,048.88 for veteran alone.

## Context

- Calculator service: `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`
- Database: `zammad_production` on bluefin (192.168.132.222)
- The combined rating formula (38 CFR 4.25) is already correctly implemented
- See KB: `KB-VETASSIST-TIER2-INTEGRATION-TESTING-JAN31-2026.md`

---
*Cherokee AI Federation — For Seven Generations*
