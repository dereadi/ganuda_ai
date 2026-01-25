# JR Instruction: VetAssist Claim Workbench with Goldfin PII Vault

## Metadata
```yaml
task_id: vetassist_claim_workbench
priority: 1
assigned_to: VetAssist Jr. + Infrastructure Jr.
target: frontend + backend + goldfin
estimated_effort: large (2-3 weeks)
dependencies:
  - Goldfin PostgreSQL (VLAN 20)
  - Presidio PII integration
  - User authentication
```

## Overview

The Claim Workbench is a veteran's private workspace to organize their VA disability claim. Documents containing PII are stored encrypted on goldfin (VLAN 20), while metadata lives on bluefin.

**Key Principle**: We're a notebook, not a law firm. Veterans do their own work; we provide tools and education.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         REDFIN                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    VetAssist Backend                      │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │ Document   │  │ Workbench  │  │ Presidio           │  │   │
│  │  │ Service    │  │ Service    │  │ PII Scanner        │  │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────────┬──────────┘  │   │
│  └────────┼───────────────┼───────────────────┼─────────────┘   │
└───────────┼───────────────┼───────────────────┼─────────────────┘
            │               │                   │
    ┌───────┴───────┐       │           ┌───────┴───────┐
    ▼               ▼       ▼           ▼               │
┌────────┐    ┌──────────────────┐    ┌─────────────────┴─┐
│GOLDFIN │    │     BLUEFIN      │    │   PII TOKEN MAP   │
│PII Vault│    │    PostgreSQL    │    │   (on goldfin)    │
│VLAN 20 │    │                  │    │                   │
│        │    │ - user_claims    │    │ SSN → tok_abc123  │
│Documents│    │ - user_documents │    │ DOB → tok_def456  │
│Encrypted│    │   (metadata)     │    │ Addr → tok_ghi789 │
│        │    │ - statements     │    │                   │
└────────┘    │ - checklists     │    └───────────────────┘
              └──────────────────┘
```

## Database Schema

### Bluefin (Main Database)

```sql
-- Claim workbench projects
CREATE TABLE user_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    claim_type VARCHAR(50) NOT NULL,  -- 'new', 'increase', 'supplemental', 'hlr', 'appeal'
    status VARCHAR(50) DEFAULT 'drafting',  -- 'drafting', 'ready', 'submitted', 'pending', 'decided'
    conditions JSONB DEFAULT '[]',  -- [{name, rating, bilateral}]
    notes_ref UUID,  -- reference to goldfin encrypted notes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document metadata (actual files on goldfin)
CREATE TABLE user_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES user_claims(id) ON DELETE SET NULL,

    -- Metadata (safe to store on bluefin)
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- 'pdf', 'image', 'doc'
    file_size_bytes INT NOT NULL,
    category VARCHAR(50),  -- 'medical', 'service_record', 'buddy_statement', 'personal', 'other'
    description TEXT,

    -- Goldfin reference (no actual file here)
    goldfin_document_id UUID NOT NULL,  -- FK to goldfin.documents
    checksum_sha256 VARCHAR(64) NOT NULL,  -- verify integrity

    -- PII detection results
    pii_detected BOOLEAN DEFAULT FALSE,
    pii_types JSONB,  -- ['SSN', 'DOB', 'ADDRESS']

    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Evidence checklists (no PII)
CREATE TABLE claim_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES user_claims(id) ON DELETE CASCADE,
    condition VARCHAR(100) NOT NULL,
    items JSONB NOT NULL,  -- [{id, label, required, checked, checked_at}]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Claim timeline milestones
CREATE TABLE claim_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES user_claims(id) ON DELETE CASCADE,
    milestone VARCHAR(100) NOT NULL,  -- 'intent_to_file', 'submitted', 'cp_exam', 'decision'
    milestone_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_user_claims_user ON user_claims(user_id);
CREATE INDEX idx_user_documents_user ON user_documents(user_id);
CREATE INDEX idx_user_documents_claim ON user_documents(claim_id);
```

### Goldfin (PII Vault - VLAN 20)

```sql
-- Encrypted document storage
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,  -- no FK, different database

    -- Encrypted content
    encrypted_content BYTEA NOT NULL,  -- AES-256-GCM encrypted
    encryption_key_id VARCHAR(100) NOT NULL,  -- key reference
    iv BYTEA NOT NULL,  -- initialization vector

    -- Metadata
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW()
);

-- PII token vault
CREATE TABLE pii_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    pii_type VARCHAR(50) NOT NULL,  -- 'SSN', 'VA_FILE_NUMBER', 'DOB', 'ADDRESS', 'PHONE'
    token VARCHAR(100) NOT NULL UNIQUE,  -- 'tok_abc123...'
    encrypted_value BYTEA NOT NULL,  -- actual PII, encrypted

    created_at TIMESTAMP DEFAULT NOW()
);

-- Encrypted notes/scratch pads
CREATE TABLE encrypted_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    claim_ref UUID,  -- reference to bluefin claim

    encrypted_content BYTEA NOT NULL,
    encryption_key_id VARCHAR(100) NOT NULL,
    iv BYTEA NOT NULL,

    updated_at TIMESTAMP DEFAULT NOW()
);

-- Personal statement drafts (may contain PII)
CREATE TABLE personal_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    claim_ref UUID,
    condition VARCHAR(100),

    -- Wizard answers (encrypted, may have PII)
    encrypted_answers BYTEA,

    -- Generated draft (encrypted)
    encrypted_draft BYTEA,

    encryption_key_id VARCHAR(100) NOT NULL,
    iv BYTEA NOT NULL,
    version INT DEFAULT 1,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Access audit log
CREATE TABLE document_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    document_id UUID,
    action VARCHAR(50) NOT NULL,  -- 'upload', 'view', 'download', 'delete'
    ip_address INET,
    user_agent TEXT,
    accessed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_pii_tokens_user ON pii_tokens(user_id);
CREATE INDEX idx_pii_tokens_token ON pii_tokens(token);
CREATE INDEX idx_access_log_user ON document_access_log(user_id);
```

## API Endpoints

### Workbench API (redfin → bluefin)

```
# Claims
POST   /api/v1/workbench/claims              - Create new claim project
GET    /api/v1/workbench/claims              - List user's claims
GET    /api/v1/workbench/claims/{id}         - Get claim details
PUT    /api/v1/workbench/claims/{id}         - Update claim
DELETE /api/v1/workbench/claims/{id}         - Delete claim (cascades)

# Checklists
GET    /api/v1/workbench/claims/{id}/checklist     - Get evidence checklist
PUT    /api/v1/workbench/claims/{id}/checklist     - Update checklist items
POST   /api/v1/workbench/claims/{id}/checklist/generate - Auto-generate from conditions

# Timeline
GET    /api/v1/workbench/claims/{id}/timeline      - Get milestones
POST   /api/v1/workbench/claims/{id}/timeline      - Add milestone
PUT    /api/v1/workbench/claims/{id}/timeline/{mid} - Update milestone
```

### Document API (redfin → goldfin via Tailscale)

```
# Documents
POST   /api/v1/documents/upload             - Upload document (multipart)
GET    /api/v1/documents                    - List user's documents
GET    /api/v1/documents/{id}               - Get document metadata
GET    /api/v1/documents/{id}/download      - Download decrypted file
DELETE /api/v1/documents/{id}               - Delete document

# PII
GET    /api/v1/documents/{id}/pii           - Get PII detection results
POST   /api/v1/documents/{id}/pii/reveal    - Temporarily reveal PII (logged)
```

### Notes API (redfin → goldfin)

```
GET    /api/v1/workbench/claims/{id}/notes  - Get decrypted notes
PUT    /api/v1/workbench/claims/{id}/notes  - Save encrypted notes
```

### Personal Statement API

```
POST   /api/v1/statements                   - Start new statement wizard
GET    /api/v1/statements/{id}              - Get statement draft
PUT    /api/v1/statements/{id}/answers      - Save wizard answers
POST   /api/v1/statements/{id}/generate     - Generate draft from answers
PUT    /api/v1/statements/{id}/draft        - Edit draft directly
GET    /api/v1/statements/{id}/export       - Export as PDF/DOCX
```

## Document Upload Flow

```python
# /api/v1/documents/upload

async def upload_document(
    file: UploadFile,
    claim_id: Optional[UUID],
    category: str,
    user: User = Depends(get_current_user)
):
    # 1. Read file content
    content = await file.read()

    # 2. Scan for PII with Presidio
    pii_results = await pii_service.scan_document(content, file.content_type)

    # 3. Generate encryption key (per-document)
    key_id, key = await key_service.generate_document_key(user.id)

    # 4. Encrypt content
    encrypted, iv = encrypt_aes_gcm(content, key)

    # 5. Store on goldfin
    goldfin_doc = await goldfin_client.store_document(
        user_id=user.id,
        encrypted_content=encrypted,
        iv=iv,
        key_id=key_id,
        filename=file.filename,
        mime_type=file.content_type
    )

    # 6. Tokenize any detected PII
    if pii_results.entities:
        for entity in pii_results.entities:
            token = generate_token()
            await goldfin_client.store_pii_token(
                user_id=user.id,
                document_id=goldfin_doc.id,
                pii_type=entity.type,
                token=token,
                encrypted_value=encrypt(entity.value, key)
            )

    # 7. Store metadata on bluefin
    doc_metadata = UserDocument(
        user_id=user.id,
        claim_id=claim_id,
        filename=file.filename,
        file_type=get_file_type(file.content_type),
        file_size_bytes=len(content),
        category=category,
        goldfin_document_id=goldfin_doc.id,
        checksum_sha256=hashlib.sha256(content).hexdigest(),
        pii_detected=bool(pii_results.entities),
        pii_types=[e.type for e in pii_results.entities]
    )

    # 8. Audit log
    await goldfin_client.log_access(
        user_id=user.id,
        document_id=goldfin_doc.id,
        action='upload',
        ip_address=request.client.host
    )

    return doc_metadata
```

## Frontend Pages

```
/dashboard
├── Overview (recent activity, claim summaries)
│
├── /dashboard/claims
│   ├── List of claim projects
│   └── "Start New Claim" button
│
├── /dashboard/claims/new
│   └── Wizard: Choose claim type → Add conditions → Create
│
├── /dashboard/claims/[id]
│   ├── Claim Overview
│   │   ├── Status badge
│   │   ├── Conditions list
│   │   └── Progress indicator
│   │
│   ├── Evidence Checklist tab
│   │   ├── Auto-generated checklist
│   │   ├── Checkboxes with explanations
│   │   └── "What's this?" tooltips
│   │
│   ├── Documents tab
│   │   ├── Upload area (drag & drop)
│   │   ├── Document list with categories
│   │   ├── PII warning badges
│   │   └── View/Download/Delete actions
│   │
│   ├── Notes tab
│   │   ├── Rich text editor (scratch pad)
│   │   └── Auto-save indicator
│   │
│   ├── Personal Statement tab
│   │   ├── Wizard or direct edit mode
│   │   ├── Guided questions
│   │   └── Export button
│   │
│   └── Timeline tab
│       ├── Visual milestone tracker
│       └── Add/edit milestone dates
│
├── /dashboard/documents
│   └── All documents across claims
│
├── /dashboard/calculations
│   └── Saved calculator results
│
└── /dashboard/chat-history
    └── Past chat sessions
```

## UI Components

### Document Upload Component
```tsx
<DocumentUploader
  claimId={claimId}
  onUpload={(doc) => addDocument(doc)}
  acceptedTypes={['.pdf', '.jpg', '.png', '.doc', '.docx']}
  maxSizeMB={25}
>
  <DropZone>
    <p>Drag files here or click to upload</p>
    <p className="text-sm text-muted">
      Your documents are encrypted and stored securely.
      Only you can access them.
    </p>
  </DropZone>
</DocumentUploader>
```

### PII Warning Badge
```tsx
{document.pii_detected && (
  <Badge variant="warning" className="flex items-center gap-1">
    <ShieldAlert className="h-3 w-3" />
    Contains sensitive info (encrypted)
  </Badge>
)}
```

### Evidence Checklist Component
```tsx
<EvidenceChecklist
  claimId={claimId}
  condition="PTSD"
  items={[
    { id: 1, label: "DD-214", required: true, checked: true },
    { id: 2, label: "Service Treatment Records", required: true, checked: false },
    { id: 3, label: "Current PTSD diagnosis", required: true, checked: false },
    { id: 4, label: "Stressor statement (VA Form 21-0781)", required: true, checked: false },
    { id: 5, label: "Nexus letter", required: false, checked: false },
    { id: 6, label: "Buddy statements", required: false, checked: false },
  ]}
  onToggle={(itemId) => toggleItem(itemId)}
/>
```

## Goldfin Connection

### Tailscale-Only Access
```python
# Backend connects to goldfin only via Tailscale
GOLDFIN_HOST = "goldfin.tail1234.ts.net"  # Tailscale hostname
GOLDFIN_PORT = 5432

# Connection string (only works from Tailscale network)
goldfin_url = f"postgresql://vetassist:{GOLDFIN_PASSWORD}@{GOLDFIN_HOST}:{GOLDFIN_PORT}/vetassist_vault"
```

### Encryption Keys
```python
# Key derivation for per-user encryption
def derive_user_key(user_id: UUID, master_key: bytes) -> bytes:
    """Derive a unique encryption key for each user."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=user_id.bytes,
        iterations=100000,
    )
    return kdf.derive(master_key)
```

## Security Checklist

- [ ] All document content encrypted with AES-256-GCM
- [ ] Encryption keys never stored with encrypted data
- [ ] PII tokenized before leaving goldfin
- [ ] All goldfin access via Tailscale only
- [ ] Document access logged with IP and timestamp
- [ ] User can only access their own documents
- [ ] No admin backdoor to user documents
- [ ] Checksums verified on download
- [ ] Rate limiting on upload/download endpoints
- [ ] File type validation (no executables)
- [ ] Max file size enforced (25MB)

## Phase Implementation

### Phase 1: Basic Workbench (Week 1)
- [ ] Claim CRUD (create, list, view, delete)
- [ ] Notes/scratch pad (encrypted on goldfin)
- [ ] Basic evidence checklist (manual)
- [ ] Dashboard page layout

### Phase 2: Document Storage (Week 2)
- [ ] Document upload with encryption
- [ ] Presidio PII scanning
- [ ] PII tokenization
- [ ] Document list and download
- [ ] Goldfin integration via Tailscale

### Phase 3: Smart Features (Week 3)
- [ ] Auto-generate checklists from conditions
- [ ] Personal statement wizard
- [ ] Timeline milestones
- [ ] Export functionality

### Phase 4: Polish (Week 4)
- [ ] Mobile responsive
- [ ] Drag-and-drop upload
- [ ] Progress indicators
- [ ] Help tooltips throughout

## Success Criteria

- [ ] Veteran can create a claim project
- [ ] Veteran can upload documents (encrypted)
- [ ] PII is detected and tokenized
- [ ] Documents stored on goldfin, metadata on bluefin
- [ ] Only document owner can access
- [ ] Evidence checklist auto-generates
- [ ] Personal statement wizard functional
- [ ] All access logged for audit

## Legal Reminder

Display prominently in UI:
```
This workbench helps you organize your claim materials.
VetAssist does not file claims on your behalf.
You maintain full control of your documents.
For assistance filing, contact an accredited VSO or attorney.
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Your claim. Your documents. Your control."*
