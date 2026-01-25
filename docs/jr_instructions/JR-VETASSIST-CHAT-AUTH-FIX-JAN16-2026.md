# JR Instruction: VetAssist Chat Auth Integration

## Metadata
```yaml
task_id: vetassist_chat_auth_fix
priority: 1
ticket_id: 1719
assigned_to: Code Jr.
target: frontend
```

## Problem

Chat page uses hardcoded user ID instead of authenticated user:

```javascript
// /ganuda/vetassist/frontend/app/chat/page.tsx line 42
const TEMP_USER_ID = "00000000-0000-0000-0000-000000000001";
```

This means:
- All users share the same chat sessions
- Sessions not tied to user accounts
- No personalization

## Solution

### Task 1: Import Auth Context

In `/ganuda/vetassist/frontend/app/chat/page.tsx`, add import:

```typescript
import { useAuth } from '@/lib/auth-context';
```

### Task 2: Get User from Context

Replace the hardcoded ID with auth context:

```typescript
// REMOVE THIS:
const TEMP_USER_ID = "00000000-0000-0000-0000-000000000001";

// ADD THIS inside the component:
const { user, isAuthenticated, isLoading } = useAuth();

// Use user.id instead of TEMP_USER_ID
const userId = user?.id;
```

### Task 3: Add Authentication Guard

Redirect unauthenticated users to login:

```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/chat');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // Rest of component using user.id
}
```

### Task 4: Update API Calls

Replace all instances of `TEMP_USER_ID` with `user.id`:

```typescript
// Create session
const response = await fetch(`${API_URL}/chat/sessions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: user.id }),  // Changed
});

// Load sessions
const response = await fetch(`${API_URL}/chat/sessions?user_id=${user.id}`);  // Changed

// Send message
const response = await fetch(`${API_URL}/chat/message`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: activeSession,
    user_id: user.id,  // Changed
    content: message,
  }),
});
```

### Task 5: Handle Login Redirect

After login, redirect back to chat if that was the intended destination.

In `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx`:

```typescript
import { useSearchParams } from 'next/navigation';

// Inside component:
const searchParams = useSearchParams();
const redirect = searchParams.get('redirect') || '/calculator';

// On successful login:
router.push(redirect);
```

## Verification

1. Log out, go to /chat → Should redirect to /login
2. Log in → Should redirect back to /chat
3. Create a chat session → Check database that user_id matches logged-in user
4. Log out, log in as different user → Should see different sessions

## Files to Modify

- `/ganuda/vetassist/frontend/app/chat/page.tsx` (main changes)
- `/ganuda/vetassist/frontend/app/(auth)/login/page.tsx` (redirect handling)

---

*Cherokee AI Federation - For the Seven Generations*
