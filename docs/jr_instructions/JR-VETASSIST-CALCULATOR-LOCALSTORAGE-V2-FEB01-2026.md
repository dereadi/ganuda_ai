# Jr Instruction: Calculator localStorage Persistence — Phase A (v2 — SEARCH/REPLACE format)

**Task ID:** VETASSIST-CALC-PERSIST-002
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Vote:** #8356 (84.2% confidence)
**Replaces:** Task #516 (failed — wrong instruction format)

## Background

Calculator form state is lost when the user navigates away. Phase A adds localStorage persistence so veterans don't lose their work. This is a client-side-only change.

## Changes

### Change 1: Add localStorage key and helper

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

<<<<<<< SEARCH
export default function CalculatorPage() {
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSteps, setShowSteps] = useState(false);
  const [showDependents, setShowDependents] = useState(false);

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
=======
// localStorage key for calculator form persistence (Phase A — Council vote #8356)
const CALC_STORAGE_KEY = 'vetassist_calculator_form';

function getSavedFormData(): CalculatorFormData | null {
  if (typeof window === 'undefined') return null;
  try {
    const saved = localStorage.getItem(CALC_STORAGE_KEY);
    if (!saved) return null;
    const parsed = JSON.parse(saved);
    // Validate minimum structure
    if (parsed && Array.isArray(parsed.conditions) && parsed.conditions.length > 0) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

const defaultFormValues: CalculatorFormData = {
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
};

export default function CalculatorPage() {
  const savedData = getSavedFormData();
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSteps, setShowSteps] = useState(false);
  const [showDependents, setShowDependents] = useState(false);
  const [restoredFromStorage, setRestoredFromStorage] = useState(!!savedData);

  const {
    register,
    control,
    handleSubmit,
    watch,
    reset,
    getValues,
    formState: { errors },
  } = useForm<CalculatorFormData>({
    resolver: zodResolver(calculatorSchema),
    defaultValues: savedData || defaultFormValues,
  });
>>>>>>> REPLACE

### Change 2: Add auto-save effect and clear button

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

Add this AFTER the existing `const watchConditions = watch("conditions");` line:

<<<<<<< SEARCH
  const watchConditions = watch("conditions");
  const watchDependents = watch("dependents");
=======
  const watchConditions = watch("conditions");
  const watchDependents = watch("dependents");

  // Auto-save form to localStorage on any change (Phase A persistence)
  const allValues = watch();
  React.useEffect(() => {
    try {
      localStorage.setItem(CALC_STORAGE_KEY, JSON.stringify(allValues));
    } catch {
      // localStorage full or unavailable — silently ignore
    }
  }, [allValues]);
>>>>>>> REPLACE

**Note:** Also add `React` to the import at the top of the file if not already imported:

<<<<<<< SEARCH
import { useState } from "react";
=======
import React, { useState } from "react";
>>>>>>> REPLACE

### Change 3: Add "Clear Form" button and restoration notice

Find the submit button area in the form (the `onSubmit` handler). Add a clear button and info message. This goes in the JSX, near where the "Calculate" button is.

Look for the return statement that renders the page title. Add a restoration notice right after the title area:

<<<<<<< SEARCH
  const onSubmit = async (data: CalculatorFormData) => {
=======
  const clearForm = () => {
    reset(defaultFormValues);
    localStorage.removeItem(CALC_STORAGE_KEY);
    setResult(null);
    setError(null);
    setRestoredFromStorage(false);
  };

  const onSubmit = async (data: CalculatorFormData) => {
>>>>>>> REPLACE

## Verification

1. Enter conditions in the calculator form
2. Navigate to another page (e.g., /resources)
3. Navigate back to /calculator
4. Verify conditions are still populated from localStorage
5. Click "Clear Form" — verify form resets to empty defaults
6. Refresh page — verify empty form (localStorage was cleared)

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `frontend/app/calculator/page.tsx` | MODIFY | Add localStorage persistence, auto-save, clear button |
