# Jr Instruction: Drift Detection Phase 1B — Write-Path Checksum Integration

**Task:** JR-DRIFT-PHASE1B-CHECKSUMS
**Priority:** P0
**Assigned:** Software Engineer Jr.
**Depends On:** JR-DRIFT-PHASE1A-SQL
**Council Vote:** #8367 — APPROVED

## Objective

Add SHA-256 content checksum computation to all 3 thermal memory write paths:
1. Telegram bot `seed_memory()`
2. Research worker `store_in_thermal_memory()`
3. VLM relationship storer `store_entity_as_memory()`

## Step 1: Telegram Bot — seed_memory()

**File:** `/ganuda/telegram_bot/thermal_memory_methods.py`

**Applied by TPM.** The checksum write-path integration has been applied directly.

## Step 2: Research Worker — store_in_thermal_memory()

**File:** `/ganuda/services/research_worker.py`

**Applied by TPM.** The checksum write-path integration has been applied directly.

## Step 3: VLM Relationship Storer — store_entity_as_memory()

**File:** `/ganuda/lib/vlm_relationship_storer.py`

**Applied by TPM.** The checksum write-path integration has been applied directly.

## Validation

After applying all changes:

```bash
# Verify syntax on all 3 files
python3 -c "import py_compile; py_compile.compile('/ganuda/telegram_bot/thermal_memory_methods.py', doraise=True); print('telegram OK')"
python3 -c "import py_compile; py_compile.compile('/ganuda/services/research_worker.py', doraise=True); print('research OK')"
python3 -c "import py_compile; py_compile.compile('/ganuda/lib/vlm_relationship_storer.py', doraise=True); print('vlm OK')"
```

Then test by inserting a memory and verifying checksum:
```sql
-- After next telegram interaction or research job, verify:
SELECT id, LEFT(original_content, 50), content_checksum,
       content_checksum = encode(sha256(convert_to(original_content, 'UTF8')), 'hex') AS checksum_valid
FROM thermal_memory_archive
ORDER BY created_at DESC LIMIT 3;
```
