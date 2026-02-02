# JR-VETASSIST-VA-LINKING-PHASE4-FRONTEND-JAN31-2026

## Metadata
- **Priority:** P1
- **Jr Type:** Engineering
- **Target Node:** sasass2 (192.168.132.200)
- **Category:** VetAssist — VA Account Linking Phase 4 (Frontend)
- **Depends On:** JR-VETASSIST-VA-LINKING-PHASE2-LINK-ENDPOINT-JAN31-2026, JR-VETASSIST-VA-LINKING-PHASE3-CALLBACK-JAN31-2026
- **Council Vote:** ULTRATHINK-EXECUTOR-SEARCH-REPLACE-ARCHITECTURE-JAN31-2026

## Objective

Create the account settings page, fix the api-client, update the va-success page for linking/linked modes, and add Settings to the navigation header.

## Step 1: Fix api-client.ts — Remove Orphaned Lines

A previous failed Jr edit left orphaned TypeScript at the bottom of the file. Remove it.

**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

<<<<<<< SEARCH
// Export class for testing
export default ApiClient;

  va_linked: boolean;
  va_linked_at?: string;
=======
// Export class for testing
export default ApiClient;
>>>>>>> REPLACE

## Step 2: Add va_linked to User Interface

**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

<<<<<<< SEARCH
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
}
=======
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
>>>>>>> REPLACE

## Step 3: Add linkVAAccount Method to ApiClient

**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

<<<<<<< SEARCH
  // ============================================================================
  // CALCULATOR ENDPOINTS
  // ============================================================================
=======
  /**
   * Link VA.gov account to current user
   */
  async linkVAAccount(vaSessionToken: string): Promise<User> {
    return this.request<User>('/auth/link-va', {
      method: 'POST',
      body: JSON.stringify({ va_session_token: vaSessionToken }),
    });
  }

  // ============================================================================
  // CALCULATOR ENDPOINTS
  // ============================================================================
>>>>>>> REPLACE

## Step 4: Create Settings Page

```bash
mkdir -p /ganuda/vetassist/frontend/app/settings
```

```bash
cat > /ganuda/vetassist/frontend/app/settings/page.tsx << 'SETTINGSEOF'
'use client';

/**
 * Account Settings Page
 * Allows veterans to view profile and link VA.gov account
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { apiClient } from '@/lib/api-client';

export default function SettingsPage() {
  const { user, loading, refreshUser } = useAuth();
  const router = useRouter();
  const [linkStatus, setLinkStatus] = useState<'idle' | 'linking' | 'success' | 'error'>('idle');
  const [linkError, setLinkError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  const handleLinkVA = () => {
    // Navigate to VA OAuth with session context for linking
    const currentToken = apiClient.getToken();
    window.location.href = `/api/v1/auth/va/login?session_id=${currentToken}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>

        {/* Profile Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile</h2>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Name</dt>
              <dd className="text-sm text-gray-900">
                {user.first_name || ''} {user.last_name || ''}
                {!user.first_name && !user.last_name && <span className="text-gray-400">Not set</span>}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Email</dt>
              <dd className="text-sm text-gray-900">{user.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Veteran Status</dt>
              <dd className="text-sm text-gray-900">{user.veteran_status ? 'Verified Veteran' : 'Not verified'}</dd>
            </div>
            {user.service_branch && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Service Branch</dt>
                <dd className="text-sm text-gray-900">{user.service_branch}</dd>
              </div>
            )}
            {user.disability_rating !== null && user.disability_rating !== undefined && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Disability Rating</dt>
                <dd className="text-sm text-gray-900">{user.disability_rating}%</dd>
              </div>
            )}
          </dl>
        </div>

        {/* VA Account Linking Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">VA.gov Account</h2>

          {user.va_linked ? (
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-green-800">VA Account Linked</p>
                {user.va_linked_at && (
                  <p className="text-xs text-gray-500">
                    Linked on {new Date(user.va_linked_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Link your VA.gov account to access your VA records, verify your veteran status,
                and enable login with VA.gov credentials.
              </p>

              {linkStatus === 'error' && linkError && (
                <div className="rounded-md bg-red-50 p-3 mb-4">
                  <p className="text-sm text-red-800">{linkError}</p>
                </div>
              )}

              {linkStatus === 'success' && (
                <div className="rounded-md bg-green-50 p-3 mb-4">
                  <p className="text-sm text-green-800">VA account linked successfully!</p>
                </div>
              )}

              <button
                onClick={handleLinkVA}
                disabled={linkStatus === 'linking'}
                className="inline-flex items-center px-4 py-2 border border-blue-300 rounded-md shadow-sm bg-blue-50 text-sm font-medium text-blue-800 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                {linkStatus === 'linking' ? 'Linking...' : 'Link VA.gov Account'}
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <Link href="/dashboard" className="text-sm text-indigo-600 hover:text-indigo-500">
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
SETTINGSEOF
```

## Step 5: Update VA Success Page for Linking and Linked Modes

Replace the entire va-success page to handle three modes: standard VA login, linked-login, and account linking.

```bash
cat > /ganuda/vetassist/frontend/app/\(auth\)/va-success/page.tsx << 'VASUCCESSEOF'
'use client';

/**
 * VA OAuth Success Page
 * Handles three modes:
 * 1. Standard VA login (token only)
 * 2. Linked-login (token + linked=true) — VA user with linked email account
 * 3. Account linking (token + linking=true) — linking VA to existing email account
 */

import { Suspense } from 'react';
import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';

function VASuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'link-success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  const token = searchParams?.get('token');
  const isLinked = searchParams?.get('linked') === 'true';
  const isLinking = searchParams?.get('linking') === 'true';
  const sessionId = searchParams?.get('session');

  useEffect(() => {
    const handleCallback = async () => {
      if (isLinked && token) {
        // Mode: Linked-login — VA user whose ICN is linked to an email account
        // Store as standard auth token and redirect to dashboard
        apiClient.setToken(token);
        setStatus('success');
        setTimeout(() => {
          router.push('/dashboard');
        }, 2000);

      } else if (isLinking && token) {
        // Mode: Account linking — user is linking VA account to their email account
        try {
          await apiClient.linkVAAccount(token);
          setStatus('link-success');
          setTimeout(() => {
            router.push('/settings');
          }, 3000);
        } catch (err: any) {
          setStatus('error');
          setErrorMessage(err?.detail || err?.message || 'Failed to link VA account');
        }

      } else if (token) {
        // Mode: Standard VA login (no linked email account)
        localStorage.setItem('va_session_token', token);
        localStorage.setItem('va_authenticated', 'true');
        localStorage.setItem('va_auth_time', new Date().toISOString());
        setStatus('success');
        setTimeout(() => {
          router.push('/dashboard');
        }, 3000);

      } else if (sessionId) {
        // Legacy: session-based (backwards compatibility)
        localStorage.setItem('va_session_id', sessionId);
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
  }, [token, isLinked, isLinking, sessionId, router]);

  return (
    <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg text-center">
      {status === 'loading' ? (
        <>
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto"></div>
          <h2 className="text-2xl font-bold text-gray-900">
            {isLinking ? 'Linking your VA account...' : 'Verifying...'}
          </h2>
        </>
      ) : status === 'error' ? (
        <>
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
            <svg className="h-10 w-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Linking Failed</h2>
          <p className="text-gray-600">{errorMessage}</p>
          <Link
            href="/settings"
            className="block w-full py-3 px-4 rounded-md shadow bg-indigo-600 text-white font-medium hover:bg-indigo-700"
          >
            Back to Settings
          </Link>
        </>
      ) : status === 'link-success' ? (
        <>
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
            <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900">VA Account Linked!</h2>
          <p className="text-gray-600">
            Your VA.gov account is now linked. You can log in with either your email or VA.gov credentials.
          </p>
          <div className="bg-blue-50 rounded-lg p-4 mt-4">
            <p className="text-sm text-blue-800">Redirecting to Settings...</p>
          </div>
        </>
      ) : (
        <>
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
            <svg className="h-10 w-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h2 className="text-3xl font-extrabold text-gray-900">
            {isLinked ? 'Welcome Back!' : 'VA.gov Login Successful'}
          </h2>

          <p className="text-gray-600">
            {isLinked
              ? 'You have been logged in with your linked VA.gov account.'
              : 'You have successfully authenticated with VA.gov. You can now access your claim status and VA records.'}
          </p>

          <div className="bg-blue-50 rounded-lg p-4 mt-4">
            <p className="text-sm text-blue-800">Redirecting to your dashboard...</p>
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
            Your session will remain active for 30 minutes of inactivity.
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
VASUCCESSEOF
```

## Step 6: Add Settings Link to Header

**File:** `/ganuda/vetassist/frontend/components/Header.tsx`

<<<<<<< SEARCH
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
=======
              <div className="flex items-center space-x-4 ml-4 pl-4 border-l">
                <span className="text-sm text-gray-600">
                  Hi, {user?.first_name || 'Veteran'}
                </span>
                <Link
                  href="/settings"
                  className="text-sm text-gray-600 hover:text-primary"
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
>>>>>>> REPLACE

## Step 7: Verify Files Exist

```bash
ls -la /ganuda/vetassist/frontend/app/settings/page.tsx
ls -la /ganuda/vetassist/frontend/app/\(auth\)/va-success/page.tsx
echo "PASS: Frontend files in place"
```

## Rollback

To undo api-client.ts and Header.tsx changes, restore from search-replace backups:
  ls -la /ganuda/vetassist/frontend/lib/api-client.ts.sr_backup_*
  ls -la /ganuda/vetassist/frontend/components/Header.tsx.sr_backup_*

To undo settings page: rm /ganuda/vetassist/frontend/app/settings/page.tsx
To undo va-success: restore from backup or git checkout
