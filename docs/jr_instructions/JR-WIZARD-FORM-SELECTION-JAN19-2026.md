# Jr Instruction: VetAssist Wizard Form Selection Page

```yaml
task_id: wizard_form_selection
priority: 1
assigned_to: it_triad_jr
target: redfin
estimated_effort: 30 minutes
```

## Objective

Replace the placeholder wizard page with a form selection interface showing the 4 VA claim types.

## File to Modify

`/ganuda/vetassist/frontend/app/wizard/page.tsx`

## Requirements

1. Show 4 form type cards:
   - 21-526EZ: Application for Disability Compensation
   - 21-0995: Supplemental Claim
   - 20-0996: Higher-Level Review
   - 10182: Board of Veterans Appeals

2. Each card should display:
   - Form number and title
   - Brief description (1-2 sentences)
   - "Start" button

3. On card click:
   - Call `POST /api/v1/wizard/start` with form type
   - Navigate to `/wizard/{session_id}`

## Code Template

```tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FileText, ArrowLeft, FileCheck, Scale, Gavel, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

const FORM_TYPES = [
  {
    id: '21-526EZ',
    title: 'Disability Compensation',
    description: 'File a new claim for service-connected disability benefits.',
    icon: FileText,
    color: 'blue',
    steps: 5
  },
  {
    id: '21-0995',
    title: 'Supplemental Claim',
    description: 'Submit new evidence for a previously denied claim.',
    icon: FileCheck,
    color: 'green',
    steps: 3
  },
  {
    id: '20-0996',
    title: 'Higher-Level Review',
    description: 'Request a senior reviewer examine your case for errors.',
    icon: Scale,
    color: 'purple',
    steps: 4
  },
  {
    id: '10182',
    title: 'Board Appeal',
    description: 'Appeal your decision to the Board of Veterans Appeals.',
    icon: Gavel,
    color: 'orange',
    steps: 4
  }
];

export default function WizardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

  const startWizard = async (formType: string) => {
    setLoading(formType);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/wizard/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wizard_type: formType,
          veteran_id: user?.id || 'anonymous'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start wizard');
      }

      const data = await response.json();
      router.push(`/wizard/${data.session_id}`);
    } catch (err) {
      setError('Could not start wizard. Please try again.');
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <Link
          href="/dashboard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Dashboard
        </Link>

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Start a New Claim</h1>
          <p className="text-gray-600 mt-2">
            Select the type of claim you want to file. We'll guide you through each step.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FORM_TYPES.map((form) => {
            const Icon = form.icon;
            const isLoading = loading === form.id;
            const colorClasses = {
              blue: 'bg-blue-100 text-blue-600 border-blue-200 hover:border-blue-400',
              green: 'bg-green-100 text-green-600 border-green-200 hover:border-green-400',
              purple: 'bg-purple-100 text-purple-600 border-purple-200 hover:border-purple-400',
              orange: 'bg-orange-100 text-orange-600 border-orange-200 hover:border-orange-400'
            }[form.color];

            return (
              <button
                key={form.id}
                onClick={() => startWizard(form.id)}
                disabled={loading !== null}
                className={`text-left p-6 bg-white rounded-lg border-2 transition-all ${colorClasses} disabled:opacity-50`}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${colorClasses.split(' ')[0]}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900">{form.title}</h3>
                      <span className="text-xs text-gray-500">Form {form.id}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{form.description}</p>
                    <div className="flex items-center justify-between mt-4">
                      <span className="text-xs text-gray-500">{form.steps} steps</span>
                      {isLoading ? (
                        <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                      ) : (
                        <span className="text-sm font-medium">Start →</span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-medium text-blue-900">Not sure which form to use?</h3>
          <p className="text-sm text-blue-700 mt-1">
            Use our <Link href="/chat" className="underline">AI Assistant</Link> to help determine the right claim type for your situation.
          </p>
        </div>
      </div>
    </div>
  );
}
```

## Success Criteria

1. [ ] Page displays 4 form type cards
2. [ ] Each card shows form number, title, description
3. [ ] Clicking card calls wizard/start API
4. [ ] Redirects to /wizard/{session_id} on success
5. [ ] Shows loading state while API call in progress
6. [ ] Shows error message on failure

---

*Cherokee AI Federation - For the Seven Generations*
