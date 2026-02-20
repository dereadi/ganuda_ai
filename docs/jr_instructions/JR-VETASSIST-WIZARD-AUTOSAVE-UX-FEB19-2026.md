# Jr Instruction: VetAssist Wizard Auto-Save & UX Trust Signals

**Task**: Add debounced auto-save, visual save indicator, Save & Exit wiring, and start page reassurance
**Priority**: 2 (HIGH — blocks user adoption, Joe froze during live testing)
**Source**: Meetup feedback from Joe (veteran user), Feb 19 2026
**Assigned Jr**: Software Engineer Jr.

## Context

During live testing, Joe (veteran, VetAssist beta tester) had two trust problems:

1. **Save anxiety**: He was afraid to leave a step without explicitly saving. The bottom of the page says "Your progress is automatically saved" in tiny gray text, but this is actually misleading — `updateField()` only updates local React state. Data is only persisted to the server when the user clicks "Continue" (`submitStep`). If Joe closes the tab mid-step, his data is LOST.

2. **Commitment anxiety**: Joe was reluctant to start a claim because he didn't know if he had to finish it in one sitting. The wizard start page says nothing about being able to come back later.

Additionally, `StepNavigation.tsx` already has a `Save & Exit` button (`onSaveExit` prop) with a Save icon imported, but it's **never wired up** in the parent page.

This instruction fixes all three issues with 4 surgical changes.

## Step 1: Add debounced auto-save and save status state

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

Add `useRef` and `useCallback` to the import:

```
<<<<<<< SEARCH
import { useEffect, useState } from 'react';
=======
import { useEffect, useState, useRef, useCallback } from 'react';
>>>>>>> REPLACE
```

Add save status state and the debounced auto-save after the existing `formData` state:

```
<<<<<<< SEARCH
  const [formData, setFormData] = useState<Record<string, any>>({});

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
=======
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedRef = useRef<string>('');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
>>>>>>> REPLACE
```

Add the auto-save function after `apiUrl`:

```
<<<<<<< SEARCH
  useEffect(() => {
    fetchWizardState();
  }, [sessionId]);
=======
  // Debounced auto-save: saves to server 2 seconds after last field change
  const autoSave = useCallback(async (data: Record<string, any>) => {
    if (!wizardState) return;
    const dataStr = JSON.stringify(data);
    if (dataStr === lastSavedRef.current) return; // No changes

    setSaveStatus('saving');
    try {
      const res = await fetch(
        `${apiUrl}/wizard/${sessionId}/step/${wizardState.current_step}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers: data, auto_save: true })
        }
      );
      if (res.ok) {
        lastSavedRef.current = dataStr;
        setSaveStatus('saved');
        // Reset to idle after 3 seconds
        setTimeout(() => setSaveStatus('idle'), 3000);
      } else {
        setSaveStatus('error');
      }
    } catch {
      setSaveStatus('error');
    }
  }, [wizardState, sessionId, apiUrl]);

  useEffect(() => {
    fetchWizardState();
  }, [sessionId]);
>>>>>>> REPLACE
```

Update `updateField` to trigger debounced auto-save:

```
<<<<<<< SEARCH
  const updateField = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
=======
  const updateField = (field: string, value: any) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      // Debounce: save 2 seconds after last keystroke
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => autoSave(updated), 2000);
      return updated;
    });
  };
>>>>>>> REPLACE
```

## Step 2: Add visual save indicator above the step content

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

Add a save status indicator and upgrade the bottom message:

```
<<<<<<< SEARCH
          <div className="mt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {currentStepTitle}
            </h2>
=======
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {currentStepTitle}
              </h2>
              <span className={`text-xs flex items-center gap-1 transition-opacity duration-300 ${
                saveStatus === 'idle' ? 'opacity-0' :
                saveStatus === 'saving' ? 'text-gray-400 opacity-100' :
                saveStatus === 'saved' ? 'text-green-600 opacity-100' :
                'text-red-500 opacity-100'
              }`}>
                {saveStatus === 'saving' && (
                  <><Loader2 className="h-3 w-3 animate-spin" /> Saving...</>
                )}
                {saveStatus === 'saved' && (
                  <><svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg> All changes saved</>
                )}
                {saveStatus === 'error' && 'Save failed — will retry'}
              </span>
            </div>
>>>>>>> REPLACE
```

## Step 3: Wire up Save & Exit button

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

Add a saveAndExit handler after the `goToStep` function:

```
<<<<<<< SEARCH
  const updateField = (field: string, value: any) => {
=======
  const saveAndExit = async () => {
    if (!wizardState) return;
    setSubmitting(true);
    try {
      await fetch(
        `${apiUrl}/wizard/${sessionId}/step/${wizardState.current_step}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers: formData, auto_save: true })
        }
      );
      router.push('/wizard');
    } catch {
      setError('Could not save. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = (field: string, value: any) => {
>>>>>>> REPLACE
```

Wire it into StepNavigation:

```
<<<<<<< SEARCH
          <StepNavigation
            currentStep={wizardState.current_step}
            totalSteps={wizardState.total_steps}
            onBack={goBack}
            onNext={submitStep}
            submitting={submitting}
          />
=======
          <StepNavigation
            currentStep={wizardState.current_step}
            totalSteps={wizardState.total_steps}
            onBack={goBack}
            onNext={submitStep}
            submitting={submitting}
            onSaveExit={saveAndExit}
          />
>>>>>>> REPLACE
```

## Step 4: Add reassurance messaging to wizard start page

File: `/ganuda/vetassist/frontend/app/wizard/page.tsx`

Find the subtitle text under "Start a New Claim" and add reassurance:

```
<<<<<<< SEARCH
        <p className="text-gray-600 mt-2">
          Select the type of claim you want to file. We will guide you through each step.
        </p>
=======
        <p className="text-gray-600 mt-2">
          Select the type of claim you want to file. We will guide you through each step.
        </p>
        <div className="mt-3 flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2 max-w-lg mx-auto">
          <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>You don&apos;t need to finish in one sitting. Your progress saves automatically and you can return anytime.</span>
        </div>
>>>>>>> REPLACE
```

## Step 5: Backend — Accept auto_save flag without advancing step

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

The `submit_step` endpoint currently advances `current_step` on every POST. When `auto_save=true`, it should save the answers without advancing:

```
<<<<<<< SEARCH
class StepAnswers(BaseModel):
    answers: Dict[str, Any] = Field(...)
=======
class StepAnswers(BaseModel):
    answers: Dict[str, Any] = Field(...)
    auto_save: bool = Field(default=False, description="If true, save without advancing step")
>>>>>>> REPLACE
```

Then in the `submit_step` function, add the auto_save branch before the current_step increment logic. Find where current_step is incremented:

```
<<<<<<< SEARCH
        # Determine next step and status
=======
        # Auto-save: store answers without advancing
        if data.auto_save:
            cur.execute("""
                UPDATE vetassist_wizard_sessions
                SET answers = %s
                WHERE session_id = %s
            """, (json.dumps(current_answers), session_id))
            conn.commit()
            return {"saved": True, "step": step_num, "auto_save": True}

        # Determine next step and status
>>>>>>> REPLACE
```

## Verification

After all 5 steps:
1. Start a new 21-526EZ claim — the start page should show green reassurance banner
2. Type in First Name field, wait 2 seconds — "All changes saved" should appear with green checkmark next to step title
3. Close the tab, reopen the session — typed data should still be there
4. Click "Save & Exit" button — should save and redirect to wizard start page
5. The "Continue" button should still advance the step as before (no regression)
6. Bottom text "Your progress is automatically saved" is now actually true
