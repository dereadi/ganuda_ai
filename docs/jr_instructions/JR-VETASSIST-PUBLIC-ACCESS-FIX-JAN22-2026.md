# JR: VetAssist Public Access Fix - External Network Error

**Date:** January 22, 2026
**Priority:** URGENT - User Testing Blocked
**Reported By:** Kensie Williams (external tester)
**Status:** Needs Implementation

## Problem

VetAssist calculator shows "Network Error" for users outside the Cherokee AI network. External users cannot reach internal IP `192.168.132.223`.

## Root Cause

The frontend `.env.local` has a hardcoded internal IP:
```
NEXT_PUBLIC_API_URL=http://192.168.132.223:8001/api/v1
```

Next.js `NEXT_PUBLIC_*` variables are **baked in at build time**. The compiled JavaScript contains the internal IP.

## Solution

### Step 1: Update Environment Variable

On redfin, edit `/ganuda/vetassist/frontend/.env.local`:

```bash
# BEFORE (internal only)
NEXT_PUBLIC_API_URL=http://192.168.132.223:8001/api/v1

# AFTER (public access via Caddy)
NEXT_PUBLIC_API_URL=https://vetassist.ganuda.us/api/v1
```

**Alternative (relative URL):**
```bash
# Uses same origin as frontend - works for both internal and external
NEXT_PUBLIC_API_URL=/api/v1
```

The relative URL approach is **preferred** because:
- Works from any domain (vetassist.ganuda.us, vetassist.cherokee.ai, localhost)
- No CORS issues
- No mixed content (http/https) issues

### Step 2: Rebuild Frontend

```bash
cd /ganuda/vetassist/frontend
npm run build
```

### Step 3: Restart Frontend Service

```bash
sudo systemctl restart vetassist-frontend
# OR if not using systemd:
pkill -f "node.*vetassist" && cd /ganuda/vetassist/frontend && npm start &
```

### Step 4: Verify Caddy Configuration

Ensure Caddy is running and serving vetassist.ganuda.us:

```bash
sudo systemctl status caddy
curl -I https://vetassist.ganuda.us/
```

### Step 5: Verify DNS

Confirm `vetassist.ganuda.us` resolves to the correct public IP:

```bash
dig vetassist.ganuda.us
nslookup vetassist.ganuda.us
```

### Step 6: Test External Access

From an external network (or use phone on cellular):
1. Visit https://vetassist.ganuda.us/
2. Navigate to Calculator
3. Enter test conditions
4. Verify calculation works

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/vetassist/frontend/.env.local` | Update NEXT_PUBLIC_API_URL |

## Verification Checklist

- [ ] .env.local updated with relative or public URL
- [ ] Frontend rebuilt (`npm run build`)
- [ ] Frontend restarted
- [ ] Caddy serving vetassist.ganuda.us
- [ ] DNS resolves correctly
- [ ] External user can access calculator
- [ ] No console errors in browser DevTools

## Notes

- The Caddyfile at `/ganuda/config/Caddyfile.vetassist` is already configured correctly
- Caddy handles TLS certificates automatically via Let's Encrypt
- The backend API doesn't need changes - it already listens on localhost:8001

## For Seven Generations

This fix enables veterans outside the Cherokee AI network to access VetAssist, expanding our ability to help those who served.
