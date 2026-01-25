# KB: Ganuda Platform Core Architecture

**Date:** January 16, 2026
**Category:** Architecture
**Status:** Active

---

## Overview

The Ganuda Platform provides shared infrastructure for all "Assist" applications (VetAssist, SSDisabilityAssist, HealthcareAssist, etc.).

## Core Packages

Location: `/ganuda/lib/`

| Package | Status | Purpose |
|---------|--------|---------|
| `ganuda_pii` | Complete | PII detection, tokenization, vault integration |
| `ganuda_council` | Complete | 7-Specialist Council client |
| `ganuda_auth` | Scaffold | JWT, password hashing, auth middleware |
| `ganuda_db` | Scaffold | SQLAlchemy patterns, session management |
| `ganuda_config` | Scaffold | Pydantic settings base |
| `ganuda_api` | Scaffold | Health checks, middleware |

## Usage Pattern

```python
import sys
sys.path.insert(0, '/ganuda/lib')

from ganuda_pii import PIIService
from ganuda_pii.recognizers import veteran  # Domain plugin
from ganuda_council import council_vote

# Initialize with domain plugins
pii = PIIService()
pii.add_recognizers(veteran.get_recognizers())

# Use Council
result = council_vote("Should we proceed?", context="...")
```

## Creating New Recognizer Plugins

```python
# /ganuda/lib/ganuda_pii/recognizers/ssdi.py
from presidio_analyzer import PatternRecognizer, Pattern

def get_recognizers():
    return [
        PatternRecognizer(
            supported_entity="SSDI_CLAIM_NUMBER",
            name="SSDIClaimRecognizer",
            patterns=[Pattern(name="SSDI", regex=r"\b\d{3}-\d{2}-\d{4}-[A-Z]\b", score=0.85)],
            context=["ssdi", "disability", "social security"]
        ),
    ]
```

## Hardware Capacity

| Resource | Capacity | Max Apps |
|----------|----------|----------|
| GPU (vLLM) | Shared model | 10+ |
| RAM | 113 GB free | 200+ backends |
| Database | PostgreSQL schemas | 50+ |
| PII Vault | goldfin | 20+ |

## Key Documents

- `/ganuda/lib/PLATFORM_README.md` - Full package documentation
- `/ganuda/docs/ultrathink/ULTRATHINK-PLATFORM-CORE-ARCHITECTURE-JAN16-2026.md` - Strategic analysis
- `/ganuda/docs/jr_instructions/JR-VETASSIST-CORE-AUDIT-JAN16-2026.md` - Audit results

## Thermal Memory References

- Council vote: `c4d00e4978e51b67` (platform scaling strategy)
- Keywords: `platform`, `core`, `architecture`, `ganuda`

---

*Cherokee AI Federation - For the Seven Generations*
