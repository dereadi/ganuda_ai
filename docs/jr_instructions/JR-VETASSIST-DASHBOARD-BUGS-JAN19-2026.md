# JR Instruction: VetAssist Dashboard Bug Fixes

## Metadata
```yaml
task_id: vetassist_dashboard_bugs_v1
priority: 1
assigned_to: it_triad_jr
target: redfin (frontend)
source: TPM user testing feedback
estimated_effort: small (1 day)
```

## Bugs Reported

### Bug 1: New Claim Button Returns 404

**Steps to reproduce:**
1. Sign in to VetAssist
2. Navigate to Dashboard
3. Click "New Claim" button
4. **Result**: 404 error page

**Expected**: New Claim wizard or form should open

**Fix**: Either:
- Create the `/claims/new` route and page, OR
- Remove/disable the button if feature not ready, OR
- Link to an existing page that handles claim creation

**Files to check:**
- `/ganuda/vetassist/frontend/src/app/claims/` - does this directory exist?
- `/ganuda/vetassist/frontend/src/app/dashboard/page.tsx` - where does button link to?

### Bug 2: Duplicate Calculator Buttons

**Steps to reproduce:**
1. Sign in to VetAssist
2. Look at navigation/dashboard
3. **Result**: Two different buttons/links both go to Calculator

**Expected**: Single clear path to Calculator

**Fix**:
- Identify where duplicates exist (sidebar? header? dashboard cards?)
- Remove one, keep the most intuitive location
- Ensure remaining button has clear label

### Bug 3: AI Research Tab Non-Functional

**Steps to reproduce:**
1. Sign in to VetAssist
2. Click "AI Research" tab/link
3. **Result**: Page loads but has no functionality

**Expected**: AI Research should either:
- Show research papers reviewed by Council
- Show technique recommendations
- Search VA/medical literature
- OR be hidden if not implemented

**Fix**:
- If feature is planned: stub out with "Coming Soon" message
- If feature is ready: wire up the backend endpoints
- If feature is not planned: remove from navigation

## Implementation Checklist

```bash
# 1. Check if claims routes exist
ls -la /ganuda/vetassist/frontend/src/app/claims/

# 2. Find where Calculator buttons are
grep -r "calculator" /ganuda/vetassist/frontend/src/app/ --include="*.tsx"

# 3. Find AI Research references
grep -r -i "research" /ganuda/vetassist/frontend/src/app/ --include="*.tsx"
```

## Acceptance Criteria

- [ ] New Claim button either works or is removed/disabled
- [ ] Only ONE Calculator button/link visible
- [ ] AI Research tab either works or shows "Coming Soon"
- [ ] No 404 errors on any navigation item
- [ ] All visible features have working backends

## Priority

Fix in this order:
1. 404 on New Claim (broken feature = frustrated user)
2. Duplicate Calculator (confusing UX)
3. AI Research (incomplete feature)

---

*Cherokee AI Federation - VetAssist*
*"If it's visible, it should work. If it doesn't work, it shouldn't be visible."*
