# Jr Instruction: VetAssist Document Upload UI

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P2
**Estimated Complexity:** Medium

---

## Objective

Create React components for document upload, processing status, and extraction review.

---

## Deliverables

1. `/ganuda/vetassist/frontend/src/components/documents/DocumentUpload.tsx`
2. `/ganuda/vetassist/frontend/src/components/documents/ProcessingStatus.tsx`
3. `/ganuda/vetassist/frontend/src/components/documents/ExtractionReview.tsx`
4. `/ganuda/vetassist/frontend/src/pages/DocumentsPage.tsx`

---

## Component Requirements

### 1. DocumentUpload.tsx

```typescript
interface DocumentUploadProps {
    onUploadComplete: (documentId: string) => void;
    allowedTypes?: string[];  // defaults to PDF, images
}

// Features:
// - Drag and drop zone
// - Click to browse
// - File type validation (client-side)
// - File size validation (50MB max)
// - Upload progress bar
// - Error display
```

UI Elements:
- Dashed border drop zone
- Icon indicating drop area
- "Drop files here or click to browse"
- File type hints: "Supported: PDF, JPG, PNG, TIFF"
- Progress bar during upload
- Success/error toast notifications

### 2. ProcessingStatus.tsx

```typescript
interface ProcessingStatusProps {
    documentId: string;
    onComplete: (extractions: any) => void;
}

// Features:
// - Poll status endpoint every 2 seconds
// - Display current processing stage
// - Progress indicator
// - Estimated time remaining (optional)
// - Cancel button
```

Processing Stages to Display:
1. "Uploading..." (upload progress)
2. "Queued for processing"
3. "Extracting text (OCR)..."
4. "Analyzing document..."
5. "Complete!" or "Review needed"

### 3. ExtractionReview.tsx

```typescript
interface ExtractionReviewProps {
    documentId: string;
    extractions: ExtractionData;
    onConfirm: (corrections: any) => void;
    onReject: () => void;
}

// Features:
// - Display extracted entities in cards
// - Highlight low-confidence items (yellow border)
// - Allow inline editing of values
// - "Add to Claim" button for conditions
// - "Confirm All" and "Reject" actions
```

Display Sections:
- Document Type (with confidence badge)
- Service Information (branch, dates, discharge)
- Conditions Found (list with ratings)
- Important Dates (timeline view)
- Evidence Strength (nexus indicators)

### 4. DocumentsPage.tsx

```typescript
// Full page combining components
// - List of user's uploaded documents
// - Upload new document button
// - Status indicators per document
// - Click to view extractions
```

---

## Styling

Follow existing VetAssist design patterns:
- Use existing color variables
- Match claim wizard styling
- Accessible contrast ratios
- Mobile responsive

---

## API Integration

```typescript
// services/documentApi.ts

export const uploadDocument = async (file: File, type?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (type) formData.append('document_type', type);

    return fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
    });
};

export const getDocumentStatus = async (id: string) => {
    return fetch(`/api/documents/${id}/status`);
};

export const getExtractions = async (id: string) => {
    return fetch(`/api/documents/${id}/extractions`);
};
```

---

## State Management

Use existing state pattern (Context or Redux if present):
- Track uploaded documents
- Cache extraction results
- Handle processing state

---

## Error Handling

- File too large: "File exceeds 50MB limit"
- Invalid type: "Unsupported file type. Use PDF, JPG, PNG, or TIFF"
- Upload failed: "Upload failed. Please try again"
- Processing error: "Document processing failed. Please try a clearer scan"

---

## Accessibility

- Keyboard navigation for upload
- Screen reader announcements for status changes
- ARIA labels on interactive elements
- Focus management after upload

---

## Integration Points

- Link from Claim Wizard "Upload Documents" step
- Extracted conditions feed into condition selector
- Extracted dates populate claim timeline

---

## Do NOT

- Auto-submit documents without user confirmation
- Display raw OCR text to users
- Skip loading states
- Forget error boundaries
