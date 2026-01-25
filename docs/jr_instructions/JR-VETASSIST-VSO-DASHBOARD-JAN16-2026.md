# JR Instruction: VetAssist VSO/Organization Dashboard

## Metadata
```yaml
task_id: vetassist_vso_dashboard
priority: 2
assigned_to: VetAssist Jr.
target: backend + frontend
pilot_partner: Combat Veterans Motorcycle Association (CVMA)
estimated_effort: large
```

## Background

VetAssist is free for individual veterans. Revenue comes from organizations (VSOs, chapters, law firms) who want to help their members/clients navigate VA claims.

### Pilot Partner: CVMA
- **What**: Combat Veterans Motorcycle Association - brotherhood of combat vets who ride
- **Structure**: Chapters across all 50 states + international
- **Membership**: Full (combat vets), Supporter (non-combat military), Auxiliary (spouses)
- **Model**: Peer support - members helping members, not formal caseworkers
- **Website**: https://www.combatvet.us/
- **Internal Contact**: Darrell (TPM) is a member

## Pricing Tiers (from BRD)

| Tier | Price | Seats | Features |
|------|-------|-------|----------|
| **VSO Basic** | $49/mo | 5 | Chapter dashboard, basic analytics |
| **VSO Pro** | $149/mo | 25 | Full analytics, API, custom branding |
| **Enterprise** | $499/mo | Unlimited | White-label, case management, SLA |

## Requirements

### Phase 1: Organization Accounts (MVP for CVMA Pilot)

#### 1.1 Organization Registration
```
New tables:
- organizations (id, name, type, slug, logo_url, created_at)
- organization_members (org_id, user_id, role, invited_by, joined_at)
- organization_invites (id, org_id, email, role, token, expires_at)
```

**Organization Types:**
- `vso` - Veterans Service Organization (DAV, VFW)
- `chapter` - Local chapter (CVMA chapters)
- `law_firm` - VA claims attorneys
- `nonprofit` - Other veteran nonprofits

**Member Roles:**
- `owner` - Created the org, billing contact
- `admin` - Can invite/remove members, view all analytics
- `member` - Can use tools, contributes to org analytics

#### 1.2 Organization Dashboard

Create `/ganuda/vetassist/frontend/app/org/[slug]/dashboard/page.tsx`:

```
Organization Dashboard
├── Overview
│   ├── Total members
│   ├── Calculator uses this month
│   ├── Chat sessions this month
│   └── Top conditions calculated
├── Members
│   ├── Member list (name, role, last active)
│   ├── Invite new member (email)
│   └── Remove member
├── Analytics (VSO Pro+)
│   ├── Usage over time chart
│   ├── Most asked questions
│   └── Common conditions
└── Settings
    ├── Organization name/logo
    ├── Billing (Stripe)
    └── Custom branding (Pro+)
```

#### 1.3 Member Experience

When a user belongs to an org:
- Show org badge in header: "CVMA Chapter 42-1"
- Usage tracked to both user AND org
- Access to org-specific resources (if any)

### Phase 2: Analytics & Reporting

#### 2.1 Organization Analytics

Track per organization:
```python
class OrgAnalytics:
    org_id: UUID
    period: str  # "2026-01", "2026-W03"
    calculator_uses: int
    chat_sessions: int
    chat_messages: int
    unique_users: int
    top_conditions: List[str]  # ["PTSD", "Tinnitus", "Back"]
    avg_combined_rating: float
```

#### 2.2 CVMA-Specific Features

Since CVMA is peer-support (not caseworker) model:
- **"Share with Brother/Sister"** - Generate shareable calculator result link
- **Chapter leaderboard** - Which chapters are most active (opt-in)
- **Combat vet focus** - Highlight conditions common to combat vets (PTSD, TBI, hearing loss)

### Phase 3: Billing Integration

#### 3.1 Stripe Integration

```python
# /api/v1/billing/
POST /subscribe - Create subscription
POST /webhook - Stripe webhook handler
GET /portal - Redirect to Stripe customer portal
GET /usage - Current usage vs plan limits
```

#### 3.2 Plan Enforcement

```python
def check_org_limits(org_id: UUID) -> bool:
    org = get_org(org_id)
    if org.plan == "basic" and org.member_count > 5:
        raise PlanLimitExceeded("Basic plan limited to 5 seats")
    return True
```

## Database Schema

```sql
-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- vso, chapter, law_firm, nonprofit
    logo_url VARCHAR(500),
    website VARCHAR(500),
    plan VARCHAR(50) DEFAULT 'trial',  -- trial, basic, pro, enterprise
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organization membership
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',  -- owner, admin, member
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Pending invites
CREATE TABLE organization_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    token VARCHAR(100) UNIQUE NOT NULL,
    invited_by UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Organization analytics (aggregated)
CREATE TABLE organization_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    period VARCHAR(20) NOT NULL,  -- '2026-01' for monthly
    calculator_uses INT DEFAULT 0,
    chat_sessions INT DEFAULT 0,
    chat_messages INT DEFAULT 0,
    unique_users INT DEFAULT 0,
    top_conditions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, period)
);

-- Track which org a usage belongs to
ALTER TABLE chat_sessions ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE calculator_results ADD COLUMN organization_id UUID REFERENCES organizations(id);
```

## API Endpoints

```
# Organization management
POST   /api/v1/orgs                     - Create organization
GET    /api/v1/orgs/{slug}              - Get organization details
PUT    /api/v1/orgs/{slug}              - Update organization
DELETE /api/v1/orgs/{slug}              - Delete organization

# Membership
GET    /api/v1/orgs/{slug}/members      - List members
POST   /api/v1/orgs/{slug}/invite       - Send invite
DELETE /api/v1/orgs/{slug}/members/{id} - Remove member
POST   /api/v1/invites/{token}/accept   - Accept invite

# Analytics
GET    /api/v1/orgs/{slug}/analytics    - Get analytics
GET    /api/v1/orgs/{slug}/analytics/export - Export CSV

# Billing
POST   /api/v1/orgs/{slug}/subscribe    - Create subscription
GET    /api/v1/orgs/{slug}/billing      - Billing portal redirect
```

## Frontend Pages

```
/org/new                    - Create organization
/org/[slug]                 - Organization public page (if enabled)
/org/[slug]/dashboard       - Main dashboard (members only)
/org/[slug]/members         - Member management (admin+)
/org/[slug]/analytics       - Usage analytics (admin+)
/org/[slug]/settings        - Settings & billing (owner)
/invite/[token]             - Accept invite landing page
```

## CVMA Pilot Plan

### Week 1: Setup
- [ ] Create CVMA organization in database
- [ ] Darrell as owner
- [ ] Manual invite for 2-3 chapter members

### Week 2-4: Beta Testing
- [ ] Members use calculator and chat
- [ ] Gather feedback on org dashboard
- [ ] Track usage metrics

### Week 5+: Expand
- [ ] Invite more chapters
- [ ] Refine based on feedback
- [ ] Prepare for paid launch

## Success Criteria

- [ ] Organization can be created and managed
- [ ] Members can be invited via email
- [ ] Usage tracked per organization
- [ ] Basic analytics dashboard functional
- [ ] CVMA pilot active with 5+ members

## Notes for CVMA

Since CVMA is **peer support** not caseworker model:
1. Keep it simple - no case management complexity
2. Focus on **sharing** - brothers helping brothers
3. Chapter identity matters - show chapter affiliation proudly
4. Combat vet conditions - PTSD, TBI, hearing loss, MST prominently featured
5. Mobile-friendly - many will access on phones at meetups

---

*Cherokee AI Federation - For the Seven Generations*
*"Ride to support veterans. Use VetAssist to empower them."*
