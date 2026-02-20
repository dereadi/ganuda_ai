# Jr Instruction: Wave 2 — Veteran Consent Framework + Document Encryption at Rest

**Task**: Add consent tracking, privacy notice, document encryption, and data retention automation
**Priority**: 1 (CRITICAL — council vote #b9d14c90d8f74bcc, PROCEED unanimous 0.9)
**Source**: Long Man Wave 2 DISCOVER/DELIBERATE — Data Sovereignty & PII Protection
**Assigned Jr**: Software Engineer Jr.

## Context

Council DISCOVER phase found:
- Veterans create accounts with NO explicit consent for PII storage or AI processing
- Uploaded documents (DD-214, medical records) are UNENCRYPTED on disk
- No data retention policy — wizard sessions persist forever
- OCAP/CARE frameworks require explicit consent and data lifecycle management
- 38 CFR 3.1000 requires written privacy notice and consent for AI processing

This instruction has 4 fixes. All are council-approved.

---

## Fix 1: Create consent tracking table (database migration)

Create `/ganuda/vetassist/backend/migrations/003_consent_framework.sql`

```sql
-- Veteran consent tracking (OCAP/CARE compliance)
CREATE TABLE IF NOT EXISTS vetassist_user_consent (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    consent_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    withdrawn_at TIMESTAMPTZ,
    ip_hash VARCHAR(64),
    consent_text_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    UNIQUE(user_id, consent_type, consent_version)
);

CREATE INDEX IF NOT EXISTS idx_consent_user ON vetassist_user_consent(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_type ON vetassist_user_consent(consent_type);

-- Data retention tracking
CREATE TABLE IF NOT EXISTS vetassist_data_retention_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    records_affected INTEGER DEFAULT 0,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE vetassist_user_consent IS 'Tracks veteran consent for data storage, AI processing, per OCAP/CARE principles';
COMMENT ON TABLE vetassist_data_retention_log IS 'Audit trail for automated data retention cleanup';
```

---

## Fix 2: Add consent checkbox to registration page

File: `/ganuda/vetassist/frontend/app/(auth)/register/page.tsx`

Add consent state after existing form state:

```
<<<<<<< SEARCH
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
=======
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [consentChecked, setConsentChecked] = useState(false);
>>>>>>> REPLACE
```

Add consent checkbox before the submit button:

```
<<<<<<< SEARCH
            <button
              type="submit"
              disabled={loading}
=======
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="consent"
                checked={consentChecked}
                onChange={(e) => setConsentChecked(e.target.checked)}
                className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                required
              />
              <label htmlFor="consent" className="text-xs text-gray-600 leading-relaxed">
                I consent to VetAssist securely storing my personal information (name, service dates, disability rating) for the purpose of supporting my disability claims. My data is protected under Cherokee Nation data sovereignty and will never be shared outside the federation. I can request deletion of my data at any time.
              </label>
            </div>

            <button
              type="submit"
              disabled={loading || !consentChecked}
>>>>>>> REPLACE
```

Add consent to the registration API call payload:

```
<<<<<<< SEARCH
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName,
        }),
=======
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          first_name: formData.firstName,
          last_name: formData.lastName,
          consent_granted: consentChecked,
        }),
>>>>>>> REPLACE
```

---

## Fix 3: Backend — Record consent on registration

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

Add consent recording after successful user creation. Find the INSERT INTO users section and add consent storage after it:

```
<<<<<<< SEARCH
        return {"message": "Registration successful", "user_id": str(user_id)}
=======
        # Record consent (OCAP/CARE compliance)
        if data.get('consent_granted'):
            import hashlib
            consent_text = "I consent to VetAssist securely storing my personal information for disability claims support."
            try:
                cur.execute("""
                    INSERT INTO vetassist_user_consent (user_id, consent_type, consent_version, ip_hash, consent_text_hash)
                    VALUES (%s, 'data_storage', '1.0', %s, %s)
                    ON CONFLICT (user_id, consent_type, consent_version) DO NOTHING
                """, (
                    str(user_id),
                    hashlib.sha256(request.client.host.encode()).hexdigest() if request.client else None,
                    hashlib.sha256(consent_text.encode()).hexdigest()
                ))
                conn.commit()
            except Exception as e:
                print(f"[CONSENT] Failed to record consent: {e}")

        return {"message": "Registration successful", "user_id": str(user_id)}
>>>>>>> REPLACE
```

---

## Fix 4: Document encryption at rest

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

Add encryption import near top of file:

```
<<<<<<< SEARCH
from app.services.ocr_service import OCRService
=======
from app.services.ocr_service import OCRService
from cryptography.fernet import Fernet
>>>>>>> REPLACE
```

In the file upload handler, encrypt the file after saving to disk. Find where the uploaded file is written:

```
<<<<<<< SEARCH
            # Save file to disk
            file_path = os.path.join(upload_dir, file_uuid + ext)
            with open(file_path, "wb") as f:
                f.write(await file.read())
=======
            # Save file to disk (encrypted at rest)
            file_path = os.path.join(upload_dir, file_uuid + ext)
            raw_bytes = await file.read()

            # Generate per-session encryption key if not exists
            cur.execute("""
                SELECT metadata->>'encryption_key' FROM vetassist_wizard_sessions
                WHERE session_id = %s
            """, (session_id,))
            key_row = cur.fetchone()
            if key_row and key_row[0]:
                session_key = key_row[0].encode()
            else:
                session_key = Fernet.generate_key()
                cur.execute("""
                    UPDATE vetassist_wizard_sessions
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                    WHERE session_id = %s
                """, (json.dumps({"encryption_key": session_key.decode()}), session_id))
                conn.commit()

            # Encrypt and write
            fernet = Fernet(session_key)
            encrypted_bytes = fernet.encrypt(raw_bytes)
            with open(file_path, "wb") as f:
                f.write(encrypted_bytes)

            # Store unencrypted copy in memory for immediate processing
            # (will be discarded after OCR extraction)
>>>>>>> REPLACE
```

Update the OCR processing to use the raw bytes (already in memory) instead of reading from encrypted file:

```
<<<<<<< SEARCH
            # Process document
            ocr_service = OCRService()
            result = await ocr_service.process_document(file_path, ext)
=======
            # Process document from raw bytes (file on disk is encrypted)
            import tempfile
            ocr_service = OCRService()
            with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
                tmp.write(raw_bytes)
                tmp.flush()
                result = await ocr_service.process_document(tmp.name, ext)
            del raw_bytes  # Clear unencrypted bytes from memory
>>>>>>> REPLACE
```

---

## Verification

1. **Consent**: Register a new account — consent checkbox must be checked before submit button enables. Check `vetassist_user_consent` table for the record.
2. **Encryption**: Upload a DD-214 to a wizard session. Check the file on disk — it should be Fernet-encrypted (starts with `gAAAAA`). The `vetassist_wizard_sessions.metadata` should contain `encryption_key`.
3. **OCR still works**: Despite encryption at rest, OCR extraction should still succeed because it processes from raw bytes in memory before encrypting to disk.
4. **Privacy notice**: The consent text should be visible during registration and accurately describe data handling.
