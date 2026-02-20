# Jr Instruction: PyPDFForm Part 4 — Frontend Component

**ID:** JR-VETASSIST-PYPDF-PART4-FRONTEND-FEB06-2026
**Priority:** P0
**Part:** 4 of 4

---

## Objective

Create the FormGenerator React component.

---

## Step 1: Create FormGenerator.tsx

**file: /ganuda/vetassist/frontend/components/FormGenerator.tsx**
```tsx
'use client'

import { useState } from 'react'

const FORMS = [
  { id: '21-526EZ', name: 'VA Form 21-526EZ - Disability Compensation' },
  { id: '21-0781', name: 'VA Form 21-0781 - PTSD Statement' },
  { id: '21-0781a', name: 'VA Form 21-0781a - PTSD Personal Assault' },
]

export function FormGenerator() {
  const [generating, setGenerating] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate(formType: string) {
    setGenerating(formType)
    setError(null)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await fetch('/api/v1/forms/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ form_type: formType }),
      })
      if (!res.ok) throw new Error('Failed to generate')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `VA_Form_${formType}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error')
    } finally {
      setGenerating(null)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Generate Pre-Filled VA Forms</h2>
      {error && <div className="bg-red-50 text-red-700 p-3 rounded mb-4">{error}</div>}
      <div className="space-y-3">
        {FORMS.map((f) => (
          <div key={f.id} className="flex justify-between items-center border p-3 rounded">
            <span>{f.name}</span>
            <button
              onClick={() => handleGenerate(f.id)}
              disabled={generating !== null}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {generating === f.id ? 'Generating...' : 'Generate'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FormGenerator
```

---

## Step 2: Verify file created

```bash
ls -la /ganuda/vetassist/frontend/components/FormGenerator.tsx
```

---

*Part 4 of 4*
