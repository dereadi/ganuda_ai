# JR Instruction: VetAssist Protected Routes

## Metadata
```yaml
task_id: vetassist_protected_routes
priority: 2
ticket_id: 1723
assigned_to: Code Jr.
target: frontend
```

## Problem

Chat and Calculator pages are accessible without login. User data isn't saved because there's no authenticated user context.

## Solution

The `withAuth` HOC already exists in `/ganuda/vetassist/frontend/lib/auth-context.tsx`. We need to apply it.

### Task 1: Protect Chat Page

In `/ganuda/vetassist/frontend/app/chat/page.tsx`:

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/chat');
    }
  }, [isLoading, isAuthenticated, router]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-800"></div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Rest of chat component...
  return (
    // existing JSX
  );
}
```

### Task 2: Optional - Protect Calculator (Partial)

Calculator can work without auth, but saving results requires auth.

Option A: Keep calculator public, show "Sign in to save" prompt:

```typescript
const { isAuthenticated } = useAuth();

// In the results section:
{!isAuthenticated && (
  <div className="mt-4 p-4 bg-blue-50 rounded border border-blue-200">
    <p className="text-blue-800">
      <Link href="/login?redirect=/calculator" className="underline font-medium">
        Sign in
      </Link>{' '}
      to save your calculations and access them later.
    </p>
  </div>
)}
```

Option B: Fully protect calculator (same pattern as chat).

### Task 3: Create withAuth HOC (Alternative)

If you prefer a reusable HOC pattern:

```typescript
// /ganuda/vetassist/frontend/lib/withAuth.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './auth-context';

export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  redirectTo: string = '/login'
) {
  return function AuthenticatedComponent(props: P) {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        const currentPath = window.location.pathname;
        router.push(`${redirectTo}?redirect=${currentPath}`);
      }
    }, [isLoading, isAuthenticated, router]);

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-800"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}
```

Usage:
```typescript
// In chat/page.tsx
export default withAuth(ChatPageContent);
```

### Task 4: Update Navigation for Auth State

Show different nav items based on auth:

```typescript
const { isAuthenticated, user, logout } = useAuth();

// In navigation:
{isAuthenticated ? (
  <div className="flex items-center gap-4">
    <span className="text-gray-600">Hi, {user?.first_name || 'Veteran'}</span>
    <button onClick={logout} className="text-gray-600 hover:text-gray-900">
      Sign Out
    </button>
  </div>
) : (
  <Link href="/login" className="text-blue-800 hover:underline">
    Sign In
  </Link>
)}
```

## Verification

1. Log out
2. Navigate to /chat → Should redirect to /login?redirect=/chat
3. Log in → Should redirect back to /chat
4. Refresh /chat while logged in → Should stay on page
5. Calculator should show "Sign in to save" prompt

---

*Cherokee AI Federation - For the Seven Generations*
