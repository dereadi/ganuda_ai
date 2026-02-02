# Jr Instruction: Field Tooltips and Per-Page Help Links

**Task ID:** VETASSIST-TOOLTIPS-001
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Votes:** #8359 (UX review), #8361 (tooltip copy)

## Goal

Add hover/tap tooltips to form fields across VetAssist, plus a help link on each major page. Keep all existing field labels unchanged — the tooltips provide plain-English explanations for veterans who need them, without cluttering the UI for those who don't.

## Files to Create/Modify

### File 1: NEW — Tooltip Component

**Create:** `/ganuda/vetassist/frontend/components/HelpTip.tsx`

```tsx
'use client';

import { useState } from 'react';

interface HelpTipProps {
  text: string;
}

export default function HelpTip({ text }: HelpTipProps) {
  const [show, setShow] = useState(false);

  return (
    <span className="relative inline-flex items-center ml-1">
      <button
        type="button"
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-200 hover:bg-blue-100 text-gray-500 hover:text-blue-600 text-xs font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onFocus={() => setShow(true)}
        onBlur={() => setShow(false)}
        onClick={() => setShow(!show)}
        aria-label="More info"
      >
        ?
      </button>
      {show && (
        <div
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-gray-800 rounded-lg shadow-lg max-w-xs w-max pointer-events-none"
        >
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
        </div>
      )}
    </span>
  );
}
```

Key design choices:
- Small `?` circle icon — unobtrusive, universally understood
- Shows on hover (desktop) AND on click/tap (mobile/tablet — important for older users)
- Shows on focus (keyboard accessible)
- Dark tooltip with arrow — high contrast, easy to read
- `max-w-xs` keeps tooltip text from running too wide
- No external dependencies

### File 2: NEW — Per-Page Help Link Component

**Create:** `/ganuda/vetassist/frontend/components/PageHelpLink.tsx`

```tsx
'use client';

import Link from 'next/link';

interface PageHelpLinkProps {
  href: string;
  text?: string;
}

export default function PageHelpLink({ href, text = 'Need help with this page?' }: PageHelpLinkProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 mb-4">
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <Link href={href} className="underline hover:no-underline">
        {text}
      </Link>
    </div>
  );
}
```

### File 3: MODIFY — Calculator Page

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

**Add imports at top:**
```tsx
import HelpTip from '@/components/HelpTip';
import PageHelpLink from '@/components/PageHelpLink';
```

**Add help link** below the page title/description area (before the form):
```tsx
<PageHelpLink
  href="/resources/understanding-va-combined-ratings"
  text="New to VA ratings? Learn how the combined rating works"
/>
```

**Add HelpTip to each field label.** For every field, find the label text and add the HelpTip component next to it. Here are the specific tooltips:

#### Condition Name
Find the label for the condition name input and add:
```tsx
Condition Name
<HelpTip text="The medical name for your issue — like PTSD, tinnitus, or knee pain. Use whatever your doctor calls it." />
```

#### Disability Rating (%)
Find the label for the rating input and add:
```tsx
Disability Rating (%)
<HelpTip text="The percentage the VA assigned for this condition. If you haven't filed yet, enter what you think it might be rated at." />
```

#### Bilateral condition checkbox
Find the label for the bilateral checkbox and add:
```tsx
Bilateral condition
<HelpTip text="Check this if the same problem affects both sides of your body — like both knees, both ears, or both shoulders." />
```

#### Which Side?
Find the label for the bilateral side selector and add:
```tsx
Which Side?
<HelpTip text="Pick which side is affected. If it's both sides, check the bilateral box above instead." />
```

#### Dependents section header
Find the dependents section header and add:
```tsx
Dependents (Optional)
<HelpTip text="If you have a spouse, kids, or parents who depend on you, your monthly payment may be higher. This only applies if your combined rating is 30% or more." />
```

#### Aid and Attendance
Find the aid and attendance checkbox label and add:
```tsx
Aid and Attendance
<HelpTip text="Check this if you need someone to help you with everyday things like bathing, dressing, or eating because of your service-connected disabilities." />
```

#### Housebound
Find the housebound checkbox label and add:
```tsx
Housebound
<HelpTip text="Check this if your disabilities keep you mostly at home. This is a separate benefit from Aid and Attendance." />
```

#### Combined Rating result (in the results display area)
Find where the combined rating result is displayed and add nearby:
```tsx
<HelpTip text="The VA doesn't just add your ratings together. They use a formula called combined ratings that starts with your highest rating first. This is your estimated combined result." />
```

#### Bilateral Factor (in calculation steps, if shown)
Find where bilateral factor appears in the step-by-step breakdown and add:
```tsx
<HelpTip text="When the same problem affects both sides of your body, the VA adds an extra 10% to those ratings before combining. This usually helps your overall number." />
```

### File 4: MODIFY — AI Chat Page

**File:** `/ganuda/vetassist/frontend/app/chat/page.tsx`

**Add imports:**
```tsx
import PageHelpLink from '@/components/PageHelpLink';
```

**Add help link** in the chat page, above or near the message input area:
```tsx
<PageHelpLink
  href="/resources/using-vetassist-ai-chat"
  text="Tips for getting the best answers from the AI assistant"
/>
```

### File 5: MODIFY — Resources Page

**File:** `/ganuda/vetassist/frontend/app/resources/page.tsx`

**Add import and help link** below the page header:
```tsx
import PageHelpLink from '@/components/PageHelpLink';
```

```tsx
<PageHelpLink
  href="/resources/getting-started-with-va-claims"
  text="Brand new to VA claims? Start here"
/>
```

### File 6: MODIFY — Dashboard Page

**File:** `/ganuda/vetassist/frontend/app/dashboard/page.tsx`

**Add import and help link:**
```tsx
import PageHelpLink from '@/components/PageHelpLink';
```

```tsx
<PageHelpLink
  href="/resources/understanding-your-dashboard"
  text="What does everything on this page mean?"
/>
```

### File 7: MODIFY — Evidence Analysis Page

If an evidence analysis page exists at `app/evidence/page.tsx` or similar, add:
```tsx
import PageHelpLink from '@/components/PageHelpLink';
```

```tsx
<PageHelpLink
  href="/resources/gathering-evidence-for-your-claim"
  text="What kind of evidence does the VA need?"
/>
```

## Tooltip Copy Reference (all in one place)

| Field | Tooltip Text |
|-------|-------------|
| Condition Name | The medical name for your issue — like PTSD, tinnitus, or knee pain. Use whatever your doctor calls it. |
| Disability Rating (%) | The percentage the VA assigned for this condition. If you haven't filed yet, enter what you think it might be rated at. |
| Bilateral condition | Check this if the same problem affects both sides of your body — like both knees, both ears, or both shoulders. |
| Which Side? | Pick which side is affected. If it's both sides, check the bilateral box above instead. |
| Dependents (Optional) | If you have a spouse, kids, or parents who depend on you, your monthly payment may be higher. This only applies if your combined rating is 30% or more. |
| Aid and Attendance | Check this if you need someone to help you with everyday things like bathing, dressing, or eating because of your service-connected disabilities. |
| Housebound | Check this if your disabilities keep you mostly at home. This is a separate benefit from Aid and Attendance. |
| Combined Rating | The VA doesn't just add your ratings together. They use a formula that starts with your highest rating first. This is your estimated combined result. |
| Bilateral Factor | When the same problem affects both sides of your body, the VA adds an extra 10% to those ratings before combining. This usually helps your overall number. |

## What NOT to Do

- Do NOT change any existing field labels or form behavior
- Do NOT add any npm dependencies — pure Tailwind + React
- Do NOT modify the Zod validation schema
- Do NOT change the calculator's math or API calls
- Do NOT create the help article pages themselves (those will be separate tasks)
- If a help link destination doesn't exist yet as a Resources article, the link will 404 — that's fine, articles will be created separately

## Verification

1. **Hover over any `?` icon** on the calculator — tooltip should appear with plain-English explanation
2. **Tap the `?` icon on mobile** — tooltip should toggle on/off
3. **Tab to a `?` icon with keyboard** — tooltip should appear on focus
4. **Check that tooltips don't overflow** the page edge on narrow screens
5. **Verify help links** appear on Calculator, AI Chat, Resources, Dashboard pages
6. **Verify no visual regression** — existing layout and styling unchanged

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `components/HelpTip.tsx` | CREATE | Reusable tooltip component |
| `components/PageHelpLink.tsx` | CREATE | Per-page help link component |
| `app/calculator/page.tsx` | MODIFY | Add HelpTip to 9 fields, add PageHelpLink |
| `app/chat/page.tsx` | MODIFY | Add PageHelpLink |
| `app/resources/page.tsx` | MODIFY | Add PageHelpLink |
| `app/dashboard/page.tsx` | MODIFY | Add PageHelpLink |
| `app/evidence/page.tsx` (if exists) | MODIFY | Add PageHelpLink |
