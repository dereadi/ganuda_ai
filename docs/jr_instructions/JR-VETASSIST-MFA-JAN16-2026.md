# JR Instruction: VetAssist Multi-Factor Authentication

## Metadata
```yaml
task_id: vetassist_mfa
priority: 1
assigned_to: VetAssist Jr.
target: backend + frontend
estimated_effort: medium
security_critical: true
```

## Overview

Implement MFA to protect veteran accounts. Support TOTP (Google Authenticator) for all users, with optional hardware token (SafeNet eToken) for admin accounts.

## MFA Options

| Method | Users | Implementation |
|--------|-------|----------------|
| TOTP | All users | pyotp library |
| Email code | All users | Send 6-digit code |
| Hardware token | Admin only | SafeNet eToken 5110 |

## Backend Implementation

### Dependencies
```
pyotp>=2.9.0
qrcode>=7.4.2
```

### Database Schema (bluefin)

```sql
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(32);
ALTER TABLE users ADD COLUMN mfa_backup_codes TEXT[];  -- encrypted
ALTER TABLE users ADD COLUMN mfa_method VARCHAR(20);  -- 'totp', 'email', 'hardware'

CREATE TABLE mfa_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    success BOOLEAN,
    method VARCHAR(20),
    ip_address INET,
    attempted_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

```python
# Enable MFA - Step 1: Generate secret
@router.post("/auth/mfa/setup")
async def setup_mfa(user: User = Depends(get_current_user)):
    secret = pyotp.random_base32()
    # Store temporarily (not in DB until verified)
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user.email, issuer_name="VetAssist")
    qr_code = generate_qr_code(uri)
    return {"secret": secret, "qr_code": qr_code}

# Enable MFA - Step 2: Verify and enable
@router.post("/auth/mfa/verify")
async def verify_mfa(code: str, secret: str, user: User = Depends(get_current_user)):
    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        user.mfa_secret = encrypt(secret)
        user.mfa_enabled = True
        backup_codes = generate_backup_codes(8)
        user.mfa_backup_codes = encrypt(backup_codes)
        return {"success": True, "backup_codes": backup_codes}
    raise HTTPException(400, "Invalid code")

# Login with MFA
@router.post("/auth/mfa/validate")
async def validate_mfa(user_id: UUID, code: str):
    user = get_user(user_id)
    totp = pyotp.TOTP(decrypt(user.mfa_secret))
    if totp.verify(code, valid_window=1):
        return issue_token(user)
    # Check backup codes
    if code in decrypt(user.mfa_backup_codes):
        remove_backup_code(user, code)
        return issue_token(user)
    raise HTTPException(401, "Invalid MFA code")

# Disable MFA (requires password)
@router.post("/auth/mfa/disable")
async def disable_mfa(password: str, user: User = Depends(get_current_user)):
    if verify_password(password, user.hashed_password):
        user.mfa_enabled = False
        user.mfa_secret = None
        return {"success": True}
    raise HTTPException(401, "Invalid password")
```

## Frontend Implementation

### MFA Setup Flow

```
Settings → Security → Enable MFA
│
├── Step 1: Show QR Code
│   ├── Display QR for Google Authenticator
│   ├── Show manual entry code
│   └── [Next]
│
├── Step 2: Verify Code
│   ├── Enter 6-digit code from app
│   └── [Verify]
│
└── Step 3: Backup Codes
    ├── Display 8 backup codes
    ├── "Save these somewhere safe"
    ├── [Download as text file]
    └── [Done]
```

### Login Flow with MFA

```
Login → Email + Password
│
├── If MFA not enabled → Dashboard
│
└── If MFA enabled → MFA Screen
    ├── Enter 6-digit code
    ├── [Use backup code] link
    ├── [Verify]
    └── → Dashboard
```

### Components

```tsx
<MFASetup
  onComplete={(backupCodes) => showBackupCodes(backupCodes)}
/>

<MFAChallenge
  onVerify={(code) => validateMFA(code)}
  onBackupCode={() => showBackupCodeInput()}
/>

<BackupCodesDisplay
  codes={backupCodes}
  onDownload={() => downloadCodes()}
/>
```

## Security Requirements

1. **Rate limiting**: Max 5 MFA attempts per 15 minutes
2. **Backup codes**: One-time use, 8 codes generated
3. **Secret storage**: Encrypted in database
4. **Session**: Require re-auth for MFA changes
5. **Logging**: All MFA attempts logged (success/fail)

## Success Criteria

- [ ] TOTP setup with QR code works
- [ ] Login requires MFA code when enabled
- [ ] Backup codes work (one-time use)
- [ ] Users can disable MFA (with password)
- [ ] Rate limiting prevents brute force
- [ ] All attempts logged for audit

---

*Cherokee AI Federation - For the Seven Generations*
