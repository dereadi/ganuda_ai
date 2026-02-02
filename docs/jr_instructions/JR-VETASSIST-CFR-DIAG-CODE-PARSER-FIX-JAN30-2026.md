# Jr Instruction: Fix CFR Diagnostic Code Parser

**Date:** January 30, 2026
**Priority:** Medium
**Assigned To:** Software Engineer Jr.
**Council Vote:** 23589699dd7b4a97

## Problem

The CFR parser (`/ganuda/vetassist/backend/app/services/cfr_parser.py`) only extracts diagnostic codes from 67 of 267 sections. Many diagnostic codes are embedded in HTML table structures that get stripped during `re.sub(r"<[^>]+>", " ", raw_text)` cleaning.

## Current Behavior

```python
# Line 64-65 in cfr_parser.py
diag_codes = re.findall(r"\b(\d{4})\b", clean_text)
diag_codes = [c for c in diag_codes if 5000 <= int(c) <= 9999]
```

This only catches standalone 4-digit numbers in already-cleaned text. Codes in `<td>` cells, `id` attributes, or structured HTML tables are lost.

## Required Changes

### Step 1 (python): Add HTML table diagnostic code extraction

In `parse_sections()` function in `/ganuda/vetassist/backend/app/services/cfr_parser.py`, before the HTML tag stripping step, add a pre-extraction pass that finds diagnostic codes in HTML table cells and data attributes.

Add this regex to search `raw_text` BEFORE the `re.sub(r"<[^>]+>", " ", raw_text)` call:

```python
# Pre-extract diagnostic codes from HTML structure before stripping tags
html_codes = re.findall(r'(?:data-code|id|class)=["\']?\b(\d{4})\b', raw_text)
html_codes += re.findall(r'<td[^>]*>\s*(\d{4})\s*</td>', raw_text)
html_codes = [c for c in html_codes if 5000 <= int(c) <= 9999]
```

Then merge with the existing post-cleaning extraction:

```python
diag_codes = list(set(html_codes + diag_codes))
```

### Step 2 (python): Add section title-based code inference

Some sections have codes in their titles (e.g., "§4.71a — Schedule of ratings—musculoskeletal system" maps to diagnostic codes 5000-5299). Add a mapping dict:

```python
SECTION_CODE_RANGES = {
    "4.71a": range(5000, 5300),
    "4.73": range(5300, 5330),
    "4.79": range(6000, 6100),
    "4.85": range(6100, 6300),
    "4.87": range(6200, 6300),
    "4.88": range(6300, 6400),
    "4.97": range(6500, 6900),
    "4.104": range(7000, 7200),
    "4.110": range(7300, 7400),
    "4.114": range(7200, 7400),
    "4.118": range(7800, 7900),
    "4.124a": range(8000, 8800),
    "4.130": range(9200, 9500),
}
```

After the existing diagnostic code extraction, check if the section_number matches any key in this dict and add the range boundaries as reference codes.

### Step 3 (bash): Re-run parser and verify

```bash
cd /ganuda/vetassist/backend && python -c "
from app.services.cfr_parser import refresh_cfr_data
count = refresh_cfr_data()
print(f'Parsed {count} sections')
from app.services.cfr_retriever import get_cfr_retriever
r = get_cfr_retriever()
r.refresh()
# Test lookup
results = r.retrieve_by_diagnostic_code('6260')
print(f'Code 6260: {len(results)} results')
results = r.retrieve_by_diagnostic_code('9411')
print(f'Code 9411: {len(results)} results')
"
```

Expected: Code lookups should now return results for common VA diagnostic codes like 6260 (tinnitus), 9411 (PTSD), 5237 (back conditions).

## Verification

- Sections with diagnostic codes should increase from 67 to 150+
- `retrieve_by_diagnostic_code("9411")` should return at least 1 section (PTSD under §4.130)
- `retrieve_by_diagnostic_code("6260")` should return at least 1 section (tinnitus under §4.87)
- Existing BM25 text search should continue to work unchanged

## Context

- See KB article: `KB-VETASSIST-TIER1-DEPLOYMENT-JAN30-2026.md` lesson #5
- The cfr_retriever.py `retrieve_by_diagnostic_code()` method is correct — the issue is upstream in cfr_parser.py data extraction

---
*Cherokee AI Federation — For Seven Generations*
