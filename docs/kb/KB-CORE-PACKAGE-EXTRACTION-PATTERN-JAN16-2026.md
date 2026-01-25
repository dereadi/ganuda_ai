# KB: Core Package Extraction Pattern

**Date:** January 16, 2026
**Category:** Architecture / Development
**Status:** Active

---

## Overview

This KB documents the pattern for extracting reusable code from app-specific implementations into core platform packages.

## Case Study: ganuda-pii

### Before (App-Specific)
- Location: `/ganuda/vetassist/backend/app/services/pii_service.py`
- Lines: 169
- Problem: Code tied to VetAssist, not reusable

### After (Core + Plugin)

**Core Package:** `/ganuda/lib/ganuda_pii/`
```
ganuda_pii/
├── __init__.py       # Package exports
├── service.py        # Generic PIIService (120 lines)
├── tokenizer.py      # Tokenization logic (60 lines)
└── recognizers/
    ├── __init__.py   # Plugin registry
    └── veteran.py    # Domain plugin (70 lines)
```

**App Wrapper:** `/ganuda/vetassist/backend/app/services/pii_service.py`
```python
# Now just 41 lines - thin wrapper
import sys
sys.path.insert(0, '/ganuda/lib')

from ganuda_pii import PIIService as CorePIIService
from ganuda_pii.recognizers import veteran

class PIIService(CorePIIService):
    def __init__(self):
        super().__init__()
        self.add_recognizers(veteran.get_recognizers())

pii_service = PIIService()  # Singleton
```

## Extraction Pattern

### Step 1: Identify Generic vs Domain-Specific

| Generic (Extract) | Domain-Specific (Keep) |
|-------------------|------------------------|
| Presidio wrapper | Veteran SSN patterns |
| Tokenization logic | VA file number patterns |
| Redaction methods | Military service numbers |
| Configuration | Context keywords |

### Step 2: Create Plugin Architecture

```python
# Core service accepts plugins
class PIIService:
    def add_recognizers(self, recognizers: List[PatternRecognizer]):
        for r in recognizers:
            self.analyzer.registry.add_recognizer(r)
```

### Step 3: Domain Plugin Interface

```python
# Each domain implements get_recognizers()
def get_recognizers() -> List[PatternRecognizer]:
    return [...]
```

### Step 4: Backward-Compatible Wrapper

Keep the original import path working:
```python
# Apps can still do:
from app.services.pii_service import pii_service
```

## Results

| Metric | Before | After |
|--------|--------|-------|
| App code lines | 169 | 41 |
| Reusable code | 0 | 180 |
| New app effort | Write from scratch | Import + configure |

## Checklist for Extraction

- [ ] Identify generic patterns
- [ ] Identify domain-specific elements
- [ ] Design plugin interface
- [ ] Create core package in `/ganuda/lib/`
- [ ] Create domain plugin
- [ ] Create app wrapper for backward compatibility
- [ ] Test original app still works
- [ ] Document in KB article
- [ ] Store in thermal memory

## Next Extraction Candidates

| File | Extract To | Lines |
|------|------------|-------|
| security.py | ganuda_auth | 149 |
| database.py | ganuda_db | 45 |
| config.py | ganuda_config | 76 |

---

*Cherokee AI Federation - For the Seven Generations*
*"Extract once, use forever."*
