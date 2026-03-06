# Jr Instruction: VetAssist Chat-to-Calculator — Wire into Pages (v2, Part 2 of 2)

**Task ID:** CHAT-CALC-WIRE-v2
**Kanban:** #1850
**Priority:** 6
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Part 2: Wire the FormContext (created in Part 1) into layout.tsx so chat can pass condition data to calculator. Depends on Part 1 completing first.

---

## Step 1: Add FormProvider to layout

File: `/ganuda/vetassist/frontend/app/layout.tsx`

```
<<<<<<< SEARCH
import { AuthProvider } from "@/lib/auth-context";
import Header from "@/components/Header";
=======
import { AuthProvider } from "@/lib/auth-context";
import { FormProvider } from "@/lib/form-context";
import Header from "@/components/Header";
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
=======
        <AuthProvider>
          <FormProvider>
          <div className="min-h-screen flex flex-col">
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
          </div>
        </AuthProvider>
=======
          </div>
          </FormProvider>
        </AuthProvider>
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/vetassist/frontend && npx next build 2>&1 | tail -5
```

## What NOT to Change

- Do NOT modify form-context.tsx or chat-data-extractor.ts (created in Part 1)
- Do NOT modify chat/page.tsx or calculator/page.tsx in this instruction (future enhancement)
