# JR Instruction: Register JWK with VA Developer Portal for CCG

**Priority**: P1 - Critical (Blocking VetAssist Production)
**Assigned To**: DevOps Jr. / Human Operator
**Created**: January 21, 2026
**Status**: Ready for Execution

## Executive Summary

The VetAssist CCG (Client Credentials Grant) authentication is failing with `invalid_client` error because the **JWK public key is not registered** with the VA developer portal for our CCG client ID.

This is a **manual registration task** that requires logging into developer.va.gov.

## Problem Statement

```
Error: invalid_client
Description: Client authentication failed (e.g., unknown client, no client authentication included,
or unsupported authentication method). audience claim must match endpoint.
```

Despite the error message mentioning "audience claim", the real issue is that VA's OAuth server doesn't recognize our client because the public key isn't registered.

## Current Configuration

| Item | Value |
|------|-------|
| CCG Client ID | `0oa19496rl35FKvM42p8` |
| Private Key Path | `/ganuda/vetassist/backend/keys/va_ccg_private.pem` |
| Public Key (JWK) | `/ganuda/vetassist/backend/keys/va_ccg_public.jwk` |
| Token Endpoint | `https://sandbox-api.va.gov/oauth2/claims/system/v1/token` |

## JWK to Register

Copy this exact JWK and register it in the VA developer portal:

```json
{
  "kty": "RSA",
  "n": "oiotJX17lt2oFJwK7rffsZhN7LwmdJa6XwLaw5VQeS8qT7agzAFAg4rmnApro3ui_4qbl5zf7P8c1NW3cJxt2whuLbojTesF90auBgSo7y1PiBQU80B5eqt_ukxwjjNMh9BrR-tKQveRkxjM3Tr7qDQadIpyJ8afcKzjwqfwhMKXtRT6VakTcQoNkKKJlbcHFGGtJq1fFH3qJeA6kPA_4MsST5svOnvGdiI_2E_BrhgdfgBPWPwrJeTy9Mm6g0p9gs4_7_fixtDMGVKihGtrjK0cViIOhGixASHaLdUdUpQ4lpN_PeCnilGpx4c49WLI9PqK_V_qNO482yQUWYwn6w",
  "e": "AQAB",
  "alg": "RS256",
  "use": "sig"
}
```

## Step-by-Step Registration Process

### Step 1: Log into VA Developer Portal

1. Navigate to: https://developer.va.gov/
2. Click "Sign In" (top right)
3. Use Cherokee AI Federation credentials
4. If no account exists, create one first

### Step 2: Navigate to Your Application

1. After login, click on your profile/dashboard
2. Find "My Applications" or "Applications"
3. Look for the VetAssist application
4. If not found, you may need to create a new application

### Step 3: Locate CCG Settings

1. In the application settings, look for:
   - "Client Credentials Grant" section
   - "CCG Configuration"
   - "System-to-System Authentication"
   - "Public Keys" or "JWK Registration"

2. The CCG Client ID should match: `0oa19496rl35FKvM42p8`

### Step 4: Register the Public Key

1. Find the option to "Add Public Key" or "Upload JWK"
2. Paste the complete JWK JSON (from above)
3. Save the configuration
4. Note any confirmation or key ID returned

### Step 5: Verify API Access

Ensure the following APIs are enabled for CCG access:
- [ ] Benefits Claims API (`/services/claims/v2/`)
- [ ] Benefits Intake API (`/services/vba_documents/v1/`)

### Step 6: Verify Registration

After registration, test with this command:

```bash
cd /ganuda/vetassist/backend && source /home/dereadi/cherokee_venv/bin/activate
python3 -c "
from app.services.va_ccg_service import VACCGService
service = VACCGService()
result = service.test_connection()
print(result)
"
```

Expected result: Should get an access token instead of `invalid_client` error.

## Alternative: Check if CCG is Already Configured

Before registering, verify what's currently configured:

1. Log into developer.va.gov
2. Go to your VetAssist application
3. Check if there are any existing CCG configurations
4. If a different key is registered, you have two options:
   - Replace it with the JWK above
   - Generate a new key pair that matches the registered one

## If Application Doesn't Exist

If VetAssist is not registered as an application:

1. Click "Request Sandbox Access" or "Create Application"
2. Fill in:
   - **Application Name**: VetAssist
   - **Organization**: Cherokee AI Federation
   - **Description**: Veteran benefits claim assistance platform
   - **Callback URL**: `https://vetassist.ganuda.us/api/v1/auth/va/callback`
3. Select APIs:
   - Benefits Intake API (for document submission)
   - Benefits Claims API (for claim status)
   - Veteran Verification API (optional, for identity)
4. Enable CCG (Client Credentials Grant)
5. Upload the JWK public key

## Troubleshooting

### Issue: "Invalid JWK format"
- Ensure the JSON is valid (no trailing commas)
- Verify all fields are present: `kty`, `n`, `e`, `alg`, `use`

### Issue: "Key already registered"
- A different key may be associated with this client
- Either update our private key to match, or delete the old registration

### Issue: "CCG not enabled for this application"
- You may need to request CCG access separately
- Contact VA developer support if needed

### Issue: After registration, still getting errors
- Wait 5-10 minutes for propagation
- Verify the correct token endpoint is being used
- Check that scopes are properly configured

## Post-Registration Configuration Update

If the token endpoint or other settings need to change after registration, update:

**File**: `/ganuda/vetassist/backend/.env`

```bash
# Update if VA provides different endpoints
VA_CCG_TOKEN_URL=https://sandbox-api.va.gov/oauth2/claims/system/v1/token
VA_CCG_AUD=https://sandbox-api.va.gov/oauth2/claims/system/v1/token
```

## Success Criteria

- [ ] Logged into VA developer portal
- [ ] Located VetAssist application (or created it)
- [ ] Registered the JWK public key with CCG client
- [ ] Test command returns access token (not error)
- [ ] Documented any changes made to portal configuration

## Notes for Human Operator

This task requires a human because:
1. VA developer portal requires interactive login (possibly MFA)
2. Portal navigation may vary based on account permissions
3. May require approval workflows for certain API access

**Estimated Time**: 15-30 minutes

## Resources

- [VA Developer Portal](https://developer.va.gov/)
- [VA CCG Documentation](https://developer.va.gov/explore/authorization/docs/client-credentials)
- [VA API Support](https://developer.va.gov/support)

---

*Cherokee AI Federation - For Seven Generations*
*"Serving those who served."*
