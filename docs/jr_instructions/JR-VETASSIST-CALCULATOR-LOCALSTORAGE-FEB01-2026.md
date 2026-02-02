# Jr Instruction: Calculator localStorage Persistence (Phase A)

**Task ID:** VETASSIST-CALC-PERSIST-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Vote:** #8356 (audit_hash: a1b5ea2972b6834a) — approved

## Goal

When a veteran enters conditions into the disability calculator and navigates away (to AI Chat, Resources, etc.), their calculator data should still be there when they come back. Currently it resets to empty.

This is Phase A — localStorage only, no backend changes.

## Single File Change

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

### What to Add

The calculator uses `react-hook-form` with `useFieldArray` and Zod validation. The form's `defaultValues` are currently hardcoded. We need to:

1. Load saved form data from localStorage on mount
2. Save form data to localStorage on every change
3. Add a "Clear Calculator" button that resets both form and localStorage
4. Show a subtle "Restored from your last session" indicator when data is loaded

### Implementation Details

#### Step 1: localStorage key constant

Add near the top of the file (after imports):

```typescript
const CALC_STORAGE_KEY = 'vetassist_calculator_form';
```

#### Step 2: Load saved data for defaultValues

The current `useForm` call has hardcoded `defaultValues`. Change the initialization pattern to load from localStorage:

**Find this pattern:**
```typescript
const {
  register,
  control,
  handleSubmit,
  watch,
  formState: { errors },
} = useForm<CalculatorFormData>({
  resolver: zodResolver(calculatorSchema),
  defaultValues: {
    conditions: [{ name: "", rating: 0, is_bilateral: false, bilateral_side: null }],
    dependents: { /* current defaults */ },
    aid_attendance: false,
    housebound: false,
  },
});
```

**Replace with:**
```typescript
// Load saved calculator data from localStorage
const getSavedFormData = (): CalculatorFormData | null => {
  if (typeof window === 'undefined') return null;
  try {
    const saved = localStorage.getItem(CALC_STORAGE_KEY);
    if (!saved) return null;
    const parsed = JSON.parse(saved);
    // Validate it has the expected shape
    if (parsed.conditions && Array.isArray(parsed.conditions) && parsed.conditions.length > 0) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
};

const savedData = getSavedFormData();
const [restoredFromStorage, setRestoredFromStorage] = useState(!!savedData);

const {
  register,
  control,
  handleSubmit,
  watch,
  reset,
  formState: { errors },
} = useForm<CalculatorFormData>({
  resolver: zodResolver(calculatorSchema),
  defaultValues: savedData || {
    conditions: [{ name: "", rating: 0, is_bilateral: false, bilateral_side: null }],
    dependents: {
      has_spouse: false,
      num_children_under_18: 0,
      num_children_over_18_in_school: 0,
      num_dependent_parents: 0,
      spouse_aid_attendance: false,
    },
    aid_attendance: false,
    housebound: false,
  },
});
```

**IMPORTANT:** Also add `reset` to the destructured return from `useForm` — it is needed for the Clear button.

#### Step 3: Auto-save on every change

Add a `useEffect` that watches the form and saves to localStorage. Place this after the `useForm` call:

```typescript
// Auto-save form data to localStorage on every change
const watchAllFields = watch();
useEffect(() => {
  try {
    localStorage.setItem(CALC_STORAGE_KEY, JSON.stringify(watchAllFields));
  } catch {
    // localStorage full or unavailable — silent fail
  }
}, [watchAllFields]);

// Dismiss the "restored" indicator after 5 seconds
useEffect(() => {
  if (restoredFromStorage) {
    const timer = setTimeout(() => setRestoredFromStorage(false), 5000);
    return () => clearTimeout(timer);
  }
}, [restoredFromStorage]);
```

#### Step 4: "Restored" indicator

Add a subtle notification below the page header when data was restored. Find the area after the page title/description and add:

```tsx
{restoredFromStorage && (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
    <p className="text-sm text-blue-800">
      Your conditions from last time are still here.
    </p>
    <button
      type="button"
      onClick={() => setRestoredFromStorage(false)}
      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
      aria-label="Dismiss notification"
    >
      Got it
    </button>
  </div>
)}
```

**Note the language:** "Your conditions from last time are still here" — not "Restored from localStorage" or "Session data loaded". Write for veterans, not developers.

#### Step 5: "Start Over" button

Add a clear/reset button near the existing "Add Condition" button or at the bottom of the conditions list:

```tsx
<button
  type="button"
  onClick={() => {
    localStorage.removeItem(CALC_STORAGE_KEY);
    reset({
      conditions: [{ name: "", rating: 0, is_bilateral: false, bilateral_side: null }],
      dependents: {
        has_spouse: false,
        num_children_under_18: 0,
        num_children_over_18_in_school: 0,
        num_dependent_parents: 0,
        spouse_aid_attendance: false,
      },
      aid_attendance: false,
      housebound: false,
    });
    setResult(null);
    setRestoredFromStorage(false);
  }}
  className="px-4 py-2 text-sm text-gray-600 hover:text-red-600 border border-gray-300 hover:border-red-300 rounded-lg transition-colors"
  aria-label="Clear all conditions and start over"
>
  Start Over
</button>
```

**Note:** The button says "Start Over" not "Clear Form" or "Reset" — plain language.

## What NOT to Do

- Do NOT create new files or hooks — all changes go in the single calculator page file
- Do NOT persist the calculation `result` to localStorage — it should recalculate fresh
- Do NOT add any backend endpoints or API calls
- Do NOT modify the Zod schema or form validation
- Do NOT change the calculator's visual layout or styling beyond what's described above

## Verification

1. **Enter 3 conditions** with names, ratings, and bilateral flags
2. **Navigate to another page** (click "AI Chat" or "Resources" in the nav)
3. **Navigate back to Calculator** — all 3 conditions should still be there with the "Your conditions from last time are still here" message
4. **Refresh the browser** (F5) — conditions should persist
5. **Click "Start Over"** — form should reset to one empty condition, localStorage cleared
6. **Navigate away and back** — should show empty form (no restoration message)
7. **Open in incognito/private window** — should show empty form (no localStorage data)

## Files Modified

| File | Change |
|------|--------|
| `app/calculator/page.tsx` | Add localStorage persistence, restore indicator, Start Over button |
