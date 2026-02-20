# Ganuda Platform Core Libraries

**Cherokee AI Federation - For the Seven Generations**

This directory contains the core platform libraries shared across all Assist applications.

## Available Packages

| Package | Status | Description |
|---------|--------|-------------|
| `ganuda_pii` | ✅ Complete | PII detection, tokenization, vault integration |
| `ganuda_auth` | 🔲 Scaffold | JWT, passwords, auth middleware |
| `ganuda_db` | 🔲 Scaffold | SQLAlchemy patterns, session management |
| `ganuda_config` | 🔲 Scaffold | Pydantic settings base |
| `ganuda_council` | ✅ Complete | 7-Specialist Council client |
| `ganuda_api` | 🔲 Scaffold | Health checks, middleware |

## Usage Pattern

```python
# In your Assist app (e.g., SSDisabilityAssist)
import sys
sys.path.insert(0, '/ganuda/lib')

from ganuda_pii import PIIService
from ganuda_pii.recognizers import veteran  # or ssdi, healthcare, etc.
from ganuda_council import council_vote
from ganuda_db import get_db, Base

# Initialize with domain-specific plugins
pii = PIIService()
pii.add_recognizers(veteran.get_recognizers())  # or your domain's recognizers
```

## Creating a New Assist App

1. **Start with core packages** - They provide 650+ lines of battle-tested code
2. **Add domain recognizers** - Create `ganuda_pii/recognizers/your_domain.py`
3. **Configure settings** - Extend `BaseAssistSettings`
4. **Connect to infrastructure** - silverfin (auth), goldfin (PII vault), redfin (LLM)

## Package Details

### ganuda_pii (Complete)

```
ganuda_pii/
├── __init__.py       # PIIService, PIITokenizer exports
├── service.py        # Core PIIService class
├── tokenizer.py      # Deterministic tokenization
└── recognizers/
    ├── __init__.py   # Plugin registry
    └── veteran.py    # VetAssist domain (SSN, VA file, service numbers)
```

**Adding a new domain:**
```python
# ganuda_pii/recognizers/ssdi.py
from presidio_analyzer import PatternRecognizer, Pattern

def get_recognizers():
    return [
        PatternRecognizer(
            supported_entity="SSDI_CLAIM_NUMBER",
            name="SSDIClaimRecognizer",
            patterns=[Pattern(name="SSDI", regex=r"...", score=0.8)],
            context=["ssdi", "disability", "claim"]
        ),
    ]
```

### ganuda_council (Complete)

Wraps existing `/ganuda/lib/specialist_council.py`:

```python
from ganuda_council import council_vote, SpecialistCouncil

# Quick vote
result = council_vote("Should we proceed with this approach?")

# Full council with options
council = SpecialistCouncil(max_tokens=500)
response = council.deliberate(question, context)
```

## Infrastructure Integration

| Service | Node | Port | Package Integration |
|---------|------|------|---------------------|
| FreeIPA | silverfin | 443 | `ganuda_auth` |
| PII Vault | goldfin | 5432 | `ganuda_pii` (tokenizer) |
| LLM Gateway | redfin | 8080 | `ganuda_council` |
| PostgreSQL | bluefin | 5432 | `ganuda_db` |

## Roadmap

- [ ] Complete `ganuda_auth` extraction
- [ ] Complete `ganuda_db` extraction
- [ ] Complete `ganuda_config` base
- [ ] Complete `ganuda_api` patterns
- [ ] Create `ganuda-assist-template` cookiecutter
- [ ] Package as pip-installable wheels

---

*"Build once, serve many. The platform is the legacy."*
