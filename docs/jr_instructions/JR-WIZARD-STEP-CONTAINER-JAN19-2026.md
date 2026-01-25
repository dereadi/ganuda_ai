# Jr Instruction: VetAssist Wizard Step Container

```yaml
task_id: wizard_step_container
priority: 1
assigned_to: it_triad_jr
target: redfin
estimated_effort: 45 minutes
depends_on: wizard_form_selection
```

## Objective

Create the dynamic step container page at `/wizard/[sessionId]` that:
1. Fetches wizard session state from backend
2. Renders the current step
3. Handles navigation (next/back)
4. Shows progress bar

## Files to Create

### 1. `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

Main container that manages wizard flow.

### 2. `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/ProgressBar.tsx`

Visual progress indicator.

### 3. `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/StepNavigation.tsx`

Back/Next buttons.

## Backend API (Already Exists)

```
GET /api/v1/wizard/{session_id}
Returns: { session_id, wizard_type, current_step, total_steps, step_data, completed_steps }

POST /api/v1/wizard/{session_id}/step/{step_num}
Body: { answers: {...} }
Returns: { success, next_step }
```

## Code Templates

### page.tsx
```tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';
import ProgressBar from './components/ProgressBar';
import StepNavigation from './components/StepNavigation';

interface WizardState {
  session_id: string;
  wizard_type: string;
  current_step: number;
  total_steps: number;
  step_data: Record<string, any>;
  completed_steps: number[];
}

export default function WizardSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [wizardState, setWizardState] = useState<WizardState | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

  useEffect(() => {
    fetchWizardState();
  }, [sessionId]);

  const fetchWizardState = async () => {
    try {
      const res = await fetch(`${apiUrl}/wizard/${sessionId}`);
      if (!res.ok) throw new Error('Session not found');
      const data = await res.json();
      setWizardState(data);
    } catch (err) {
      setError('Could not load wizard session');
    } finally {
      setLoading(false);
    }
  };

  const submitStep = async (answers: Record<string, any>) => {
    if (!wizardState) return;
    setSubmitting(true);

    try {
      const res = await fetch(
        `${apiUrl}/wizard/${sessionId}/step/${wizardState.current_step}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers })
        }
      );

      if (!res.ok) throw new Error('Failed to submit');

      const data = await res.json();
      if (data.completed) {
        router.push(`/wizard/${sessionId}/complete`);
      } else {
        await fetchWizardState();
      }
    } catch (err) {
      setError('Could not save your answers. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const goBack = () => {
    if (wizardState && wizardState.current_step > 1) {
      // Navigate to previous step via API
      setWizardState({
        ...wizardState,
        current_step: wizardState.current_step - 1
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !wizardState) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-2xl mx-auto text-center py-12">
          <p className="text-red-600 mb-4">{error || 'Session not found'}</p>
          <Link href="/wizard" className="text-blue-600 hover:underline">
            Start a new claim
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <Link
          href="/wizard"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Form Selection
        </Link>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <ProgressBar
            currentStep={wizardState.current_step}
            totalSteps={wizardState.total_steps}
            wizardType={wizardState.wizard_type}
          />

          <div className="mt-6">
            {/* Step content will be rendered here based on wizard_type and current_step */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-600">
                Step {wizardState.current_step} of {wizardState.total_steps}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Form: {wizardState.wizard_type}
              </p>
              {/* TODO: Render step-specific component */}
            </div>
          </div>

          <StepNavigation
            currentStep={wizardState.current_step}
            totalSteps={wizardState.total_steps}
            onBack={goBack}
            onNext={() => submitStep({})}
            submitting={submitting}
          />
        </div>
      </div>
    </div>
  );
}
```

### ProgressBar.tsx
```tsx
interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  wizardType: string;
}

export default function ProgressBar({ currentStep, totalSteps, wizardType }: ProgressBarProps) {
  const progress = (currentStep / totalSteps) * 100;

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">
          Form {wizardType}
        </span>
        <span className="text-sm text-gray-500">
          Step {currentStep} of {totalSteps}
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

### StepNavigation.tsx
```tsx
import { Loader2 } from 'lucide-react';

interface StepNavigationProps {
  currentStep: number;
  totalSteps: number;
  onBack: () => void;
  onNext: () => void;
  submitting: boolean;
}

export default function StepNavigation({
  currentStep,
  totalSteps,
  onBack,
  onNext,
  submitting
}: StepNavigationProps) {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;

  return (
    <div className="flex justify-between mt-6 pt-6 border-t border-gray-200">
      <button
        onClick={onBack}
        disabled={isFirstStep || submitting}
        className="px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Back
      </button>
      <button
        onClick={onNext}
        disabled={submitting}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
      >
        {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
        {isLastStep ? 'Submit' : 'Continue'}
      </button>
    </div>
  );
}
```

## Directory Structure

Create these directories and files:
```
/ganuda/vetassist/frontend/app/wizard/[sessionId]/
├── page.tsx
└── components/
    ├── ProgressBar.tsx
    └── StepNavigation.tsx
```

## Verification

```bash
# Check files exist
ls -la /ganuda/vetassist/frontend/app/wizard/[sessionId]/
ls -la /ganuda/vetassist/frontend/app/wizard/[sessionId]/components/

# Rebuild
cd /ganuda/vetassist/frontend && npm run build

# Test (need a valid session_id from wizard/start)
curl -X POST http://localhost:8001/api/v1/wizard/start \
  -H "Content-Type: application/json" \
  -d '{"wizard_type": "21-526EZ", "veteran_id": "test"}'
```

## Success Criteria

1. [ ] `/wizard/[sessionId]` page renders
2. [ ] Progress bar shows current step
3. [ ] Back/Next navigation works
4. [ ] Session state fetched from API
5. [ ] Errors handled gracefully

---
*Cherokee AI Federation - For the Seven Generations*
