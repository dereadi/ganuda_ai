# JR INSTRUCTION: VetAssist Dashboard Frontend Components

## Document Control
```yaml
jr_instruction_id: JR-VETASSIST-DASHBOARD-FRONTEND
created: 2026-01-18
author: TPM Claude (Opus 4.5)
priority: HIGH
assigned_jr: it_triad_jr
category: frontend_development
ultrathink_ref: ULTRATHINK-VETASSIST-DASHBOARD-JAN18-2026
council_approval: b344aada7439ac4c (87.2% confidence)
```

---

## Executive Summary

Build the VetAssist personalized dashboard frontend with:
1. **ScratchpadEditor** - Auto-saving notes textarea
2. **FileDropZone** - Drag-and-drop file upload
3. **ResearchPanel** - Expandable AI research results
4. **ClaimsTracker** - Claims progress cards
5. **QuickActions** - Action button grid

**Stack**: Next.js 14, TypeScript, Tailwind CSS, react-dropzone, @tiptap/react

---

## Prerequisites

Install required dependencies:
```bash
cd /ganuda/vetassist/frontend
npm install react-dropzone @tiptap/react @tiptap/starter-kit @tanstack/react-query lucide-react
```

---

## File Structure to Create

```
/ganuda/vetassist/frontend/src/
├── components/
│   └── dashboard/
│       ├── ScratchpadEditor.tsx
│       ├── FileDropZone.tsx
│       ├── ResearchPanel.tsx
│       ├── ClaimsTracker.tsx
│       ├── QuickActions.tsx
│       └── index.ts
├── hooks/
│   ├── useAutoSave.ts
│   ├── useFileUpload.ts
│   └── useDashboardData.ts
└── app/
    └── dashboard/
        └── page.tsx
```

---

## Component 1: ScratchpadEditor.tsx

```typescript
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Save, CheckCircle, AlertCircle } from 'lucide-react';

interface ScratchpadEditorProps {
  veteranId: string;
  initialContent?: string;
  onSave?: (content: string) => void;
}

export function ScratchpadEditor({ veteranId, initialContent = '', onSave }: ScratchpadEditorProps) {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const editor = useEditor({
    extensions: [StarterKit],
    content: initialContent,
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
        'aria-label': 'Scratchpad editor - your personal notes',
        role: 'textbox',
        'aria-multiline': 'true',
      },
    },
  });

  // Debounced auto-save
  const saveContent = useCallback(async (content: string) => {
    setSaveStatus('saving');
    try {
      const response = await fetch(`/api/v1/dashboard/${veteranId}/scratchpad`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) throw new Error('Save failed');

      setSaveStatus('saved');
      setLastSaved(new Date());
      onSave?.(content);

      // Reset to idle after 2 seconds
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      setSaveStatus('error');
      console.error('Scratchpad save error:', error);
    }
  }, [veteranId, onSave]);

  // Auto-save on content change (debounced 2 seconds)
  useEffect(() => {
    if (!editor) return;

    const timeoutId = setTimeout(() => {
      const content = editor.getHTML();
      if (content !== initialContent) {
        saveContent(content);
      }
    }, 2000);

    return () => clearTimeout(timeoutId);
  }, [editor?.getHTML(), saveContent, initialContent]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">My Notes</h2>
        <div className="flex items-center gap-2 text-sm" aria-live="polite">
          {saveStatus === 'saving' && (
            <span className="flex items-center gap-1 text-blue-600">
              <Save className="h-4 w-4 animate-pulse" aria-hidden="true" />
              Saving...
            </span>
          )}
          {saveStatus === 'saved' && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle className="h-4 w-4" aria-hidden="true" />
              Saved
            </span>
          )}
          {saveStatus === 'error' && (
            <span className="flex items-center gap-1 text-red-600">
              <AlertCircle className="h-4 w-4" aria-hidden="true" />
              Error saving
            </span>
          )}
          {lastSaved && saveStatus === 'idle' && (
            <span className="text-gray-500">
              Last saved: {lastSaved.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
```

---

## Component 2: FileDropZone.tsx

```typescript
'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react';

interface UploadedFile {
  id: number;
  filename: string;
  file_type: string;
  category: string;
  uploaded_at: string;
  file_size: number;
}

interface FileDropZoneProps {
  veteranId: string;
  onUploadComplete?: (file: UploadedFile) => void;
  existingFiles?: UploadedFile[];
}

const ALLOWED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tiff', '.tif'],
  'image/gif': ['.gif'],
};

const MAX_SIZE = 25 * 1024 * 1024; // 25MB

const CATEGORIES = [
  { value: 'medical', label: 'Medical Records' },
  { value: 'service_records', label: 'Service Records' },
  { value: 'buddy_statement', label: 'Buddy Statement' },
  { value: 'nexus_letter', label: 'Nexus Letter' },
  { value: 'other', label: 'Other Evidence' },
];

export function FileDropZone({ veteranId, onUploadComplete, existingFiles = [] }: FileDropZoneProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('medical');
  const [files, setFiles] = useState<UploadedFile[]>(existingFiles);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploadError(null);
    setUploading(true);

    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', selectedCategory);
      formData.append('description', '');

      try {
        const response = await fetch(`/api/v1/dashboard/${veteranId}/files`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        setFiles(prev => [result.file, ...prev]);
        onUploadComplete?.(result.file);
      } catch (error) {
        setUploadError(error instanceof Error ? error.message : 'Upload failed');
      }
    }

    setUploading(false);
  }, [veteranId, selectedCategory, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ALLOWED_TYPES,
    maxSize: MAX_SIZE,
    disabled: uploading,
  });

  const deleteFile = async (fileId: number) => {
    try {
      const response = await fetch(`/api/v1/dashboard/${veteranId}/files/${fileId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setFiles(prev => prev.filter(f => f.id !== fileId));
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Evidence Files</h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Category selector */}
        <div>
          <label htmlFor="file-category" className="block text-sm font-medium text-gray-700 mb-1">
            File Category
          </label>
          <select
            id="file-category"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors duration-200
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
            ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          role="button"
          aria-label="Drop files here or click to select. Accepts PDF and images up to 25MB"
          tabIndex={0}
        >
          <input {...getInputProps()} aria-label="File input" />
          <Upload className="mx-auto h-12 w-12 text-gray-400" aria-hidden="true" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive ? 'Drop files here...' : 'Drag and drop files, or click to select'}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            PDF, JPG, PNG, TIFF, GIF up to 25MB
          </p>
        </div>

        {/* Upload status */}
        {uploading && (
          <div className="flex items-center gap-2 text-blue-600" aria-live="polite">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
            Uploading...
          </div>
        )}

        {uploadError && (
          <div className="flex items-center gap-2 text-red-600" role="alert">
            <AlertCircle className="h-4 w-4" />
            {uploadError}
          </div>
        )}

        {/* File list */}
        {files.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700">Uploaded Files</h3>
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
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## Component 3: ResearchPanel.tsx

```typescript
'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Search, Clock, CheckCircle, Loader, Copy } from 'lucide-react';

interface ResearchResult {
  research_id: string;
  question: string;
  condition: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  summary: string | null;
  full_result: any;
  created_at: string;
  completed_at: string | null;
}

interface ResearchPanelProps {
  sessionId: string;
  veteranId: string;
  onSaveToScratchpad?: (content: string) => void;
}

export function ResearchPanel({ sessionId, veteranId, onSaveToScratchpad }: ResearchPanelProps) {
  const [results, setResults] = useState<ResearchResult[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch research results
  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`/api/v1/research/results/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          setResults(data.results || []);
        }
      } catch (error) {
        console.error('Failed to fetch research results:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchResults, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      case 'in_progress':
        return <Loader className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <div className="animate-pulse flex items-center gap-2">
          <div className="h-4 w-4 bg-gray-200 rounded" />
          <div className="h-4 w-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Search className="h-5 w-5" aria-hidden="true" />
            AI Research
          </h2>
        </div>
        <div className="p-4 text-center text-gray-500">
          <p>No research tasks yet.</p>
          <p className="text-sm mt-1">Ask the AI a question to trigger deep research.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Search className="h-5 w-5" aria-hidden="true" />
          AI Research ({results.length})
        </h2>
      </div>
      <ul className="divide-y divide-gray-100" role="list" aria-label="Research results">
        {results.map(result => (
          <li key={result.research_id} className="p-4">
            <button
              onClick={() => setExpandedId(expandedId === result.research_id ? null : result.research_id)}
              className="w-full text-left focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-expanded={expandedId === result.research_id}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  {getStatusIcon(result.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900 line-clamp-2">
                      {result.question}
                    </p>
                    {result.condition && (
                      <p className="text-xs text-gray-500 mt-1">
                        Condition: {result.condition}
                      </p>
                    )}
                  </div>
                </div>
                {expandedId === result.research_id ? (
                  <ChevronUp className="h-5 w-5 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0" />
                )}
              </div>
            </button>

            {expandedId === result.research_id && result.status === 'completed' && (
              <div className="mt-4 pl-6 space-y-3">
                {result.summary && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Summary</h4>
                    <p className="text-sm text-gray-600">{result.summary}</p>
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => onSaveToScratchpad?.(result.summary || result.question)}
                    className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Save to Notes
                  </button>
                  <button
                    onClick={() => copyToClipboard(result.summary || '')}
                    className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center gap-1"
                  >
                    <Copy className="h-3 w-3" />
                    Copy
                  </button>
                </div>
              </div>
            )}

            {expandedId === result.research_id && result.status !== 'completed' && (
              <div className="mt-4 pl-6">
                <p className="text-sm text-gray-500">
                  {result.status === 'pending' && 'Research is queued...'}
                  {result.status === 'in_progress' && 'Research in progress...'}
                </p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Component 4: ClaimsTracker.tsx

```typescript
'use client';

import { FileText, Clock, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface Claim {
  id: number;
  claim_type: string;
  status: 'draft' | 'submitted' | 'in_review' | 'decision' | 'appeal';
  conditions: string[] | null;
  created_at: string;
  updated_at: string;
}

interface ClaimsTrackerProps {
  claims: Claim[];
}

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'gray', icon: FileText },
  submitted: { label: 'Submitted', color: 'blue', icon: Clock },
  in_review: { label: 'In Review', color: 'yellow', icon: Clock },
  decision: { label: 'Decision Made', color: 'green', icon: CheckCircle },
  appeal: { label: 'Appeal', color: 'orange', icon: AlertTriangle },
};

export function ClaimsTracker({ claims }: ClaimsTrackerProps) {
  const getStatusConfig = (status: string) => {
    return STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.draft;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">My Claims</h2>
        <Link
          href="/wizard"
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
        >
          New Claim
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {claims.length === 0 ? (
        <div className="p-4 text-center text-gray-500">
          <FileText className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2">No claims started yet.</p>
          <Link
            href="/wizard"
            className="mt-2 inline-block text-sm text-blue-600 hover:underline"
          >
            Start your first claim
          </Link>
        </div>
      ) : (
        <ul className="divide-y divide-gray-100" role="list" aria-label="Your claims">
          {claims.map(claim => {
            const config = getStatusConfig(claim.status);
            const StatusIcon = config.icon;

            return (
              <li key={claim.id} className="p-4 hover:bg-gray-50">
                <Link href={`/claims/${claim.id}`} className="block focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-full bg-${config.color}-100`}>
                        <StatusIcon className={`h-4 w-4 text-${config.color}-600`} aria-hidden="true" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {claim.claim_type === 'disability' ? 'Disability Compensation' : claim.claim_type}
                        </p>
                        <p className={`text-xs text-${config.color}-600 font-medium`}>
                          {config.label}
                        </p>
                        {claim.conditions && claim.conditions.length > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            {claim.conditions.slice(0, 3).join(', ')}
                            {claim.conditions.length > 3 && ` +${claim.conditions.length - 3} more`}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(claim.updated_at)}
                    </div>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
```

---

## Component 5: QuickActions.tsx

```typescript
'use client';

import Link from 'next/link';
import { Calculator, MessageCircle, FileText, BookOpen, Upload, Download } from 'lucide-react';

interface QuickAction {
  label: string;
  href: string;
  icon: string;
  description?: string;
}

interface QuickActionsProps {
  actions?: QuickAction[];
}

const ICON_MAP: Record<string, any> = {
  calculator: Calculator,
  'message-circle': MessageCircle,
  'file-plus': FileText,
  'book-open': BookOpen,
  upload: Upload,
  download: Download,
};

const DEFAULT_ACTIONS: QuickAction[] = [
  { label: 'Calculator', href: '/calculator', icon: 'calculator', description: 'Calculate your combined rating' },
  { label: 'Ask AI', href: '/chat', icon: 'message-circle', description: 'Get answers to your questions' },
  { label: 'New Claim', href: '/wizard', icon: 'file-plus', description: 'Start a new claim' },
  { label: 'Resources', href: '/resources', icon: 'book-open', description: 'Learn about VA benefits' },
];

export function QuickActions({ actions = DEFAULT_ACTIONS }: QuickActionsProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-4 py-2 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
      </div>
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3" role="navigation" aria-label="Quick actions">
          {actions.map(action => {
            const Icon = ICON_MAP[action.icon] || FileText;
            return (
              <Link
                key={action.label}
                href={action.href}
                className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label={action.description || action.label}
              >
                <Icon className="h-6 w-6 text-blue-600 mb-2" aria-hidden="true" />
                <span className="text-sm font-medium text-gray-700">{action.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
```

---

## Component 6: Dashboard Page (app/dashboard/page.tsx)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { ScratchpadEditor } from '@/components/dashboard/ScratchpadEditor';
import { FileDropZone } from '@/components/dashboard/FileDropZone';
import { ResearchPanel } from '@/components/dashboard/ResearchPanel';
import { ClaimsTracker } from '@/components/dashboard/ClaimsTracker';
import { QuickActions } from '@/components/dashboard/QuickActions';

interface DashboardData {
  veteran_id: string;
  scratchpad: { content: string; last_updated: string | null };
  files: any[];
  claims: any[];
  research_history: any[];
  wizard_sessions: any[];
  quick_actions: any[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get veteran ID from auth context (simplified - use your auth system)
  const veteranId = 'current-user-id'; // Replace with actual auth

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(`/api/v1/dashboard/${veteranId}`);
        if (!response.ok) throw new Error('Failed to load dashboard');
        const dashboardData = await response.json();
        setData(dashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [veteranId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 w-48 bg-gray-200 rounded" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 h-64 bg-gray-200 rounded-lg" />
              <div className="h-64 bg-gray-200 rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700" role="alert">
            Error loading dashboard: {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My Dashboard</h1>
          <p className="text-gray-600">Welcome back. Here's your VetAssist overview.</p>
        </header>

        {/* Quick Actions */}
        <section className="mb-6" aria-label="Quick actions">
          <QuickActions actions={data?.quick_actions} />
        </section>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Scratchpad & Research */}
          <div className="lg:col-span-2 space-y-6">
            <section aria-label="Scratchpad">
              <ScratchpadEditor
                veteranId={veteranId}
                initialContent={data?.scratchpad?.content || ''}
              />
            </section>

            <section aria-label="AI Research">
              <ResearchPanel
                sessionId={veteranId}
                veteranId={veteranId}
              />
            </section>
          </div>

          {/* Right Column - Files & Claims */}
          <div className="space-y-6">
            <section aria-label="Evidence files">
              <FileDropZone
                veteranId={veteranId}
                existingFiles={data?.files || []}
              />
            </section>

            <section aria-label="Claims tracker">
              <ClaimsTracker claims={data?.claims || []} />
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
```

---

## Component Index (components/dashboard/index.ts)

```typescript
export { ScratchpadEditor } from './ScratchpadEditor';
export { FileDropZone } from './FileDropZone';
export { ResearchPanel } from './ResearchPanel';
export { ClaimsTracker } from './ClaimsTracker';
export { QuickActions } from './QuickActions';
```

---

## Accessibility Checklist

Before submitting, verify:

- [ ] All interactive elements have focus states
- [ ] All images/icons have aria-hidden or alt text
- [ ] Forms have proper labels
- [ ] Error messages are announced (aria-live)
- [ ] Color contrast meets 4.5:1 ratio
- [ ] Keyboard navigation works logically
- [ ] Screen reader testing passes

---

## Testing Commands

```bash
# Run lint
npm run lint

# Run type check
npm run type-check

# Run tests
npm run test

# Build
npm run build
```

---

## Notes for Jr

1. **Do not install additional libraries** without TPM approval
2. **All components must pass accessibility audits**
3. **Use the existing Tailwind config** - no custom CSS
4. **Follow the existing auth patterns** in the codebase
5. **Test with keyboard-only navigation**

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-DASHBOARD-JAN18-2026.md`

---

**For Seven Generations**

Cherokee AI Federation
