# ULTRATHINK: VetAssist VA OAuth Session Management
## Cherokee AI Federation
### January 20, 2026

---

## Executive Summary

VetAssist successfully authenticates veterans through VA.gov OAuth (Login.gov/ID.me) but lacks session persistence. This ULTRATHINK designs a secure, scalable session management system that stores VA tokens, creates VetAssist user accounts, and issues frontend JWTs.

**Council Vote:** PROCEED (82.5% confidence)
**Priority:** HIGH - Blocking full VA integration

---

## Current State Analysis

### What Works
1. OAuth redirect to VA.gov ✅
2. Login.gov/ID.me authentication ✅
3. Authorization code exchange for tokens ✅
4. Callback processing ✅

### What's Missing
1. VA token storage (access_token, refresh_token, expiry)
2. User account creation/linking from VA identity
3. VetAssist JWT issuance for frontend
4. Token refresh handling
5. Session invalidation/logout

### Current Flow (Broken)
```
User → VA Login → Token Exchange → Redirect to /va-success?session=None → 404/No Session
```

### Target Flow
```
User → VA Login → Token Exchange → Create/Link User → Store Tokens → Issue JWT → Redirect with JWT → Frontend Authenticated
```

---

## Seven Generations Analysis

### Privacy (Generation 1-3)
- Veterans' VA tokens contain sensitive identity data
- Tokens must be encrypted at rest
- Minimal data retention - only what's necessary
- Clear data deletion path

### Security (Generation 4-5)
- Token encryption using AES-256-GCM
- Separate encryption keys per user (key derivation)
- Refresh tokens stored with additional protection
- Audit logging of all token operations

### Sustainability (Generation 6-7)
- Design for VA API changes
- Support multiple identity providers
- Graceful degradation if VA is down
- Future-proof schema for additional OAuth providers

---

## Technical Architecture

### Database Schema

```sql
-- VA-linked user accounts
CREATE TABLE IF NOT EXISTS vetassist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- VA Identity (from token claims)
    va_icn VARCHAR(50) UNIQUE,           -- VA Integration Control Number
    va_veteran_status VARCHAR(20),        -- confirmed, not_confirmed, etc.

    -- Profile (from VA or user-entered)
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Account status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- VA OAuth tokens (encrypted)
CREATE TABLE IF NOT EXISTS vetassist_va_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES vetassist_users(id) ON DELETE CASCADE,

    -- Encrypted tokens
    access_token_encrypted BYTEA NOT NULL,
    refresh_token_encrypted BYTEA,

    -- Token metadata (not sensitive)
    token_type VARCHAR(20) DEFAULT 'Bearer',
    scope VARCHAR(500),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    refreshed_at TIMESTAMPTZ,

    UNIQUE(user_id)  -- One active token set per user
);

-- VetAssist sessions (for JWT tracking)
CREATE TABLE IF NOT EXISTS vetassist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES vetassist_users(id) ON DELETE CASCADE,

    -- Session data
    jwt_id VARCHAR(64) UNIQUE NOT NULL,  -- jti claim for revocation
    device_info JSONB,                    -- User agent, IP (hashed)

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,

    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_jwt (jwt_id)
);

-- Audit log for security
CREATE TABLE IF NOT EXISTS vetassist_auth_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES vetassist_users(id),
    event_type VARCHAR(50) NOT NULL,     -- login, logout, token_refresh, etc.
    event_data JSONB,                     -- Non-sensitive metadata
    ip_hash VARCHAR(64),                  -- SHA-256 of IP
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Token Encryption Strategy

```python
# Key derivation: unique key per user
def derive_user_key(user_id: str, master_key: bytes) -> bytes:
    """Derive user-specific encryption key using HKDF."""
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"vetassist_token_v1",
        info=user_id.encode()
    )
    return hkdf.derive(master_key)

# Encryption: AES-256-GCM
def encrypt_token(token: str, user_key: bytes) -> bytes:
    """Encrypt token with AES-256-GCM."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import os

    nonce = os.urandom(12)
    aesgcm = AESGCM(user_key)
    ciphertext = aesgcm.encrypt(nonce, token.encode(), None)
    return nonce + ciphertext  # Prepend nonce for decryption
```

### JWT Structure

```python
# VetAssist JWT claims
{
    "sub": "user_uuid",           # User ID
    "iss": "vetassist.ganuda.us", # Issuer
    "aud": "vetassist-frontend",  # Audience
    "exp": 1234567890,            # Expiry (30 min)
    "iat": 1234567890,            # Issued at
    "jti": "unique_session_id",   # JWT ID for revocation
    "va_linked": true,            # VA account linked
    "va_icn": "1012667145V762142" # VA ICN (for API calls)
}
```

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VA OAuth Callback                         │
│                  /api/v1/auth/va/callback                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              VASessionService                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Extract VA identity from token (ICN, name)       │   │
│  │ 2. Find or create VetAssist user                    │   │
│  │ 3. Encrypt & store VA tokens                        │   │
│  │ 4. Create session record                            │   │
│  │ 5. Generate VetAssist JWT                           │   │
│  │ 6. Audit log the login                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Redirect to Frontend with JWT                        │
│    /va-success?token=eyJ...&expires=1234567890              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Database Schema (Jr Task 1)
- Create migration for new tables
- Add indexes for performance
- Test schema on bluefin

### Phase 2: Token Encryption Service (Jr Task 2)
- Implement key derivation
- Implement encrypt/decrypt functions
- Add master key to secrets management
- Unit tests for encryption

### Phase 3: VA Session Service (Jr Task 3)
- Create VASessionService class
- Implement user creation/linking
- Implement token storage
- Implement JWT generation
- Integrate with OAuth callback

### Phase 4: Token Refresh (Jr Task 4)
- Background job for token refresh
- Refresh before expiry (5 min buffer)
- Handle refresh failures gracefully

### Phase 5: Frontend Integration (Jr Task 5)
- Update /va-success to handle JWT
- Store JWT in httpOnly cookie or localStorage
- Add auth context/provider
- Protected route wrapper

### Phase 6: Logout & Session Management (Jr Task 6)
- Logout endpoint (revoke session)
- Session listing for user
- Force logout all sessions

---

## Security Considerations

### Must Have
1. **Encrypt VA tokens at rest** - Never store plaintext
2. **Use httpOnly cookies** for JWT if possible
3. **Short JWT expiry** (30 min) with refresh
4. **Audit all auth events**
5. **Rate limit login attempts**

### Should Have
1. Device fingerprinting for session binding
2. Anomaly detection for suspicious logins
3. IP-based session validation

### Nice to Have
1. WebAuthn/passkey support
2. Remember device functionality
3. Session activity timeline

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| VA token exchange fails | Redirect to /va-error with message |
| User creation fails | Log error, show generic message |
| Token encryption fails | Critical - don't store, log alert |
| JWT generation fails | Retry once, then error page |
| Token refresh fails | Force re-login on next request |

---

## Testing Strategy

1. **Unit Tests**
   - Token encryption/decryption roundtrip
   - User creation from VA claims
   - JWT generation and validation

2. **Integration Tests**
   - Full OAuth flow with mock VA
   - Token refresh job
   - Session revocation

3. **Security Tests**
   - SQL injection on user lookup
   - Token tampering detection
   - Session fixation prevention

---

## Rollout Plan

1. **Deploy database migrations** (no user impact)
2. **Deploy backend services** (feature flagged)
3. **Enable for internal testing**
4. **Enable for beta users**
5. **Full rollout**

---

## Success Metrics

- OAuth completion rate > 95%
- Session creation latency < 500ms
- Token refresh success rate > 99%
- Zero plaintext token exposures

---

## References

- Council Vote: PROCEED (82.5% confidence)
- VA Lighthouse OAuth Docs: developer.va.gov
- OWASP Session Management: owasp.org

---

*Cherokee AI Federation - For Seven Generations*
