# ULTRATHINK: VetAssist Sprint - Auth & UX
## Date: January 24, 2026
## Cherokee AI Federation - For Seven Generations

---

## Council Decision

**Question:** VetAssist Sprint Priority - which items first?
**Vote:** Auth-First approach
**Confidence:** 87.2% (High)
**Concerns:** Security, 7GEN, Consensus, Performance

**Consensus:** "Address auth issues first due to significant security risks. Next, tackle UX gaps."

---

## Current State Analysis

### Auth Issues (P1-P2)
1. **Chat hardcoded user ID** - Chat endpoint uses hardcoded user, not session
2. **Protected routes not enforced** - Frontend routes accessible without auth
3. **No Forgot Password flow** - Users can't recover accounts

### UX Gaps (P1-P2)
4. **Missing /about page** - 404 error
5. **No shared Header component** - Inconsistent navigation
6. **No mobile navigation** - Poor mobile experience

### Features (P3 - Backlog)
7. Calculator results not saved
8. PDF export
9. Educational content seeding

---

## Implementation Plan

### Constraint: Max 3 files per Jr task (KB-QWEN-MULTIFILE-001)

---

## Phase 1: Auth Hardening (3 tasks)

### Task 1: Chat Auth Integration (2 files)
**Files:**
- `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`
- `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py` (if session helper needed)

**Changes:**
- Remove hardcoded `user_id = "demo-user"`
- Get user_id from JWT token/session
- Return 401 if not authenticated

### Task 2: Protected Routes - Backend (3 files)
**Files:**
- `/ganuda/vetassist/backend/app/core/security.py` (create auth dependency)
- `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`
- `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`

**Changes:**
- Create `get_current_user` dependency
- Add auth requirement to sensitive endpoints

### Task 3: Protected Routes - Frontend (3 files)
**Files:**
- `/ganuda/vetassist/frontend/middleware.ts` (or create)
- `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`
- `/ganuda/vetassist/frontend/app/dashboard/page.tsx`

**Changes:**
- Add auth check middleware
- Redirect unauthenticated users to /login

---

## Phase 2: UX Foundation (3 tasks)

### Task 4: Shared Header Component (2 files)
**Files:**
- `/ganuda/vetassist/frontend/components/Header.tsx` (create)
- `/ganuda/vetassist/frontend/app/layout.tsx`

**Changes:**
- Create reusable Header with nav links
- Integrate into root layout

### Task 5: Mobile Navigation (2 files)
**Files:**
- `/ganuda/vetassist/frontend/components/MobileNav.tsx` (create)
- `/ganuda/vetassist/frontend/components/Header.tsx` (update)

**Changes:**
- Hamburger menu for mobile
- Slide-out navigation drawer

### Task 6: About Page (1 file)
**Files:**
- `/ganuda/vetassist/frontend/app/about/page.tsx` (create)

**Changes:**
- Mission statement
- How VetAssist helps veterans
- Privacy/security commitment

---

## Phase 3: Forgot Password (2 tasks)

### Task 7: Forgot Password - Backend (2 files)
**Files:**
- `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`
- `/ganuda/vetassist/backend/app/services/email_service.py` (if needed)

**Changes:**
- POST /auth/forgot-password endpoint
- Generate reset token, send email

### Task 8: Forgot Password - Frontend (2 files)
**Files:**
- `/ganuda/vetassist/frontend/app/forgot-password/page.tsx` (create)
- `/ganuda/vetassist/frontend/app/reset-password/[token]/page.tsx` (create)

**Changes:**
- Email input form
- Password reset form

---

## Task Summary

| Phase | Task | Files | Priority |
|-------|------|-------|----------|
| 1 | Chat Auth Integration | 2 | P1 |
| 1 | Protected Routes Backend | 3 | P1 |
| 1 | Protected Routes Frontend | 3 | P1 |
| 2 | Shared Header | 2 | P1 |
| 2 | Mobile Navigation | 2 | P2 |
| 2 | About Page | 1 | P1 |
| 3 | Forgot Password Backend | 2 | P2 |
| 3 | Forgot Password Frontend | 2 | P2 |

**Total: 8 tasks, 17 files, all within 3-file limit**

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Chat uses authenticated user ID
- [ ] Sensitive endpoints require auth
- [ ] Unauthenticated users redirected to login

### Phase 2 Complete When:
- [ ] Consistent header across all pages
- [ ] Mobile users have working navigation
- [ ] /about page loads without 404

### Phase 3 Complete When:
- [ ] Users can request password reset
- [ ] Reset email sent successfully
- [ ] New password can be set via token

---

## Risk Mitigation

**Crawdad (Security):** Auth changes tested thoroughly before deploy
**Turtle (7GEN):** Building auth foundation that scales
**Gecko (Performance):** Auth checks should be lightweight (JWT validation)
**Peace Chief:** Clear task boundaries prevent conflicts

---

**FOR SEVEN GENERATIONS** - Secure foundations protect those who come after.
