# JR Instruction: VetAssist Forgot Password Flow

## Metadata
```yaml
task_id: vetassist_forgot_password
priority: 2
ticket_id: 1722
assigned_to: Code Jr.
target: frontend + backend
```

## Problem

Login page has no password reset option. Users who forget passwords cannot recover their accounts.

## Solution

### Task 1: Backend - Add Password Reset Endpoints

In `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`, add:

```python
from datetime import datetime, timedelta
import secrets

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Request password reset. Generates token and would send email.
    For now, returns token directly (in production, send via email).
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Don't reveal if email exists
        return {"message": "If that email exists, a reset link has been sent."}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expiry = datetime.utcnow() + timedelta(hours=1)

    # Store token (add these fields to User model)
    user.reset_token = reset_token
    user.reset_token_expiry = reset_expiry
    db.commit()

    # TODO: Send email with reset link
    # For development, return token directly
    return {
        "message": "If that email exists, a reset link has been sent.",
        "dev_token": reset_token  # Remove in production
    }


@router.post("/reset-password")
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(..., min_length=8),
    db: Session = Depends(get_db)
):
    """Reset password using token from email."""
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expiry > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Update password
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

    return {"message": "Password has been reset successfully"}
```

### Task 2: Backend - Update User Model

In `/ganuda/vetassist/backend/app/models/user.py`, add fields:

```python
reset_token = Column(String(100), nullable=True)
reset_token_expiry = Column(DateTime, nullable=True)
```

Run migration or add columns manually.

### Task 3: Frontend - Forgot Password Page

Create `/ganuda/vetassist/frontend/app/(auth)/forgot-password/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setSubmitted(true);
      } else {
        setError('Something went wrong. Please try again.');
      }
    } catch (err) {
      setError('Unable to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Check Your Email</h1>
          <p className="text-gray-600 mb-6">
            If an account exists for {email}, we've sent password reset instructions.
          </p>
          <Link href="/login" className="text-blue-800 hover:underline">
            Return to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Forgot Password</h1>
        <p className="text-gray-600 mb-6">
          Enter your email and we'll send you reset instructions.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              placeholder="you@example.com"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-800 text-white rounded hover:bg-blue-900 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          Remember your password?{' '}
          <Link href="/login" className="text-blue-800 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
```

### Task 4: Add Link to Login Page

In `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`, add:

```typescript
<Link href="/forgot-password" className="text-sm text-blue-800 hover:underline">
  Forgot your password?
</Link>
```

## Verification

1. Go to /login, click "Forgot your password?"
2. Enter email, submit
3. Should see "Check Your Email" message
4. Use token to reset password (dev mode)
5. Login with new password should work

---

*Cherokee AI Federation - For the Seven Generations*
