#!/bin/bash
# =============================================================================
# VetAssist Redfin Restore - JR-VETASSIST-BACKEND-REDFIN-RESTORE-JAN30-2026
# Run as: sudo bash /ganuda/scripts/vetassist_redfin_restore.sh
# =============================================================================
set -e

echo "=========================================="
echo " VetAssist Redfin Restore - Jan 30 2026"
echo "=========================================="

# ---------- TASK 5: Create upload directory ----------
echo ""
echo "[1/5] Creating upload directory..."
mkdir -p /ganuda/vetassist/uploads
chown dereadi:dereadi /ganuda/vetassist/uploads
echo "  OK: /ganuda/vetassist/uploads created"

# ---------- TASK 1: Add file upload/delete endpoints to dashboard.py ----------
echo ""
echo "[2/5] Adding file upload/delete endpoints to dashboard.py..."

DASHBOARD="/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py"
cp "$DASHBOARD" "${DASHBOARD}.backup_$(date +%Y%m%d_%H%M%S)"

# Patch imports — add os, uuid, UploadFile, File, Form after existing imports
python3 << 'PYEOF'
import re

path = "/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py"
with open(path, "r") as f:
    content = f.read()

# Add new imports after existing imports block
old_imports = "from app.core.database_config import get_db_connection"
new_imports = """from app.core.database_config import get_db_connection
import os
import uuid
from fastapi import UploadFile, File as FastAPIFile, Form"""

if "import os" not in content:
    content = content.replace(old_imports, new_imports)

# Add the two new endpoints at the end of the file
new_endpoints = '''

@router.post("/{veteran_id}/files")
async def upload_file(
    veteran_id: str,
    file: UploadFile = FastAPIFile(...),
    category: str = Form(default="other"),
    description: str = Form(default=""),
    current_user: dict = Depends(get_current_user)
):
    """Upload an evidence file for a veteran's dashboard."""
    MAX_SIZE = 25 * 1024 * 1024
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 25MB.")

    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed.")

    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    stored_name = f"{uuid.uuid4()}{ext}"
    upload_dir = os.path.join("/ganuda/vetassist/uploads", veteran_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)

    with open(file_path, "wb") as out:
        out.write(content_bytes)

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            dashboard_session_id = f"dashboard-{veteran_id}"
            cur.execute("""
                INSERT INTO vetassist_wizard_sessions (session_id, veteran_id, wizard_type, status, current_step, answers)
                VALUES (%s, %s, \'dashboard\', \'active\', 0, \'{}\')
                ON CONFLICT (session_id) DO NOTHING
            """, (dashboard_session_id, veteran_id))
            cur.execute("""
                INSERT INTO vetassist_wizard_files
                    (session_id, original_name, stored_name, mime_type, file_size, category, file_path, deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, false)
                RETURNING id, original_name as filename, mime_type as file_type, category,
                          created_at as uploaded_at, file_size
            """, (dashboard_session_id, file.filename, stored_name, file.content_type,
                  len(content_bytes), category, file_path))
            result = cur.fetchone()
            conn.commit()

        file_data = dict(result)
        if file_data.get("uploaded_at"):
            file_data["uploaded_at"] = str(file_data["uploaded_at"])
        return {"status": "uploaded", "file": file_data}
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.delete("/{veteran_id}/files/{file_id}")
def delete_file(
    veteran_id: str,
    file_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Soft-delete an evidence file from the dashboard."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT f.id, f.file_path
                FROM vetassist_wizard_files f
                INNER JOIN vetassist_wizard_sessions s ON f.session_id::text = s.session_id::text
                WHERE f.id = %s AND s.veteran_id = %s AND NOT f.deleted
            """, (file_id, veteran_id))
            file_record = cur.fetchone()
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            cur.execute("UPDATE vetassist_wizard_files SET deleted = true WHERE id = %s", (file_id,))
            conn.commit()
        return {"status": "deleted", "file_id": file_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass
'''

if "upload_file" not in content:
    content = content.rstrip() + "\n" + new_endpoints

with open(path, "w") as f:
    f.write(content)

print("  OK: dashboard.py patched with file upload/delete endpoints")
PYEOF

# ---------- TASK 2: Revert Caddy to localhost:8001 ----------
echo ""
echo "[3/5] Reverting Caddy proxy to localhost:8001..."

CADDY="/etc/caddy/Caddyfile"
cp "$CADDY" "${CADDY}.backup_$(date +%Y%m%d_%H%M%S)"
sed -i 's|reverse_proxy 192.168.132.222:8001|reverse_proxy localhost:8001|' "$CADDY"
systemctl reload caddy
echo "  OK: Caddy reverted to localhost:8001 and reloaded"

# ---------- TASK 3: Fix frontend auth headers ----------
echo ""
echo "[4/5] Fixing frontend component auth headers..."

# --- FileDropZone.tsx ---
FDZ="/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx"
cp "$FDZ" "${FDZ}.backup_$(date +%Y%m%d_%H%M%S)"
python3 << 'PYEOF'
path = "/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx"
with open(path, "r") as f:
    content = f.read()

# Patch the upload fetch
old_upload = """const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
          method: 'POST',
          body: formData,
        });"""

new_upload = """const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files`, {
          method: 'POST',
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
          body: formData,
        });"""

if "auth_token" not in content:
    content = content.replace(old_upload, new_upload)

# Patch the delete fetch
old_delete = """const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
        method: 'DELETE',
      });"""

new_delete = """const delToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          ...(delToken ? { 'Authorization': `Bearer ${delToken}` } : {}),
        },
      });"""

if "delToken" not in content:
    content = content.replace(old_delete, new_delete)

with open(path, "w") as f:
    f.write(content)
print("  OK: FileDropZone.tsx patched")
PYEOF

# --- ScratchpadEditor.tsx ---
SCR="/ganuda/vetassist/frontend/components/dashboard/ScratchpadEditor.tsx"
cp "$SCR" "${SCR}.backup_$(date +%Y%m%d_%H%M%S)"
python3 << 'PYEOF'
path = "/ganuda/vetassist/frontend/components/dashboard/ScratchpadEditor.tsx"
with open(path, "r") as f:
    content = f.read()

old_save = """const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: textContent }),
      });"""

new_save = """const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/dashboard/${veteranId}/scratchpad`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content: textContent }),
      });"""

if "auth_token" not in content:
    content = content.replace(old_save, new_save)

with open(path, "w") as f:
    f.write(content)
print("  OK: ScratchpadEditor.tsx patched")
PYEOF

# --- ResearchPanel.tsx ---
RES="/ganuda/vetassist/frontend/components/dashboard/ResearchPanel.tsx"
cp "$RES" "${RES}.backup_$(date +%Y%m%d_%H%M%S)"
python3 << 'PYEOF'
path = "/ganuda/vetassist/frontend/components/dashboard/ResearchPanel.tsx"
with open(path, "r") as f:
    content = f.read()

# Patch fetchResults
old_fetch = """const response = await fetch(`${apiUrl}/research/results/${sessionId}`);"""
new_fetch = """const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/research/results/${sessionId}`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      });"""

if "auth_token" not in content:
    content = content.replace(old_fetch, new_fetch)

# Patch handleSubmit
old_submit = """const response = await fetch(`${apiUrl}/research/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },"""

new_submit = """const submitToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/research/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(submitToken ? { 'Authorization': `Bearer ${submitToken}` } : {}),
        },"""

if "submitToken" not in content:
    content = content.replace(old_submit, new_submit)

with open(path, "w") as f:
    f.write(content)
print("  OK: ResearchPanel.tsx patched")
PYEOF

# ---------- TASK 4: Restart backend + rebuild frontend ----------
echo ""
echo "[5/5] Restarting backend and rebuilding frontend..."

# Restart backend
systemctl restart vetassist-backend
sleep 2
echo "  Backend restarted"

# Verify backend health
HEALTH=$(curl -s -m 5 http://localhost:8001/health 2>/dev/null || echo "FAIL")
echo "  Backend health: $HEALTH"

# Rebuild frontend
echo "  Building frontend (this may take a moment)..."
cd /ganuda/vetassist/frontend
sudo -u dereadi npm run build 2>&1 | tail -5

# Restart Next.js
pkill -f 'next-server' 2>/dev/null || true
sleep 1
sudo -u dereadi bash -c 'cd /ganuda/vetassist/frontend && nohup npm start -- -p 3000 > /ganuda/logs/vetassist_frontend.log 2>&1 &'
sleep 3
echo "  Frontend restarted on port 3000"

# ---------- Final verification ----------
echo ""
echo "=========================================="
echo " Verification"
echo "=========================================="
echo ""

# Backend health
echo "Backend health:"
curl -s -m 5 http://localhost:8001/health 2>/dev/null || echo "  FAILED"
echo ""

# Caddy proxy
echo "Caddy proxy test:"
curl -s -m 5 -k --resolve vetassist.ganuda.us:443:127.0.0.1 https://vetassist.ganuda.us/health 2>/dev/null || echo "  FAILED"
echo ""

# Check new endpoint exists in docs
echo "File upload endpoint exists:"
curl -s -m 5 http://localhost:8001/api/docs 2>/dev/null | grep -q "files" && echo "  YES" || echo "  NOT FOUND IN DOCS"

echo ""
echo "=========================================="
echo " DONE. Test at https://vetassist.ganuda.us/dashboard"
echo "=========================================="
