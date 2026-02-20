# Jr Instruction: VetAssist Hardcoded User ID Fix

**Kanban:** #1719
**Council Vote:** #fadf71ec28884489 (PROCEED, 0.89)
**Priority:** 2
**Assigned Jr:** Software Engineer Jr.
**Long Man Phase:** BUILD

---

## Overview

Replace hardcoded `TEMP_USER_ID` in VetAssist chat with authenticated user identity from the `useAuth()` hook. This fixes session isolation — currently ALL users share the same chat sessions.

---

## Step 1: Replace TEMP_USER_ID with useAuth in WizardChatHelper

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/WizardChatHelper.tsx`

<<<<<<< SEARCH
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send, Loader2, Sparkles } from 'lucide-react';
=======
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send, Loader2, Sparkles } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
>>>>>>> REPLACE

---

## Step 2: Add auth hook and remove hardcoded ID

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/WizardChatHelper.tsx`

<<<<<<< SEARCH
export default function WizardChatHelper({ wizardType, currentStep, stepTitle, formData }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
  // Temporary user ID until auth is integrated (same pattern as main chat page)
  const TEMP_USER_ID = '00000000-0000-0000-0000-000000000001';
=======
export default function WizardChatHelper({ wizardType, currentStep, stepTitle, formData }: Props) {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';
>>>>>>> REPLACE

---

## Step 3: Use user.id in createChatSession

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/WizardChatHelper.tsx`

<<<<<<< SEARCH
  const createChatSession = async () => {
    try {
      // Use Duplo unified session pattern - source indicates wizard context
      const response = await axios.post(`${apiUrl}/chat/sessions`, {
        user_id: TEMP_USER_ID,
        title: `Wizard Help: ${wizardType} Step ${currentStep}`,
=======
  const createChatSession = async () => {
    if (!user?.id) return;
    try {
      // Use Duplo unified session pattern - source indicates wizard context
      const response = await axios.post(`${apiUrl}/chat/sessions`, {
        user_id: user.id,
        title: `Wizard Help: ${wizardType} Step ${currentStep}`,
>>>>>>> REPLACE

---

## Step 4: Clean up hardcoded user ID in test file

File: `/ganuda/vetassist/backend/test_api_integration.py`

<<<<<<< SEARCH
TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"
=======
# Test user ID — set via environment variable for real integration tests
TEMP_USER_ID = os.environ.get("VETASSIST_TEST_USER_ID", "00000000-0000-0000-0000-000000000001")
>>>>>>> REPLACE

---

## Step 5: Add os import if not present in test file

File: `/ganuda/vetassist/backend/test_api_integration.py`

Check if `import os` exists at the top of the file. If not, add it after the existing imports.

<<<<<<< SEARCH
import requests
import json
=======
import requests
import json
import os
>>>>>>> REPLACE

---

## Manual Steps (TPM)

After Jr completes:

1. Rebuild the VetAssist frontend on redfin:
```text
cd /ganuda/vetassist/frontend && npm run build
```

2. Clean up orphaned sessions in the database:
```text
psql -h 192.168.132.222 -U claude -d zammad_production -c "DELETE FROM chat_sessions WHERE user_id = '00000000-0000-0000-0000-000000000001';"
```

3. Verify the auth-context module exists:
```text
ls /ganuda/vetassist/frontend/lib/auth-context*
```

---

## Acceptance Criteria

- [ ] No `TEMP_USER_ID` constant in WizardChatHelper.tsx
- [ ] `useAuth()` hook imported and used for user.id
- [ ] Guard added: `if (!user?.id) return;` before creating sessions
- [ ] Test file reads user ID from environment variable
- [ ] Frontend builds without errors
