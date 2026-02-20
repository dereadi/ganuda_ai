# Jr Instruction: MobileNav Deprecation Comment

**Task ID:** VETASSIST-NAV-002
**Priority:** P3
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026
**Depends On:** VETASSIST-NAV-001 (Shared Header — Steps 1-2 completed)

## Context

The VetAssist Shared Header instruction (#672) succeeded on Steps 1-2 (Header.tsx upgrade + layout.tsx main-content id) but failed on Step 3 (MobileNav deprecation comment). This instruction applies only Step 3 as a standalone fix.

Mobile navigation is now handled inside `Header.tsx` directly. `MobileNav.tsx` is kept for reference but marked deprecated.

## Edit 1: Add deprecation comment to MobileNav

File: `/ganuda/vetassist/frontend/components/MobileNav.tsx`

```
<<<<<<< SEARCH
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
=======
/**
 * @deprecated Mobile navigation is now handled directly inside
 * components/Header.tsx (slide-down menu with Escape key + aria).
 * Kept for reference only. Remove after Feb 28, 2026 if no imports reference it.
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
>>>>>>> REPLACE
```

## Do NOT

- Do not delete MobileNav.tsx — only add the deprecation comment
- Do not modify Header.tsx or layout.tsx — those are already correct
