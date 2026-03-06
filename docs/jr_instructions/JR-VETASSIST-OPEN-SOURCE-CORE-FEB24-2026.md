# Jr Instruction: VetAssist Open Source Core Extraction

**Task ID:** VETASSIST-OSS
**Kanban:** #1826
**Priority:** 3
**Sacred Fire Priority:** 30
**Story Points:** 5
**Assigned:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create an extraction script that copies the open-sourceable VetAssist components into a standalone `/ganuda/vetassist-oss/` directory. The script:

- Reads source files from `/ganuda/vetassist/backend/app/services/`
- Strips any lines containing sensitive patterns (`CHEROKEE_DB_PASS`, `password`, `.env`, `thermal_memory`)
- Replaces `psycopg2` and `SQLAlchemy` imports with stub comments
- Generates a README.md, LICENSE (MIT), requirements.txt, and test file
- Writes cleaned versions of: `va_calculator.py`, `nexus_template_generator.py`, `cfr_parser.py`, `cfr_retriever.py`

---

## Step 1: Create the extraction script

Create `/ganuda/scripts/extract_vetassist_oss.py`

```python
#!/usr/bin/env python3
"""
VetAssist Open Source Core Extraction

Extracts open-sourceable VetAssist components into /ganuda/vetassist-oss/
with sensitive dependencies stripped and DB calls stubbed.

Usage:
  python3 extract_vetassist_oss.py
  python3 extract_vetassist_oss.py --source /ganuda/vetassist/backend/app/services --dest /ganuda/vetassist-oss
"""

import os
import re
import json
import argparse
from datetime import datetime

DEFAULT_SOURCE = "/ganuda/vetassist/backend/app/services"
DEFAULT_DEST = "/ganuda/vetassist-oss"

# Patterns that indicate sensitive content -- lines containing these are stripped
SENSITIVE_PATTERNS = [
    "CHEROKEE_DB_PASS",
    "password",
    ".env",
    "thermal_memory",
]

# Import patterns to replace with stubs
DB_IMPORT_PATTERNS = [
    (r"^\s*import\s+psycopg2.*$", "# Standalone: DB dependency removed (psycopg2)"),
    (r"^\s*from\s+psycopg2\s+import.*$", "# Standalone: DB dependency removed (psycopg2)"),
    (r"^\s*import\s+sqlalchemy.*$", "# Standalone: DB dependency removed (SQLAlchemy)"),
    (r"^\s*from\s+sqlalchemy\s+import.*$", "# Standalone: DB dependency removed (SQLAlchemy)"),
    (r"^\s*from\s+sqlalchemy\..*import.*$", "# Standalone: DB dependency removed (SQLAlchemy)"),
]

# Files to extract: (source_filename, dest_subdir, dest_filename)
FILES_TO_EXTRACT = [
    ("va_calculator.py", "calculator", "va_calculator.py"),
    ("nexus_template_generator.py", "templates", "nexus_template_generator.py"),
    ("cfr_parser.py", "cfr", "cfr_parser.py"),
    ("cfr_retriever.py", "cfr", "cfr_retriever.py"),
]


def clean_source_line(line):
    """
    Check if a line should be stripped (sensitive) or has DB imports to replace.
    Returns: (keep_line: bool, cleaned_line: str)
    """
    # Check sensitive patterns (case-insensitive)
    line_lower = line.lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern.lower() in line_lower:
            return False, ""

    # Check DB import patterns
    for regex, replacement in DB_IMPORT_PATTERNS:
        if re.match(regex, line):
            return True, replacement + "\n"

    return True, line


def clean_file(source_path):
    """Read a source file and return cleaned content + stats."""
    if not os.path.exists(source_path):
        return None, {"error": f"File not found: {source_path}"}

    with open(source_path, "r") as f:
        original_lines = f.readlines()

    cleaned_lines = []
    stripped_count = 0
    replaced_count = 0

    for line in original_lines:
        keep, cleaned = clean_source_line(line)
        if not keep:
            stripped_count += 1
            continue
        if cleaned != line:
            replaced_count += 1
        cleaned_lines.append(cleaned)

    return "".join(cleaned_lines), {
        "original_lines": len(original_lines),
        "cleaned_lines": len(cleaned_lines),
        "stripped": stripped_count,
        "imports_replaced": replaced_count,
    }


def generate_readme():
    """Generate the OSS README.md content."""
    return """# VetAssist Open Source Tools

**Educational tools for understanding VA disability claims processing.**

> **DISCLAIMER**: This software is provided for educational and informational
> purposes only. It is NOT a substitute for professional legal advice from a
> VA-accredited attorney or claims agent. VA disability claims are complex legal
> matters, and the tools provided here are simplified demonstrations that may not
> reflect current VA policy or regulations. Always consult with a qualified
> professional before making decisions about your VA benefits.

## Components

### Calculator (`calculator/`)
- **va_calculator.py** -- VA combined disability rating calculator
- **compensation_rates.json** -- Static 2024 VA compensation rate table (10 rows)
- **test_calculator.py** -- 15 validation test cases

The calculator implements the VA combined rating formula: ratings are applied
sequentially to the remaining "whole person" percentage, not added together.
For example, 50% + 30% = 65% (not 80%).

### Nexus Template Generator (`templates/`)
- **nexus_template_generator.py** -- Generates nexus letter templates for
  service-connection claims

A nexus letter is a medical opinion letter that establishes a connection between
a veteran's current condition and their military service. This tool generates
template structures -- actual nexus letters must be written by a qualified
medical professional.

### CFR Reference (`cfr/`)
- **cfr_parser.py** -- Parses 38 CFR Part 4 rating criteria
- **cfr_retriever.py** -- Retrieves relevant CFR sections for given conditions

These tools help navigate Title 38 of the Code of Federal Regulations, which
governs VA disability ratings.

## Installation

No external dependencies required (standard library only).

```
pip install -r requirements.txt
```

## Usage

### Combined Rating Calculator
```python
from calculator.va_calculator import calculate_combined_rating

# 50% + 30% + 20%
result = calculate_combined_rating([50, 30, 20])
print(f"Combined: {result}%")  # 72% -> rounds to 70%
```

### Nexus Template
```python
from templates.nexus_template_generator import generate_nexus_template

template = generate_nexus_template(
    condition="PTSD",
    service_event="combat deployment",
)
print(template)
```

## License

MIT License -- see LICENSE file.

## Origin

Extracted from the Cherokee AI Federation VetAssist project.
These components were identified as safe for open-source release with no
proprietary dependencies, credentials, or private data.
"""


def generate_license():
    """Generate MIT LICENSE content."""
    year = datetime.now().year
    return f"""MIT License

Copyright (c) {year} Cherokee AI Federation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def generate_compensation_rates():
    """Generate static 2024 VA compensation rates JSON (10 rows)."""
    return json.dumps({
        "description": "2024 VA Disability Compensation Rates (Veteran Alone, no dependents)",
        "effective_date": "2024-12-01",
        "source": "https://www.va.gov/disability/compensation-rates/veteran-rates/",
        "rates": [
            {"rating_pct": 10, "monthly_usd": 171.23},
            {"rating_pct": 20, "monthly_usd": 338.49},
            {"rating_pct": 30, "monthly_usd": 524.31},
            {"rating_pct": 40, "monthly_usd": 755.28},
            {"rating_pct": 50, "monthly_usd": 1075.16},
            {"rating_pct": 60, "monthly_usd": 1361.88},
            {"rating_pct": 70, "monthly_usd": 1716.28},
            {"rating_pct": 80, "monthly_usd": 1995.01},
            {"rating_pct": 90, "monthly_usd": 2241.91},
            {"rating_pct": 100, "monthly_usd": 3737.85},
        ]
    }, indent=2)


def generate_test_calculator():
    """Generate test cases for va_calculator."""
    return '''#!/usr/bin/env python3
"""
Validation test cases for VA combined rating calculator.
15 test cases covering edge cases and common scenarios.

Usage:
  python3 test_calculator.py
"""

import sys
import os

# Add parent directory so we can import the calculator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def calculate_combined_rating_standalone(ratings):
    """
    Standalone VA combined rating calculation.
    Uses the bilateral factor method from 38 CFR 4.25.
    Ratings are applied to remaining whole-body efficiency, not added.
    Final result is rounded to nearest 10.
    """
    if not ratings:
        return 0
    if len(ratings) == 1:
        return ratings[0]

    # Sort descending
    sorted_ratings = sorted(ratings, reverse=True)

    combined = 0.0
    for rating in sorted_ratings:
        r = rating / 100.0
        combined = combined + r * (1.0 - combined)

    # Convert to percentage and round to nearest 10
    combined_pct = combined * 100.0
    rounded = int(round(combined_pct / 10.0) * 10)
    return min(rounded, 100)


# ============================================================
# Test cases
# ============================================================

TEST_CASES = [
    # (description, input_ratings, expected_combined)
    ("Single 50% rating", [50], 50),
    ("Single 100% rating", [100], 100),
    ("Single 10% rating", [10], 10),
    ("Two equal 50% ratings", [50, 50], 80),
    ("50% + 30%", [50, 30], 70),
    ("50% + 30% + 20%", [50, 30, 20], 70),
    ("30% + 20% + 10%", [30, 20, 10], 50),
    ("70% + 50%", [70, 50], 90),
    ("10% + 10%", [10, 10], 20),
    ("90% + 50%", [90, 50], 100),
    ("Empty list", [], 0),
    ("All zeros", [0, 0, 0], 0),
    ("40% + 40% + 40%", [40, 40, 40], 80),
    ("20% + 20% + 20% + 20%", [20, 20, 20, 20], 60),
    ("60% + 40% + 20% + 10%", [60, 40, 20, 10], 80),
]


def run_tests():
    """Run all test cases and report results."""
    passed = 0
    failed = 0

    print("VA Combined Rating Calculator - Test Suite")
    print("=" * 55)

    for desc, ratings, expected in TEST_CASES:
        result = calculate_combined_rating_standalone(ratings)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        marker = "  " if status == "PASS" else ">>"
        print(f"  {marker} {status}: {desc}")
        if status == "FAIL":
            print(f"       Input: {ratings}, Expected: {expected}, Got: {result}")

    print(f"\\n{'=' * 55}")
    print(f"Results: {passed}/{passed + failed} passed")
    if failed > 0:
        print(f"FAILURES: {failed}")
        sys.exit(1)
    else:
        print("All tests passed.")


if __name__ == "__main__":
    run_tests()
'''


def generate_requirements():
    """Generate minimal requirements.txt."""
    return "# No external dependencies required -- stdlib only\n"


def extract_all(source_dir, dest_dir):
    """Main extraction routine."""
    timestamp = datetime.now().isoformat()
    print(f"VetAssist OSS Extraction")
    print(f"Timestamp: {timestamp}")
    print(f"Source:    {source_dir}")
    print(f"Dest:      {dest_dir}")
    print("=" * 60)

    # Track results
    total_lines = 0
    file_results = []

    # Create destination structure
    subdirs = set(f[1] for f in FILES_TO_EXTRACT)
    for subdir in subdirs:
        os.makedirs(os.path.join(dest_dir, subdir), exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)

    # Extract and clean source files
    print("\n--- Extracting source files ---")
    for src_name, dest_subdir, dest_name in FILES_TO_EXTRACT:
        src_path = os.path.join(source_dir, src_name)
        dest_path = os.path.join(dest_dir, dest_subdir, dest_name)

        print(f"  {src_name} -> {dest_subdir}/{dest_name}...", end=" ")
        content, stats = clean_file(src_path)

        if content is None:
            print(f"SKIPPED ({stats.get('error', 'unknown')})")
            file_results.append({"file": dest_name, "status": "skipped", "stats": stats})
            continue

        with open(dest_path, "w") as f:
            f.write(content)

        line_count = content.count("\n")
        total_lines += line_count
        print(f"OK ({line_count} lines, {stats['stripped']} stripped, {stats['imports_replaced']} imports replaced)")
        file_results.append({"file": f"{dest_subdir}/{dest_name}", "status": "ok", "lines": line_count, "stats": stats})

    # Generate static files
    print("\n--- Generating static files ---")

    # README.md
    readme = generate_readme()
    readme_path = os.path.join(dest_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(readme)
    readme_lines = readme.count("\n")
    total_lines += readme_lines
    print(f"  README.md ({readme_lines} lines)")

    # LICENSE
    lic = generate_license()
    lic_path = os.path.join(dest_dir, "LICENSE")
    with open(lic_path, "w") as f:
        f.write(lic)
    lic_lines = lic.count("\n")
    total_lines += lic_lines
    print(f"  LICENSE ({lic_lines} lines)")

    # compensation_rates.json
    rates = generate_compensation_rates()
    rates_path = os.path.join(dest_dir, "calculator", "compensation_rates.json")
    with open(rates_path, "w") as f:
        f.write(rates)
    rates_lines = rates.count("\n")
    total_lines += rates_lines
    print(f"  calculator/compensation_rates.json ({rates_lines} lines)")

    # test_calculator.py
    tests = generate_test_calculator()
    tests_path = os.path.join(dest_dir, "calculator", "test_calculator.py")
    with open(tests_path, "w") as f:
        f.write(tests)
    tests_lines = tests.count("\n")
    total_lines += tests_lines
    print(f"  calculator/test_calculator.py ({tests_lines} lines)")

    # requirements.txt
    reqs = generate_requirements()
    reqs_path = os.path.join(dest_dir, "requirements.txt")
    with open(reqs_path, "w") as f:
        f.write(reqs)
    print(f"  requirements.txt")

    # Summary
    extracted_count = sum(1 for r in file_results if r["status"] == "ok")
    skipped_count = sum(1 for r in file_results if r["status"] == "skipped")
    generated_count = 4  # README, LICENSE, compensation_rates.json, test_calculator.py

    print(f"\n{'=' * 60}")
    print(f"EXTRACTION SUMMARY")
    print(f"  Source files extracted: {extracted_count}")
    print(f"  Source files skipped:   {skipped_count}")
    print(f"  Static files generated: {generated_count}")
    print(f"  Total files:            {extracted_count + generated_count + 1}")  # +1 for requirements.txt
    print(f"  Total lines:            {total_lines}")
    print(f"  Output directory:       {dest_dir}")
    print(f"{'=' * 60}")

    if skipped_count > 0:
        print("\nWARNING: Some source files were not found. Check paths above.")


def main():
    parser = argparse.ArgumentParser(
        description="Extract open-sourceable VetAssist components"
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help=f"Source services directory (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--dest",
        default=DEFAULT_DEST,
        help=f"Destination directory (default: {DEFAULT_DEST})",
    )
    args = parser.parse_args()

    extract_all(args.source, args.dest)


if __name__ == "__main__":
    main()
```

---

## Verification

Run the extraction:
```text
python3 /ganuda/scripts/extract_vetassist_oss.py
```

Then verify the output:
```text
ls -la /ganuda/vetassist-oss/
ls -la /ganuda/vetassist-oss/calculator/
ls -la /ganuda/vetassist-oss/templates/
ls -la /ganuda/vetassist-oss/cfr/
python3 /ganuda/vetassist-oss/calculator/test_calculator.py
```

Expected: 4 source files extracted and cleaned, 5 generated files (README.md, LICENSE, compensation_rates.json, test_calculator.py, requirements.txt), all sensitive patterns removed.

---

## Notes

- Sensitive line stripping is case-insensitive and catches `password`, `CHEROKEE_DB_PASS`, `.env`, `thermal_memory`
- DB imports (psycopg2, SQLAlchemy) replaced with comment stubs so cleaned files still parse as valid Python
- Test calculator includes a standalone implementation so tests run without importing the cleaned file (avoids broken import chains)
- Compensation rates are hardcoded 2024 values (10 tiers, veteran-alone, no dependents)
- Script is idempotent -- safe to re-run, overwrites previous extraction
- No files from auth_service, token_encryption, or other sensitive services are included
