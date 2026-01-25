# JR Instruction: VetAssist Chat Auth Integration (FIXED FORMAT)
## Task ID: CHAT-AUTH-002
## Priority: P1

---

## Objective

Fix chat page to use authenticated user ID instead of hardcoded value. Currently all users share the same chat sessions.

---

## Implementation

### Step 1: Update chat page with auth integration

Modify: `/ganuda/vetassist/frontend/app/chat/page.tsx`

```typescript
'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/chat');
    }
  }, [isLoading, isAuthenticated, router]);

  // Load sessions when user is available
  useEffect(() => {
    if (user?.id) {
      loadSessions();
    }
  }, [user?.id]);

  const loadSessions = async () => {
    if (!user?.id) return;
    try {
      const res = await fetch(`${API_URL}/chat/sessions?user_id=${user.id}`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const createSession = async () => {
    if (!user?.id) return;
    try {
      const res = await fetch(`${API_URL}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id }),
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(prev => [data, ...prev]);
        setActiveSession(data.id);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeSession || !user?.id || sending) return;

    const userMessage = input;
    setInput('');
    setSending(true);

    // Optimistic update
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }]);

    try {
      const res = await fetch(`${API_URL}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSession,
          user_id: user.id,
          content: userMessage,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          id: data.id,
          role: 'assistant',
          content: data.response,
          created_at: data.created_at,
        }]);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 p-4 border-r">
        <button
          onClick={createSession}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded mb-4"
        >
          New Chat
        </button>
        <div className="space-y-2">
          {sessions.map(session => (
            <button
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`w-full text-left p-2 rounded ${
                activeSession === session.id ? 'bg-blue-100' : 'hover:bg-gray-200'
              }`}
            >
              {session.title || 'New Chat'}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map(msg => (
            <div
              key={msg.id}
              className={`p-3 rounded ${
                msg.role === 'user' ? 'bg-blue-100 ml-auto max-w-md' : 'bg-gray-100 max-w-md'
              }`}
            >
              {msg.content}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type a message..."
              className="flex-1 p-2 border rounded"
              disabled={!activeSession || sending}
            />
            <button
              onClick={sendMessage}
              disabled={!activeSession || sending}
              className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Verification

```bash
# Check file was updated
grep -n "useAuth" /ganuda/vetassist/frontend/app/chat/page.tsx

# Check hardcoded ID is removed
grep -c "TEMP_USER_ID" /ganuda/vetassist/frontend/app/chat/page.tsx || echo "Good - no hardcoded ID"
```

---

## Acceptance Criteria

1. Chat page imports and uses useAuth hook
2. Unauthenticated users redirected to login
3. User ID from auth context used for API calls
4. No hardcoded TEMP_USER_ID

---

*Cherokee AI Federation - For Seven Generations*
