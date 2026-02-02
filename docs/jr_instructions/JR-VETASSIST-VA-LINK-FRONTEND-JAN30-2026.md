# JR-VETASSIST-VA-LINK-FRONTEND-JAN30-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Frontend / TypeScript / React
- **Target Node:** redfin (192.168.132.223) or wherever frontend builds run
- **Depends On:** JR-VETASSIST-VA-LINK-ENDPOINT-JAN30-2026 (Phase 2), JR-VETASSIST-VA-CALLBACK-LINKING-JAN30-2026 (Phase 3)
- **Blocks:** Nothing (this is Phase 4)

## Context

After the backend supports account linking (Phase 2) and the OAuth callback handles linking/linked-login modes (Phase 3), the frontend needs:

1. A new **Settings page** where authenticated users can link their VA.gov account
2. Updates to the **VA Success page** to handle three modes: `linking=true`, `linked=true`, and default
3. A `linkVAAccount()` method in the **API client**
4. `va_linked` and `va_linked_at` fields in the **User type** and **auth context**
5. A **Settings nav link** in the Header

## Files to Modify/Create

| File | Action |
|------|--------|
| `frontend/lib/api-client.ts` | Add `linkVAAccount()`, update `User` type |
| `frontend/lib/auth-context.tsx` | No structural changes needed (already exposes `refreshUser`) |
| `frontend/app/settings/page.tsx` | **CREATE** — New account settings page |
| `frontend/app/(auth)/va-success/page.tsx` | **MODIFY** — Handle linking/linked modes |
| `frontend/components/Header.tsx` | Add Settings link |

---

## Step 1: Update API Client

**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

### A) Add `va_linked` and `va_linked_at` to the `User` interface

After `is_active: boolean` (line 36), add:

```typescript
  va_linked: boolean;
  va_linked_at?: string;
```

The complete `User` interface should be:

```typescript
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  veteran_status: boolean;
  service_branch?: string;
  service_start_date?: string;
  service_end_date?: string;
  disability_rating?: number;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  email_verified: boolean;
  is_active: boolean;
  va_linked: boolean;
  va_linked_at?: string;
}
```

### B) Add `VALinkRequest` and `VALinkResponse` interfaces

After the `ProfileUpdateRequest` interface (around line 73), add:

```typescript
export interface VALinkRequest {
  va_session_token: string;
}
```

### C) Add `linkVAAccount()` method to ApiClient class

In the AUTH ENDPOINTS section (after `updateProfile`, around line 229), add:

```typescript
  /**
   * Link VA.gov account to current email-based account
   */
  async linkVAAccount(vaSessionToken: string): Promise<User> {
    return this.request<User>('/auth/link-va', {
      method: 'POST',
      body: JSON.stringify({ va_session_token: vaSessionToken }),
    });
  }
```

---

## Step 2: Create Settings Page

**File:** `/ganuda/vetassist/frontend/app/settings/page.tsx` (CREATE NEW FILE)

```tsx
'use client';

/**
 * Account Settings Page
 * Allows users to view profile info and link VA.gov account
 */

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Shield, CheckCircle, ExternalLink } from 'lucide-react';

export default function SettingsPage() {
  const { user, loading, refreshUser } = useAuth();
  const router = useRouter();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    router.push('/login');
    return null;
  }

  const handleLinkVA = () => {
    // Get the current auth token to pass as session_id
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Navigate to VA OAuth with session_id to trigger linking mode
      window.location.href = `/api/v1/auth/va/login?session_id=${encodeURIComponent(token)}`;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>

        {/* Profile Info Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">Name</label>
              <p className="mt-1 text-sm text-gray-900">
                {user.first_name || user.last_name
                  ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                  : 'Not provided'}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Email</label>
              <p className="mt-1 text-sm text-gray-900">{user.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">Veteran Status</label>
              <p className="mt-1 text-sm text-gray-900">
                {user.veteran_status ? 'Verified Veteran' : 'Not verified'}
              </p>
            </div>
            {user.service_branch && (
              <div>
                <label className="block text-sm font-medium text-gray-500">Service Branch</label>
                <p className="mt-1 text-sm text-gray-900">{user.service_branch}</p>
              </div>
            )}
            {user.disability_rating !== null && user.disability_rating !== undefined && (
              <div>
                <label className="block text-sm font-medium text-gray-500">Disability Rating</label>
                <p className="mt-1 text-sm text-gray-900">{user.disability_rating}%</p>
              </div>
            )}
          </div>
        </div>

        {/* VA Account Linking Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">VA.gov Account</h2>

          {user.va_linked ? (
            // Already linked
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-6 w-6 text-green-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-800">
                  VA.gov Account Linked
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Your VA.gov account is linked to this VetAssist account.
                  {user.va_linked_at && (
                    <> Linked on {new Date(user.va_linked_at).toLocaleDateString()}.</>
                  )}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  You can now log in using either your email/password or your VA.gov credentials.
                </p>
              </div>
            </div>
          ) : (
            // Not linked yet
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Link your VA.gov account to access your claim status, medical records,
                and other VA services directly through VetAssist. You&apos;ll also be able
                to log in with your VA.gov credentials.
              </p>

              <button
                onClick={handleLinkVA}
                className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md shadow-sm bg-blue-50 text-sm font-medium text-blue-800 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Shield className="h-5 w-5 mr-2" />
                Link VA.gov Account
                <ExternalLink className="h-4 w-4 ml-2" />
              </button>

              <p className="text-xs text-gray-500 mt-3">
                You&apos;ll be redirected to VA.gov to sign in with ID.me, Login.gov, or DS Logon.
              </p>
            </div>
          )}
        </div>

        {/* Back to Dashboard */}
        <div className="text-center">
          <Link
            href="/dashboard"
            className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 3: Update VA Success Page

**File:** `/ganuda/vetassist/frontend/app/(auth)/va-success/page.tsx`

Replace the `VASuccessContent` component (keep `LoadingFallback` and `VASuccessPage` wrapper unchanged).

The new component handles three modes based on URL query params:

```tsx
'use client';

/**
 * VA OAuth Success Page
 * Handles three modes:
 * 1. linking=true — user is linking VA to existing account
 * 2. linked=true — user logged in via VA with linked account
 * 3. default — standalone VA login (existing behavior)
 */

import { Suspense } from 'react';
import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

function VASuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [mode, setMode] = useState<'linking' | 'linked' | 'default'>('default');

  const token = searchParams?.get('token');
  const isLinking = searchParams?.get('linking') === 'true';
  const isLinked = searchParams?.get('linked') === 'true';
  const sessionId = searchParams?.get('session');

  useEffect(() => {
    const handleCallback = async () => {
      // ---- MODE 1: LINKING ----
      // User just completed VA OAuth from settings page
      if (isLinking && token) {
        setMode('linking');
        try {
          // Call POST /auth/link-va with the VA JWT
          await apiClient.linkVAAccount(token);

          // Refresh the user profile to pick up va_linked: true
          await refreshUser();

          setStatus('success');

          // Redirect to settings after 3 seconds
          setTimeout(() => {
            router.push('/settings');
          }, 3000);
        } catch (err: any) {
          setStatus('error');
          setErrorMessage(
            err?.detail || err?.message || 'Failed to link VA.gov account. Please try again.'
          );
        }
        return;
      }

      // ---- MODE 2: LINKED LOGIN ----
      // User logged in via VA.gov with a previously linked account
      if (isLinked && token) {
        setMode('linked');
        try {
          // Store the email-format JWT as auth_token (same as email login)
          apiClient.setToken(token);

          // Refresh user profile
          await refreshUser();

          setStatus('success');

          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 2000);
        } catch (err: any) {
          setStatus('error');
          setErrorMessage('Login failed. Please try again.');
          apiClient.setToken(null);
        }
        return;
      }

      // ---- MODE 3: DEFAULT (standalone VA login) ----
      if (sessionId || token) {
        setMode('default');
        if (sessionId) {
          localStorage.setItem('va_session_id', sessionId);
        }
        if (token) {
          localStorage.setItem('va_session_id', token);
        }
        localStorage.setItem('va_authenticated', 'true');
        localStorage.setItem('va_auth_time', new Date().toISOString());
        setStatus('success');

        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);
      } else {
        setStatus('success');
      }
    };

    handleCallback();
  }, [token, isLinking, isLinked, sessionId, router, refreshUser]);

  // ---- RENDER: LOADING ----
  if (status === 'loading') {
    return (
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto"></div>
        <h2 className="text-2xl font-bold text-gray-900">
          {mode === 'linking' ? 'Linking your VA account...' : 'Verifying...'}
        </h2>
      </div>
    );
  }

  // ---- RENDER: ERROR ----
  if (status === 'error') {
    return (
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
          <svg className="h-10 w-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900">
          {mode === 'linking' ? 'Linking Failed' : 'Authentication Failed'}
        </h2>
        <p className="text-gray-600">{errorMessage}</p>
        <div className="mt-6 space-y-3">
          {mode === 'linking' ? (
            <Link
              href="/settings"
              className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
            >
              Back to Settings
            </Link>
          ) : (
            <Link
              href="/login"
              className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
            >
              Back to Login
            </Link>
          )}
        </div>
      </div>
    );
  }

  // ---- RENDER: SUCCESS ----
  return (
    <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
      <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
        <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>

      {mode === 'linking' ? (
        <>
          <h2 className="text-3xl font-extrabold text-gray-900">VA Account Linked</h2>
          <p className="text-gray-600">
            Your VA.gov account has been successfully linked to your VetAssist account.
            You can now log in with either method.
          </p>
          <div className="bg-blue-50 rounded-lg p-4 mt-4">
            <p className="text-sm text-blue-800">Redirecting to Settings...</p>
          </div>
          <Link
            href="/settings"
            className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
          >
            Go to Settings
          </Link>
        </>
      ) : mode === 'linked' ? (
        <>
          <h2 className="text-3xl font-extrabold text-gray-900">Welcome Back</h2>
          <p className="text-gray-600">
            Signed in with your VA.gov account.
          </p>
          <div className="bg-blue-50 rounded-lg p-4 mt-4">
            <p className="text-sm text-blue-800">Redirecting to Dashboard...</p>
          </div>
          <Link
            href="/dashboard"
            className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
          >
            Go to Dashboard
          </Link>
        </>
      ) : (
        <>
          <h2 className="text-3xl font-extrabold text-gray-900">VA.gov Login Successful</h2>
          <p className="text-gray-600">
            You have successfully authenticated with VA.gov. You can now access your claim status and VA records.
          </p>
          <div className="bg-blue-50 rounded-lg p-4 mt-4">
            <p className="text-sm text-blue-800">Redirecting to your dashboard in 3 seconds...</p>
          </div>
          <div className="mt-6 space-y-3">
            <Link
              href="/dashboard"
              className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
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
  );
}

function LoadingFallback() {
  return (
    <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto"></div>
      <h2 className="text-2xl font-bold text-gray-900">Loading...</h2>
    </div>
  );
}

export default function VASuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-100 py-12 px-4">
      <Suspense fallback={<LoadingFallback />}>
        <VASuccessContent />
      </Suspense>
    </div>
  );
}
```

---

## Step 4: Add Settings Link to Header

**File:** `/ganuda/vetassist/frontend/components/Header.tsx`

### A) Add Settings to desktop nav (authenticated section)

In the desktop auth section (the `{isLoggedIn ? (` block, around line 48), add a Settings link before "Sign Out":

Replace the current authenticated block:

```tsx
{isLoggedIn ? (
  <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
    <span className="text-sm text-gray-600">
      Hi, {user?.first_name || 'Veteran'}
    </span>
    <button
      onClick={logout}
      className="text-sm text-gray-600 hover:text-primary"
    >
      Sign Out
    </button>
  </div>
) : (
```

With:

```tsx
{isLoggedIn ? (
  <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
    <span className="text-sm text-gray-600">
      Hi, {user?.first_name || 'Veteran'}
    </span>
    <Link
      href="/settings"
      className={`text-sm hover:text-primary transition ${
        pathname === '/settings' ? 'text-primary font-semibold' : 'text-gray-600'
      }`}
    >
      Settings
    </Link>
    <button
      onClick={logout}
      className="text-sm text-gray-600 hover:text-primary"
    >
      Sign Out
    </button>
  </div>
) : (
```

### B) Add Settings to mobile nav (authenticated section)

In the mobile nav `{isLoggedIn ? (` block (around line 101), add a Settings link before "Sign Out":

Add this before the Sign Out button:

```tsx
<Link
  href="/settings"
  onClick={() => setMobileMenuOpen(false)}
  className={`py-2 ${
    pathname === '/settings' ? 'text-primary font-semibold' : ''
  }`}
>
  Settings
</Link>
```

---

## Verification

### Test 1: User type has va_linked

Open browser dev tools, log in, and check the user object in React state. It should include `va_linked: false` and `va_linked_at: null` for a user who hasn't linked yet.

### Test 2: Settings page renders

Navigate to `/settings` while logged in. Verify:
- Profile info section shows name, email, veteran status
- VA Account section shows "Link VA.gov Account" button (if not linked)
- Not accessible when logged out (redirects to login)

### Test 3: Settings page after linking

After completing the linking flow, navigate to `/settings`. Verify:
- VA Account section shows green checkmark and "VA.gov Account Linked"
- Shows the date it was linked
- "Link VA.gov Account" button is no longer visible

### Test 4: VA Success handles linking mode

Navigate to `/va-success?linking=true&token=<valid-va-jwt>` while logged in. Verify:
- Shows "Linking your VA account..." loading state
- Then shows "VA Account Linked" success
- Redirects to /settings

### Test 5: VA Success handles linked-login mode

Navigate to `/va-success?token=<valid-email-jwt>&linked=true`. Verify:
- Stores token as `auth_token` in localStorage
- Shows "Welcome Back" message
- Redirects to /dashboard

### Test 6: Header shows Settings link

Log in and verify "Settings" appears in the nav bar between the user greeting and "Sign Out".

### Test 7: Mobile nav has Settings

Open on mobile viewport, tap hamburger menu. "Settings" should appear before "Sign Out".
