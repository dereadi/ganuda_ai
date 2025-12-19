# Jr Build Instructions: GitHub Repository Setup

**Priority**: MEDIUM  
**Assigned To**: GitHub Jr (DevOps)  
**Date**: December 13, 2025

## Objective

Create two new GitHub repositories and push existing local code to establish version control for critical Cherokee AI Federation infrastructure.

## Prerequisites

- GitHub account: `dereadi`
- SSH key configured: `/home/dereadi/.ssh/ganuda_github`
- SSH config: `~/.ssh/config` has GitHub host entry

## Repository 1: LLM Gateway

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `llm-gateway`
3. Description: `Cherokee AI Federation LLM Gateway v1.1 - OpenAI-compatible API with 7-Specialist Council`
4. Visibility: **Private** (contains API architecture)
5. DO NOT initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Push Local Code

```bash
ssh dereadi@192.168.132.223 "cd /ganuda/services/llm_gateway && \
  git remote add origin git@github.com:dereadi/llm-gateway.git && \
  git branch -M main && \
  git push -u origin main"
```

### Step 3: Verify

```bash
ssh dereadi@192.168.132.223 "cd /ganuda/services/llm_gateway && git remote -v && git log --oneline -1"
```

Expected output:
```
origin  git@github.com:dereadi/llm-gateway.git (fetch)
origin  git@github.com:dereadi/llm-gateway.git (push)
ae718d5 Initial commit: LLM Gateway v1.1 - Cherokee AI Federation
```

---

## Repository 2: SAG Unified Interface

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `sag-unified-interface`
3. Description: `Cherokee AI Federation ITSM Frontend - Event Management, Kanban, Tribe Dashboard`
4. Visibility: **Private** (contains internal tooling)
5. DO NOT initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Push Local Code

```bash
ssh dereadi@192.168.132.223 "cd /ganuda/home/dereadi/sag_unified_interface && \
  git remote add origin git@github.com:dereadi/sag-unified-interface.git && \
  git branch -M main && \
  git push -u origin main"
```

### Step 3: Verify

```bash
ssh dereadi@192.168.132.223 "cd /ganuda/home/dereadi/sag_unified_interface && git remote -v && git log --oneline -1"
```

Expected output:
```
origin  git@github.com:dereadi/sag-unified-interface.git (fetch)
origin  git@github.com:dereadi/sag-unified-interface.git (push)
67f5f1a Initial commit: SAG Unified Interface - Cherokee AI Federation ITSM
```

---

## Repository Contents Summary

### llm-gateway (1 file, ~40KB)
```
/ganuda/services/llm_gateway/
├── .gitignore
├── gateway.py          # Main LLM Gateway v1.1
├── gateway.py.bak      # (ignored)
├── venv/               # (ignored)
└── __pycache__/        # (ignored)
```

**Key Features in gateway.py:**
- `/v1/chat/completions` - OpenAI-compatible endpoint
- `/v1/council/vote` - 7-Specialist Council voting
- `/v1/council/history` - Vote history retrieval
- `/v1/models` - Model listing
- `/health` - Health check
- Thermal memory integration
- API key authentication

### sag-unified-interface (39 files, ~15K lines)
```
/ganuda/home/dereadi/sag_unified_interface/
├── app.py                    # Main Flask app (72KB)
├── templates/
│   ├── index.html           # Main UI with all tabs
│   └── infrastructure.html
├── static/
│   ├── css/                 # Themes, sidebar styles
│   ├── js/                  # UI logic
│   └── img/                 # Logos, favicons
├── *.py                     # Integration modules
├── *.md                     # Documentation
└── *.sh                     # Utility scripts
```

**Key Features:**
- Event Management Dashboard
- Kanban Board integration (port 3001)
- Cherokee AI Monitoring (port 5555)
- Grafana integration (port 3000)
- IoT Device Management
- Email Intelligence
- Tribe Dashboard (thermal memory, trails, council)
- Hardware CMDB

---

## Post-Setup Tasks

### Add Repository Topics (Optional)

For `llm-gateway`:
- `cherokee-ai`, `llm`, `api-gateway`, `openai-compatible`, `python`, `flask`

For `sag-unified-interface`:
- `cherokee-ai`, `itsm`, `dashboard`, `flask`, `monitoring`, `devops`

### Update CMDB

After repos are created, log to thermal memory:

```bash
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production << 'EOSQL'
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
VALUES (
    'GITHUB-REPOS-CREATED-20251213',
    'GitHub repositories created: llm-gateway and sag-unified-interface. Both pushed with initial commits. LLM Gateway contains OpenAI-compatible API with Council voting. SAG UI contains ITSM frontend with Tribe Dashboard.',
    'FRESH',
    95.0,
    true
);
EOSQL"
```

---

## Troubleshooting

### SSH Key Issues
```bash
# Test GitHub connection
ssh -T git@github.com

# Should see: Hi dereadi! You've successfully authenticated...
```

### Permission Denied
```bash
# Ensure correct key is used
ssh -vT git@github.com 2>&1 | grep "Offering public key"

# Should show: /home/dereadi/.ssh/ganuda_github
```

### Remote Already Exists
```bash
# If remote 'origin' already exists, update it
git remote set-url origin git@github.com:dereadi/REPO_NAME.git
```

---

## Success Criteria

- [ ] llm-gateway repo created on GitHub
- [ ] llm-gateway code pushed successfully
- [ ] sag-unified-interface repo created on GitHub
- [ ] sag-unified-interface code pushed successfully
- [ ] Both repos show commits in GitHub web UI
- [ ] CMDB updated with repo creation

---

FOR SEVEN GENERATIONS - Version control preserves tribal knowledge.
