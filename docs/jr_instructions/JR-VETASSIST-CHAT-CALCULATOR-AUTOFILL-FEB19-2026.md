# Jr Instruction: VetAssist Chat-to-Calculator Autofill

**Task ID**: VETASSIST-AUTOFILL-001
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false
**Council Vote**: #94a2923d35ec7bed (PROCEED WITH CAUTION, 0.70)

## Context

VetAssist Chat, Calculator, and Wizard are completely isolated — no shared state. When a veteran types "I have PTSD at 50% and tinnitus at 10%" in AI Chat, they must manually re-enter that data in the Calculator.

**Goal**: Extract structured condition/rating data from chat responses and let users autofill the Calculator with one click.

**Approach**: Phase 1 — lightweight, client-side only. React Context for cross-page state, regex extraction from chat text, explicit user opt-in button.

**Security**: Session-only storage (cleared on page close), no PII persistence, user must click to transfer.

## Step 1: Create the FormContext for cross-page state sharing

Create `/ganuda/vetassist/frontend/lib/form-context.tsx`

```typescript
'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface ExtractedCondition {
  name: string;
  rating: number;
  is_bilateral: boolean;
}

interface FormContextData {
  conditions: ExtractedCondition[];
  source: { specialist?: string; messageId?: string; timestamp?: string } | null;
}

interface FormContextType {
  formData: FormContextData;
  setConditions: (conditions: ExtractedCondition[], source?: FormContextData['source']) => void;
  clearFormData: () => void;
  hasAutofillData: boolean;
}

const defaultData: FormContextData = { conditions: [], source: null };

const FormContext = createContext<FormContextType>({
  formData: defaultData,
  setConditions: () => {},
  clearFormData: () => {},
  hasAutofillData: false,
});

export function FormProvider({ children }: { children: ReactNode }) {
  const [formData, setFormData] = useState<FormContextData>(defaultData);

  const setConditions = useCallback((conditions: ExtractedCondition[], source?: FormContextData['source']) => {
    setFormData({ conditions, source: source || null });
  }, []);

  const clearFormData = useCallback(() => {
    setFormData(defaultData);
  }, []);

  return (
    <FormContext.Provider value={{
      formData,
      setConditions,
      clearFormData,
      hasAutofillData: formData.conditions.length > 0,
    }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext() {
  return useContext(FormContext);
}
```

## Step 2: Create the ChatDataExtractor utility

Create `/ganuda/vetassist/frontend/lib/chat-data-extractor.ts`

```typescript
import { ExtractedCondition } from './form-context';

/**
 * Extract disability conditions and ratings from natural language text.
 * Handles patterns like:
 *   "PTSD at 50%", "tinnitus rated 10%", "50% for PTSD",
 *   "back condition (40%)", "bilateral knee pain at 10% each"
 */

// Common VA disability conditions for fuzzy matching
const KNOWN_CONDITIONS = [
  'PTSD', 'tinnitus', 'hearing loss', 'back pain', 'lumbar strain',
  'knee pain', 'knee condition', 'migraine', 'migraines', 'sleep apnea',
  'anxiety', 'depression', 'TBI', 'traumatic brain injury',
  'shoulder', 'hip', 'ankle', 'radiculopathy', 'sciatica',
  'GERD', 'IBS', 'sinusitis', 'rhinitis', 'plantar fasciitis',
  'carpal tunnel', 'flat feet', 'pes planus', 'eczema', 'asthma',
];

// Valid VA rating percentages
const VALID_RATINGS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];

// Bilateral keywords
const BILATERAL_KEYWORDS = ['bilateral', 'both', 'left and right', 'each side'];

export function extractConditions(text: string): ExtractedCondition[] {
  const conditions: ExtractedCondition[] = [];
  const seen = new Set<string>();

  // Pattern 1: "CONDITION at/rated XX%" or "CONDITION (XX%)"
  const pattern1 = /([A-Za-z\s]+?)\s+(?:at|rated|is|=)\s*(\d{1,3})\s*%/gi;
  let match;
  while ((match = pattern1.exec(text)) !== null) {
    const name = match[1].trim();
    const rating = parseInt(match[2], 10);
    if (VALID_RATINGS.includes(rating) && name.length > 1) {
      const key = name.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        const isBilateral = BILATERAL_KEYWORDS.some(kw => text.toLowerCase().includes(kw) && text.toLowerCase().indexOf(kw) < text.indexOf(match![0]) + 50);
        conditions.push({ name: capitalize(name), rating, is_bilateral: isBilateral });
      }
    }
  }

  // Pattern 2: "XX% for CONDITION" or "XX% CONDITION"
  const pattern2 = /(\d{1,3})\s*%\s+(?:for\s+)?([A-Za-z\s]{2,30})/gi;
  while ((match = pattern2.exec(text)) !== null) {
    const rating = parseInt(match[1], 10);
    const name = match[2].trim().replace(/[.,;:!?]$/, '');
    if (VALID_RATINGS.includes(rating) && name.length > 1) {
      const key = name.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        conditions.push({ name: capitalize(name), rating, is_bilateral: false });
      }
    }
  }

  return conditions;
}

function capitalize(s: string): string {
  // Keep known acronyms uppercase
  const upper = s.toUpperCase();
  if (['PTSD', 'TBI', 'GERD', 'IBS'].includes(upper)) return upper;
  return s.replace(/\b\w/g, c => c.toUpperCase());
}

export function hasExtractableData(text: string): boolean {
  return extractConditions(text).length > 0;
}
```

## Step 3: Wrap layout with FormProvider

File: `/ganuda/vetassist/frontend/app/layout.tsx`

<<<<<<< SEARCH
import { AuthProvider } from '@/lib/auth-context';
=======
import { AuthProvider } from '@/lib/auth-context';
import { FormProvider } from '@/lib/form-context';
>>>>>>> REPLACE

File: `/ganuda/vetassist/frontend/app/layout.tsx`

<<<<<<< SEARCH
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
=======
        <AuthProvider>
          <FormProvider>
          <div className="min-h-screen flex flex-col">
>>>>>>> REPLACE

File: `/ganuda/vetassist/frontend/app/layout.tsx`

Find the closing `</AuthProvider>` and add `</FormProvider>` before it:

<<<<<<< SEARCH
          </div>
        </AuthProvider>
=======
          </div>
          </FormProvider>
        </AuthProvider>
>>>>>>> REPLACE

## Step 4: Add "Use for Calculator" button to chat page

File: `/ganuda/vetassist/frontend/app/chat/page.tsx`

Find the import section at the top and add:

<<<<<<< SEARCH
'use client';
=======
'use client';

// Chat-to-Calculator autofill (Council Vote #94a2923d35ec7bed)
import { useFormContext } from '@/lib/form-context';
import { extractConditions, hasExtractableData } from '@/lib/chat-data-extractor';
>>>>>>> REPLACE

Then find where assistant messages are rendered. Look for the message bubble or message display section. Add a button after assistant message content that appears when extractable data is detected:

The button should:
- Only show on assistant messages (role === 'assistant')
- Only show when `hasExtractableData(message.content)` returns true
- On click: call `setConditions(extractConditions(message.content))` from FormContext
- Show a toast/notification: "Conditions ready for Calculator"
- Visual: small link-style button below the message, e.g. "Use for Calculator →"

**NOTE**: The exact SEARCH/REPLACE for this step depends on the chat page's message rendering structure. The Jr should read the chat page, find where messages are mapped/rendered, and add the button there. The pattern is:

```typescript
// Inside the message rendering loop, after the message content:
{msg.role === 'assistant' && hasExtractableData(msg.content) && (
  <button
    onClick={() => {
      const conditions = extractConditions(msg.content);
      setConditions(conditions, { timestamp: new Date().toISOString() });
      setAutofillToast(true);
      setTimeout(() => setAutofillToast(false), 3000);
    }}
    className="mt-2 text-sm text-primary hover:text-primary/80 underline transition"
  >
    Use {extractConditions(msg.content).length} condition(s) for Calculator →
  </button>
)}
```

## Step 5: Add autofill merge to Calculator page

File: `/ganuda/vetassist/frontend/app/calculator/page.tsx`

Add import at top:

<<<<<<< SEARCH
'use client';
=======
'use client';

// Chat-to-Calculator autofill (Council Vote #94a2923d35ec7bed)
import { useFormContext } from '@/lib/form-context';
>>>>>>> REPLACE

Then inside the component function, add a merge effect that runs on mount:

```typescript
const { formData, clearFormData, hasAutofillData } = useFormContext();

// Merge autofill data from chat on mount
useEffect(() => {
  if (hasAutofillData && formData.conditions.length > 0) {
    // Convert to calculator format and merge with existing
    const autofilled = formData.conditions.map(c => ({
      name: c.name,
      rating: c.rating,
      bilateral: c.is_bilateral,
    }));
    // Merge: autofill replaces empty state, appends to existing
    setConditions(prev => prev.length === 0 ? autofilled : [...prev, ...autofilled]);
    clearFormData(); // One-time use
  }
}, [hasAutofillData]);
```

**NOTE**: The Jr should find the existing state variable for conditions in the calculator (likely `conditions` or similar useState) and integrate the merge logic. The exact variable name and structure must match what the calculator already uses.

## Verification

1. Build: `cd /ganuda/vetassist/frontend && npm run build`
2. Open chat, send "I have PTSD at 50% and tinnitus at 10%"
3. Verify "Use for Calculator →" button appears on assistant response
4. Click button, navigate to Calculator
5. Verify conditions auto-populate

## Manual Steps (TPM on redfin)

1. After Jr applies changes: rebuild and restart VetAssist frontend
2. Test the full flow in browser
3. Clear .next cache if needed: `rm -rf /ganuda/vetassist/frontend/.next`
