# Jr Instruction: VetAssist Protected Routes - Frontend

**Task ID:** VETASSIST-PROTECTED-FRONTEND
**Priority:** P1
**Date:** January 24, 2026
**Phase:** Auth Hardening (3 of 3)

## Objective

Add frontend middleware to protect authenticated routes. Redirect unauthenticated users to /login.

## Files to Modify (3 files)

1. `/ganuda/vetassist/frontend/middleware.ts` (create)
2. `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`
3. `/ganuda/vetassist/frontend/app/dashboard/page.tsx`

## Required Changes

### 1. middleware.ts - Create auth middleware

Create `/ganuda/vetassist/frontend/middleware.ts`:

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Routes that require authentication
const PROTECTED_ROUTES = [
  '/dashboard',
  '/wizard',
  '/profile',
  '/claims',
];

// Routes that should redirect authenticated users
const AUTH_ROUTES = [
  '/login',
  '/register',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Get token from cookie
  const token = request.cookies.get('vetassist_token')?.value;
  const isAuthenticated = !!token;

  // Check if accessing protected route
  const isProtectedRoute = PROTECTED_ROUTES.some(route =>
    pathname.startsWith(route)
  );

  // Check if accessing auth route
  const isAuthRoute = AUTH_ROUTES.some(route =>
    pathname.startsWith(route)
  );

  // Redirect unauthenticated users from protected routes
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users from auth routes
  if (isAuthRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
```

### 2. wizard/[sessionId]/page.tsx - Add auth check

Add client-side auth check at the top of the component:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function WizardPage({ params }: { params: { sessionId: string } }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('vetassist_token');
    if (!token) {
      router.push(`/login?redirect=/wizard/${params.sessionId}`);
      return;
    }
    setIsLoading(false);
  }, [router, params.sessionId]);

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  // ... rest of component
}
```

### 3. dashboard/page.tsx - Add auth check

Add client-side auth check:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('vetassist_token');
    if (!token) {
      router.push('/login?redirect=/dashboard');
      return;
    }

    // Fetch user profile
    fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Not authenticated');
      return res.json();
    })
    .then(data => {
      setUser(data);
      setIsLoading(false);
    })
    .catch(() => {
      localStorage.removeItem('vetassist_token');
      router.push('/login?redirect=/dashboard');
    });
  }, [router]);

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  // ... rest of component
}
```

## Output

Generate each file completely.

## Success Criteria

- [ ] middleware.ts created and protects routes
- [ ] Wizard page checks authentication before rendering
- [ ] Dashboard page checks authentication before rendering
- [ ] Unauthenticated users redirected to /login with redirect param
