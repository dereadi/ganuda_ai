# Jr Instruction: VetAssist VA Session Management - Phase 5: Frontend Integration

## Priority: HIGH
## Estimated Effort: Medium
## Dependencies: Phase 1-3

---

## Objective

Update the VetAssist frontend to:
1. Handle JWT token from VA OAuth redirect
2. Store token securely (httpOnly cookie preferred, localStorage fallback)
3. Create auth context/provider for app-wide auth state
4. Implement protected route wrapper

---

## Context

After successful VA OAuth, the backend redirects to `/va-success?token=JWT&expires=ISO_DATE`. The frontend needs to capture this token, store it, and use it for subsequent API calls.

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/frontend/app/contexts/AuthContext.tsx`

```typescript
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  vaLinked: boolean;
  vaIcn?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string, expiresAt: string) => void;
  logout: () => Promise<void>;
  getToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from stored token on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('vetassist_token');
    const storedExpiry = localStorage.getItem('vetassist_token_expires');

    if (storedToken && storedExpiry) {
      const expiresAt = new Date(storedExpiry);
      if (expiresAt > new Date()) {
        setToken(storedToken);
        decodeAndSetUser(storedToken);
      } else {
        // Token expired, clear it
        localStorage.removeItem('vetassist_token');
        localStorage.removeItem('vetassist_token_expires');
      }
    }

    setIsLoading(false);
  }, []);

  const decodeAndSetUser = (jwt: string) => {
    try {
      // Decode JWT payload (base64)
      const payload = JSON.parse(atob(jwt.split('.')[1]));
      setUser({
        id: payload.sub,
        vaLinked: payload.va_linked || false,
        vaIcn: payload.va_icn
      });
    } catch (e) {
      console.error('Failed to decode token:', e);
      setUser(null);
    }
  };

  const login = (newToken: string, expiresAt: string) => {
    localStorage.setItem('vetassist_token', newToken);
    localStorage.setItem('vetassist_token_expires', expiresAt);
    setToken(newToken);
    decodeAndSetUser(newToken);
  };

  const logout = async () => {
    try {
      // Call backend to revoke session
      if (token) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (e) {
      console.error('Logout API call failed:', e);
    }

    // Clear local state regardless of API result
    localStorage.removeItem('vetassist_token');
    localStorage.removeItem('vetassist_token_expires');
    setToken(null);
    setUser(null);
  };

  const getToken = () => {
    // Check expiry before returning
    const storedExpiry = localStorage.getItem('vetassist_token_expires');
    if (storedExpiry && new Date(storedExpiry) <= new Date()) {
      logout();
      return null;
    }
    return token;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        getToken
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

---

### File: `/ganuda/vetassist/frontend/app/components/ProtectedRoute.tsx`

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Redirect to login
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
```

---

### File: `/ganuda/vetassist/frontend/app/(auth)/va-success/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';

export default function VASuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get('token');
    const expires = searchParams.get('expires');

    if (!token) {
      setStatus('error');
      setError('No authentication token received');
      return;
    }

    try {
      // Store token and update auth state
      login(token, expires || new Date(Date.now() + 30 * 60 * 1000).toISOString());
      setStatus('success');

      // Redirect to dashboard after brief success message
      setTimeout(() => {
        router.push('/dashboard');
      }, 1500);

    } catch (e) {
      setStatus('error');
      setError('Failed to process authentication');
    }
  }, [searchParams, login, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        {status === 'processing' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Completing sign in...
            </h2>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Successfully signed in with VA.gov
            </h2>
            <p className="mt-2 text-gray-600">
              Redirecting to your dashboard...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Sign in failed
            </h2>
            <p className="mt-2 text-red-600">
              {error || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### File: `/ganuda/vetassist/frontend/app/(auth)/va-error/page.tsx`

```typescript
'use client';

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

const errorMessages: Record<string, string> = {
  'token_exchange_failed': 'We could not complete the sign-in process with VA.gov. Please try again.',
  'unknown': 'An unexpected error occurred during sign-in.',
  'session_expired': 'Your session has expired. Please sign in again.',
};

export default function VAErrorPage() {
  const searchParams = useSearchParams();
  const errorCode = searchParams.get('error') || 'unknown';
  const errorMessage = errorMessages[errorCode] || errorMessages['unknown'];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 text-center">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
          <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h2 className="text-2xl font-bold text-gray-900">
          Sign-in Error
        </h2>

        <p className="text-gray-600">
          {errorMessage}
        </p>

        <div className="mt-6 space-y-3">
          <Link
            href="/api/v1/auth/va/login"
            className="block w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try signing in again
          </Link>

          <Link
            href="/"
            className="block w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Return to home
          </Link>
        </div>

        <p className="text-sm text-gray-500">
          If this problem persists, please contact support or try again later.
        </p>
      </div>
    </div>
  );
}
```

---

### Update Root Layout

Modify `/ganuda/vetassist/frontend/app/layout.tsx` to include AuthProvider:

```typescript
import { AuthProvider } from './contexts/AuthContext';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

## API Client Helper

### File: `/ganuda/vetassist/frontend/app/lib/api.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('vetassist_token');

  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  // Handle 401 - token expired
  if (response.status === 401) {
    localStorage.removeItem('vetassist_token');
    localStorage.removeItem('vetassist_token_expires');
    window.location.href = '/';
  }

  return response;
}
```

---

## Verification

1. Build frontend:
```bash
cd /ganuda/vetassist/frontend
npm run build
```

2. Test OAuth flow:
- Navigate to https://vetassist.ganuda.us
- Click "Login with VA.gov"
- Complete VA login
- Verify redirect to /va-success shows success message
- Verify redirect to /dashboard
- Check localStorage for token

3. Test protected route:
- Clear localStorage
- Navigate directly to /dashboard
- Verify redirect to home page

---

## Success Criteria

- [ ] AuthContext implemented
- [ ] va-success page handles JWT
- [ ] va-error page shows appropriate messages
- [ ] ProtectedRoute wrapper working
- [ ] Token stored in localStorage
- [ ] Auth state persists across page refresh

---

*Cherokee AI Federation - For Seven Generations*
