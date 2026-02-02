# Jr Instruction: Add Tooltips to Calculator Fields (v2 — SEARCH/REPLACE format)

**Task ID:** VETASSIST-TOOLTIPS-002
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Created:** February 1, 2026
**Created By:** TPM (Claude Opus 4.5)
**Council Vote:** #8361 (tooltip copy approved)
**Replaces:** Task #517 (partial — components created, calculator page edit failed)

## Background

Components `HelpTip.tsx` and `PageHelpLink.tsx` were already created by task #517. This instruction ONLY adds the tooltips to the calculator page and the help link.

## Pre-existing Components

These already exist — do NOT recreate:
- `/ganuda/vetassist/frontend/components/HelpTip.tsx` (37 lines)
- `/ganuda/vetassist/frontend/components/PageHelpLink.tsx` (21 lines)

## Changes

### Change 1: Add imports for HelpTip and PageHelpLink

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

<<<<<<< SEARCH
import Link from "next/link";
import { logger } from "@/lib/logger";
=======
import Link from "next/link";
import { logger } from "@/lib/logger";
import HelpTip from "@/components/HelpTip";
import PageHelpLink from "@/components/PageHelpLink";
>>>>>>> REPLACE

### Change 2: Add PageHelpLink to the page

Find where the page title "VA Disability Calculator" is rendered and add the help link nearby. Look for the `<Calculator` icon usage or the h1 title in the JSX. Add the PageHelpLink component right after:

**File:** `/ganuda/vetassist/frontend/app/calculator/page.tsx`

Find the page header area (the h1 with "VA Disability Calculator") and add after the subtitle paragraph:

This change is context-dependent — the Jr should look for the heading block in the return JSX and insert:

```tsx
<PageHelpLink href="/resources" text="Need help understanding VA ratings?" />
```

### Change 3: Add HelpTip tooltips to form field labels

The Jr should find each form field label in the JSX and add `<HelpTip>` after the label text. Here are the exact tooltip texts (Council Vote #8361):

| Field | Tooltip Text |
|-------|-------------|
| Condition Name | "The medical name for your issue — like PTSD, tinnitus, or knee pain. Use whatever your doctor calls it." |
| Disability Rating (%) | "The percentage the VA assigned for this condition. If you haven't filed yet, enter what you think it might be rated at." |
| Bilateral | "Check this if the same problem affects both sides of your body — like both knees, both ears, or both shoulders." |
| Dependents | "If you have a spouse, kids, or parents who depend on you, your monthly payment may be higher. This only applies if your combined rating is 30% or more." |
| Aid & Attendance | "Check this if you need someone to help you with everyday things like bathing, dressing, or eating because of your service-connected disabilities." |
| Housebound | "Check this if your disabilities keep you mostly at home. This is a separate benefit from Aid and Attendance." |

Example pattern for adding to a label:

```tsx
{/* Before: */}
<label>Condition Name</label>

{/* After: */}
<label>Condition Name<HelpTip text="The medical name for your issue — like PTSD, tinnitus, or knee pain. Use whatever your doctor calls it." /></label>
```

**Note:** Since the exact label JSX varies, the Jr should search the file for each label text and add the corresponding HelpTip inline.

## Verification

1. Hover over "Condition Name" label — tooltip appears
2. Hover over "Disability Rating (%)" label — tooltip appears
3. Hover over "Bilateral" checkbox label — tooltip appears
4. Click the "Need help" link — navigates to /resources
5. Tooltips work on mobile (tap to toggle)

## Files Summary

| File | Action | Change |
|------|--------|--------|
| `frontend/app/calculator/page.tsx` | MODIFY | Add imports, page help link, HelpTip tooltips on all fields |
