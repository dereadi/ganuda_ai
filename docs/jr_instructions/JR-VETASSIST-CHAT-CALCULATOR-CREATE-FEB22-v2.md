# Jr Instruction: VetAssist Chat-to-Calculator — Create Shared Context (v2, Part 1 of 2)

**Task ID:** CHAT-CALC-CREATE-v2
**Kanban:** #1850
**Priority:** 5
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Create a shared React context that allows chat to pass extracted condition data to the calculator for autofill. Part 1 creates the new files. Part 2 wires them into existing pages.

---

## Step 1: Create FormContext for cross-page data sharing

Create `/ganuda/vetassist/frontend/lib/form-context.tsx`

```typescript
"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ExtractedCondition {
  name: string;
  rating: number;
  source: string;  // "chat" or "wizard"
}

interface FormContextType {
  extractedConditions: ExtractedCondition[];
  setExtractedConditions: (conditions: ExtractedCondition[]) => void;
  addExtractedConditions: (conditions: ExtractedCondition[]) => void;
  clearExtracted: () => void;
}

const FormContext = createContext<FormContextType | null>(null);

export function FormProvider({ children }: { children: ReactNode }) {
  const [extractedConditions, setExtractedConditions] = useState<ExtractedCondition[]>([]);

  const addExtractedConditions = (newConditions: ExtractedCondition[]) => {
    setExtractedConditions(prev => {
      // Deduplicate by name
      const existing = new Set(prev.map(c => c.name.toLowerCase()));
      const unique = newConditions.filter(c => !existing.has(c.name.toLowerCase()));
      return [...prev, ...unique];
    });
  };

  const clearExtracted = () => setExtractedConditions([]);

  return (
    <FormContext.Provider value={{ extractedConditions, setExtractedConditions, addExtractedConditions, clearExtracted }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext() {
  const ctx = useContext(FormContext);
  if (!ctx) {
    // Return a no-op context if FormProvider is not mounted (graceful degradation)
    return {
      extractedConditions: [],
      setExtractedConditions: () => {},
      addExtractedConditions: () => {},
      clearExtracted: () => {},
    };
  }
  return ctx;
}
```

---

## Step 2: Create chat data extractor utility

Create `/ganuda/vetassist/frontend/lib/chat-data-extractor.ts`

```typescript
/**
 * Extract condition names and ratings from chat messages.
 * Looks for patterns like "PTSD 70%", "tinnitus (10%)", "back pain rated at 30%"
 */

interface ExtractedCondition {
  name: string;
  rating: number;
  source: string;
}

const COMMON_CONDITIONS = [
  "PTSD", "tinnitus", "hearing loss", "back pain", "knee pain",
  "sleep apnea", "depression", "anxiety", "migraines", "radiculopathy",
  "plantar fasciitis", "TBI", "GERD", "hypertension", "diabetes",
  "shoulder pain", "neck pain", "sciatica", "flat feet", "sinusitis"
];

export function extractConditions(text: string): ExtractedCondition[] {
  const conditions: ExtractedCondition[] = [];
  const seen = new Set<string>();

  // Pattern: "condition 70%" or "condition (70%)" or "condition rated at 70%"
  const ratingPattern = /(\w[\w\s]{2,30}?)\s*(?:\(|rated\s+at\s+|at\s+)?(\d{1,3})\s*%/gi;
  let match;

  while ((match = ratingPattern.exec(text)) !== null) {
    const name = match[1].trim();
    const rating = parseInt(match[2]);
    if (rating >= 0 && rating <= 100 && rating % 10 === 0 && !seen.has(name.toLowerCase())) {
      seen.add(name.toLowerCase());
      conditions.push({ name, rating, source: "chat" });
    }
  }

  // Also look for known condition names without explicit ratings
  for (const cond of COMMON_CONDITIONS) {
    const lower = text.toLowerCase();
    if (lower.includes(cond.toLowerCase()) && !seen.has(cond.toLowerCase())) {
      seen.add(cond.toLowerCase());
      conditions.push({ name: cond, rating: 0, source: "chat" });
    }
  }

  return conditions;
}
```

---

## Verification

```text
ls -la /ganuda/vetassist/frontend/lib/form-context.tsx
ls -la /ganuda/vetassist/frontend/lib/chat-data-extractor.ts
```

## What NOT to Change

- Do NOT modify any existing files in this instruction
- Part 2 handles wiring into layout, chat, and calculator
