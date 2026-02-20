# Jr Instruction: VetAssist File View, Edit & Delete — Dashboard Evidence Files

**Task ID**: VETASSIST-FILE-OPS-001
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false

## Context

Veterans upload evidence files (DD-214, medical records, nexus letters) to their dashboard but cannot open/view them, edit metadata, or easily find the delete button. The files show as plain text with only a tiny X to delete. Joe uploaded a document and can't click on it.

**Backend**: Files stored at `/ganuda/vetassist/uploads/{veteran_id}/{uuid}.ext`. Upload and soft-delete endpoints exist. No download/serve endpoint. No edit endpoint.

**Frontend**: FileDropZone component lists files but filenames are not clickable. No view/download. No edit. Delete is a small X icon.

## Step 1: Add file download endpoint to dashboard.py

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

<<<<<<< SEARCH
@router.delete("/{veteran_id}/files/{file_id}")
=======
@router.get("/{veteran_id}/files/{file_id}")
def get_file(
    veteran_id: str,
    file_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Serve an uploaded evidence file for viewing/download."""
    from fastapi.responses import FileResponse
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT f.id, f.file_path, f.original_name, f.mime_type
                FROM vetassist_wizard_files f
                INNER JOIN vetassist_wizard_sessions s ON f.session_id::text = s.session_id::text
                WHERE f.id = %s AND s.veteran_id = %s AND NOT f.deleted
            """, (file_id, veteran_id))
            file_record = cur.fetchone()
        conn.close()

        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = file_record['file_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=file_path,
            filename=file_record['original_name'],
            media_type=file_record['mime_type'] or 'application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")


@router.patch("/{veteran_id}/files/{file_id}")
def update_file(
    veteran_id: str,
    file_id: int,
    update: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update file metadata (category, description)."""
    allowed_fields = {'category', 'description'}
    updates = {k: v for k, v in update.items() if k in allowed_fields}
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verify ownership
            cur.execute("""
                SELECT f.id FROM vetassist_wizard_files f
                INNER JOIN vetassist_wizard_sessions s ON f.session_id::text = s.session_id::text
                WHERE f.id = %s AND s.veteran_id = %s AND NOT f.deleted
            """, (file_id, veteran_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="File not found")

            set_clauses = []
            values = []
            for field, value in updates.items():
                set_clauses.append(f"{field} = %s")
                values.append(value)
            values.append(file_id)

            cur.execute(f"""
                UPDATE vetassist_wizard_files
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id, original_name as filename, category
            """, values)
            result = cur.fetchone()
            conn.commit()
        conn.close()
        return {"status": "updated", "file": dict(result)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")


@router.delete("/{veteran_id}/files/{file_id}")
>>>>>>> REPLACE

## Step 2: Update FileDropZone with clickable files, edit, and visible delete

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

<<<<<<< SEARCH
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
=======
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, Eye, Pencil, Trash2, Check } from 'lucide-react';
>>>>>>> REPLACE

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

<<<<<<< SEARCH
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
=======
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editCategory, setEditCategory] = useState('');
>>>>>>> REPLACE

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

<<<<<<< SEARCH
  const deleteFile = async (fileId: number) => {
    try {
      const delToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          ...(delToken ? { 'Authorization': `Bearer ${delToken}` } : {}),
        },
      });
      if (response.ok) {
        setFiles(prev => prev.filter(f => f.id !== fileId));
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };
=======
  const viewFile = (fileId: number) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    window.open(`${apiUrl}/dashboard/${veteranId}/files/${fileId}?token=${token}`, '_blank');
  };

  const deleteFile = async (fileId: number) => {
    if (!confirm('Delete this file? This cannot be undone.')) return;
    try {
      const delToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          ...(delToken ? { 'Authorization': `Bearer ${delToken}` } : {}),
        },
      });
      if (response.ok) {
        setFiles(prev => prev.filter(f => f.id !== fileId));
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const updateFile = async (fileId: number, category: string) => {
    try {
      const updToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const response = await fetch(`${apiUrl}/dashboard/${veteranId}/files/${fileId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(updToken ? { 'Authorization': `Bearer ${updToken}` } : {}),
        },
        body: JSON.stringify({ category }),
      });
      if (response.ok) {
        setFiles(prev => prev.map(f => f.id === fileId ? { ...f, category } : f));
        setEditingId(null);
      }
    } catch (error) {
      console.error('Update failed:', error);
    }
  };
>>>>>>> REPLACE

File: `/ganuda/vetassist/frontend/components/dashboard/FileDropZone.tsx`

<<<<<<< SEARCH
            <ul className="divide-y divide-gray-100" role="list" aria-label="Uploaded files">
              {files.map(file => (
                <li key={file.id} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-2">
                    <File className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                      <p className="text-xs text-gray-500">
                        {CATEGORIES.find(c => c.value === file.category)?.label || file.category}
                        {' · '}
                        {formatFileSize(file.file_size)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteFile(file.id)}
                    className="p-1 text-gray-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
                    aria-label={`Delete ${file.filename}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
=======
            <ul className="divide-y divide-gray-100" role="list" aria-label="Uploaded files">
              {files.map(file => (
                <li key={file.id} className="py-3">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => viewFile(file.id)}
                      className="flex items-center gap-2 text-left hover:text-blue-600 transition group flex-1 min-w-0"
                      aria-label={`View ${file.filename}`}
                    >
                      <File className="h-5 w-5 text-gray-400 group-hover:text-blue-500 flex-shrink-0" aria-hidden="true" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 truncate">
                          {file.filename}
                        </p>
                        {editingId === file.id ? (
                          <div className="flex items-center gap-1 mt-1">
                            <select
                              value={editCategory}
                              onChange={(e) => setEditCategory(e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="text-xs border rounded px-1 py-0.5"
                            >
                              {CATEGORIES.map(cat => (
                                <option key={cat.value} value={cat.value}>{cat.label}</option>
                              ))}
                            </select>
                            <button
                              onClick={(e) => { e.stopPropagation(); updateFile(file.id, editCategory); }}
                              className="p-0.5 text-green-600 hover:text-green-700"
                              aria-label="Save category"
                            >
                              <Check className="h-3 w-3" />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); setEditingId(null); }}
                              className="p-0.5 text-gray-400 hover:text-gray-600"
                              aria-label="Cancel edit"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ) : (
                          <p className="text-xs text-gray-500">
                            {CATEGORIES.find(c => c.value === file.category)?.label || file.category}
                            {' · '}
                            {formatFileSize(file.file_size)}
                          </p>
                        )}
                      </div>
                    </button>
                    <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                      <button
                        onClick={() => viewFile(file.id)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 rounded hover:bg-blue-50 transition"
                        aria-label={`Open ${file.filename}`}
                        title="View file"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => { setEditingId(file.id); setEditCategory(file.category); }}
                        className="p-1.5 text-gray-400 hover:text-amber-600 rounded hover:bg-amber-50 transition"
                        aria-label={`Edit ${file.filename}`}
                        title="Edit category"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteFile(file.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded hover:bg-red-50 transition"
                        aria-label={`Delete ${file.filename}`}
                        title="Delete file"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
>>>>>>> REPLACE

## Verification

1. Build: `cd /ganuda/vetassist/frontend && npm run build`
2. Upload a PDF to the dashboard
3. Click the filename — should open in a new tab
4. Click the eye icon — same behavior
5. Click the pencil icon — category dropdown appears inline
6. Change category, click checkmark — updates
7. Click the trash icon — confirmation prompt, then removes

## Manual Steps (TPM on redfin)

1. Restart VetAssist backend after Jr applies changes
2. Rebuild and restart VetAssist frontend
3. Test with Joe's account
