# Jr Instruction: VetAssist VA OAuth Frontend Integration
## Task ID: VetAssist Sprint 4 - Task 3
## Priority: P1
## Estimated Complexity: Medium

---

## Objective

Integrate VA.gov OAuth login into the VetAssist frontend. Veterans should be able to authenticate with their VA credentials (ID.me, Login.gov, or DS Logon) to access their claim status.

---

## Background

Backend VA OAuth endpoints are complete:
- `GET /api/v1/auth/va/login` - Redirects to VA.gov OAuth
- `GET /api/v1/auth/va/callback` - Handles OAuth callback from VA
- `POST /api/v1/auth/va/refresh` - Refreshes expired tokens

Now we need frontend pages to:
1. Offer "Login with VA.gov" option
2. Handle successful authentication redirects
3. Handle error redirects
4. Store VA session state

---

## Implementation Steps

### Step 1: Create VA Success Page

Create `/ganuda/vetassist/frontend/app/(auth)/va-success/page.tsx`:

```tsx
'use client';

/**
 * VA OAuth Success Page
 * Handles successful VA.gov authentication callback
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

export default function VASuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  const sessionId = searchParams.get('session');

  useEffect(() => {
    // Store VA authentication state
    if (sessionId) {
      localStorage.setItem('va_session_id', sessionId);
      localStorage.setItem('va_authenticated', 'true');
      localStorage.setItem('va_auth_time', new Date().toISOString());
      setStatus('success');

      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);
    } else {
      setStatus('success');
    }
  }, [sessionId, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-100 py-12 px-4">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
        {status === 'loading' ? (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto"></div>
            <h2 className="text-2xl font-bold text-gray-900">Verifying...</h2>
          </>
        ) : (
          <>
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
              <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <h2 className="text-3xl font-extrabold text-gray-900">
              VA.gov Login Successful
            </h2>

            <p className="text-gray-600">
              You've successfully authenticated with VA.gov. You can now access your claim status and VA records.
            </p>

            <div className="bg-blue-50 rounded-lg p-4 mt-4">
              <p className="text-sm text-blue-800">
                Redirecting to your dashboard in 3 seconds...
              </p>
            </div>

            <div className="mt-6 space-y-3">
              <Link
                href="/dashboard"
                className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Go to Dashboard
              </Link>

              <Link
                href="/wizard"
                className="block w-full py-3 px-4 rounded-md shadow border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50"
              >
                Start New Claim
              </Link>
            </div>

            <p className="text-xs text-gray-500 mt-6">
              Your VA session will remain active for 30 minutes of inactivity.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
```

### Step 2: Create VA Error Page

Create `/ganuda/vetassist/frontend/app/(auth)/va-error/page.tsx`:

```tsx
'use client';

/**
 * VA OAuth Error Page
 * Handles failed VA.gov authentication
 */

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

const ERROR_MESSAGES: Record<string, string> = {
  token_exchange_failed: 'We couldn\'t complete the login with VA.gov. This may be a temporary issue.',
  access_denied: 'Access was denied. Please ensure you authorized VetAssist to access your VA information.',
  invalid_state: 'The login session expired or was invalid. Please try again.',
  unknown: 'An unexpected error occurred during login.',
};

export default function VAErrorPage() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error') || 'unknown';
  const errorMessage = ERROR_MESSAGES[error] || ERROR_MESSAGES.unknown;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-100 py-12 px-4">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
          <svg className="h-10 w-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>

        <h2 className="text-3xl font-extrabold text-gray-900">
          VA.gov Login Failed
        </h2>

        <p className="text-gray-600">
          {errorMessage}
        </p>

        <div className="bg-yellow-50 rounded-lg p-4 mt-4">
          <p className="text-sm text-yellow-800">
            <strong>Don't worry!</strong> You can still use VetAssist without VA.gov login.
            VA login is only needed to check your claim status.
          </p>
        </div>

        <div className="mt-6 space-y-3">
          <a
            href="/api/v1/auth/va/login"
            className="block w-full py-3 px-4 rounded-md shadow bg-blue-600 text-white font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Try VA Login Again
          </a>

          <Link
            href="/login"
            className="block w-full py-3 px-4 rounded-md shadow border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50"
          >
            Use Email Login Instead
          </Link>

          <Link
            href="/calculator"
            className="block w-full py-3 px-4 rounded-md shadow border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50"
          >
            Use Calculator (No Login Required)
          </Link>
        </div>

        <p className="text-xs text-gray-500 mt-6">
          Error code: {error}
        </p>
      </div>
    </div>
  );
}
```

### Step 3: Add VA Login Button to Login Page

Edit `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`.

Add after the email/password form's submit button, before the closing `</form>`:

```tsx
{/* VA.gov Login Option */}
<div className="mt-6">
  <div className="relative">
    <div className="absolute inset-0 flex items-center">
      <div className="w-full border-t border-gray-300" />
    </div>
    <div className="relative flex justify-center text-sm">
      <span className="px-2 bg-white text-gray-500">Or continue with</span>
    </div>
  </div>

  <div className="mt-6">
    <a
      href="/api/v1/auth/va/login"
      className="w-full flex justify-center items-center py-3 px-4 border border-blue-300 rounded-md shadow-sm bg-blue-50 text-sm font-medium text-blue-800 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
      </svg>
      Login with VA.gov
    </a>
    <p className="mt-2 text-xs text-center text-gray-500">
      Use ID.me, Login.gov, or DS Logon
    </p>
  </div>
</div>
```

### Step 4: Create VA Auth Context Hook (Optional Enhancement)

Create `/ganuda/vetassist/frontend/lib/va-auth-context.tsx`:

```tsx
'use client';

/**
 * VA Authentication Context
 * Manages VA.gov OAuth session state
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface VAAuthState {
  isAuthenticated: boolean;
  sessionId: string | null;
  authTime: Date | null;
}

interface VAAuthContextType extends VAAuthState {
  checkVAAuth: () => void;
  clearVAAuth: () => void;
  isSessionExpired: () => boolean;
}

const VAAuthContext = createContext<VAAuthContextType | undefined>(undefined);

export function VAAuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<VAAuthState>({
    isAuthenticated: false,
    sessionId: null,
    authTime: null,
  });

  const checkVAAuth = () => {
    if (typeof window === 'undefined') return;

    const isAuth = localStorage.getItem('va_authenticated') === 'true';
    const sessionId = localStorage.getItem('va_session_id');
    const authTimeStr = localStorage.getItem('va_auth_time');

    setAuthState({
      isAuthenticated: isAuth,
      sessionId,
      authTime: authTimeStr ? new Date(authTimeStr) : null,
    });
  };

  const clearVAAuth = () => {
    localStorage.removeItem('va_authenticated');
    localStorage.removeItem('va_session_id');
    localStorage.removeItem('va_auth_time');
    setAuthState({
      isAuthenticated: false,
      sessionId: null,
      authTime: null,
    });
  };

  const isSessionExpired = (): boolean => {
    if (!authState.authTime) return true;
    const thirtyMinutes = 30 * 60 * 1000;
    return Date.now() - authState.authTime.getTime() > thirtyMinutes;
  };

  useEffect(() => {
    checkVAAuth();
  }, []);

  return (
    <VAAuthContext.Provider value={{
      ...authState,
      checkVAAuth,
      clearVAAuth,
      isSessionExpired
    }}>
      {children}
    </VAAuthContext.Provider>
  );
}

export function useVAAuth() {
  const context = useContext(VAAuthContext);
  if (context === undefined) {
    throw new Error('useVAAuth must be used within a VAAuthProvider');
  }
  return context;
}
```

---

## Verification (Required before marking complete)

```bash
# 1. Check va-success page exists
ls -la /ganuda/vetassist/frontend/app/\(auth\)/va-success/page.tsx

# 2. Check va-error page exists
ls -la /ganuda/vetassist/frontend/app/\(auth\)/va-error/page.tsx

# 3. Check login page has VA button
grep -n "VA.gov" /ganuda/vetassist/frontend/app/\(auth\)/login/page.tsx

# 4. Build frontend (must succeed)
cd /ganuda/vetassist/frontend && npm run build

# 5. Test pages load
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/va-success
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/va-error
```

---

## Testing the Full Flow

1. Go to https://vetassist.ganuda.us/login
2. Click "Login with VA.gov"
3. Should redirect to VA.gov sandbox login
4. After login, should redirect to /va-success
5. Should then redirect to /dashboard

---

## Acceptance Criteria

1. [ ] `/va-success` page created and displays success message
2. [ ] `/va-error` page created and displays appropriate error messages
3. [ ] Login page has "Login with VA.gov" button
4. [ ] VA.gov button redirects to backend OAuth endpoint
5. [ ] VA session stored in localStorage after success
6. [ ] Frontend builds successfully with no TypeScript errors

---

*Cherokee AI Federation - For Seven Generations*
