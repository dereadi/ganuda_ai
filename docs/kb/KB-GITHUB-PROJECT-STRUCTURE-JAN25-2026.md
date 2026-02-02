# KB: GitHub Project Structure
## Cherokee AI Federation

**Date:** 2026-01-25
**Author:** TPM (Opus 4.5)
**Category:** Infrastructure / Source Control

---

## GitHub Account: dereadi

### Repository Summary

| Repository | Visibility | Purpose | Last Updated |
|------------|-----------|---------|--------------|
| **vetassist** | Private | VA disability claims assistance platform | Jan 25, 2026 |
| **ganuda-federation** | Public | Main Cherokee AI Federation codebase | Jan 25, 2026 |
| **ganuda_ai** | Public | Original Phase 1 discovery system | Dec 23, 2025 |
| **llm-gateway** | Private | LLM inference routing gateway | Dec 19, 2025 |
| **pathfinder-wisdom** | Private | Commercial intelligence layer | Dec 13, 2025 |
| **sag-unified-interface** | Private | SAG web interface | Dec 13, 2025 |
| **pathfinder-constitutional-ai** | Private | Pathfinder policy framework | Dec 13, 2025 |
| **qdad-apps** | Private | QDAD applications | Dec 13, 2025 |
| **pathfinder-vision** | Public | Open-source AI observability | Nov 17, 2025 |
| **video-enhancer-pro** | Private | Video processing tools | Aug 12, 2025 |
| **qdad-os** | Private | QDAD operating system | Aug 11, 2025 |
| **ganuda** | Private | Legacy ganuda (pre-federation) | Aug 10, 2025 |
| **ai-monitoring** | Private | Distributed AI monitoring | Jun 11, 2025 |
| **Claude_projects** | Private | Claude utility scripts | Jun 11, 2025 |
| **claude** | Private | Claude APIs and scripts | Jun 11, 2025 |

---

## Primary Repositories

### 1. vetassist (Private)
**URL:** https://github.com/dereadi/vetassist

VetAssist - AI-powered VA disability claims assistance platform.

**Contents:**
- `backend/` - FastAPI Python backend
  - `app/api/v1/endpoints/` - REST API endpoints
  - `app/services/` - Business logic services
  - `app/ml/` - ML models (crisis detection, rating prediction)
- `frontend/` - Next.js React frontend (separate build)
- `lib/` - Shared document processing libraries
- `docs/` - Implementation documentation

**Team Access:**
- dereadi (owner)
- jsdorn (collaborator - push access)

**Initial Commit:** Jan 25, 2026
- 129 files, 22,949 lines
- Backend: FastAPI with VA OAuth, PII protection
- Frontend: Dashboard, wizard, workbench
- Council integration for claim analysis

---

### 2. ganuda-federation (Public)
**URL:** https://github.com/dereadi/ganuda-federation

Main Cherokee AI Federation monorepo. Contains core platform infrastructure.

**Contents:**
- `jr_executor/` - Junior agent execution system
  - Task executor, queue worker, learning store
  - RLM executor (recursive language model)
  - Research task executor
- `lib/` - Core platform libraries
  - `specialist_council.py` - 7-specialist voting
  - `constitutional_constraints.py` - Policy enforcement
  - `consciousness_cascade/` - Emergent coordination
  - `ganuda_*/` - Platform submodules
- `telegram_bot/` - Telegram Chief interface
- `sag/` - SAG web interface
- `docs/` - Federation documentation
  - `jr_instructions/` - 374 Jr task definitions
  - `kb/` - 40+ Knowledge Base articles
  - `ultrathink/` - 43 design documents

**Recent Commits:**
- `1afddee` Jan 25, 2026 - Phase 3.2 (505 files)
- `a25b4d0` - SAG Governance Enhancement
- `f560018` - Phase 3.1 Complete

---

### 3. ganuda_ai (Public)
**URL:** https://github.com/dereadi/ganuda_ai

Original Phase 1 system - Cherokee Constitutional AI Discovery.

**Status:** Historical / Reference only
**Note:** Active development moved to ganuda-federation

---

## Local Repository Locations

### Bluefin (192.168.132.222)
```
/ganuda/                    -> ganuda-federation
/ganuda/vetassist/          -> vetassist
```

### Redfin (192.168.132.44)
```
/ganuda/                    -> ganuda-federation (clone)
```

### Sasass (macOS)
```
/Users/Shared/ganuda/       -> ganuda-federation (sync)
```

---

## Git Remote Configuration

### /ganuda (main)
```
federation  git@github.com:dereadi/ganuda-federation.git
origin      git@github.com:dereadi/ganuda_ai.git
```

**Primary remote:** `federation` (use for all pushes)

### /ganuda/vetassist
```
origin      git@github.com:dereadi/vetassist.git
```

---

## Workflow

### Committing Changes
1. Stage relevant files: `git add <files>`
2. Commit with descriptive message
3. Push to appropriate remote:
   - Main repo: `git push federation main`
   - VetAssist: `git push origin main`

### Co-authorship
All AI-assisted commits should include:
```
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Access Management

### VetAssist Collaborators
- **dereadi** - Owner
- **jsdorn** (Joe) - Push access (invitation pending)
- **TODO:** Add Kenzie when needed

### Public Repos
- ganuda-federation - Open source
- ganuda_ai - Open source
- pathfinder-vision - Open source

---

## For Seven Generations

This documentation ensures future maintainers understand:
1. Where code lives and why
2. How to commit and push changes
3. Access patterns for different team members

The Federation's code is our collective memory. Treat it with respect.
