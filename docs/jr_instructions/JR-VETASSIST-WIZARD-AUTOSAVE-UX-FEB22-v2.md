# Jr Instruction: VetAssist Wizard Auto-Save & UX Trust Signals — Remaining (v2)

**Task ID:** WIZARD-AUTOSAVE-UX-v2
**Kanban:** #1848
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Previous Jr attempt (#811) partially applied. The saveStatus state, save indicator UI, and saveAndExit function are ALREADY in place. What's missing: the autoSave callback, debounced updateField, StepNavigation wiring, reassurance banner, and backend auto_save support.

---

## Step 1: Add autoSave callback function

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

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

---

## Step 2: Add debounce to updateField

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

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

---

## Step 3: Wire onSaveExit into StepNavigation

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

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

---

## Step 4: Add reassurance banner to wizard start page

File: `/ganuda/vetassist/frontend/app/wizard/page.tsx`

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

---

## Step 5: Backend — Add auto_save field to StepAnswers

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```python
<<<<<<< SEARCH
class StepAnswers(BaseModel):
    answers: Dict[str, Any]
=======
class StepAnswers(BaseModel):
    answers: Dict[str, Any]
    auto_save: bool = Field(default=False, description="If true, save without advancing step")
>>>>>>> REPLACE
```

---

## Step 6: Backend — Add auto_save branch before step advance

File: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

```python
<<<<<<< SEARCH
            # Determine next step
            next_step = min(step_num + 1, total_steps)
=======
            # Auto-save: store answers without advancing
            if data.auto_save:
                cur.execute("""
                    UPDATE vetassist_wizard_sessions
                    SET answers = %s
                    WHERE session_id = %s
                """, (json.dumps(answers), session_id))
                conn.commit()
                conn.close()
                return {"saved": True, "step": step_num, "auto_save": True}

            # Determine next step
            next_step = min(step_num + 1, total_steps)
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/vetassist/frontend && npx next build 2>&1 | tail -5
```

## What NOT to Change

- Do NOT modify saveStatus state (already exists)
- Do NOT modify saveAndExit function (already exists)
- Do NOT modify the save indicator UI (already exists)
- Do NOT modify ProgressBar or step components
