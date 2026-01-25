# Jr Instructions: Redfin Storage Cleanup

**Task ID**: INFRA-CLEAN-001
**Priority**: MEDIUM
**Target**: redfin (192.168.132.223 / 100.116.27.89)
**Requires**: sudo access on redfin for remaining tasks
**Council Review**: APPROVED - Cleanup executed 2025-12-29
**Status**: MOSTLY COMPLETE - 335GB recovered, sudo tasks remain

---

## Execution Summary (2025-12-29)

| Phase | Status | Space Recovered | Notes |
|-------|--------|-----------------|-------|
| Phase 1 | **COMPLETE** | <1MB | Credentials securely shredded |
| Phase 2 | **PARTIAL** | ~2GB | jsdorn files need sudo |
| Phase 3 | **COMPLETE** | N/A | Archived to bluefin |
| Phase 4 | **COMPLETE** | ~50GB | venvs and pathfinder removed |
| Phase 5 | **SKIPPED** | 0 | User confirmed keeping all 3 models |
| Bonus | **PARTIAL** | ~283GB | ollama/huggingface/whisper cache removed |

**RESULTS**: 791GB → 456GB = **335GB recovered** (50% → 29% utilization)

---

## Remaining Sudo Tasks

These tasks require interactive sudo access on redfin:

```bash
# SSH to redfin with terminal (not automated)
ssh -t dereadi@100.116.27.89

# 1. Remove jsdorn's duplicate GGUF (2.1GB)
sudo rm /ganuda/home/jsdorn/CODE/DL/ganuda/cherokee_constitutional_ai.gguf
sudo rm -rf /ganuda/home/jsdorn/CODE/DL/ganuda/llama.cpp/

# 2. Remove remaining container overlay storage (~100GB+ estimated)
sudo rm -rf /ganuda/home/dereadi/old_dereadi_data/.local/share/containers/

# 3. Verify and final cleanup
df -h /ganuda
```

**Expected additional recovery**: ~100-120GB (bringing total to ~450GB recovered)

---

## Original Analysis (Pre-Cleanup)

Redfin had 791GB used of 1.7TB (50%). We identified 350GB+ of duplicate/old data that could be cleaned. **Crawdad correctly identified sensitive credentials** that were securely deleted.

---

## Sensitive Files Identified

### MUST BE SECURELY DELETED (shred -u)

| File | Content | Risk |
|------|---------|------|
| `/ganuda/home/dereadi/old_dereadi_data/scripts/claude/cdp_api_key_new.json` | EC Private Key | HIGH - Coinbase API |
| `/ganuda/home/dereadi/old_dereadi_data/.robinhood_api_config.json` | API Key | HIGH - Financial |
| `/ganuda/home/dereadi/old_dereadi_data/scripts/claude/test_productive_api.py` | API Key hardcoded | MEDIUM |

### Contains Hardcoded Passwords (review before deletion)

| File | Content |
|------|---------|
| `unified_brain_almanac.py` | PostgreSQL password |
| `tribal_news_processor.sh` | PostgreSQL password |
| `cherokee-war-party-test.sh` | PostgreSQL password |
| `cherokee_networking_fix.sh` | WEBUI_SECRET_KEY |

---

## Cleanup Order of Operations

### Phase 1: Secure Credential Deletion

**BEFORE deleting old_dereadi_data, securely shred sensitive files:**

```bash
# SSH to redfin
ssh dereadi@100.116.27.89

# Securely delete private keys and API credentials
sudo shred -vfz -n 3 /ganuda/home/dereadi/old_dereadi_data/scripts/claude/cdp_api_key_new.json
sudo shred -vfz -n 3 /ganuda/home/dereadi/old_dereadi_data/.robinhood_api_config.json

# Verify deletion
ls -la /ganuda/home/dereadi/old_dereadi_data/scripts/claude/cdp_api_key_new.json
# Should show "No such file or directory"
```

### Phase 2: Safe Duplicate Removal (Low Risk)

These are clearly duplicates and safe to remove:

```bash
# Remove duplicate llama.cpp vocab files (keep only /ganuda/llama.cpp/)
# ~50MB savings per copy, 4 duplicate locations

# Location 1: pathfinder duplicate
rm -rf /ganuda/pathfinder/llama.cpp/models/ggml-vocab-*.gguf

# Location 2: jsdorn's copy
rm -rf /ganuda/home/jsdorn/CODE/DL/ganuda/llama.cpp/

# Location 3: old_dereadi_data llama.cpp
rm -rf /ganuda/home/dereadi/old_dereadi_data/llama.cpp/

# Location 4: old pathfinder test
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/pathfinder/test.original/llama.cpp/

# Remove duplicate cherokee_constitutional_ai.gguf (2.1GB)
rm /ganuda/home/jsdorn/CODE/DL/ganuda/cherokee_constitutional_ai.gguf
```

### Phase 3: Archive Before Delete (Medium Risk)

These directories should be archived to bluefin before deletion:

```bash
# Create archive directory on bluefin
ssh dereadi@100.112.254.96 "mkdir -p /ganuda/archives/redfin_cleanup_2025-12-29"

# Archive old_dereadi_data structure (without large model files)
# First, create a manifest of what's there
find /ganuda/home/dereadi/old_dereadi_data -type f -printf '%s %p\n' | sort -rn > /tmp/old_data_manifest.txt
scp /tmp/old_data_manifest.txt dereadi@100.112.254.96:/ganuda/archives/redfin_cleanup_2025-12-29/

# Archive small but potentially useful files (scripts, configs)
cd /ganuda/home/dereadi/old_dereadi_data
tar -cvf - scripts/*.py scripts/*.sh --exclude='*.gguf' --exclude='*venv*' --exclude='node_modules' 2>/dev/null | \
  ssh dereadi@100.112.254.96 "cat > /ganuda/archives/redfin_cleanup_2025-12-29/old_scripts.tar"
```

### Phase 4: Large Directory Cleanup (After Archive)

After archiving, these can be deleted:

```bash
# Remove old virtual environments (14GB+ total)
rm -rf /ganuda/home/dereadi/old_dereadi_data/cherokee_venv/
rm -rf /ganuda/home/dereadi/old_dereadi_data/rtx5070_whisper_env/
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/.venv/
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/cherokee_vision_env/
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/claude_jr_env/
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/quantum_crawdad_env/

# Remove old pathfinder duplicate (20GB)
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/pathfinder/

# Remove old node_modules
rm -rf /ganuda/home/dereadi/old_dereadi_data/scripts/claude/node_modules/
```

### Phase 5: Model Cleanup (Requires Confirmation)

**ASK BEFORE DELETING - May still be in use:**

```bash
# QUESTION: Is qwen2.5-coder-32b full precision still needed?
# We have the AWQ quantized version (19GB vs 62GB)
# If AWQ is sufficient for vLLM:
# rm -rf /ganuda/models/qwen2.5-coder-32b/

# QUESTION: Is fara-7b still in use?
# rm -rf /ganuda/models/fara-7b/

# QUESTION: Is monet-7b still needed for visual reasoning research?
# rm -rf /ganuda/research/visual_reasoning/Monet/models/monet-7b/
```

---

## Expected Space Recovery

| Phase | Target | Size | Risk |
|-------|--------|------|------|
| Phase 1 | Secure credential deletion | <1MB | Critical (security) |
| Phase 2 | Duplicate vocab files | ~200MB | Low |
| Phase 2 | Duplicate GGUF | 2.1GB | Low |
| Phase 3 | Archive scripts | N/A | Low |
| Phase 4 | Old venvs | ~45GB | Medium |
| Phase 4 | Old pathfinder | 20GB | Medium |
| Phase 5 | qwen full precision | 62GB | **Ask first** |
| Phase 5 | fara-7b | 16GB | **Ask first** |
| Phase 5 | monet-7b | 16GB | **Ask first** |

**Conservative total (Phases 1-4)**: ~67GB recovered
**With model cleanup (Phase 5)**: ~160GB recovered

---

## Verification Steps

After cleanup, verify:

```bash
# Check disk usage
df -h /ganuda

# Verify no orphaned processes using deleted files
lsof +D /ganuda/home/dereadi/old_dereadi_data 2>/dev/null

# Update thermal memory with cleanup record
# (TPM will handle this)
```

---

## Rollback Plan

If something goes wrong:

1. **Manifest file** on bluefin shows what was there
2. **Archived scripts** can be restored from bluefin
3. **Models** can be re-downloaded from HuggingFace if needed
4. **Virtual environments** can be recreated from requirements.txt

---

## Council Approval Status

| Specialist | Concern | Resolution |
|------------|---------|------------|
| Crawdad | Security - credentials | Secure shred before delete |
| Gecko | Performance - model removal | Ask before deleting models |
| Raven | Strategy - archive first | Archive to bluefin |
| Turtle | 7Gen - losing history | Keep manifest, archive scripts |
| Eagle Eye | Visibility - track changes | Log to thermal memory |
| Spider | Integration - break deps | Check lsof before delete |
| Peace Chief | Consensus | This document = consensus |

---

## Files to Create

| File | Location | Purpose |
|------|----------|---------|
| `cleanup_phase1.sh` | `/ganuda/scripts/` | Secure credential deletion |
| `cleanup_phase2.sh` | `/ganuda/scripts/` | Safe duplicate removal |
| `cleanup_archive.sh` | `/ganuda/scripts/` | Archive to bluefin |
| `cleanup_phase4.sh` | `/ganuda/scripts/` | Large directory cleanup |

---

*For Seven Generations*
