# Dependency Change Log

All dependency changes across Cherokee AI Federation nodes.

**Security Principle:** CIA Triad (Confidentiality, Integrity, Availability)

---

## 2026-01-27

### redfin - PyTorch Downgrade (AVAILABILITY FIX)

**Incident:** vLLM service in restart loop (517 attempts)
**Root Cause:** PyTorch upgraded to dev/nightly (2.11.0.dev) broke ABI compatibility with vLLM 0.11.2
**Impact:** Council endpoint unavailable, LLM Gateway degraded

**Changes:**
| Package | Before | After |
|---------|--------|-------|
| torch | 2.11.0.dev20260119+cu128 | 2.9.0 |
| torchvision | dev | 0.24.0 |
| torchaudio | dev | 2.9.0 |
| vllm | 0.11.2 | 0.11.2 (reinstalled) |

**JR:** JR-VLLM-PYTORCH-STABLE-JAN27-2026

**Lesson Learned:** Never use nightly/dev PyTorch in production. torch/vllm are ABI-coupled.

---

### goldfin - PII Database Setup

**Change:** Installed pgcrypto extension, created PII tables
**Purpose:** VetAssist veteran data isolation
**Tables Created:**
- vetassist_wizard_sessions
- vetassist_files

**JR:** JR-VETASSIST-GOLDFIN-PII-SETUP-JAN27-2026

---

### All Nodes - Dependency Tracking System

**Change:** Created dependency manifest files
**Files:**
- /ganuda/config/dependencies/redfin.yaml
- /ganuda/config/dependencies/bluefin.yaml
- /ganuda/config/dependencies/greenfin.yaml
- /ganuda/config/dependencies/goldfin.yaml

**JR:** JR-DEPENDENCY-TRACKING-SYSTEM-JAN27-2026

---

## Template for Future Entries

```markdown
### <node> - <brief description>

**Change:** <what changed>
**Reason:** <why>
**Impact:** <CIA implications>

| Package | Before | After |
|---------|--------|-------|
| pkg | x.x.x | y.y.y |

**JR:** JR-XXX-YYYY-MM-DD
**Tested:** [yes/no]
**Rollback:** <plan>
```

---

FOR SEVEN GENERATIONS
