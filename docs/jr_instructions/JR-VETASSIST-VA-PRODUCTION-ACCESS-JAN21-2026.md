# JR Instruction: VetAssist VA Production Access

**Priority**: P2 - High
**Assigned To**: Software Engineer Jr. / DevOps Jr.
**Created**: January 21, 2026
**Status**: Ready for Execution

## Executive Summary

VetAssist has **fully functional VA sandbox integration**. This instruction documents the path to production access.

## Current Status

### Sandbox Integration (WORKING)

| Component | Status | Evidence |
|-----------|--------|----------|
| Lighthouse Benefits Intake API | ✅ **WORKING** | Successfully gets upload GUIDs, status checks work |
| OAuth User Login | ✅ Configured | Credentials set, endpoints configured |
| CCG Server-to-Server | ⚠️ 404 Error | Token endpoint returning 404 |
| RSA Key Pair | ✅ Generated | Private/public keys in `/ganuda/vetassist/backend/keys/` |

### Credentials Located

```
/ganuda/vetassist/backend/.env:
- VA_LIGHTHOUSE_API_KEY=Bnb9P1df1TBsQTuVW6bpSB887di9SJVT
- VA_OAUTH_CLIENT_ID=0oa19441es2SkUgu32p8
- VA_OAUTH_CLIENT_SECRET=VPoIz3Q...
- VA_CCG_CLIENT_ID=0oa19496rl35FKvM42p8
```

### Test Results (January 21, 2026)

```
[Step 1] Request Upload Location...
  ✅ SUCCESS!
  GUID: 0c14bd43-d96d-4e2c-bb36-d873787237ea
  Status: pending
  Location URL: https://sandbox-api.va.gov/services_user_content/vba_documents/...

[Step 2] Check Status Endpoint...
  ✅ Status check works!
  Current status: pending
```

## Production Access Path

### Step 1: Verify Sandbox Completeness

Before requesting production access:

- [ ] Lighthouse Benefits Intake: Upload test PDF successfully
- [ ] OAuth: Complete full login flow with test veteran
- [ ] CCG: Fix 404 error and obtain test token
- [ ] Document submission: Verify full workflow end-to-end

### Step 2: Fix CCG 404 Issue

The CCG token endpoint is returning 404. Possible causes:

1. **Wrong URL**: Current URL is `https://sandbox-api.va.gov/oauth2/benefits-claims/system/v1/token`
   - Check VA developer docs for correct endpoint
   - May need different path for sandbox vs production

2. **CCG Not Registered**: The public key may not be registered with VA
   - Upload `va_ccg_public.jwk` to VA developer portal
   - Associate with CCG client ID

3. **Scope Issues**: May need different scopes
   - Try: `system/claim.read system/claim.write`

**Debug Command:**
```bash
cd /ganuda/vetassist/backend && source /home/dereadi/cherokee_venv/bin/activate
python3 -c "
from app.services.va_ccg_service import VACCGService
service = VACCGService()
result = service.test_connection()
print(result)
"
```

### Step 3: Request Production Access

**Portal**: [developer.va.gov/production-access](https://developer.va.gov/production-access)

**Process:**
1. Log in to VA Developer Portal
2. Navigate to "Request Production Access"
3. Select APIs needed:
   - Benefits Intake API (document submission)
   - Benefits Claims API (claim status)
   - Veteran Verification API (identity)
4. Complete application form
5. Schedule demo with VA stakeholders

**Required Information:**
- Application name: VetAssist
- Organization: Cherokee AI Federation
- Use case description
- Privacy policy URL
- Terms of service URL
- Technical contact information
- Expected API usage volume

### Step 4: Production Configuration

After receiving production credentials:

**Update `/ganuda/vetassist/backend/.env`:**
```bash
# Change sandbox to production
VA_API_BASE=https://api.va.gov

# Update OAuth URLs
VA_OAUTH_AUTH_URL=https://api.va.gov/oauth2/authorization
VA_OAUTH_TOKEN_URL=https://api.va.gov/oauth2/token

# Update CCG URLs
VA_CCG_TOKEN_URL=https://api.va.gov/oauth2/benefits-claims/system/v1/token
VA_CCG_AUD=https://api.va.gov/oauth2/benefits-claims/system/v1/token

# Replace with production credentials
VA_LIGHTHOUSE_API_KEY=<production_key>
VA_OAUTH_CLIENT_ID=<production_client_id>
VA_OAUTH_CLIENT_SECRET=<production_secret>
VA_CCG_CLIENT_ID=<production_ccg_client_id>
```

**Generate Production Keys:**
```bash
cd /ganuda/vetassist/backend/keys
openssl genrsa -out va_ccg_private_prod.pem 2048
openssl rsa -in va_ccg_private_prod.pem -pubout -out va_ccg_public_prod.pem
chmod 600 va_ccg_private_prod.pem
```

## VA API Documentation

### Benefits Intake API (Document Submission)

**Purpose**: Upload claim documents (PDFs) to VA

**Workflow**:
1. `POST /services/vba_documents/v1/uploads` - Get upload location
2. `PUT {location}` - Upload PDF with metadata
3. `GET /services/vba_documents/v1/uploads/{guid}` - Check status

**Statuses**: pending → uploaded → received → processing → success → vbms

### Benefits Claims API (Claim Status)

**Purpose**: Check status of veteran's claims

**Endpoints**:
- `GET /services/claims/v2/veterans/claims` - List all claims
- `GET /services/claims/v2/veterans/claims/{id}` - Claim details

**Requires**: OAuth access token with `claim.read` scope

### OAuth Flow

**Scopes Available**:
- `openid` - Required for authentication
- `profile` - Veteran profile info
- `claim.read` - Read claim status
- `claim.write` - Submit claims

**Callback URL**: `https://vetassist.ganuda.us/api/v1/auth/va/callback`

## Testing Commands

### Test Lighthouse API
```bash
curl -X POST "https://sandbox-api.va.gov/services/vba_documents/v1/uploads" \
  -H "apikey: Bnb9P1df1TBsQTuVW6bpSB887di9SJVT" \
  -H "Content-Type: application/json"
```

### Test OAuth Login URL
```bash
cd /ganuda/vetassist/backend && python3 -c "
from app.services.va_oauth_service import VAOAuthService
service = VAOAuthService()
url, state = service.get_authorization_url()
print(f'Login URL: {url}')
"
```

### Test Full Upload Workflow
```bash
cd /ganuda/vetassist/backend && python3 -c "
from app.services.va_api_service import VAAPIService
service = VAAPIService()

# Get upload location
result = service.get_upload_location()
print(f'Upload GUID: {result[\"guid\"]}')
print(f'Location: {result[\"location\"][:80]}...')
"
```

## Security Considerations

1. **Never commit credentials to git**
2. **Private keys must have 600 permissions**
3. **Use Silverfin vault for production secrets**
4. **Rotate keys annually**
5. **Log all API access for audit trail**

## Success Criteria

- [ ] All sandbox tests pass
- [ ] Production access request submitted
- [ ] Demo scheduled with VA
- [ ] Production credentials received
- [ ] Production environment configured
- [ ] End-to-end production test successful

## Resources

- [VA Developer Portal](https://developer.va.gov/)
- [Benefits Intake API Docs](https://developer.va.gov/explore/benefits/docs/benefits)
- [OAuth Documentation](https://developer.va.gov/explore/authorization)
- [GitHub: vets-api-clients](https://github.com/department-of-veterans-affairs/vets-api-clients)

---

*Cherokee AI Federation - For Seven Generations*
*"Serving those who served."*
