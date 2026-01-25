# JR Task Assignment: Fix Code Review Issues
**Date:** December 27, 2025
**Platform:** Bluefin (192.168.132.222)
**Project:** Ganuda VetAssist Platform
**Phase:** Code Review Fixes

---

## Context

JR 19 and JR 20 have completed comprehensive code reviews:
- **JR 19 Backend Review:** 7 HIGH priority issues, 11 MEDIUM issues
- **JR 20 Frontend Review:** 3 HIGH priority issues, 6 MEDIUM issues

**Before deployment (JR 18), we must fix all HIGH priority issues.**

---

## JR Task Assignments

### JR 21: Fix Backend HIGH Priority Issues (7 issues)
**Priority:** CRITICAL
**Dependencies:** Backend code from JRs 15-17
**Platform:** Bluefin

**Review Report:** `/ganuda/vetassist/docs/JR19_BACKEND_CODE_REVIEW_COMPREHENSIVE.md`

**Issues to Fix:**

#### 1. [HIGH] Change Default SECRET_KEY
**File:** `/ganuda/vetassist/backend/app/core/config.py:30`
**Current:**
```python
SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"
```

**Fix:**
```python
SECRET_KEY: str = Field(
    ...,  # Required, no default
    description="JWT secret key - must be set in .env"
)
```

**Also update:**
- `/ganuda/vetassist/backend/.env.example` - Add instructions to generate key
- Add startup validation in `main.py` to check SECRET_KEY isn't default

**Test:** Try to start app without SECRET_KEY - should fail with clear error

---

#### 2. [HIGH] Add Password Strength Requirements
**File:** `/ganuda/vetassist/backend/app/core/security.py:73`

**Current:**
```python
if len(password) < 8:
    raise ValueError("Password must be at least 8 characters")
```

**Fix:**
```python
def validate_password_strength(password: str) -> None:
    """
    Validate password meets strength requirements

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise ValueError("Password must contain at least one special character")
```

**Update:** `auth_service.py` to call `validate_password_strength()` before hashing

**Test:** Try to register with weak passwords - should fail with helpful messages

---

#### 3. [HIGH] Sanitize User Input (XSS Prevention)
**Files:**
- `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py:67`
- `/ganuda/vetassist/backend/app/services/council_chat.py:89`

**Install:** `pip install bleach` (add to requirements.txt)

**Create:** `/ganuda/vetassist/backend/app/core/sanitize.py`
```python
import bleach

def sanitize_html(text: str) -> str:
    """Remove HTML tags and dangerous content from user input"""
    # Allow no HTML tags
    return bleach.clean(text, tags=[], strip=True)

def sanitize_session_title(title: str) -> str:
    """Sanitize chat session title"""
    sanitized = sanitize_html(title)
    # Truncate to reasonable length
    return sanitized[:200]
```

**Fix:** Sanitize all user input before storing:
- Chat session titles
- Chat messages (before storing, not before sending to Council)
- User profile fields (name, phone)

**Test:** Try to create chat session with `<script>alert('XSS')</script>` as title

---

#### 4. [HIGH] Don't Log Database Credentials
**File:** `/ganuda/vetassist/backend/app/main.py:28`

**Current:**
```python
logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
```

**Fix:**
```python
# Extract only host and database name, not credentials
if '@' in settings.DATABASE_URL:
    parts = settings.DATABASE_URL.split('@')
    if len(parts) > 1:
        host_and_db = parts[1]
        logger.info(f"Database: {host_and_db}")
else:
    logger.info("Database: configured")
```

**Test:** Check startup logs - should see host/db but NOT username/password

---

#### 5. [HIGH] Improve Test Coverage to 70%
**Current:** ~30-40% coverage
**Target:** 70% minimum

**Create tests for:**

**`/ganuda/vetassist/backend/tests/test_security.py`:**
```python
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    decode_access_token
)

def test_password_hashing():
    password = "TestPass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

def test_password_strength_validation():
    # Valid passwords
    validate_password_strength("StrongP@ss123")

    # Invalid passwords
    with pytest.raises(ValueError):
        validate_password_strength("weak")  # Too short
    with pytest.raises(ValueError):
        validate_password_strength("nouppercase123!")
    with pytest.raises(ValueError):
        validate_password_strength("NOLOWERCASE123!")
    with pytest.raises(ValueError):
        validate_password_strength("NoNumbers!")
    with pytest.raises(ValueError):
        validate_password_strength("NoSpecialChars123")

def test_jwt_tokens():
    data = {"sub": "user123"}
    token = create_access_token(data)
    assert token

    decoded = decode_access_token(token)
    assert decoded["sub"] == "user123"
```

**`/ganuda/vetassist/backend/tests/test_calculator_service.py`:**
- Test all 15 JR 13 validation cases
- Test bilateral factor calculation
- Test dependents calculation
- Test edge cases (0%, 100%, invalid input)

**`/ganuda/vetassist/backend/tests/test_content_endpoints.py`:**
- Test content listing with filters
- Test content search
- Test pagination
- Test tag filtering

**Run:** `pytest --cov=app --cov-report=html`
**Goal:** 70%+ coverage before deployment

---

#### 6. [HIGH] Hide Internal Error Details in Production
**File:** `/ganuda/vetassist/backend/app/main.py:59`

**Current:**
```python
return JSONResponse(
    status_code=500,
    content={
        "detail": "Internal server error",
        "message": str(exc) if settings.DEBUG else "An error occurred"
    }
)
```

**Fix:**
```python
# Log full error internally
logger.error(f"Unhandled exception: {exc}", exc_info=True)

# Return sanitized error to client
if settings.DEBUG:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )
else:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )
```

**Test:** Set DEBUG=false, trigger error, check response doesn't leak details

---

#### 7. [HIGH] Implement Rate Limiting
**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`

**Install:** `pip install slowapi` (add to requirements.txt)

**Create:** `/ganuda/vetassist/backend/app/core/rate_limit.py`
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

**Update:** `main.py`
```python
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

def _rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )
```

**Update:** Auth endpoints
```python
@router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(request: Request, ...):
```

**Test:** Make 6 login requests in 1 minute - 6th should return 429

---

### Deliverables (JR 21)
- [ ] All 7 HIGH priority backend issues fixed
- [ ] Test coverage at 70%+
- [ ] All new tests passing
- [ ] Updated requirements.txt
- [ ] Updated .env.example
- [ ] Verification report with before/after

---

## JR 22: Fix Frontend HIGH Priority Issues (3 issues)
**Priority:** CRITICAL
**Dependencies:** Frontend code from JRs 14-17
**Platform:** Bluefin

**Review Report:** `/ganuda/vetassist/docs/JR20_FRONTEND_CODE_REVIEW.md`

**Issues to Fix:**

#### 1. [HIGH] Add ARIA Labels Throughout Application
**Files:** Multiple components

**Already created:** `/ganuda/vetassist/frontend/lib/types.ts` (TypeScript types)
**Already created:** `/ganuda/vetassist/frontend/lib/logger.ts` (Logger utility)

**Fix calculator page:**
`/ganuda/vetassist/frontend/app/calculator/page.tsx`

```tsx
// Add Condition button
<button
  type="button"
  onClick={() => append({ name: '', rating: 0, is_bilateral: false })}
  aria-label="Add new disability condition to calculator"
  className="..."
>
  <Plus className="h-4 w-4 mr-1" aria-hidden="true" />
  Add Condition
</button>

// Remove Condition button
<button
  type="button"
  onClick={() => remove(index)}
  aria-label={`Remove condition ${index + 1}`}
  className="..."
>
  <Trash2 className="h-4 w-4" aria-hidden="true" />
</button>

// Condition name input
<input
  {...register(`conditions.${index}.name`)}
  aria-label={`Condition ${index + 1} name`}
  placeholder="e.g., PTSD, Tinnitus, Back Pain"
  className="..."
/>

// Rating select
<select
  {...register(`conditions.${index}.rating`, { valueAsNumber: true })}
  aria-label={`Condition ${index + 1} disability rating percentage`}
  className="..."
>
```

**Fix chat page:**
`/ganuda/vetassist/frontend/app/chat/page.tsx`

```tsx
// Message input
<input
  type="text"
  value={messageInput}
  onChange={(e) => setMessageInput(e.target.value)}
  aria-label="Type your question about VA disability claims"
  aria-describedby="chat-input-hint"
  placeholder="Ask about VA disability claims..."
  className="..."
/>
<span id="chat-input-hint" className="sr-only">
  Ask questions about VA claims, evidence requirements, or the appeals process
</span>

// Send button
<button
  onClick={sendMessage}
  disabled={!messageInput.trim() || isSending}
  aria-label="Send message to AI assistant"
  className="..."
>
  <Send className="h-5 w-5" aria-hidden="true" />
</button>

// Loading spinner with ARIA
<div role="status" aria-live="polite">
  <div className="animate-spin ..." aria-hidden="true"></div>
  <span className="sr-only">AI is thinking, please wait...</span>
</div>
```

**Fix resources page:**
`/ganuda/vetassist/frontend/app/resources/page.tsx`

```tsx
// Search input
<input
  type="text"
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  aria-label="Search educational resources by keyword"
  aria-describedby="search-help"
  placeholder="Search articles..."
  className="..."
/>
<span id="search-help" className="sr-only">
  Search by condition name, topic, or keyword
</span>

// Filter buttons
<button
  onClick={() => setDifficultyFilter(level)}
  aria-label={`Filter to show ${level} level articles`}
  aria-pressed={difficultyFilter === level}
  className="..."
>
  {level}
</button>
```

**Add to ALL loading states:**
```tsx
<div role="status" aria-live="polite">
  <div className="animate-spin ..." aria-hidden="true"></div>
  <span className="sr-only">Loading...</span>
</div>
```

---

#### 2. [HIGH] Add Keyboard Navigation Support
**File:** `/ganuda/vetassist/frontend/app/chat/page.tsx:220-248`

**Fix chat session list:**
```tsx
<div
  role="button"
  tabIndex={0}
  onClick={() => setCurrentSessionId(session.id)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setCurrentSessionId(session.id);
    }
  }}
  aria-label={`Select chat session: ${session.title || 'Untitled'}`}
  aria-current={currentSessionId === session.id ? 'true' : 'false'}
  className={`p-3 cursor-pointer hover:bg-gray-100 border-b ${
    currentSessionId === session.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
  }`}
>
```

**Also add keyboard support to:**
- Content cards in resources page
- Filter buttons
- Any other clickable divs

**Test:** Navigate entire app using only keyboard (Tab, Enter, Space)

---

#### 3. [HIGH] Fix TypeScript `any` Types
**File:** `/ganuda/vetassist/frontend/lib/api-client.ts`

**Types already created in:** `/ganuda/vetassist/frontend/lib/types.ts`

**Update api-client.ts:**
```typescript
import type {
  CalculatorRequest,
  CalculationResult,
  ChatMessageRequest,
  ChatMessageResponse,
} from './types';

/**
 * Calculate VA disability rating
 */
async calculateRating(request: CalculatorRequest): Promise<CalculationResult> {
  return this.request<CalculationResult>('/calculator/calculate', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Send chat message
 */
async sendChatMessage(request: ChatMessageRequest): Promise<ChatMessageResponse> {
  return this.request<ChatMessageResponse>('/chat/message', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
```

**Update calculator page:**
```typescript
import type { CalculationResult } from '@/lib/types';

// Change from: setResult(data);
setResult(data as CalculationResult);

// Change catch blocks from:
} catch (err: any) {
// To:
} catch (err: unknown) {
  const error = err as Error;
  logger.error('Calculation failed', { error });
}
```

**Replace all console.error with logger:**
```typescript
import { logger } from '@/lib/logger';

// Instead of: console.error('Failed:', error);
logger.error('Failed to load data', { context: 'ComponentName', error });
```

---

### Additional Frontend Fixes (MEDIUM - bonus)

#### 4. [MEDIUM] Connect Chat to Auth Context
**File:** `/ganuda/vetassist/frontend/app/chat/page.tsx`

**Remove:**
```typescript
const TEMP_USER_ID = "00000000-0000-0000-0000-000000000001";
```

**Add:**
```typescript
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';

export default function ChatPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login?redirect=/chat');
    }
  }, [user, router]);

  // Use user.id instead of TEMP_USER_ID
  const response = await axios.get(`${API_URL}/chat/sessions`, {
    params: { user_id: user?.id, limit: 50 },
  });
}
```

---

### Deliverables (JR 22)
- [ ] All ARIA labels added to interactive elements
- [ ] Keyboard navigation works throughout app
- [ ] All TypeScript `any` types removed
- [ ] Logger utility used instead of console.error
- [ ] Chat connected to auth context
- [ ] WCAG 2.1 AA compliance verified
- [ ] Keyboard-only navigation tested
- [ ] Screen reader tested (if possible)
- [ ] Verification report with screenshots

---

## Success Criteria

**Code review fixes are complete when:**
1. ✅ All 7 backend HIGH priority issues fixed (JR 21)
2. ✅ All 3 frontend HIGH priority issues fixed (JR 22)
3. ✅ Backend test coverage at 70%+
4. ✅ All tests passing
5. ✅ WCAG 2.1 AA compliance verified
6. ✅ Keyboard navigation works
7. ✅ No TypeScript `any` types
8. ✅ Security improvements verified

**After fixes:** Ready for JR 18 deployment

---

## Testing Requirements

### Backend (JR 21)
```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Check coverage percentage
# Should be 70% or higher

# Test rate limiting
# Make 6 requests in 1 minute - 6th should fail

# Test password strength
# Try weak passwords - should reject

# Check logs
# Start app, verify no credentials in logs
```

### Frontend (JR 22)
```bash
# Type check
npm run type-check
# Should have 0 errors

# Lint check
npm run lint
# Should have 0 errors

# Build check
npm run build
# Should succeed

# Keyboard navigation test
# Tab through entire app
# Enter/Space should activate buttons
# Escape should close modals

# Screen reader test (optional)
# Use browser dev tools accessibility tree
# Check all interactive elements have labels
```

---

## Timeline

**Target: All fixes complete in 6-8 hours**

- JR 21 (Backend fixes): 4-5 hours
- JR 22 (Frontend fixes): 2-3 hours
- Total: 6-8 hours

**After completion:** JR 18 deploys to Bluefin staging

---

## For the Seven Generations.

**Big Mac (TPM) - Ganuda AI**
**December 27, 2025**
