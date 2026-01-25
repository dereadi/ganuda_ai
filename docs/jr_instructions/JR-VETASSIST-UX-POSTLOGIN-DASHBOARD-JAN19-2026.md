# JR Instruction: VetAssist UX - Post-Login Dashboard Experience

## Metadata
```yaml
task_id: vetassist_ux_dashboard_v1
priority: 1
assigned_to: it_triad_jr
target: bluefin (database) + redfin (frontend)
source: TPM user testing feedback
estimated_effort: small (2-3 days)
```

## User Story

As a veteran using VetAssist, when I sign in, I want to land on MY dashboard - not a calculator page. The dashboard should show my saved rating calculations, and I should be able to add/update them without leaving my home page.

## Current Behavior (Problem)

1. User visits VetAssist home page
2. User clicks "Sign In"
3. User authenticates successfully
4. **User lands on /calculator** ← Wrong
5. User has to navigate to find dashboard

## Expected Behavior (Solution)

1. User visits VetAssist home page
2. User clicks "Sign In"
3. User authenticates successfully
4. **User lands on /dashboard** ← Correct
5. Dashboard contains embedded calculator widget
6. User's calculations are saved and visible
7. User can update/reconfigure without leaving dashboard

## Implementation Tasks

### Task 1: Fix Post-Login Redirect

**File**: `/ganuda/vetassist/frontend/src/app/auth/` or equivalent auth handler

Change the post-authentication redirect from `/calculator` to `/dashboard`.

```typescript
// BEFORE
router.push('/calculator')

// AFTER
router.push('/dashboard')
```

### Task 2: Embed Calculator in Dashboard

**File**: `/ganuda/vetassist/frontend/src/app/dashboard/page.tsx`

Import and embed the calculator component as a widget within the dashboard layout.

```typescript
// Dashboard should include:
// - Welcome message with user name
// - Calculator widget (embedded, not linked)
// - Saved calculations list
// - Quick actions
```

### Task 3: Create User Calculations Table

**Database**: bluefin (zammad_production)

```sql
CREATE TABLE vetassist_user_calculations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,  -- Auth user ID
    name VARCHAR(200),              -- User's label for this calculation
    ratings JSONB NOT NULL,         -- Array of ratings [70, 30, 20]
    combined_rating INTEGER,        -- Calculated result
    bilateral_applied BOOLEAN DEFAULT FALSE,
    notes TEXT,                     -- User notes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_primary BOOLEAN DEFAULT FALSE  -- User's "main" calculation
);

CREATE INDEX idx_user_calcs_user ON vetassist_user_calculations(user_id);
CREATE INDEX idx_user_calcs_primary ON vetassist_user_calculations(user_id, is_primary);
```

### Task 4: API Endpoints for Saved Calculations

**File**: `/ganuda/vetassist/backend/app/api/v1/endpoints/calculations.py`

```python
# GET /api/v1/calculations - List user's saved calculations
# POST /api/v1/calculations - Save new calculation
# PUT /api/v1/calculations/{id} - Update calculation
# DELETE /api/v1/calculations/{id} - Delete calculation
# PATCH /api/v1/calculations/{id}/primary - Set as primary
```

### Task 5: Dashboard Calculator Widget

Create a calculator widget component that:
- Shows current/primary saved calculation
- Allows inline editing
- Auto-saves on change (debounced)
- Shows "Save as new" option for variants

### Task 6: Dashboard Layout

Dashboard sections:
1. **Header**: Welcome, {user name}
2. **Primary Calculator Widget**: Embedded, editable
3. **Saved Calculations**: List with edit/delete
4. **Quick Links**: Evidence checklist, chat, resources

## Acceptance Criteria

- [ ] Post-login redirects to /dashboard
- [ ] Calculator is embedded in dashboard (not separate page)
- [ ] User can save calculations with custom names
- [ ] User can update existing calculations
- [ ] User can set a "primary" calculation
- [ ] Calculations persist across sessions
- [ ] Mobile-responsive layout

## UX Principles

1. **Dashboard is home** - Everything the user needs, one place
2. **Save by default** - Don't lose user's work
3. **Configurable** - User controls their experience
4. **No hunting** - Key tools visible, not buried in menus

## Notes

This is the first UX feedback from real user testing. Prioritize user flow over feature completeness.

---

*Cherokee AI Federation - VetAssist*
*"The veteran's dashboard is their command center."*
