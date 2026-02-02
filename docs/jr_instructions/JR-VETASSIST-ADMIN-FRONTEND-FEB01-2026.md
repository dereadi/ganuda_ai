# Jr Instruction: VetAssist Admin Frontend Panel

**Task:** JR-VETASSIST-ADMIN-FRONTEND
**Priority:** P1
**Assigned:** Software Engineer Jr.
**Depends On:** JR-VETASSIST-ADMIN-BACKEND-ENDPOINTS
**Platform:** Greenfin (192.168.132.223:3000)
**Council Vote:** #8365 — APPROVED

## Objective

Create the admin panel frontend:
1. Add admin API methods to api-client.ts
2. Add admin_tier + is_admin to User type and auth context
3. Create admin dashboard page at /admin
4. Add Admin link in Header (visible only to admins)

## Step 1: Add admin_tier to User Type and API Methods

**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

<<<<<<< SEARCH
  va_linked: boolean;
  va_linked_at?: string;
}
=======
  va_linked: boolean;
  va_linked_at?: string;
  admin_tier: number;
  is_admin: boolean;
}
>>>>>>> REPLACE

<<<<<<< SEARCH
  // ============================================================================
  // CALCULATOR ENDPOINTS
  // ============================================================================
=======
  // ============================================================================
  // ADMIN ENDPOINTS
  // ============================================================================

  /**
   * Get admin stats (Tier 2+)
   */
  async getAdminStats(): Promise<AdminStats> {
    return this.request<AdminStats>('/admin/stats', { method: 'GET' });
  }

  /**
   * List users (masked view, Tier 2+)
   */
  async getAdminUsers(page = 1, search?: string): Promise<AdminUserList> {
    const params = new URLSearchParams({ page: String(page), page_size: '20' });
    if (search) params.set('search', search);
    return this.request<AdminUserList>(`/admin/users?${params}`, { method: 'GET' });
  }

  /**
   * Get single user detail (masked, Tier 2+)
   */
  async getAdminUser(userId: string): Promise<AdminUserView> {
    return this.request<AdminUserView>(`/admin/users/${userId}`, { method: 'GET' });
  }

  /**
   * Challenge-response identity verification (Tier 2+)
   */
  async verifyUserIdentity(userId: string, claimedEmail: string): Promise<{ match: boolean; user_id: string }> {
    return this.request(`/admin/users/${userId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ claimed_email: claimedEmail }),
    });
  }

  /**
   * Reset user password (Tier 2+)
   */
  async resetUserPassword(userId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/admin/users/${userId}/reset-password`, { method: 'POST' });
  }

  /**
   * Deactivate user (Tier 2+)
   */
  async deactivateUser(userId: string): Promise<{ id: string; is_active: boolean }> {
    return this.request(`/admin/users/${userId}/deactivate`, { method: 'POST' });
  }

  /**
   * Reactivate user (Tier 2+)
   */
  async reactivateUser(userId: string): Promise<{ id: string; is_active: boolean }> {
    return this.request(`/admin/users/${userId}/reactivate`, { method: 'POST' });
  }

  /**
   * Get user sessions (Tier 2+)
   */
  async getUserSessions(userId: string): Promise<any[]> {
    return this.request(`/admin/users/${userId}/sessions`, { method: 'GET' });
  }

  /**
   * Revoke all user sessions / force logout (Tier 2+)
   */
  async revokeUserSessions(userId: string): Promise<{ revoked_sessions: number }> {
    return this.request(`/admin/users/${userId}/sessions`, { method: 'DELETE' });
  }

  // ============================================================================
  // CALCULATOR ENDPOINTS
  // ============================================================================
>>>>>>> REPLACE

Add type definitions after the existing interfaces (after `ProfileUpdateRequest`):

<<<<<<< SEARCH
class ApiClient {
=======
// Admin types
export interface AdminUserView {
  id: string;
  first_name?: string;
  last_name: string;
  veteran_status: boolean;
  is_active: boolean;
  email_verified: boolean;
  va_linked: boolean;
  va_linked_at?: string;
  admin_tier: number;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  disability_rating?: number;
}

export interface AdminUserList {
  users: AdminUserView[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  verified_users: number;
  va_linked_users: number;
  veteran_users: number;
  total_chat_sessions: number;
  total_chat_messages: number;
}

class ApiClient {
>>>>>>> REPLACE

## Step 2: Add Admin Link to Header (Conditional)

**File:** `/ganuda/vetassist/frontend/components/Header.tsx`

<<<<<<< SEARCH
import { useAuth } from '@/lib/auth-context';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];
=======
import { useAuth } from '@/lib/auth-context';

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/calculator', label: 'Calculator' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/resources', label: 'Resources' },
  { href: '/about', label: 'About' },
];

const adminNavItems = [
  { href: '/admin', label: 'Admin' },
];
>>>>>>> REPLACE

<<<<<<< SEARCH
            {/* Auth Section */}
            {isLoggedIn ? (
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
=======
            {/* Admin Nav (only if admin) */}
            {isLoggedIn && user?.is_admin && adminNavItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`hover:text-primary transition text-sm font-medium ${
                  pathname === item.href ? 'text-primary font-semibold' : 'text-amber-700'
                }`}
              >
                {item.label}
              </Link>
            ))}

            {/* Auth Section */}
            {isLoggedIn ? (
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
>>>>>>> REPLACE

## Step 3: Create Admin Dashboard Page

**Create:** `/ganuda/vetassist/frontend/app/admin/page.tsx`

```tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Users, Search, CheckCircle, XCircle, RefreshCw, Eye, LogOut, KeyRound } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { apiClient, AdminUserView, AdminUserList, AdminStats } from '@/lib/api-client';

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [userList, setUserList] = useState<AdminUserList | null>(null);
  const [selectedUser, setSelectedUser] = useState<AdminUserView | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Verification state
  const [verifyUserId, setVerifyUserId] = useState<string | null>(null);
  const [claimedEmail, setClaimedEmail] = useState('');
  const [verifyResult, setVerifyResult] = useState<boolean | null>(null);

  // Action feedback
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Redirect non-admins
  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      router.push('/dashboard');
    }
  }, [user, authLoading, router]);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, usersData] = await Promise.all([
        apiClient.getAdminStats(),
        apiClient.getAdminUsers(page, search || undefined),
      ]);
      setStats(statsData);
      setUserList(usersData);
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    if (user?.is_admin) {
      loadData();
    }
  }, [user, loadData]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  // Handle verify identity
  const handleVerify = async () => {
    if (!verifyUserId || !claimedEmail) return;
    try {
      const result = await apiClient.verifyUserIdentity(verifyUserId, claimedEmail);
      setVerifyResult(result.match);
    } catch (err: any) {
      setError(err.detail || 'Verification failed');
    }
  };

  // Handle password reset
  const handleResetPassword = async (userId: string) => {
    try {
      const result = await apiClient.resetUserPassword(userId);
      setActionMessage(result.message);
      setTimeout(() => setActionMessage(null), 5000);
    } catch (err: any) {
      setError(err.detail || 'Password reset failed');
    }
  };

  // Handle deactivate/reactivate
  const handleToggleActive = async (userId: string, currentlyActive: boolean) => {
    try {
      if (currentlyActive) {
        await apiClient.deactivateUser(userId);
        setActionMessage('User deactivated');
      } else {
        await apiClient.reactivateUser(userId);
        setActionMessage('User reactivated');
      }
      loadData(); // Refresh
      setTimeout(() => setActionMessage(null), 5000);
    } catch (err: any) {
      setError(err.detail || 'Action failed');
    }
  };

  // Handle force logout
  const handleForceLogout = async (userId: string) => {
    try {
      const result = await apiClient.revokeUserSessions(userId);
      setActionMessage(`Revoked ${result.revoked_sessions} session(s)`);
      setTimeout(() => setActionMessage(null), 5000);
    } catch (err: any) {
      setError(err.detail || 'Force logout failed');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading admin panel...</div>
      </div>
    );
  }

  if (!user?.is_admin) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex items-center gap-3 mb-8">
        <Shield className="h-8 w-8 text-amber-700" />
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <span className="text-sm bg-amber-100 text-amber-800 px-2 py-1 rounded">
          Tier {user.admin_tier}
        </span>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-sm underline">Dismiss</button>
        </div>
      )}
      {actionMessage && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded">
          {actionMessage}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Users" value={stats.total_users} />
          <StatCard label="Active" value={stats.active_users} />
          <StatCard label="VA Linked" value={stats.va_linked_users} />
          <StatCard label="Chat Sessions" value={stats.total_chat_sessions} />
        </div>
      )}

      {/* Search */}
      <div className="mb-6">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by first name..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
            Search
          </button>
          <button type="button" onClick={loadData} className="px-3 py-2 border rounded-lg hover:bg-gray-50">
            <RefreshCw className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* User Table */}
      {userList && (
        <div className="border rounded-lg overflow-hidden mb-8">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">VA</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Created</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Last Login</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {userList.users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium">{u.first_name || '—'} {u.last_name}</div>
                    <div className="text-xs text-gray-400">{u.id?.slice(0, 8)}...</div>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active ? (
                      <span className="inline-flex items-center gap-1 text-green-700 text-sm">
                        <CheckCircle className="h-3 w-3" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-600 text-sm">
                        <XCircle className="h-3 w-3" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {u.va_linked ? (
                      <span className="text-green-700">Linked</span>
                    ) : (
                      <span className="text-gray-400">No</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        onClick={() => {
                          setVerifyUserId(u.id);
                          setVerifyResult(null);
                          setClaimedEmail('');
                        }}
                        className="p-1.5 text-gray-500 hover:text-primary rounded hover:bg-gray-100"
                        title="Verify Identity"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleResetPassword(u.id)}
                        className="p-1.5 text-gray-500 hover:text-amber-600 rounded hover:bg-gray-100"
                        title="Reset Password"
                      >
                        <KeyRound className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleToggleActive(u.id, u.is_active)}
                        className={`p-1.5 rounded hover:bg-gray-100 ${
                          u.is_active ? 'text-gray-500 hover:text-red-600' : 'text-gray-500 hover:text-green-600'
                        }`}
                        title={u.is_active ? 'Deactivate' : 'Reactivate'}
                      >
                        {u.is_active ? <XCircle className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                      </button>
                      <button
                        onClick={() => handleForceLogout(u.id)}
                        className="p-1.5 text-gray-500 hover:text-red-600 rounded hover:bg-gray-100"
                        title="Force Logout"
                      >
                        <LogOut className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="px-4 py-3 bg-gray-50 flex items-center justify-between text-sm">
            <span className="text-gray-600">
              {userList.total} user{userList.total !== 1 ? 's' : ''} total
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1">Page {page}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={userList.users.length < 20}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Identity Verification Modal */}
      {verifyUserId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-lg font-bold mb-2">Identity Verification</h2>
            <p className="text-sm text-gray-600 mb-4">
              Ask the veteran: &quot;What email address is on your account?&quot;
              <br />Enter their response below. The system will compare without revealing the actual email.
            </p>

            <input
              type="email"
              value={claimedEmail}
              onChange={(e) => setClaimedEmail(e.target.value)}
              placeholder="Enter email the veteran provided..."
              className="w-full px-3 py-2 border rounded-lg mb-3 focus:ring-2 focus:ring-primary"
            />

            {verifyResult !== null && (
              <div className={`mb-3 p-3 rounded ${
                verifyResult ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {verifyResult ? 'MATCH — Identity verified' : 'NO MATCH — Email does not match'}
              </div>
            )}

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setVerifyUserId(null);
                  setClaimedEmail('');
                  setVerifyResult(null);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={handleVerify}
                disabled={!claimedEmail}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
              >
                Verify
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Compliance Notice */}
      <div className="text-xs text-gray-400 mt-8 border-t pt-4">
        All admin actions are logged per 38 CFR 0.605.
        PII fields are masked — email, phone, and VA ICN are not displayed.
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}
```

## Validation

After deploying:

1. Build frontend: `cd /ganuda/vetassist/frontend && npm run build`
2. Login as non-admin → Admin link should NOT appear in header
3. Set admin tier: `UPDATE users SET admin_tier = 2 WHERE email = '<admin-email>';`
4. Login as admin → Admin link appears, /admin page loads
5. Verify user table shows masked last names (e.g., "D***")
6. Test identity verification flow
7. Check audit log has entries after admin actions
