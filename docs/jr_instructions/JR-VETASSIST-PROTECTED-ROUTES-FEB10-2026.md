# Jr Instruction: VetAssist Protected Routes Wrapper

**ID:** JR-VETASSIST-PROTECTED-ROUTES-FEB10-2026
**Kanban:** #1723
**Priority:** P1
**Estimated Effort:** 2-3 hours
**Assigned Node:** SE Jr (any)

---

## Objective

Create a reusable `ProtectedRoute` wrapper component that handles authentication gating for pages that require login. Replace the duplicated manual auth-check `useEffect` pattern currently copy-pasted across Chat, Settings, and Dashboard pages with a single, consistent component. Apply the wrapper to Chat and Calculator routes.

---

## Context

### Current State (the problem)

Three pages currently implement their own auth redirects with slightly different patterns:

- **Chat** (`app/chat/page.tsx`): Uses `useEffect` + `router.push("/login?redirect=/chat")`
- **Settings** (`app/settings/page.tsx`): Uses `useEffect` + `router.push('/login')` (no redirect param)
- **Dashboard** (`app/dashboard/page.tsx` in `src/`): Uses `localStorage.getItem('vetassist_user_id')` directly (different auth mechanism entirely)

There is also a `withAuth` HOC in `lib/auth-context.tsx` (lines 169-196), but it:
1. Does NOT pass a `redirect` query param to the login page
2. Shows a plain "Loading..." text instead of a branded loading state
3. Is never actually used by any page

### Target State

A new `ProtectedRoute` component that:
- Wraps page content and checks `useAuth()` context
- Shows a branded loading spinner while auth state resolves
- Redirects to `/login?redirect=<current_path>` if unauthenticated
- Is imported and used by Chat, Calculator, and future protected pages
- Replaces the manual `useEffect` redirect pattern

### Auth Architecture

- Auth token is stored in `localStorage` as `auth_token` (managed by `apiClient` in `lib/api-client.ts`)
- The `AuthProvider` in `lib/auth-context.tsx` loads the user on mount via `apiClient.getCurrentUser()`
- The `useAuth()` hook returns `{ user, loading, error, login, register, logout, clearError, refreshUser }`
- `user` is `null` when not authenticated; `loading` is `true` during initial token validation

---

## Acceptance Criteria

1. New `ProtectedRoute` component created at `/ganuda/vetassist/frontend/components/ProtectedRoute.tsx`
2. Component checks `useAuth()` for user state
3. While `loading` is true, renders a centered loading spinner (consistent with existing Loader2 pattern)
4. When `loading` is false and `user` is null, redirects to `/login?redirect=<encodeURIComponent(pathname)>`
5. When `loading` is false and `user` is present, renders children
6. Chat page refactored to use `ProtectedRoute` instead of manual auth useEffect
7. Calculator page wrapped with `ProtectedRoute` (currently unprotected -- Kanban #1723 requirement)
8. The existing `withAuth` HOC in `auth-context.tsx` gets a deprecation comment pointing to ProtectedRoute
9. All TypeScript types are clean (no `any`)

---

## Implementation

### Step 1: Create ProtectedRoute Component

Create `/ganuda/vetassist/frontend/components/ProtectedRoute.tsx`

```tsx
'use client';

/**
 * ProtectedRoute - Wraps page content that requires authentication.
 *
 * Usage:
 *   <ProtectedRoute>
 *     <YourPageContent />
 *   </ProtectedRoute>
 *
 * Behavior:
 *   - Shows loading spinner while auth state is resolving
 *   - Redirects to /login?redirect=<current_path> if not authenticated
 *   - Renders children if authenticated
 */

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Optional: override the redirect destination (defaults to current pathname) */
  fallbackRedirect?: string;
}

export default function ProtectedRoute({ children, fallbackRedirect }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      const redirectPath = fallbackRedirect || pathname;
      router.push(`/login?redirect=${encodeURIComponent(redirectPath)}`);
    }
  }, [loading, user, router, pathname, fallbackRedirect]);

  // Auth state still loading -- show branded spinner
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-3" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">Verifying your session...</p>
        </div>
      </div>
    );
  }

  // Not authenticated -- render nothing while redirect happens
  if (!user) {
    return null;
  }

  // Authenticated -- render page content
  return <>{children}</>;
}
```

### Step 2: Refactor Chat Page to Use ProtectedRoute

File: `/ganuda/vetassist/frontend/app/chat/page.tsx`

First, add the ProtectedRoute import near the top imports:

<<<<<<< SEARCH
import { logger } from "@/lib/logger";
import { useAuth } from "@/lib/auth-context";
import type { ChatSession as ChatSessionType, ChatMessage } from "@/lib/types";
=======
import { logger } from "@/lib/logger";
import { useAuth } from "@/lib/auth-context";
import ProtectedRoute from "@/components/ProtectedRoute";
import type { ChatSession as ChatSessionType, ChatMessage } from "@/lib/types";
>>>>>>> REPLACE

Next, remove the manual auth redirect useEffect and the auth loading/guard renders. Replace these three blocks:

<<<<<<< SEARCH
  const { user, loading: authLoading } = useAuth();
  const isAuthenticated = !!user;
  const [sessions, setSessions] = useState<ChatSession[]>([]);
=======
  const { user } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
>>>>>>> REPLACE

<<<<<<< SEARCH
  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login?redirect=/chat");
    }
  }, [authLoading, isAuthenticated, router]);

  // Scroll to bottom when messages change
=======
  // Scroll to bottom when messages change
>>>>>>> REPLACE

Remove the auth loading and guard returns at the bottom of the component (before the main return):

<<<<<<< SEARCH
  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-80px)]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
=======
  return (
    <ProtectedRoute>
    <div className="flex flex-col h-[calc(100vh-80px)]">
>>>>>>> REPLACE

And close the ProtectedRoute wrapper at the end of the component's return:

<<<<<<< SEARCH
    </div>
  );
}

// Message Bubble Component
=======
    </div>
    </ProtectedRoute>
  );
}

// Message Bubble Component
>>>>>>> REPLACE

### Step 3: Wrap Calculator Page with ProtectedRoute

The calculator is currently public. Per Kanban #1723, wrap it so only authenticated users can use it. Non-authenticated users will be redirected to login, then sent back to `/calculator` after signing in.

File: `/ganuda/vetassist/frontend/app/calculator/page.tsx`

Add the import:

<<<<<<< SEARCH
import Link from "next/link";
import { logger } from "@/lib/logger";
=======
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import { logger } from "@/lib/logger";
>>>>>>> REPLACE

Wrap the return in ProtectedRoute:

<<<<<<< SEARCH
  return (
    <div className="bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Page Title */}
=======
  return (
    <ProtectedRoute>
    <div className="bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Page Title */}
>>>>>>> REPLACE

Close the ProtectedRoute wrapper at the end of the calculator return:

<<<<<<< SEARCH
          </div>
        </div>
      </div>
    </div>
  );
}
=======
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
>>>>>>> REPLACE

### Step 4: Deprecate the withAuth HOC

File: `/ganuda/vetassist/frontend/lib/auth-context.tsx`

<<<<<<< SEARCH
/**
 * HOC to protect routes (require authentication)
 */
export function withAuth<P extends object>(
=======
/**
 * @deprecated Use the <ProtectedRoute> component from '@/components/ProtectedRoute'
 * instead. This HOC does not support redirect params or branded loading states.
 * Scheduled for removal after March 2026.
 *
 * HOC to protect routes (require authentication)
 */
export function withAuth<P extends object>(
>>>>>>> REPLACE

### Step 5: Handle redirect param in Login page

The login page currently redirects to `/dashboard` after successful login. It should check for a `redirect` query parameter first.

File: `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`

Add `useSearchParams` to the imports:

<<<<<<< SEARCH
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
=======
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
>>>>>>> REPLACE

Use the redirect param in the login handler:

<<<<<<< SEARCH
  const { login, error, loading, clearError } = useAuth();
  const router = useRouter();
=======
  const { login, error, loading, clearError } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/dashboard';
>>>>>>> REPLACE

Update the submit handler to use the redirect destination:

<<<<<<< SEARCH
    try {
      await login({
        email: formData.email,
        password: formData.password,
        remember_me: formData.remember_me,
      });
      // Router push is handled by auth context
    } catch (err) {
=======
    try {
      await login({
        email: formData.email,
        password: formData.password,
        remember_me: formData.remember_me,
      });
      // Navigate to the originally requested page (or dashboard)
      router.push(redirectTo);
    } catch (err) {
>>>>>>> REPLACE

---

## Verification

After applying all edits:

1. **Chat page**: Navigate to `/chat` while logged out. You should be redirected to `/login?redirect=%2Fchat`. After logging in, you should land on `/chat`.
2. **Calculator page**: Navigate to `/calculator` while logged out. You should be redirected to `/login?redirect=%2Fcalculator`. After logging in, you should land on `/calculator`.
3. **Login redirect**: The `redirect` query param should be visible in the browser URL bar on the login page.
4. **Authenticated access**: When logged in, both `/chat` and `/calculator` should render immediately with a brief loading spinner while the auth token is validated.
5. **Loading state**: The loading spinner should show "Verifying your session..." text with the primary-colored Loader2 icon.
6. **TypeScript**: Run `npx tsc --noEmit` to confirm no type errors.

---

## Notes

- The `ProtectedRoute` component uses `usePathname()` to determine the current page for the redirect URL. This works correctly with Next.js App Router.
- The `fallbackRedirect` prop is provided as an escape hatch for pages that need to redirect to a different path than the current one (e.g., a wizard step that should redirect back to the wizard root).
- The `auth-context.tsx` `login()` method does its own `router.push('/dashboard')`. The login page's explicit `router.push(redirectTo)` will race with it. This is acceptable because the auth context's push only fires on the default path. For a cleaner solution in a future ticket, the auth context's `login()` should accept an optional `redirectTo` parameter instead of hardcoding `/dashboard`.
- Dashboard page (`src/app/dashboard/page.tsx`) uses a completely different auth pattern (localStorage `vetassist_user_id`). Migrating it to ProtectedRoute is out of scope for this ticket.
