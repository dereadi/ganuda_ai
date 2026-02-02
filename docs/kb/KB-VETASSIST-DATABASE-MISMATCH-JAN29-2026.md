# KB: VetAssist Research Data Not Showing - Database Mismatch

**KB ID:** KB-VETASSIST-DATABASE-MISMATCH-JAN29-2026
**Created:** January 29, 2026
**Status:** RESOLVED

---

## Symptoms

- VetAssist dashboard shows empty research history
- User submits research queries but results never appear
- File watcher logs show "Stored result" but data not visible

---

## Root Cause

The `research_file_watcher.py` was configured to write to `triad_federation` database while the VetAssist dashboard queries `zammad_production`.

**Wrong config (line 39):**
```python
DB_CONFIG = {
    'database': 'triad_federation',  # WRONG!
    ...
}
```

**Correct config:**
```python
DB_CONFIG = {
    'database': 'zammad_production',  # Fixed Jan 29, 2026
    ...
}
```

---

## Database Architecture

VetAssist uses `zammad_production` as the primary database:
- `vetassist_wizard_sessions` - claim wizard data
- `vetassist_wizard_files` - uploaded files
- `vetassist_research_results` - AI research results
- `vetassist_scratchpads` - user notes

The `triad_federation` database is for:
- Cherokee AI Triad operations
- Council votes
- Agent coordination

---

## Resolution

1. **Fixed file watcher**: `/ganuda/services/research_file_watcher.py` line 39
   - Changed `database: 'triad_federation'` to `database: 'zammad_production'`

2. **Fixed backend .env**: `/ganuda/vetassist/backend/.env` lines 5, 8
   - Changed `DATABASE_URL` and `DB_NAME` from `triad_federation` to `zammad_production`

3. **Migrated orphaned data** from triad_federation to zammad_production:
```python
# Data was exported from triad_federation and inserted into zammad_production
# 6 records migrated for veteran aa549d11-e4f5-4022-9b62-8c127b6a6213
```

3. **Restarts required**:
```bash
sudo systemctl restart research-file-watcher
sudo systemctl restart vetassist-backend
```

---

## Prevention

- Add database consistency checks to deployment scripts
- Include database name in log messages for debugging
- Consider environment variables for database config to prevent hardcoding

---

## Related Files

- `/ganuda/services/research_file_watcher.py` - File watcher (fixed)
- `/ganuda/services/research_worker.py` - Research worker (separate service)
- `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py` - Dashboard API
- `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py` - Research trigger

---

FOR SEVEN GENERATIONS
