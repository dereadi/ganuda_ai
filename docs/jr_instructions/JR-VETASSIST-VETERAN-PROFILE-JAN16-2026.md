# JR Instruction: Enhanced Veteran Profile with PII Separation

## Metadata
```yaml
task_id: vetassist_veteran_profile
priority: 1
assigned_to: VetAssist Jr.
target: backend + frontend + goldfin
estimated_effort: medium
dependencies:
  - User authentication (complete)
  - Goldfin PII vault
  - Presidio integration
```

## Overview

Enhance the veteran profile to store service history, current VA status, and personal information. PII fields stored encrypted on goldfin; non-PII on bluefin.

## Data Model

### What Goes Where

| Field | Location | Why |
|-------|----------|-----|
| Name, email | Bluefin | Auth, non-sensitive |
| Service branch, dates, MOS | Bluefin | Not PII |
| Discharge type, rank | Bluefin | Not PII |
| Current VA rating | Bluefin | Not PII |
| Dependents (counts only) | Bluefin | Not PII |
| VSO representation | Bluefin | Not PII |
| **SSN** | Goldfin | PII - encrypted |
| **DOB** | Goldfin | PII - encrypted |
| **VA File Number** | Goldfin | PII - encrypted |
| **Phone** | Goldfin | PII - encrypted |
| **Address** | Goldfin | PII - encrypted |
| **Documents** | Goldfin | May contain PII |

## Database Schema

### Bluefin - User Profile Extension

```sql
-- Extend existing users table or create profile table
CREATE TABLE veteran_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Service Information
    service_branch VARCHAR(50),  -- 'army', 'navy', 'usmc', 'usaf', 'uscg', 'space_force'
    service_start_date DATE,
    service_end_date DATE,
    military_occupation VARCHAR(100),  -- MOS/Rating/AFSC
    rank_at_discharge VARCHAR(50),
    discharge_type VARCHAR(50),  -- 'honorable', 'general', 'other_than_honorable', 'bad_conduct', 'dishonorable'
    combat_veteran BOOLEAN DEFAULT FALSE,

    -- Current VA Status
    has_va_rating BOOLEAN DEFAULT FALSE,
    current_combined_rating INT,  -- 0-100
    rating_effective_date DATE,
    is_permanent_total BOOLEAN DEFAULT FALSE,  -- P&T status

    -- Individual Ratings (JSONB for flexibility)
    individual_ratings JSONB DEFAULT '[]',
    -- Example: [{"condition": "PTSD", "rating": 70, "effective_date": "2023-01-15"}]

    -- Dependents (for compensation calculation)
    has_spouse BOOLEAN DEFAULT FALSE,
    spouse_aid_attendance BOOLEAN DEFAULT FALSE,
    children_under_18 INT DEFAULT 0,
    children_18_23_in_school INT DEFAULT 0,
    dependent_parents INT DEFAULT 0,

    -- Representation
    has_vso BOOLEAN DEFAULT FALSE,
    vso_organization VARCHAR(100),  -- 'dav', 'vfw', 'american_legion', 'other'
    vso_representative_name VARCHAR(255),

    -- Profile completion tracking
    profile_completion_pct INT DEFAULT 0,
    onboarding_completed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_veteran_profiles_user ON veteran_profiles(user_id);
```

### Goldfin - PII Storage

```sql
-- Personal PII (encrypted)
CREATE TABLE veteran_pii (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,  -- references bluefin users.id

    -- All fields encrypted with user's key
    encrypted_ssn BYTEA,
    encrypted_dob BYTEA,
    encrypted_va_file_number BYTEA,
    encrypted_phone BYTEA,
    encrypted_address BYTEA,  -- JSON: {street, city, state, zip}

    encryption_key_id VARCHAR(100) NOT NULL,
    iv BYTEA NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit log for PII access
CREATE TABLE pii_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    field_accessed VARCHAR(50),  -- 'ssn', 'dob', 'address', etc.
    action VARCHAR(50),  -- 'view', 'update', 'delete'
    ip_address INET,
    accessed_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Profile API

```
# Get profile (combines bluefin + goldfin)
GET /api/v1/profile
Response: {
  "user": { "id", "email", "first_name", "last_name" },
  "service": { "branch", "dates", "mos", "rank", "discharge", "combat" },
  "va_status": { "has_rating", "combined_rating", "individual_ratings", "p_and_t" },
  "dependents": { "spouse", "children", "parents" },
  "representation": { "has_vso", "organization", "rep_name" },
  "pii": {
    "has_ssn": true,  // boolean only, not actual value
    "has_dob": true,
    "has_phone": true,
    "has_address": true
  },
  "completion_pct": 75
}

# Update service info (bluefin)
PUT /api/v1/profile/service
Body: { "branch", "start_date", "end_date", "mos", "rank", "discharge", "combat" }

# Update VA status (bluefin)
PUT /api/v1/profile/va-status
Body: { "has_rating", "combined_rating", "individual_ratings", "effective_date", "p_and_t" }

# Update dependents (bluefin)
PUT /api/v1/profile/dependents
Body: { "has_spouse", "spouse_aa", "children_under_18", "children_school", "parents" }

# Update representation (bluefin)
PUT /api/v1/profile/representation
Body: { "has_vso", "organization", "rep_name" }

# Update PII (goldfin - encrypted)
PUT /api/v1/profile/personal
Body: { "ssn", "dob", "va_file_number", "phone", "address" }
Note: Encrypted before storage, logged

# Get PII (requires re-auth, logged)
POST /api/v1/profile/personal/reveal
Body: { "fields": ["ssn", "dob"], "password": "..." }
Response: { "ssn": "123-45-6789", "dob": "1985-03-15" }
Note: Requires password confirmation, all access logged
```

## Frontend Pages

### Profile Page Layout

```
/dashboard/profile
│
├── Header
│   ├── Avatar / Photo upload
│   ├── Name (editable)
│   └── Profile completion bar (75%)
│
├── Service History Section
│   ├── Branch: [dropdown]
│   ├── Dates: [date pickers]
│   ├── MOS/Rate: [text input]
│   ├── Rank at discharge: [dropdown]
│   ├── Discharge type: [dropdown]
│   └── Combat veteran: [checkbox]
│
├── Current VA Status Section
│   ├── Do you have a VA rating? [yes/no toggle]
│   ├── If yes:
│   │   ├── Combined rating: [slider 0-100]
│   │   ├── Effective date: [date picker]
│   │   ├── P&T status: [checkbox]
│   │   └── Individual ratings: [add/remove list]
│   └── "Don't know your rating? Use our calculator"
│
├── Dependents Section
│   ├── Spouse: [yes/no]
│   │   └── If yes: Spouse needs A&A? [yes/no]
│   ├── Children under 18: [number input]
│   ├── Children 18-23 in school: [number input]
│   └── Dependent parents: [0/1/2 dropdown]
│
├── Personal Information Section (PII - goldfin)
│   ├── Info banner: "This info is encrypted and only you can access it"
│   ├── Date of Birth: [date picker]
│   ├── SSN: [masked input] ●●●-●●-6789
│   ├── VA File Number: [masked input]
│   ├── Phone: [phone input]
│   └── Address: [address form]
│
├── VSO Representation Section
│   ├── Do you have VSO representation? [yes/no]
│   └── If yes:
│       ├── Organization: [dropdown with common VSOs]
│       └── Representative name: [text input]
│
└── My Documents Section
    ├── DD-214: [upload or view existing]
    ├── VA Decision Letters: [list]
    └── "Manage all documents" link
```

### Profile Completion Widget

```tsx
<ProfileCompletion
  completed={75}
  missing={[
    "Add your service dates",
    "Upload your DD-214",
    "Enter your current VA rating"
  ]}
/>
```

### PII Field Component

```tsx
<PIIField
  label="Social Security Number"
  value={profile.pii.has_ssn ? "●●●-●●-" + lastFour : null}
  onReveal={async () => {
    // Requires password re-entry
    const password = await promptPassword();
    const revealed = await revealPII(['ssn'], password);
    return revealed.ssn;
  }}
  onUpdate={async (newValue) => {
    await updatePII({ ssn: newValue });
  }}
  encrypted={true}
  helpText="Optional. Used to auto-fill forms. Encrypted and only you can access."
/>
```

## Profile Onboarding Flow

For new users, guide them through profile setup:

```
Step 1: Welcome
├── "Let's set up your profile to personalize your experience"
└── [Get Started]

Step 2: Service History
├── Branch, dates, MOS, discharge
└── [Next] [Skip for now]

Step 3: Current VA Status
├── Do you have a rating?
├── If yes: combined rating, conditions
└── [Next] [Skip for now]

Step 4: Dependents
├── Quick form for spouse/children/parents
└── [Next] [Skip for now]

Step 5: Personal Info (Optional)
├── "Optional: Add your SSN and DOB to auto-fill forms"
├── Privacy assurance: "Encrypted, only you can access"
└── [Complete Setup] [Skip]

→ Redirect to dashboard with completion widget
```

## Auto-Population Features

Profile data auto-fills other features:

| Feature | Auto-populated From |
|---------|---------------------|
| Calculator | Dependents section |
| Claim Workbench | Service dates, current ratings |
| Personal Statement | Branch, MOS, service dates |
| Evidence Checklist | Combat status, conditions |
| Compensation lookup | Rating, dependents |

Example:
```tsx
// Calculator page
const { profile } = useProfile();

// Pre-fill dependents from profile
const defaultDependents = {
  has_spouse: profile.dependents.has_spouse,
  children_under_18: profile.dependents.children_under_18,
  // ...
};
```

## Security Considerations

### PII Access Controls

```python
@router.post("/profile/personal/reveal")
async def reveal_pii(
    request: RevealPIIRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(401, "Invalid password")

    # 2. Rate limit (max 5 reveals per hour)
    if await is_rate_limited(user.id, "pii_reveal"):
        raise HTTPException(429, "Too many requests")

    # 3. Fetch and decrypt from goldfin
    pii = await goldfin_client.get_pii(user.id, request.fields)

    # 4. Log access
    for field in request.fields:
        await goldfin_client.log_pii_access(
            user_id=user.id,
            field=field,
            action="view",
            ip=request.client.host
        )

    return pii
```

### Never Log Raw PII

```python
# BAD
logger.info(f"User updated SSN to {ssn}")

# GOOD
logger.info(f"User {user_id} updated SSN field")
```

## Implementation Phases

### Phase 1: Profile Structure (3 days)
- [ ] Create veteran_profiles table on bluefin
- [ ] Create veteran_pii table on goldfin
- [ ] Basic CRUD API endpoints
- [ ] Profile page UI with sections

### Phase 2: PII Integration (2 days)
- [ ] Encryption/decryption for PII fields
- [ ] Password-protected reveal flow
- [ ] Access logging
- [ ] Masked display component

### Phase 3: Auto-population (2 days)
- [ ] Calculator pre-fill from dependents
- [ ] Profile data in claim workbench
- [ ] Onboarding wizard

### Phase 4: Documents Link (1 day)
- [ ] DD-214 quick upload on profile
- [ ] Link to full documents section
- [ ] Profile completion tracking

## Success Criteria

- [ ] Veteran can save service history
- [ ] Veteran can save current VA rating
- [ ] Veteran can save dependents (auto-fills calculator)
- [ ] PII fields encrypted on goldfin
- [ ] PII reveal requires password
- [ ] All PII access logged
- [ ] Profile completion shows progress
- [ ] Onboarding guides new users

---

*Cherokee AI Federation - For the Seven Generations*
